"""
LungRay Multi-Task Baseline Training Script for Kaggle Cloud (kaggle/train_kaggle.py)
====================================================================================
Designed for Kaggle GPU environments (NVIDIA P100 / 2x T4).
Automatically discovers Kaggle input mounts or local datasets, configures
the 60:25:15 Multi-Task Batch Sampler, trains DenseNet-121 3-Head CADx network,
and exports checkpoint and metrics artifacts.
"""
import os
import sys
import argparse
from typing import Dict, Tuple
import matplotlib.pyplot as plt
import pandas as pd
import torch
from torch.utils.data import DataLoader, ConcatDataset

# Add project root to sys.path if running as script
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.dataset import ChestXrayDataset
from src.data.sampler import WeightedMultiTaskBatchSampler
from src.data.transforms import get_train_transforms, get_val_transforms
from src.models.multi_task_net import MultiTaskChestXrayNet
from src.models.losses import MaskedMultiTaskLoss
from src.models.trainer import MultiTaskTrainer, multitask_collate_fn


def resolve_dataset_paths() -> Dict[str, str]:
    """
    Auto-detects dataset paths between Kaggle environment and local workspace.
    """
    kaggle_base = "/kaggle/input"
    is_kaggle = os.path.exists(kaggle_base)

    if is_kaggle:
        print("[Kaggle Environment Detected] Searching for mounted datasets...")
        # Adapt common Kaggle dataset mount names
        nih_candidates = [
            os.path.join(kaggle_base, "data-nih-chestxray14"),
            os.path.join(kaggle_base, "nih-chest-xrays"),
            os.path.join(kaggle_base, "data"),
        ]
        covid_candidates = [
            os.path.join(kaggle_base, "covidx-cxr2"),
            os.path.join(kaggle_base, "covid19-radiography-database"),
            os.path.join(kaggle_base, "covid19-radiography-dataset"),
        ]
        tb_candidates = [
            os.path.join(kaggle_base, "tuberculosis-tb-chest-xray-dataset"),
            os.path.join(kaggle_base, "tb-chest-xray"),
        ]

        nih_path = next((p for p in nih_candidates if os.path.exists(p)), "dataset/nih_chestxray14")
        covid_path = next((p for p in covid_candidates if os.path.exists(p)), "dataset/covid19_radiography")
        tb_path = next((p for p in tb_candidates if os.path.exists(p)), "dataset/tb_chestxray")
        output_dir = "/kaggle/working"
    else:
        print("[Local Environment Detected] Using workspace relative paths...")
        nih_path = "dataset/nih_chestxray14"
        covid_path = "dataset/covidx_cxr4" if os.path.exists("dataset/covidx_cxr4") else "dataset/covid19_radiography"
        tb_path = "dataset/tb_chestxray"
        output_dir = "checkpoints"

    return {
        "nih_dir": nih_path,
        "covid_dir": covid_path,
        "tb_dir": tb_path,
        "output_dir": output_dir,
    }


