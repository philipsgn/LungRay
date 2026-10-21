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


def locate_file(filename: str, search_dirs: list) -> str:
    """Finds a file in a list of candidate directories or their immediate children."""
    for d in search_dirs:
        if not d or not os.path.exists(d):
            continue
        direct = os.path.join(d, filename)
        if os.path.exists(direct):
            return direct
        for root, _, files in os.walk(d):
            if filename in files:
                return os.path.join(root, filename)
    return ""


def find_kaggle_dataset(target_keys: list) -> str:
    kaggle_base = "/kaggle/input"
    if not os.path.exists(kaggle_base):
        return ""
    for root, dirs, _ in os.walk(kaggle_base):
        for d in dirs:
            if any(k in d.lower() for k in target_keys):
                return os.path.join(root, d)
        bname = os.path.basename(root).lower()
        if any(k in bname for k in target_keys):
            return root
    return ""


def resolve_dataset_paths() -> Dict[str, str]:
    """
    Auto-detects dataset paths between Kaggle environment and local workspace.
    Prioritizes pre-resized 512x512 datasets (lungray-nih-512, lungray-covidx-512).
    """
    kaggle_base = "/kaggle/input"
    is_kaggle = os.path.exists(kaggle_base)

    if is_kaggle:
        print("[Kaggle Environment Detected] Searching for mounted datasets...")
        nih_path = find_kaggle_dataset(["lungray-nih-512", "nih-512", "nih_512", "chestxray", "nih-chest"]) or "dataset/nih_chestxray14"
        covid_path = find_kaggle_dataset(["lungray-covidx-512", "covidx-512", "covidx_512", "covidx", "covid19-radiography"]) or "dataset/covid19_radiography"
        tb_path = find_kaggle_dataset(["tuberculosis-tb-chest-xray-dataset", "tb_chest", "tb-chest"]) or "dataset/tb_chestxray"
        output_dir = "/kaggle/working"
    else:
        print("[Local Environment Detected] Using workspace relative paths...")
        nih_candidates = ["data/processed/nih_512", "dataset/nih-chestXray-14", "dataset/nih_chestxray14"]
        covid_candidates = ["data/processed/covidx_512", "dataset/covidx_cxr4", "dataset/covid19_radiography"]
        nih_path = next((p for p in nih_candidates if os.path.exists(p)), "dataset/nih_chestxray14")
        covid_path = next((p for p in covid_candidates if os.path.exists(p)), "dataset/covid19_radiography")
        tb_path = "dataset/tb_chestxray"
        output_dir = "checkpoints"

    nih_pre_resized = "512" in os.path.basename(nih_path).lower() or os.path.exists(os.path.join(nih_path, "images"))
    covid_pre_resized = "512" in os.path.basename(covid_path).lower() or "512" in str(covid_path).lower()
    tb_pre_resized = True  # TB dataset is natively 512x512

    print(f"[Dataset Auto-Detect] NIH: {nih_path} (pre_resized={nih_pre_resized})")
    print(f"[Dataset Auto-Detect] COVIDx: {covid_path} (pre_resized={covid_pre_resized})")
    print(f"[Dataset Auto-Detect] TB: {tb_path} (pre_resized={tb_pre_resized})")

    return {
        "nih_dir": nih_path,
        "covid_dir": covid_path,
        "tb_dir": tb_path,
        "nih_pre_resized": nih_pre_resized,
        "covid_pre_resized": covid_pre_resized,
        "tb_pre_resized": tb_pre_resized,
        "output_dir": output_dir,
    }


