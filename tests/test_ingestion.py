"""Unit tests for Kaggle path resolution and COVIDx CXR-4 ingestion."""
import os
import warnings

import cv2
import numpy as np
import pandas as pd

from src.data.ingestion import (
    _parse_covidx_class,
    audit_split_coverage,
    build_recursive_file_map,
    find_kaggle_dataset,
    load_covid_dataframe,
    resolve_dataset_paths,
)
from src.data.sampler import WeightedMultiTaskBatchSampler
from src.data.transforms import get_train_transforms, get_val_transforms


def _write_image(path: str) -> None:
    cv2.imwrite(path, np.full((64, 64, 3), 128, dtype=np.uint8))


def _build_mock_kaggle(tmp_path):
    kaggle_base = tmp_path / "kaggle" / "input"
    user_dir = kaggle_base / "datasets" / "phanphat"
    nih_dir = user_dir / "lungray-nih-512"
    covid_dir = user_dir / "lungray-covidx-512"
    tb_dir = kaggle_base / "datasets" / "tawsifurrahman" / "tuberculosis-tb-chest-xray-dataset"

    (nih_dir / "images").mkdir(parents=True)
    (covid_dir / "train").mkdir(parents=True)
    (covid_dir / "test").mkdir(parents=True)
    (tb_dir / "Normal").mkdir(parents=True)
    (tb_dir / "Tuberculosis").mkdir(parents=True)

    for index in range(12):
        filename = f"0000000{index}_000.png"
        _write_image(str(nih_dir / "images" / filename))

    train_lines = []
    for index in range(20):
        patient = f"p{index:03d}"
        filename = f"{patient}_000.png"
        _write_image(str(covid_dir / "train" / filename))
        label = "positive" if index % 2 == 0 else "negative"
        train_lines.append(f"{patient} {filename} {label}\n")
    (covid_dir / "train.txt").write_text("".join(train_lines), encoding="utf-8")

    test_lines = []
    for index in range(10):
        patient = f"t{index:03d}"
        filename = f"{patient}_000.png"
        _write_image(str(covid_dir / "test" / filename))
        label = "positive" if index % 2 == 0 else "normal"
        test_lines.append(f"{patient} {filename} {label}\n")
    (covid_dir / "test.txt").write_text("".join(test_lines), encoding="utf-8")

    for index in range(4):
        _write_image(str(tb_dir / "Tuberculosis" / f"Tuberculosis-{index}.png"))
        _write_image(str(tb_dir / "Normal" / f"Normal-{index}.png"))

    return kaggle_base, nih_dir, covid_dir, tb_dir


def test_nested_kaggle_resolution_returns_leaf_dataset(tmp_path):
    """The resolver must return lungray-*-512, never the <username> parent."""
    kaggle_base, nih_dir, covid_dir, tb_dir = _build_mock_kaggle(tmp_path)

    assert find_kaggle_dataset(["lungray-nih-512"], base_dir=str(kaggle_base)) == str(nih_dir)
    assert find_kaggle_dataset(["lungray-covidx-512"], base_dir=str(kaggle_base)) == str(covid_dir)

    paths = resolve_dataset_paths(kaggle_base=str(kaggle_base))
    assert paths["nih_dir"] == str(nih_dir)
    assert paths["covid_dir"] == str(covid_dir)
    assert paths["tb_dir"] == str(tb_dir)
    assert paths["nih_pre_resized"] is True
    assert paths["covid_pre_resized"] is True


def test_covidx_manifest_loading_and_patient_stratified_validation(tmp_path):
    """COVIDx train.txt/test.txt must be preferred over the legacy split CSV."""
    _, _, covid_dir, _ = _build_mock_kaggle(tmp_path)

    df = load_covid_dataframe(str(covid_dir))

    assert set(df["split"]) == {"train", "val", "test"}
    assert set(df["label"]).issubset({0, 1})
    assert df.loc[df["filename"].str.startswith("p"), "label"].isin([0, 1]).all()

    patients = {
        split: set(df.loc[df["split"] == split, "patient_id"]) for split in ("train", "val", "test")
    }
    assert patients["train"].isdisjoint(patients["val"])
    assert patients["train"].isdisjoint(patients["test"])
    assert patients["val"].isdisjoint(patients["test"])
    assert len(patients["val"]) > 0


def test_covidx_coverage_reaches_one_hundred_percent(tmp_path):
    """Every manifest row must resolve to a file on disk."""
    _, _, covid_dir, _ = _build_mock_kaggle(tmp_path)
    df = load_covid_dataframe(str(covid_dir))

    _, total, percentage = audit_split_coverage(
        df, build_recursive_file_map(str(covid_dir)), "COVIDx"
    )
    assert total > 0
    assert percentage == 100.0


def test_covidx_classes_collapse_to_binary_positive_vs_negative():
    """COVIDx labels: COVID variants -> 1; normal/pneumonia/non-COVID -> 0."""
    for token in ("positive", "COVID", "COVID-19", "covid19", "1"):
        assert _parse_covidx_class(token) == 1
    for token in ("negative", "Normal", "pneumonia", "non-COVID", "0"):
        assert _parse_covidx_class(token) == 0


def test_transforms_accept_both_size_aliases_without_warnings():
    """img_size and image_size are interchangeable; no deprecated value warning."""
    image = np.zeros((300, 400, 3), dtype=np.uint8)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        train_tensor = get_train_transforms(image_size=512)(image=image)["image"]
        val_tensor = get_val_transforms(img_size=512)(image=image)["image"]

    assert train_tensor.shape == (3, 512, 512)
    assert val_tensor.shape == (3, 512, 512)
    assert not [item for item in captured if issubclass(item.category, UserWarning)]


def test_sampler_cycles_small_pools_to_full_batch():
    """Small task pools are oversampled instead of shrinking the batch."""
    sampler = WeightedMultiTaskBatchSampler(
        nih_indices=[0, 1, 2],
        covid_indices=[10, 11, 12],
        tb_indices=[20, 21],
        batch_size=16,
        seed=42,
    )
    batch = next(iter(sampler))

    assert len(batch) == 16
    assert sum(1 for index in batch if index < 10) == 10
    assert sum(1 for index in batch if 10 <= index < 20) == 4
    assert sum(1 for index in batch if index >= 20) == 2