def plot_and_save_curves(history_df: pd.DataFrame, output_path: str):
    """
    Renders clean, publication-ready training loss and validation AUC curves.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Loss subplot
    axes[0].plot(history_df["epoch"], history_df["train_loss"], label="Train Loss (Total)", color="#1E88E5", lw=2)
    if "train_loss_a" in history_df:
        axes[0].plot(history_df["epoch"], history_df["train_loss_a"], label="Loss Head A (NIH)", ls="--", color="#43A047")
    if "train_loss_b" in history_df:
        axes[0].plot(history_df["epoch"], history_df["train_loss_b"], label="Loss Head B (TB)", ls="--", color="#FB8C00")
    if "train_loss_c" in history_df:
        axes[0].plot(history_df["epoch"], history_df["train_loss_c"], label="Loss Head C (COVID)", ls="--", color="#E53935")
    axes[0].set_title("Training Loss across Heads", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Validation Combined Score subplot
    axes[1].plot(history_df["epoch"], history_df["val_combined_score"], label="Combined S_val", color="#8E24AA", lw=2.5)
    if "val_auc_a" in history_df:
        axes[1].plot(history_df["epoch"], history_df["val_auc_a"], label="Macro AUC Head A", ls=":", color="#43A047")
    if "val_auc_b" in history_df:
        axes[1].plot(history_df["epoch"], history_df["val_auc_b"], label="AUC Head B (TB)", ls=":", color="#FB8C00")
    if "val_auc_c" in history_df:
        axes[1].plot(history_df["epoch"], history_df["val_auc_c"], label="Macro AUC Head C", ls=":", color="#E53935")
    axes[1].set_title("Multi-Task Validation AUC Performance", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("ROC-AUC")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Plotting] Training curves exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="LungRay Multi-Task Baseline Training on Kaggle GPU")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size per step (16 for 512x512)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Peak learning rate for AdamW")
    parser.add_argument("--backbone", type=str, default="densenet121", help="Encoder backbone architecture")
    args = parser.parse_args()

    paths = resolve_dataset_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Device] Using compute hardware: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    # Load Splits
    split_dir = "dataset/splits"
    nih_split_csv = os.path.join(split_dir, "patient_splits.csv")
    covid_split_csv = os.path.join(split_dir, "covid_splits.csv")
    tb_split_csv = os.path.join(split_dir, "tb_splits.csv")

    assert os.path.exists(nih_split_csv), f"Missing split file: {nih_split_csv}"
    assert os.path.exists(covid_split_csv), f"Missing split file: {covid_split_csv}"
    assert os.path.exists(tb_split_csv), f"Missing split file: {tb_split_csv}"

    df_nih = pd.read_csv(nih_split_csv)
    df_covid = pd.read_csv(covid_split_csv)
    df_tb = pd.read_csv(tb_split_csv)

    # Filter train & val sets
    train_nih = df_nih[df_nih["split"] == "train"].reset_index(drop=True)
    val_nih = df_nih[df_nih["split"] == "val"].reset_index(drop=True)

    train_covid = df_covid[df_covid["split"] == "train"].reset_index(drop=True)
    val_covid = df_covid[df_covid["split"] == "val"].reset_index(drop=True)

    train_tb = df_tb[df_tb["split"] == "train"].reset_index(drop=True)
    val_tb = df_tb[df_tb["split"] == "val"].reset_index(drop=True)

    train_transforms = get_train_transforms(image_size=512)
    val_transforms = get_val_transforms(image_size=512)

    # Build Training Datasets
    ds_train_nih = ChestXrayDataset(train_nih, paths["nih_dir"], "Finding Labels", 0, 14, train_transforms, ignore_missing=True)
    ds_train_covid = ChestXrayDataset(train_covid, paths["covid_dir"], "label", 2, 3, train_transforms, ignore_missing=True)
    ds_train_tb = ChestXrayDataset(train_tb, paths["tb_dir"], "label", 1, 1, train_transforms, ignore_missing=True)

    concat_train = ConcatDataset([ds_train_nih, ds_train_covid, ds_train_tb])

    # Index offsets for Sampler
    offset_nih = 0
    offset_covid = len(ds_train_nih)
    offset_tb = offset_covid + len(ds_train_covid)

    nih_indices = list(range(offset_nih, offset_covid))
    covid_indices = list(range(offset_covid, offset_tb))
    tb_indices = list(range(offset_tb, len(concat_train)))

    # Weighted Sampler (60% NIH, 25% COVID, 15% TB)
    batch_sampler = WeightedMultiTaskBatchSampler(
        nih_indices=nih_indices,
        covid_indices=covid_indices,
        tb_indices=tb_indices,
        batch_size=args.batch_size,
        ratios=(0.60, 0.25, 0.15),
        shuffle=True,
    )

    train_loader = DataLoader(
        concat_train,
        batch_sampler=batch_sampler,
        collate_fn=multitask_collate_fn,
        num_workers=2 if os.name != "nt" else 0,
        pin_memory=torch.cuda.is_available(),
    )

    # Validation DataLoaders per head
    ds_val_nih = ChestXrayDataset(val_nih, paths["nih_dir"], "Finding Labels", 0, 14, val_transforms, ignore_missing=True)
    ds_val_covid = ChestXrayDataset(val_covid, paths["covid_dir"], "label", 2, 3, val_transforms, ignore_missing=True)
    ds_val_tb = ChestXrayDataset(val_tb, paths["tb_dir"], "label", 1, 1, val_transforms, ignore_missing=True)

    val_loader_a = DataLoader(ds_val_nih, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)
    val_loader_b = DataLoader(ds_val_tb, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)
    val_loader_c = DataLoader(ds_val_covid, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)

    # Model & Loss Initialization
    model = MultiTaskChestXrayNet(backbone_name=args.backbone, pretrained=True, img_size=512, num_classes_c=3)
    criterion = MaskedMultiTaskLoss(
        weights={"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        head_a_criterion="bce",
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)

    trainer = MultiTaskTrainer(
        model=model,
        criterion=criterion,
        optimizer=optimizer,
        lr_scheduler=scheduler,
        device=device,
        mixed_precision=True,
        early_stopping_patience=5,
        checkpoint_dir=paths["output_dir"],
        results_dir="results",
    )

    print(f"\n[MultiTaskTrainer] Launching {args.epochs} Epochs on {device}...")
    history_df = trainer.fit(
        train_loader=train_loader,
        val_loader_a=val_loader_a,
        val_loader_b=val_loader_b,
        val_loader_c=val_loader_c,
        epochs=args.epochs,
        save_name="checkpoint_baseline_multitask.pth",
    )

    # Export Curves
    curve_path = os.path.join("results", "baseline_training_curves.png")
    plot_and_save_curves(history_df, curve_path)
    print(f"[Done] Multi-Task Baseline Training pipeline executed successfully!")


if __name__ == "__main__":
    main()
