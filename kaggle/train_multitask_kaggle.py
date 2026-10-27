"""
LungRay Optimized Multi-Task Training Script for Kaggle GPU
===========================================================
``kaggle/train_multitask_kaggle.py`` (TASK-013)

Production training entrypoint for the 3-Head CADx network with:
- Clinically tuned head criteria: class-weighted Focal Loss (default) or
  Asymmetric Loss for Head A, BCE for Head B, Focal/ASL/BCE for Head C.
- AMP, Cosine Annealing, early stopping, atomic checkpoints, and resume support
  via :class:`src.models.trainer.MultiTaskTrainer`.
- Post-training decision-threshold calibration on the validation splits using
  Youden's J statistic (per-NIH-pathology tau_c, tau_B for TB, tau_C for COVID).
- Dataset construction, 60:25:15 balanced sampler, and curve plotting are reused
  from ``kaggle/train_kaggle.py`` to keep a single source of truth.

Usage:
    python kaggle/train_multitask_kaggle.py --head-a-criterion focal
    python kaggle/train_multitask_kaggle.py --head-a-criterion asl --resume
"""
import argparse
import os
import sys
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import torch

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
for path in (project_root, current_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

import train_kaggle  # noqa: E402  (shared dataloader/plotting pipeline)

if not hasattr(train_kaggle, "cv2"):
    # train_kaggle's DataLoader worker_init references a module-level cv2 that it
    # never imports; inject it so Kaggle Linux workers do not crash.
    train_kaggle.cv2 = cv2

from src.data.ingestion import resolve_dataset_paths  # noqa: E402
from src.models.losses import MaskedMultiTaskLoss  # noqa: E402
from src.models.multi_task_net import MultiTaskChestXrayNet  # noqa: E402
from src.models.trainer import MultiTaskTrainer  # noqa: E402
from src.utils.threshold_tuning import (  # noqa: E402
    NIH_PATHOLOGY_NAMES,
    find_best_threshold_youden,
    save_thresholds_json,
    tune_multilabel_thresholds,
)


NIH_POSITIVE_COUNTS = [
    11559, 2776, 13317, 19894, 5782, 6331, 1431,
    5302, 4667, 2303, 2516, 1686, 3385, 227,
]
NIH_TOTAL_IMAGES = 112120


def build_pos_weights(clamp: float = 50.0) -> torch.Tensor:
    """Class-balanced positive weights for the 14 NIH pathologies.

    ``pos_weight_c = (N_neg / N_pos)`` clipped at ``clamp`` so ultra-rare
    findings (Hernia: 227/112120) do not destabilize early optimization.
    """
    counts = torch.tensor(NIH_POSITIVE_COUNTS, dtype=torch.float32).clamp(min=1.0)
    weights = (float(NIH_TOTAL_IMAGES) - counts) / counts
    return weights.clamp(max=float(clamp))


def build_criterion(args: argparse.Namespace) -> MaskedMultiTaskLoss:
    """Builds the masked multi-task criterion for the requested strategies."""
    kwargs = {
        "weights": {"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        "head_a_criterion": args.head_a_criterion,
        "focal_gamma": args.focal_gamma,
        "focal_alpha": args.focal_alpha,
        "asl_gamma_neg": args.asl_gamma_neg,
        "asl_gamma_pos": args.asl_gamma_pos,
        "asl_clip": args.asl_clip,
        "head_c_criterion": args.head_c_criterion,
    }

    if args.head_a_criterion == "bce":
        kwargs["pos_weight_a"] = build_pos_weights(args.pos_weight_clamp)
    elif args.head_a_criterion == "focal":
        kwargs["focal_pos_weight_a"] = build_pos_weights(args.pos_weight_clamp)

    return MaskedMultiTaskLoss(**kwargs)


@torch.no_grad()
def collect_probabilities(
    model: MultiTaskChestXrayNet,
    loader,
    head_name: str,
    device: torch.device,
    max_batches: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Collects (probabilities, labels) for one head from a single-task loader."""
    model.eval()
    all_probs = []
    all_labels = []

    for batch_idx, batch in enumerate(loader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        images = batch["images"].to(device)
        probs = model.predict(images)[head_name].float().cpu().numpy()
        labels = batch["labels"]
        if isinstance(labels, list):
            labels = torch.stack(labels).cpu().numpy()
        else:
            labels = labels.cpu().numpy()
        all_probs.append(probs)
        all_labels.append(labels)

    if not all_probs:
        return np.empty((0,), dtype=np.float32), np.empty((0,), dtype=np.float32)
    return np.concatenate(all_probs, axis=0), np.concatenate(all_labels, axis=0)


def calibrate_thresholds(
    model: MultiTaskChestXrayNet,
    loaders: Dict[str, object],
    device: torch.device,
    max_batches: Optional[int] = None,
) -> Dict[str, object]:
    """Derives clinical decision thresholds with Youden's J statistic."""
    thresholds: Dict[str, object] = {
        "version": "TASK-013",
        "default_fallback_threshold": 0.50,
    }

    probs_a, labels_a = collect_probabilities(
        model, loaders["val_loader_a"], "head_a", device, max_batches
    )
    if probs_a.size > 0:
        thresholds["head_a_nih_14"] = tune_multilabel_thresholds(
            labels_a,
            probs_a,
            class_names=NIH_PATHOLOGY_NAMES,
            method="youden",
        )

    binary_specs = [
        ("val_loader_b", "head_b", "head_b_tb", "Tuberculosis"),
        ("val_loader_c", "head_c", "head_c_covid", "COVID-19"),
    ]
    for loader_key, head_name, output_key, positive_class in binary_specs:
        probs, labels = collect_probabilities(
            model, loaders[loader_key], head_name, device, max_batches
        )
        if probs.size == 0:
            continue
        best_threshold, best_j = find_best_threshold_youden(
            labels.ravel(), probs.ravel()
        )
        thresholds[output_key] = {
            "threshold": round(float(best_threshold), 4),
            "youden_j": round(float(best_j), 4),
            "positive_class": positive_class,
        }

    return thresholds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LungRay Optimized Multi-Task Training on Kaggle GPU"
    )
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--backbone", type=str, default="densenet121")
    parser.add_argument(
        "--head-norm",
        type=str,
        default="layernorm",
        choices=["layernorm", "batchnorm", "none"],
    )
    parser.add_argument(
        "--head-a-criterion",
        type=str,
        default="focal",
        choices=["bce", "focal", "asl"],
    )
    parser.add_argument(
        "--head-c-criterion",
        type=str,
        default="focal",
        choices=["bce", "focal", "asl"],
    )
    parser.add_argument("--focal-alpha", type=float, default=0.25)
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--asl-gamma-neg", type=float, default=4.0)
    parser.add_argument("--asl-gamma-pos", type=float, default=1.0)
    parser.add_argument("--asl-clip", type=float, default=0.05)
    parser.add_argument(
        "--pos-weight-clamp",
        type=float,
        default=50.0,
        help="Upper bound for per-class NIH positive weights",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=600,
        help="Cap training batches per epoch for Kaggle limits (0 = full epoch)",
    )
    parser.add_argument(
        "--max-val-batches",
        type=int,
        default=120,
        help="Cap validation batches per head for monitoring (0 = full)",
    )
    parser.add_argument(
        "--save-name",
        type=str,
        default="checkpoint_multitask_optimized.pth",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--no-calibrate", action="store_true")
    parser.add_argument(
        "--thresholds-out",
        type=str,
        default=None,
        help="Defaults to <project_root>/configs/optimal_thresholds.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    paths = resolve_dataset_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[Device] Using compute hardware: {device} ({gpu_name})")

    loaders = train_kaggle.build_dataloaders(
        paths, batch_size=args.batch_size, allow_missing=args.allow_missing
    )

    model = MultiTaskChestXrayNet(
        backbone_name=args.backbone,
        pretrained=True,
        img_size=512,
        num_classes_c=1,
        head_norm=args.head_norm,
    )
    criterion = build_criterion(args)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max(1, args.epochs), eta_min=1e-6
    )

    trainer = MultiTaskTrainer(
        model=model,
        criterion=criterion,
        optimizer=optimizer,
        lr_scheduler=scheduler,
        device=device,
        mixed_precision=True,
        early_stopping_patience=5,
        checkpoint_dir=str(paths["output_dir"]),
        results_dir=str(paths["results_dir"]),
        max_batches_per_epoch=args.max_batches if args.max_batches > 0 else None,
        max_val_batches_per_head=(
            args.max_val_batches if args.max_val_batches > 0 else None
        ),
        log_interval=50,
    )

    print(
        f"[Criterion] Head A={args.head_a_criterion} | Head B=bce | "
        f"Head C={args.head_c_criterion} | head_norm={args.head_norm}"
    )
    print(f"\n[MultiTaskTrainer] Launching {args.epochs} epochs on {device}...")

    history_df = trainer.fit(
        train_loader=loaders["train_loader"],
        val_loader_a=loaders["val_loader_a"],
        val_loader_b=loaders["val_loader_b"],
        val_loader_c=loaders["val_loader_c"],
        epochs=args.epochs,
        save_name=args.save_name,
        resume_from=(
            os.path.join(str(paths["output_dir"]), "last_model.pth")
            if args.resume
            else None
        ),
    )

    best_path = os.path.join(str(paths["output_dir"]), args.save_name)
    if os.path.isfile(best_path):
        checkpoint = torch.load(best_path, map_location=device, weights_only=False)
        state = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state)
        print(f"[Calibration] Loaded best checkpoint from {best_path}")

    train_kaggle.plot_and_save_curves(
        history_df,
        os.path.join(str(paths["results_dir"]), "multitask_training_curves.png"),
    )

    if not args.no_calibrate:
        thresholds = calibrate_thresholds(
            model,
            loaders,
            device,
            max_batches=(
                args.max_val_batches if args.max_val_batches > 0 else None
            ),
        )
        thresholds_out = args.thresholds_out or os.path.join(
            project_root, "configs", "optimal_thresholds.json"
        )
        save_thresholds_json(thresholds, thresholds_out)
        print(f"[Calibration] Optimal thresholds saved to {thresholds_out}")

    print("[Done] Optimized Multi-Task Training pipeline executed successfully!")


if __name__ == "__main__":
    main()
