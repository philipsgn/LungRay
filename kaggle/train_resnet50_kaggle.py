#!/usr/bin/env python3
"""
kaggle/train_resnet50_kaggle.py - ResNet-50 Multi-Task Training Script for Kaggle GPU
======================================================================================
Trains the ResNet-50 shared encoder for the LungRay Triple-Backbone Ensemble:
- Backbone: ResNet-50 (pretrained on ImageNet, 2048-dim feature representation).
- Multi-Task Head Isolation: Parameter-free LayerNorm feature projection.
- Loss Engine: Asymmetric Loss (ASL: gamma_neg=4, gamma_pos=1, m=0.05) on Head A;
  Binary Cross-Entropy on Head B (TB) and Head C (COVIDx).
- Batch Sampling: WeightedMultiTaskBatchSampler (60% NIH : 25% COVIDx : 15% TB).
- Optimization: CosineAnnealingLR, Automatic Mixed Precision (AMP FP16), AdamW.
- Output Checkpoint: best_resnet50.pth.

Usage on Kaggle:
    python kaggle/train_resnet50_kaggle.py --epochs 15 --batch-size 16 --lr 1e-4
"""
import argparse
import os
import sys

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
for p in (project_root, current_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

import cv2
import torch
import train_kaggle

if not hasattr(train_kaggle, "cv2"):
    train_kaggle.cv2 = cv2

from src.data.ingestion import resolve_dataset_paths
from src.models.losses import MaskedMultiTaskLoss
from src.models.multi_task_net import MultiTaskChestXrayNet
from src.models.trainer import MultiTaskTrainer
from src.utils.threshold_tuning import save_thresholds_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LungRay ResNet-50 Multi-Task Training on Kaggle")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size per forward pass (20 splits into exact 12:5:3 ratio)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Peak AdamW learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay for regularization")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--backbone", type=str, default="resnet50", help="Encoder backbone architecture")
    parser.add_argument("--head-a-criterion", type=str, default="asl", choices=["bce", "focal", "asl"])
    parser.add_argument("--head-c-criterion", type=str, default="bce", choices=["bce", "focal", "asl"])
    parser.add_argument("--asl-gamma-neg", type=float, default=4.0)
    parser.add_argument("--asl-gamma-pos", type=float, default=1.0)
    parser.add_argument("--asl-clip", type=float, default=0.05)
    parser.add_argument("--max-batches", type=int, default=0, help="Max train batches per epoch (0 = full)")
    parser.add_argument("--max-val-batches", type=int, default=0, help="Max val batches per head (0 = full)")
    parser.add_argument("--save-name", type=str, default="best_resnet50.pth")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--no-calibrate", action="store_true")
    return parser.parse_args()


def set_seed(seed: int = 42) -> None:
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    print("=" * 65, flush=True)
    print(" LUNGRAY: RESNET-50 MULTI-TASK TRAINING (KAGGLE GPU)", flush=True)
    print("=" * 65, flush=True)
    print(f"[*] Backbone: {args.backbone.upper()} | Criterion A: {args.head_a_criterion.upper()} | Epochs: {args.epochs} | Seed: {args.seed}", flush=True)

    paths = resolve_dataset_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[*] Compute Device: {device} ({gpu_name})", flush=True)

    loaders = train_kaggle.build_dataloaders(
        paths, batch_size=args.batch_size, allow_missing=args.allow_missing
    )

    print(f"[*] Building MultiTaskChestXrayNet with {args.backbone}...", flush=True)
    model = MultiTaskChestXrayNet(
        backbone_name=args.backbone,
        pretrained=True,
        head_norm="layernorm",
        dropout_rate=0.2,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[OK] ResNet-50 instantiated: {total_params:,} total parameters ({trainable_params:,} trainable)", flush=True)

    criterion = MaskedMultiTaskLoss(
        weights={"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        head_a_criterion=args.head_a_criterion,
        asl_gamma_neg=args.asl_gamma_neg,
        asl_gamma_pos=args.asl_gamma_pos,
        asl_clip=args.asl_clip,
        head_c_criterion=args.head_c_criterion,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
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

    resume_path = None
    if args.resume:
        candidates = [
            os.path.join(str(paths["output_dir"]), "last_resnet50.pth"),
            os.path.join(str(paths["output_dir"]), "last_model.pth"),
        ]
        resume_path = next((p for p in candidates if os.path.isfile(p)), None)
        if resume_path:
            print(f"[*] Resuming ResNet-50 training from {resume_path}", flush=True)
        else:
            print("[!] Warning: --resume requested but no previous checkpoint found. Starting from scratch.", flush=True)

    print(f"\n[*] Starting ResNet-50 Multi-Task Training Loop ({args.epochs} epochs)...", flush=True)
    history_df = trainer.fit(
        train_loader=loaders["train_loader"],
        val_loader_a=loaders["val_loader_a"],
        val_loader_b=loaders["val_loader_b"],
        val_loader_c=loaders["val_loader_c"],
        epochs=args.epochs,
        save_name=args.save_name,
        resume_from=resume_path,
    )

    # Sync last_model.pth to last_resnet50.pth for reliable resume tracking
    last_model_src = os.path.join(str(paths["output_dir"]), "last_model.pth")
    last_resnet_dst = os.path.join(str(paths["output_dir"]), "last_resnet50.pth")
    if os.path.isfile(last_model_src):
        import shutil
        shutil.copy2(last_model_src, last_resnet_dst)
        print(f"[OK] Checkpoint resume artifact synced to {last_resnet_dst}", flush=True)

    best_path = os.path.join(str(paths["output_dir"]), args.save_name)
    if os.path.isfile(best_path):
        checkpoint = torch.load(best_path, map_location=device, weights_only=False)
        state = checkpoint.get("model_state_dict", checkpoint)
        model.load_state_dict(state)
        print(f"[OK] Reloaded best ResNet-50 weights from {best_path}", flush=True)

    plot_path = os.path.join(str(paths["results_dir"]), "resnet50_training_curves.png")
    train_kaggle.plot_and_save_curves(history_df, plot_path)
    print(f"[OK] Training curves exported to {plot_path}", flush=True)

    if not args.no_calibrate:
        print("[*] Calibrating Youden J Decision Thresholds for ResNet-50...", flush=True)
        thresholds = train_kaggle.calibrate_thresholds(
            model,
            loaders,
            device,
            max_batches=(
                args.max_val_batches if args.max_val_batches > 0 else None
            ),
        )
        thresholds_out = os.path.join(project_root, "configs", "optimal_thresholds_resnet50.json")
        save_thresholds_json(thresholds, thresholds_out)
        print(f"[OK] ResNet-50 optimal thresholds saved to {thresholds_out}", flush=True)
        # Also copy to output_dir so it sits directly in /kaggle/working/
        thresholds_working = os.path.join(str(paths["output_dir"]), "optimal_thresholds_resnet50.json")
        save_thresholds_json(thresholds, thresholds_working)
        print(f"[OK] Optimal thresholds replicated to output directory: {thresholds_working}", flush=True)

    print("\n[SUCCESS] ResNet-50 Multi-Task Training pipeline completed successfully!", flush=True)


if __name__ == "__main__":
    main()
