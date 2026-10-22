"""
LungRay Multi-Task Baseline Training Script for Kaggle Cloud (kaggle/train_kaggle.py)
====================================================================================
Designed for Kaggle GPU environments (NVIDIA P100 / 2x T4).

- Resolves the concrete Kaggle dataset mounts (``lungray-nih-512``,
  ``lungray-covidx-512``, TB database) including nested
  ``/kaggle/input/datasets/<user>/<slug>`` layouts.
- Loads COVIDx CXR-4 from its official ``train.txt`` / ``test.txt`` manifests and
  creates a patient-stratified 10% validation split.
- Trains the DenseNet-121 3-Head network with the fixed 60:25:15 sampler and
  masked multi-task loss under PyTorch mixed precision.
"""
import argparse
import os
import sys
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import torch
from torch.utils.data import ConcatDataset, DataLoader

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.dataset import ChestXrayDataset
from src.data.ingestion import (
    audit_split_coverage,
    build_recursive_file_map,
    load_covid_dataframe,
    resolve_dataset_paths,
)
from src.data.sampler import WeightedMultiTaskBatchSampler
from src.data.transforms import get_train_transforms, get_val_transforms
from src.models.losses import MaskedMultiTaskLoss
from src.models.multi_task_net import MultiTaskChestXrayNet
from src.models.trainer import MultiTaskTrainer, multitask_collate_fn


def _select_column(df: pd.DataFrame, candidates: list) -> str:
    """Returns the first existing column from ``candidates``."""
    for column in candidates:
        if column in df.columns:
            return column
    raise KeyError(f"None of the candidate columns {candidates} exist in {list(df.columns)}")


