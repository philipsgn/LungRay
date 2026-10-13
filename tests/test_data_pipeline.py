"""
Unit tests for LungRay Data Ingestion, Transforms, and Zero Data Leakage Pipeline.
"""
import numpy as np
import pandas as pd
import torch
import pytest

from src.data.transforms import get_train_transforms, get_val_transforms
from src.data.dataset import ChestXrayDataset
from src.data.make_splits import split_nih_by_patient_id


def test_zero_patient_data_leakage():
    """Verify that split_nih_by_patient_id guarantees disjoint patient sets."""
    # Synthetic dataset with repeating patients
    patients = [f"P_{i:03d}" for i in range(100)]
    records = []
    for i in range(500):
        records.append({
            "Image Index": f"img_{i:04d}.png",
            "Patient ID": np.random.choice(patients),
            "Finding Labels": "Effusion" if i % 3 == 0 else "No Finding"
        })
    df = pd.DataFrame(records)

    split_df = split_nih_by_patient_id(df, seed=42)

    train_pts = set(split_df[split_df["split"] == "train"]["Patient ID"])
    val_pts = set(split_df[split_df["split"] == "val"]["Patient ID"])
    test_pts = set(split_df[split_df["split"] == "test"]["Patient ID"])

    assert len(train_pts & val_pts) == 0, "Patient leakage found between Train and Val"
    assert len(train_pts & test_pts) == 0, "Patient leakage found between Train and Test"
    assert len(val_pts & test_pts) == 0, "Patient leakage found between Val and Test"


def test_transforms_512_output_shape():
    """Verify transforms always output (3, 512, 512) tensor regardless of input resolution."""
    val_trans = get_val_transforms(img_size=512)
    train_trans = get_train_transforms(img_size=512)

    # Test with arbitrary non-512 input size (e.g. 1024x1024 or 224x224)
    dummy_img_1024 = np.zeros((1024, 1024, 3), dtype=np.uint8)
    dummy_img_300 = np.zeros((300, 400, 3), dtype=np.uint8)

    t1 = val_trans(image=dummy_img_1024)["image"]
    t2 = train_trans(image=dummy_img_300)["image"]

    assert t1.shape == (3, 512, 512), f"Expected (3, 512, 512), got {t1.shape}"
    assert t2.shape == (3, 512, 512), f"Expected (3, 512, 512), got {t2.shape}"


def test_dataset_dual_mode_mock(tmp_path):
    """Verify ChestXrayDataset correctly returns 512x512 tensors and label format."""
    import cv2
    dummy_file = tmp_path / "00000001_000.png"
    cv2.imwrite(str(dummy_file), np.zeros((100, 100, 3), dtype=np.uint8))

    df = pd.DataFrame([
        {"Image Index": "00000001_000.png", "Finding Labels": "Cardiomegaly|Effusion", "Patient ID": "P_001"}
    ])

    dataset = ChestXrayDataset(
        df=df,
        image_dir=str(tmp_path),
        label_col="Finding Labels",
        task_id=0,
        num_classes=14,
        target_size=512
    )

    sample = dataset[0]
    assert "image" in sample
    assert "labels" in sample
    assert "task_id" in sample
    assert sample["image"].shape == (3, 512, 512)
    assert sample["labels"].shape == (14,)
    # Verify Cardiomegaly (index 1) and Effusion (index 2) are set
    assert sample["labels"][1] == 1.0  # Cardiomegaly
    assert sample["labels"][2] == 1.0  # Effusion


def test_smart_path_resolution_nested(tmp_path):
    """Verify Smart Path Indexer resolves images located in arbitrary subdirectories."""
    import cv2
    nested_dir = tmp_path / "COVID" / "images"
    nested_dir.mkdir(parents=True)
    dummy_img_path = nested_dir / "COVID-999.png"
    cv2.imwrite(str(dummy_img_path), np.ones((100, 100, 3), dtype=np.uint8) * 128)

    df = pd.DataFrame([{"Image Index": "COVID-999.png", "label": 0}])
    dataset = ChestXrayDataset(
        df=df,
        image_dir=str(tmp_path),
        label_col="label",
        task_id=2,
        num_classes=4,
        ignore_missing=False,
        target_size=512
    )

    sample = dataset[0]
    assert sample["image"].shape == (3, 512, 512)
    assert sample["labels"].item() == 0