def load_covid_data(covid_dir: str, split_candidates: list) -> pd.DataFrame:
    """Loads COVID data from COVIDx train.txt/test.txt if present, or falls back to split CSV."""
    train_txt = None
    test_txt = None
    if covid_dir and os.path.exists(covid_dir):
        for r, _, files in os.walk(covid_dir):
            for f in files:
                if f.lower() == "train.txt": train_txt = os.path.join(r, f)
                elif f.lower() == "test.txt": test_txt = os.path.join(r, f)

    if train_txt and test_txt:
        print(f"[*] Auto-detected COVIDx CXR-4 Benchmark with train.txt & test.txt:")
        class_map = {"positive": 1, "negative": 0, "normal": 0, "pneumonia": 0}
        records = []
        for split_name, txt_file in [("train", train_txt), ("test", test_txt)]:
            with open(txt_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        pid = parts[0]
                        fname = parts[1]
                        raw_cls = parts[2].lower()
                        lbl = class_map.get(raw_cls, 1 if "covid" in raw_cls or "pos" in raw_cls else 0)
                        records.append({"patient_id": pid, "filename": fname, "Image Index": fname, "label": lbl, "split": split_name})
        df = pd.DataFrame(records)
        train_mask = df["split"] == "train"
        train_pids = df[train_mask]["patient_id"].unique()
        np.random.seed(42)
        val_pids = set(np.random.choice(train_pids, size=max(1, int(len(train_pids) * 0.1)), replace=False))
        df.loc[train_mask & df["patient_id"].isin(val_pids), "split"] = "val"
        print(f"[OK] COVIDx CXR-4: Train={sum(df['split']=='train'):,d}, Val={sum(df['split']=='val'):,d}, Test={sum(df['split']=='test'):,d}")
        return df
    else:
        covid_split_csv = locate_file("covid_splits.csv", split_candidates)
        if covid_split_csv and os.path.exists(covid_split_csv):
            print(f"[Splits Loaded] COVID Split CSV: {covid_split_csv}")
            return pd.read_csv(covid_split_csv)
        raise FileNotFoundError(f"[ERROR] Neither COVIDx train.txt/test.txt nor covid_splits.csv found in {covid_dir} or {split_candidates}")


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

    # Resilient Split File Discovery
    split_candidates = [
        "/kaggle/working/LungRay/dataset/splits",
        "/kaggle/working/LungRay/data/splits",
        "dataset/splits",
        "data/splits",
        "../dataset/splits",
        "/kaggle/input/lungray-splits",
        paths["nih_dir"],
        paths["covid_dir"],
        paths["tb_dir"],
    ]

    nih_split_csv = locate_file("patient_splits.csv", split_candidates)
    covid_split_csv = locate_file("covid_splits.csv", split_candidates)
    tb_split_csv = locate_file("tb_splits.csv", split_candidates)

    if not nih_split_csv or not os.path.exists(nih_split_csv):
        raise FileNotFoundError(f"[ERROR] patient_splits.csv not found in candidate paths: {split_candidates}")
    if not covid_split_csv or not os.path.exists(covid_split_csv):
        raise FileNotFoundError(f"[ERROR] covid_splits.csv not found in candidate paths: {split_candidates}")
    if not tb_split_csv or not os.path.exists(tb_split_csv):
        raise FileNotFoundError(f"[ERROR] tb_splits.csv not found in candidate paths: {split_candidates}")

    print(f"[Splits Loaded] NIH Split   : {nih_split_csv}")
    print(f"[Splits Loaded] TB Split    : {tb_split_csv}")

    df_nih = pd.read_csv(nih_split_csv)
    df_covid = load_covid_data(paths["covid_dir"], split_candidates)
    df_tb = pd.read_csv(tb_split_csv)

    # Filter train & val sets
    train_nih = df_nih[df_nih["split"] == "train"].reset_index(drop=True)
    val_nih = df_nih[df_nih["split"] == "val"].reset_index(drop=True)

    train_covid = df_covid[df_covid["split"] == "train"].reset_index(drop=True)
    val_covid = df_covid[df_covid["split"] == "val"].reset_index(drop=True)

    train_tb = df_tb[df_tb["split"] == "train"].reset_index(drop=True)
    val_tb = df_tb[df_tb["split"] == "val"].reset_index(drop=True)

    train_transforms = get_train_transforms(img_size=512)
    val_transforms = get_val_transforms(img_size=512)

    # Build Training Datasets with Dual-Mode High-Speed Support
    ds_train_nih = ChestXrayDataset(
        df=train_nih,
        image_dir=paths["nih_dir"],
        image_col="Image Index" if "Image Index" in train_nih.columns else "image_id",
        label_col="Finding Labels" if "Finding Labels" in train_nih.columns else "label",
        task_id=0,
        num_classes=14,
        transforms=train_transforms,
        pre_resized=paths["nih_pre_resized"],
        ignore_missing=True,
    )
    covid_train_col = "Image Index" if "Image Index" in train_covid.columns else ("filename" if "filename" in train_covid.columns else "image_id")
    ds_train_covid = ChestXrayDataset(
        df=train_covid,
        image_dir=paths["covid_dir"],
        image_col=covid_train_col,
        label_col="label" if "label" in train_covid.columns else "Finding Labels",
        task_id=2,
        num_classes=1,
        transforms=train_transforms,
        pre_resized=paths["covid_pre_resized"],
        ignore_missing=True,
    )
    ds_train_tb = ChestXrayDataset(
        df=train_tb,
        image_dir=paths["tb_dir"],
        image_col="filename" if "filename" in train_tb.columns else "image_id",
        label_col="label" if "label" in train_tb.columns else "Finding Labels",
        task_id=1,
        num_classes=1,
        transforms=train_transforms,
        pre_resized=paths["tb_pre_resized"],
        ignore_missing=True,
    )

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
        num_workers=4 if os.name != "nt" else 0,
        pin_memory=torch.cuda.is_available(),
    )

    # Validation DataLoaders per head
    ds_val_nih = ChestXrayDataset(
        df=val_nih,
        image_dir=paths["nih_dir"],
        image_col="Image Index" if "Image Index" in val_nih.columns else "image_id",
        label_col="Finding Labels" if "Finding Labels" in val_nih.columns else "label",
        task_id=0,
        num_classes=14,
        transforms=val_transforms,
        pre_resized=paths["nih_pre_resized"],
        ignore_missing=True,
    )
    covid_val_col = "Image Index" if "Image Index" in val_covid.columns else ("filename" if "filename" in val_covid.columns else "image_id")
    ds_val_covid = ChestXrayDataset(
        df=val_covid,
        image_dir=paths["covid_dir"],
        image_col=covid_val_col,
        label_col="label" if "label" in val_covid.columns else "Finding Labels",
        task_id=2,
        num_classes=1,
        transforms=val_transforms,
        pre_resized=paths["covid_pre_resized"],
        ignore_missing=True,
    )
    ds_val_tb = ChestXrayDataset(
        df=val_tb,
        image_dir=paths["tb_dir"],
        image_col="filename" if "filename" in val_tb.columns else "image_id",
        label_col="label" if "label" in val_tb.columns else "Finding Labels",
        task_id=1,
        num_classes=1,
        transforms=val_transforms,
        pre_resized=paths["tb_pre_resized"],
        ignore_missing=True,
    )

    val_loader_a = DataLoader(ds_val_nih, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)
    val_loader_b = DataLoader(ds_val_tb, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)
    val_loader_c = DataLoader(ds_val_covid, batch_size=args.batch_size, shuffle=False, collate_fn=multitask_collate_fn)

    # Model & Loss Initialization
    model = MultiTaskChestXrayNet(backbone_name=args.backbone, pretrained=True, img_size=512, num_classes_c=1)
    criterion = MaskedMultiTaskLoss(
        weights={"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        head_a_criterion="bce",
        head_c_criterion="bce",
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