def plot_and_save_curves(history_df: pd.DataFrame, output_path: str) -> None:
    """Renders publication-ready training loss and validation AUC curves."""
    if history_df.empty:
        print("[Plotting] Empty history; skipping curve export.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(
        history_df["epoch"], history_df["train_loss"], label="Train Loss (Total)", color="#1E88E5", lw=2
    )
    if "train_loss_a" in history_df:
        axes[0].plot(
            history_df["epoch"], history_df["train_loss_a"],
            label="Loss Head A (NIH)", ls="--", color="#43A047",
        )
    if "train_loss_b" in history_df:
        axes[0].plot(
            history_df["epoch"], history_df["train_loss_b"],
            label="Loss Head B (TB)", ls="--", color="#FB8C00",
        )
    if "train_loss_c" in history_df:
        axes[0].plot(
            history_df["epoch"], history_df["train_loss_c"],
            label="Loss Head C (COVIDx)", ls="--", color="#E53935",
        )
    axes[0].set_title("Training Loss across Heads", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(
        history_df["epoch"], history_df["val_combined_score"],
        label="Combined S_val", color="#8E24AA", lw=2.5,
    )
    if "val_auc_a" in history_df:
        axes[1].plot(
            history_df["epoch"], history_df["val_auc_a"],
            label="Macro AUC Head A", ls=":", color="#43A047",
        )
    if "val_auc_b" in history_df:
        axes[1].plot(
            history_df["epoch"], history_df["val_auc_b"],
            label="AUC Head B (TB)", ls=":", color="#FB8C00",
        )
    if "val_auc_c" in history_df:
        axes[1].plot(
            history_df["epoch"], history_df["val_auc_c"],
            label="AUC Head C (COVIDx)", ls=":", color="#E53935",
        )
    axes[1].set_title("Multi-Task Validation AUC Performance", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("ROC-AUC")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plotting] Training curves exported to {output_path}")


def build_dataloaders(
    paths: Dict[str, object], batch_size: int, allow_missing: bool
) -> Dict[str, DataLoader]:
    """Builds the unified train loader and one validation loader per head."""
    required_splits = [paths["nih_split_csv"], paths["tb_split_csv"]]
    for split_path in required_splits:
        if not split_path or not os.path.exists(str(split_path)):
            raise FileNotFoundError(f"[ERROR] Required split CSV not found: {split_path}")

    df_nih = pd.read_csv(str(paths["nih_split_csv"]))
    df_tb = pd.read_csv(str(paths["tb_split_csv"]))
    df_covid = load_covid_dataframe(
        str(paths["covid_dir"]),
        split_dirs=[str(paths["split_dir"]), os.path.join(project_root, "dataset", "splits")],
    )

    nih_col = _select_column(df_nih, ["Image Index", "filename", "image_id"])
    tb_col = _select_column(df_tb, ["filename", "Image Index", "image_id"])
    covid_col = _select_column(df_covid, ["filename", "Image Index", "image_id"])
    nih_label_col = _select_column(df_nih, ["Finding Labels", "label"])
    tb_label_col = _select_column(df_tb, ["label", "Finding Labels"])
    covid_label_col = _select_column(df_covid, ["label", "Finding Labels"])

    file_maps = {
        "NIH": build_recursive_file_map(str(paths["nih_dir"])),
        "COVIDx": build_recursive_file_map(str(paths["covid_dir"])),
        "TB": build_recursive_file_map(str(paths["tb_dir"])),
    }
    for name, df in (("NIH", df_nih), ("COVIDx", df_covid), ("TB", df_tb)):
        _, total, pct = audit_split_coverage(df, file_maps[name], name)
        if not allow_missing and total > 0 and pct < 100.0:
            raise AssertionError(f"[CRITICAL] {name} split coverage is {pct:.2f}% (< 100.00%).")

    train_nih = df_nih[df_nih["split"] == "train"].reset_index(drop=True)
    val_nih = df_nih[df_nih["split"] == "val"].reset_index(drop=True)
    train_covid = df_covid[df_covid["split"] == "train"].reset_index(drop=True)
    val_covid = df_covid[df_covid["split"] == "val"].reset_index(drop=True)
    train_tb = df_tb[df_tb["split"] == "train"].reset_index(drop=True)
    val_tb = df_tb[df_tb["split"] == "val"].reset_index(drop=True)

    train_transforms = get_train_transforms(image_size=512)
    val_transforms = get_val_transforms(image_size=512)
    ignore_missing = bool(allow_missing)

    ds_train_nih = ChestXrayDataset(
        df=train_nih,
        image_dir=str(paths["nih_dir"]),
        image_col=nih_col,
        label_col=nih_label_col,
        task_id=0,
        num_classes=14,
        transforms=train_transforms,
        pre_resized=bool(paths["nih_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["NIH"],
    )
    ds_train_covid = ChestXrayDataset(
        df=train_covid,
        image_dir=str(paths["covid_dir"]),
        image_col=covid_col,
        label_col=covid_label_col,
        task_id=2,
        num_classes=1,
        transforms=train_transforms,
        pre_resized=bool(paths["covid_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["COVIDx"],
    )
    ds_train_tb = ChestXrayDataset(
        df=train_tb,
        image_dir=str(paths["tb_dir"]),
        image_col=tb_col,
        label_col=tb_label_col,
        task_id=1,
        num_classes=1,
        transforms=train_transforms,
        pre_resized=bool(paths["tb_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["TB"],
    )

    concat_train = ConcatDataset([ds_train_nih, ds_train_covid, ds_train_tb])
    offset_covid = len(ds_train_nih)
    offset_tb = offset_covid + len(ds_train_covid)
    nih_indices = list(range(0, offset_covid))
    covid_indices = list(range(offset_covid, offset_tb))
    tb_indices = list(range(offset_tb, len(concat_train)))

    batch_sampler = WeightedMultiTaskBatchSampler(
        nih_indices=nih_indices,
        covid_indices=covid_indices,
        tb_indices=tb_indices,
        batch_size=batch_size,
        ratios=(0.60, 0.25, 0.15),
        shuffle=True,
    )

    num_workers = 4 if os.name != "nt" else 0
    train_loader = DataLoader(
        concat_train,
        batch_sampler=batch_sampler,
        collate_fn=multitask_collate_fn,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    ds_val_nih = ChestXrayDataset(
        df=val_nih,
        image_dir=str(paths["nih_dir"]),
        image_col=nih_col,
        label_col=nih_label_col,
        task_id=0,
        num_classes=14,
        transforms=val_transforms,
        pre_resized=bool(paths["nih_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["NIH"],
    )
    ds_val_covid = ChestXrayDataset(
        df=val_covid,
        image_dir=str(paths["covid_dir"]),
        image_col=covid_col,
        label_col=covid_label_col,
        task_id=2,
        num_classes=1,
        transforms=val_transforms,
        pre_resized=bool(paths["covid_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["COVIDx"],
    )
    ds_val_tb = ChestXrayDataset(
        df=val_tb,
        image_dir=str(paths["tb_dir"]),
        image_col=tb_col,
        label_col=tb_label_col,
        task_id=1,
        num_classes=1,
        transforms=val_transforms,
        pre_resized=bool(paths["tb_pre_resized"]),
        ignore_missing=ignore_missing,
        file_map=file_maps["TB"],
    )

    val_loader_a = DataLoader(
        ds_val_nih, batch_size=batch_size, shuffle=False, collate_fn=multitask_collate_fn
    )
    val_loader_b = DataLoader(
        ds_val_tb, batch_size=batch_size, shuffle=False, collate_fn=multitask_collate_fn
    )
    val_loader_c = DataLoader(
        ds_val_covid, batch_size=batch_size, shuffle=False, collate_fn=multitask_collate_fn
    )

    if not allow_missing:
        for loader_name, loader in (
            ("val_loader_a", val_loader_a),
            ("val_loader_b", val_loader_b),
            ("val_loader_c", val_loader_c),
        ):
            if len(loader) == 0:
                raise AssertionError(f"[CRITICAL] {loader_name} has zero batches.")

    print(
        f"[DataLoaders] Train={len(train_loader)} batches | "
        f"Val NIH={len(val_loader_a)}, TB={len(val_loader_b)}, COVIDx={len(val_loader_c)} batches"
    )
    return {
        "train_loader": train_loader,
        "val_loader_a": val_loader_a,
        "val_loader_b": val_loader_b,
        "val_loader_c": val_loader_c,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LungRay Multi-Task Baseline Training on Kaggle GPU")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size per step (16 for 512x512)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Peak learning rate for AdamW")
    parser.add_argument("--backbone", type=str, default="densenet121", help="Encoder backbone architecture")
    parser.add_argument(
        "--max-batches", type=int, default=1200,
        help="Cap batches per epoch for Kaggle session limits (0 = full epoch)",
    )
    parser.add_argument(
        "--allow-missing", action="store_true", help="Local dry-run: silently skip missing images"
    )
    args = parser.parse_args()

    paths = resolve_dataset_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[Device] Using compute hardware: {device} ({gpu_name})")

    loaders = build_dataloaders(paths, batch_size=args.batch_size, allow_missing=args.allow_missing)

    model = MultiTaskChestXrayNet(backbone_name=args.backbone, pretrained=True, img_size=512, num_classes_c=1)

    pos_counts = [11559, 2776, 13317, 19894, 5782, 6331, 1431, 5302, 4667, 2303, 2516, 1686, 3385, 227]
    total_nih = 112120
    pos_weights = torch.tensor(
        [min(50.0, (total_nih - count) / max(1, count)) for count in pos_counts],
        dtype=torch.float32,
    )
    criterion = MaskedMultiTaskLoss(
        weights={"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        head_a_criterion="bce",
        head_c_criterion="bce",
        pos_weight_a=pos_weights,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, args.epochs), eta_min=1e-6)

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
        log_interval=50,
    )

    print(f"\n[MultiTaskTrainer] Launching {args.epochs} Epochs on {device}...")
    print(
        f"[MultiTaskTrainer] Batches/epoch: "
        f"{args.max_batches if args.max_batches > 0 else len(loaders['train_loader']):,d} "
        f"of {len(loaders['train_loader']):,d} available."
    )
    history_df = trainer.fit(
        train_loader=loaders["train_loader"],
        val_loader_a=loaders["val_loader_a"],
        val_loader_b=loaders["val_loader_b"],
        val_loader_c=loaders["val_loader_c"],
        epochs=args.epochs,
        save_name="checkpoint_baseline_multitask.pth",
    )

    curve_path = os.path.join(str(paths["results_dir"]), "baseline_training_curves.png")
    plot_and_save_curves(history_df, curve_path)
    print("[Done] Multi-Task Baseline Training pipeline executed successfully!")


if __name__ == "__main__":
    main()