def test_masks_folder_is_strictly_excluded_from_indexing(tmp_path):
    """Verify that parallel masks/ folder with duplicate filenames is NEVER loaded instead of CXR images."""
    import cv2
    img_dir = tmp_path / "COVID" / "images"
    mask_dir = tmp_path / "COVID" / "masks"
    img_dir.mkdir(parents=True)
    mask_dir.mkdir(parents=True)

    # CXR image has high brightness (pixel value 200)
    cxr_file = img_dir / "COVID-101.png"
    cv2.imwrite(str(cxr_file), np.ones((100, 100, 3), dtype=np.uint8) * 200)

    # Binary mask has zero brightness (pixel value 0)
    mask_file = mask_dir / "COVID-101.png"
    cv2.imwrite(str(mask_file), np.zeros((100, 100, 3), dtype=np.uint8))

    df = pd.DataFrame([{"Image Index": "COVID-101.png", "label": 0}])
    dataset = ChestXrayDataset(
        df=df,
        image_dir=str(tmp_path),
        label_col="label",
        task_id=2,
        num_classes=4,
        ignore_missing=False,
        target_size=512
    )

    resolved = dataset._resolve_path("COVID-101.png")
    assert resolved is not None, "Failed to resolve COVID-101.png"
    assert "masks" not in resolved.replace("\\", "/").split("/"), f"Resolved path incorrectly points to masks: {resolved}"
    assert "images" in resolved.replace("\\", "/").split("/"), f"Resolved path must point to images: {resolved}"

    # Verify loaded sample
    sample = dataset[0]
    # Because normalization divides by std, check that original was not all zero mask
    assert sample["image"].shape == (3, 512, 512)


def test_strict_file_not_found_on_missing(tmp_path):
    """Verify ChestXrayDataset strictly raises FileNotFoundError in training mode when image is missing."""
    df = pd.DataFrame([{"Image Index": "non_existent_image.png", "label": 0}])
    dataset = ChestXrayDataset(
        df=df,
        image_dir=str(tmp_path),
        label_col="label",
        task_id=1,
        num_classes=1,
        ignore_missing=False
    )

    with pytest.raises(FileNotFoundError):
        _ = dataset[0]


def test_weighted_multitask_sampler_ratio():
    """Verify WeightedMultiTaskBatchSampler produces batches adhering to the 60:25:15 ratio."""
    from src.data.sampler import WeightedMultiTaskBatchSampler

    nih_idx = list(range(0, 1000))
    covid_idx = list(range(1000, 1300))
    tb_idx = list(range(1300, 1400))

    batch_size = 20  # 12 NIH (60%), 5 COVID (25%), 3 TB (15%)
    sampler = WeightedMultiTaskBatchSampler(
        nih_indices=nih_idx,
        covid_indices=covid_idx,
        tb_indices=tb_idx,
        batch_size=batch_size,
        shuffle=True,
        seed=42
    )

    batches = list(sampler)
    assert len(batches) > 0, "Sampler yielded no batches"

    # Check composition of first 10 batches
    for b in batches[:10]:
        assert len(b) == batch_size, f"Batch size mismatch: {len(b)} != {batch_size}"
        nih_count = sum(1 for idx in b if idx < 1000)
        covid_count = sum(1 for idx in b if 1000 <= idx < 1300)
        tb_count = sum(1 for idx in b if idx >= 1300)

        assert nih_count == 12, f"Expected 12 NIH samples, got {nih_count}"
        assert covid_count == 5, f"Expected 5 COVID samples, got {covid_count}"
        assert tb_count == 3, f"Expected 3 TB samples, got {tb_count}"


def test_split_files_integrity():
    """Verify that all 3 split CSV files exist and have non-empty valid splits."""
    import os
    for filename in ["patient_splits.csv", "covid_splits.csv", "tb_splits.csv"]:
        filepath = os.path.join("dataset", "splits", filename)
        assert os.path.exists(filepath), f"Missing split file: {filepath}"
        df = pd.read_csv(filepath)
        assert "split" in df.columns, f"'split' column missing in {filename}"
        assert set(df["split"].unique()) == {"train", "val", "test"}

