"""
LungRay Dataset Discovery & COVIDx CXR-4 Ingestion
==================================================
Resolves the concrete Kaggle dataset mount for each training source and builds
the COVID-19 (Head C) split directly from the official COVIDx CXR-4 manifests.

Design rules:
- Kaggle mounts user datasets at ``/kaggle/input/<slug>`` or
  ``/kaggle/input/datasets/<username>/<slug>``. The resolver must return the
  specific dataset directory (never the ``<username>`` parent).
- COVIDx CXR-4 is the source of truth for Head C when ``train.txt`` and
  ``test.txt`` are present. The legacy ``covid_splits.csv`` (COVID-19
  Radiography, ``COVID-1.png`` filenames) is only a fallback.
- Validation is carved out of the official train split at patient level with
  class stratification, guaranteeing zero patient leakage between Train/Val/Test.
"""
from __future__ import annotations

import glob
import os
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".dcm")
_EXCLUDED_DIRS = {"masks", ".git", "__pycache__", "images_masks"}

POSITIVE_CLASS_TOKENS = {"positive", "covid", "covid19", "covid-19", "1", "1.0", "true"}
NEGATIVE_CLASS_TOKENS = {"negative", "normal", "pneumonia", "non-covid", "0", "0.0", "false"}


def _normalise_token(value: str) -> str:
    """Normalises a folder/key string for tolerant slug comparison."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_recursive_file_map(root_dir: str) -> Dict[str, str]:
    """Builds an ``filename -> absolute path`` index, excluding mask folders.

    Args:
        root_dir: Dataset root directory to scan recursively.

    Returns:
        Mapping from basename to resolved image path. Missing roots return an
        empty mapping instead of raising.
    """
    file_map: Dict[str, str] = {}
    if not root_dir or not os.path.isdir(root_dir):
        return file_map

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d.lower() not in _EXCLUDED_DIRS]
        if any(part.lower() in _EXCLUDED_DIRS for part in os.path.normpath(root).split(os.sep)):
            continue
        for filename in files:
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                file_map.setdefault(filename, os.path.join(root, filename))
    return file_map


def _contains_images(
    directory: str, min_images: int = 1, max_files: int = 5000
) -> bool:
    """Checks for images while capping the scan to avoid slow network walks."""
    if not os.path.isdir(directory):
        return False
    found = 0
    scanned = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d.lower() not in _EXCLUDED_DIRS]
        for filename in files:
            scanned += 1
            if scanned > max_files:
                return False
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                found += 1
                if found >= min_images:
                    return True
    return False


def find_covidx_manifests(
    root_dir: str, max_depth: int = 2
) -> Tuple[Optional[str], Optional[str]]:
    """Locates ``train.txt`` and ``test.txt`` inside a COVIDx dataset tree.

    Args:
        root_dir: Directory that may contain the COVIDx manifests.
        max_depth: Maximum subdirectory depth to inspect (manifests normally
            live at the dataset root or one folder below).

    Returns:
        ``(train_txt_path, test_txt_path)`` or ``(None, None)``.
    """
    train_txt: Optional[str] = None
    test_txt: Optional[str] = None
    if not root_dir or not os.path.isdir(root_dir):
        return None, None

    base_depth = os.path.normpath(root_dir).count(os.sep)
    for root, dirs, files in os.walk(root_dir):
        depth = os.path.normpath(root).count(os.sep) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d.lower() not in _EXCLUDED_DIRS]
        lowered = {f.lower(): f for f in files}
        if train_txt is None and "train.txt" in lowered:
            train_txt = os.path.join(root, lowered["train.txt"])
        if test_txt is None and "test.txt" in lowered:
            test_txt = os.path.join(root, lowered["test.txt"])
        if train_txt and test_txt:
            break
        if depth == max_depth:
            dirs[:] = []
    return train_txt, test_txt


def find_kaggle_dataset(
    slug_keys: Sequence[str],
    base_dir: str = "/kaggle/input",
    require_images: bool = False,
    require_manifest: bool = False,
    max_depth: int = 5,
) -> Optional[str]:
    """Finds the most specific Kaggle dataset directory matching ``slug_keys``.

    Matching is performed on directory basenames (exact slug match wins over a
    substring match; deeper directories win over shallower ones). Candidate
    directories are validated against their content so an ancestor such as a
    Kaggle username folder is never returned.

    Args:
        slug_keys: Dataset slugs, most specific first.
        base_dir: Kaggle input mount.
        require_images: Only accept candidates containing image files.
        require_manifest: Only accept candidates containing train.txt/test.txt.
        max_depth: Maximum directory depth below ``base_dir`` to inspect.

    Returns:
        Absolute path of the resolved dataset directory, or ``None``.
    """
    if not os.path.isdir(base_dir):
        return None

    normalised_keys = [(_normalise_token(k), i) for i, k in enumerate(slug_keys)]
    base_depth = os.path.normpath(base_dir).count(os.sep)

    # Kaggle mounts are shallow: /kaggle/input/<slug>,
    # /kaggle/input/<user>/<slug>, /kaggle/input/datasets/<user>/<slug>.
    # Glob only directory names; never walk full image trees (can take hours).
    search_dirs = {os.path.normpath(base_dir)}
    patterns = [
        os.path.join(base_dir, "*"),
        os.path.join(base_dir, "*", "*"),
        os.path.join(base_dir, "datasets", "*", "*"),
        os.path.join(base_dir, "datasets", "*", "*", "*"),
    ]
    for pattern in patterns:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                search_dirs.add(os.path.normpath(path))

    candidates: List[Tuple[int, int, int, str]] = []
    for root in search_dirs:
        depth = os.path.normpath(root).count(os.sep) - base_depth
        basename = os.path.basename(root)
        normalised_name = _normalise_token(basename)
        for normalised_key, key_order in normalised_keys:
            if normalised_name == normalised_key:
                candidates.append((2, -key_order, depth, root))
                break
            if normalised_key and normalised_key in normalised_name:
                candidates.append((1, -key_order, depth, root))
                break

    for _, _, _, candidate in sorted(candidates, reverse=True):
        if require_manifest:
            train_txt, test_txt = find_covidx_manifests(candidate, max_depth=2)
            if not (train_txt and test_txt):
                continue
        if require_images and not _contains_images(candidate, max_files=5000):
            continue
        return candidate
    return None


def _sample_image_paths(directory: str, limit: int = 5) -> List[str]:
    """Returns up to ``limit`` image paths without indexing the entire dataset."""
    paths: List[str] = []
    if not os.path.isdir(directory):
        return paths
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d.lower() not in _EXCLUDED_DIRS]
        for filename in files:
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                paths.append(os.path.join(root, filename))
                if len(paths) >= limit:
                    return paths
    return paths


def _looks_pre_resized(directory: str) -> bool:
    """Detects a pre-resized 512x512 dataset from its slug or a sample image."""
    if not directory:
        return False
    if "512" in os.path.basename(os.path.normpath(directory)).lower():
        return True

    sample_paths = _sample_image_paths(directory)
    if not sample_paths:
        return False

    try:
        import cv2

        for path in sample_paths:
            image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if image is not None and image.shape[0] == 512 and image.shape[1] == 512:
                return True
    except Exception:
        return False
    return False


def locate_file(filename: str, search_dirs: Iterable[Optional[str]]) -> Optional[str]:
    """Finds ``filename`` directly or recursively inside candidate directories."""
    for directory in search_dirs:
        if not directory or not os.path.isdir(directory):
            continue
        direct = os.path.join(directory, filename)
        if os.path.isfile(direct):
            return direct
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d.lower() not in _EXCLUDED_DIRS]
            if filename in files:
                return os.path.join(root, filename)
    return None


def _project_root() -> str:
    """Returns the repository root (two levels above this module)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_split_dir(is_kaggle: bool, kaggle_base: str) -> str:
    """Resolves the directory holding the canonical split CSV artifacts."""
    project_root = _project_root()
    candidates = [
        os.path.join(project_root, "dataset", "splits"),
        os.path.join(project_root, "data", "splits"),
        os.path.join(os.getcwd(), "dataset", "splits"),
        os.path.join(kaggle_base, "lungray-splits"),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    return candidates[0]


def resolve_dataset_paths(kaggle_base: str = "/kaggle/input") -> Dict[str, object]:
    """Resolves dataset, split and output paths for Kaggle or local execution.

    Args:
        kaggle_base: Root of the Kaggle input mount (overridable for tests).

    Returns:
        Dictionary with resolved directories, split CSV paths, pre-resize flags
        and output locations. Raises ``FileNotFoundError`` when a Kaggle run
        cannot find one of the three mandatory datasets.
    """
    is_kaggle = os.path.isdir(kaggle_base)
    project_root = _project_root()

    if is_kaggle:
        nih_dir = find_kaggle_dataset(
            ["lungray-nih-512", "nih-512", "nih_512", "chestxray14", "chest-xray14"],
            base_dir=kaggle_base,
            require_images=True,
        )
        covid_dir = find_kaggle_dataset(
            ["lungray-covidx-512", "covidx-512", "covidx-cxr4", "covidx-cxr2", "covidx"],
            base_dir=kaggle_base,
            require_manifest=True,
        )
        if covid_dir is None:
            covid_dir = find_kaggle_dataset(
                ["covid19-radiography-database", "covid-19-radiography", "covid19-radiography"],
                base_dir=kaggle_base,
                require_images=True,
            )
        tb_dir = find_kaggle_dataset(
            ["tuberculosis-tb-chest-xray-dataset", "tb-chest-xray", "tb-chest", "tuberculosis"],
            base_dir=kaggle_base,
            require_images=True,
        )

        missing = [
            name
            for name, path in (("NIH", nih_dir), ("COVIDx", covid_dir), ("TB", tb_dir))
            if not path
        ]
        if missing:
            raise FileNotFoundError(
                "[LungRay] Missing Kaggle dataset mount(s): "
                + ", ".join(missing)
                + f" under {kaggle_base}. Expected slugs: lungray-nih-512, "
                "lungray-covidx-512, tawsifurrahman/tuberculosis-tb-chest-xray-dataset."
            )

        nih_pre_resized = _looks_pre_resized(nih_dir)
        covid_pre_resized = _looks_pre_resized(covid_dir)
        tb_pre_resized = True
        output_dir = "/kaggle/working"
        results_dir = "/kaggle/working/results/baseline"
    else:
        local_nih = [
            os.path.join(project_root, "data", "processed", "nih_512"),
            os.path.join(project_root, "dataset", "lungray-nih-512"),
            os.path.join(project_root, "dataset", "nih-chestXray-14"),
            os.path.join(project_root, "dataset", "nih_chestxray14"),
        ]
        local_covid = [
            os.path.join(project_root, "data", "processed", "covidx_512"),
            os.path.join(project_root, "dataset", "lungray-covidx-512"),
            os.path.join(project_root, "dataset", "covidx_cxr4"),
            os.path.join(project_root, "dataset", "covid19_radiography"),
        ]
        local_tb = [
            os.path.join(project_root, "dataset", "tb_chestxray"),
            os.path.join(project_root, "dataset", "tb-chestxray"),
            os.path.join(project_root, "dataset", "tb_meta"),
        ]
        nih_dir = next((p for p in local_nih if os.path.isdir(p)), local_nih[-1])
        covid_dir = next((p for p in local_covid if os.path.isdir(p)), local_covid[-1])
        tb_dir = next((p for p in local_tb if os.path.isdir(p)), local_tb[0])
        nih_pre_resized = _looks_pre_resized(nih_dir)
        covid_pre_resized = _looks_pre_resized(covid_dir)
        tb_pre_resized = True
        output_dir = os.path.join(project_root, "checkpoints")
        results_dir = os.path.join(project_root, "results", "baseline")

    split_dir = _resolve_split_dir(is_kaggle, kaggle_base)
    split_search = [split_dir, os.path.join(project_root, "dataset", "splits")]
    split_paths = {
        "nih_split_csv": locate_file("patient_splits.csv", split_search),
        "covid_split_csv": locate_file("covid_splits.csv", split_search),
        "tb_split_csv": locate_file("tb_splits.csv", split_search),
    }

    return {
        "is_kaggle": is_kaggle,
        "nih_dir": nih_dir,
        "covid_dir": covid_dir,
        "tb_dir": tb_dir,
        "nih_pre_resized": nih_pre_resized,
        "covid_pre_resized": covid_pre_resized,
        "tb_pre_resized": tb_pre_resized,
        "split_dir": split_dir,
        **split_paths,
        "output_dir": output_dir,
        "results_dir": results_dir,
    }


def _parse_covidx_class(raw_class: str) -> int:
    """Maps a COVIDx class token to the binary Head C label (positive=1)."""
    token = str(raw_class).strip().lower()
    if (
        token in NEGATIVE_CLASS_TOKENS
        or "non-covid" in token
        or "noncovid" in token
        or "neg" in token
        or "normal" in token
    ):
        return 0
    if token in POSITIVE_CLASS_TOKENS or "covid" in token or "pos" in token:
        return 1
    return 0


def _read_covidx_manifest(txt_path: str, split_name: str) -> List[Dict[str, object]]:
    """Parses one COVIDx manifest file into normalised record dictionaries."""
    records: List[Dict[str, object]] = []
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.strip().split()
            if len(parts) < 2 or parts[0].startswith("#"):
                continue
            data_source = "covidx_cxr4"
            if len(parts) >= 4:
                patient_id, raw_filename, raw_class, data_source = parts[0], parts[1], parts[2], parts[3]
            elif len(parts) >= 3:
                patient_id, raw_filename, raw_class = parts[0], parts[1], parts[2]
            else:
                raw_filename, raw_class = parts[0], parts[1]
                patient_id = os.path.splitext(os.path.basename(raw_filename))[0]

            filename = os.path.basename(raw_filename)
            if data_source == "covidx_cxr4":
                lower_name = filename.lower()
                if "bimcv" in lower_name or "covid-19-ar" in lower_name:
                    data_source = "bimcv"
                elif "sirm" in lower_name:
                    data_source = "sirm"
                elif "cohen" in lower_name or "1-s2.0" in lower_name:
                    data_source = "cohen"
                elif "fig1" in lower_name:
                    data_source = "fig1"
                elif "ricord" in lower_name or "midrc" in lower_name:
                    data_source = "ricord"
                elif any(k in lower_name for k in ["pneumonia", "normal", "bacteria", "virus"]):
                    data_source = "rsna"

            records.append(
                {
                    "patient_id": str(patient_id),
                    "filename": filename,
                    "relative_path": raw_filename,
                    "Image Index": filename,
                    "label": _parse_covidx_class(raw_class),
                    "data_source": str(data_source),
                    "split": split_name,
                }
            )
    return records


def make_patient_stratified_split(
    df: pd.DataFrame,
    val_ratio: float = 0.10,
    seed: int = 42,
    patient_col: str = "patient_id",
    label_col: str = "label",
) -> pd.DataFrame:
    """Carves a stratified validation set out of the train split by patient ID.

    Args:
        df: DataFrame containing at least train/test rows.
        val_ratio: Fraction of *train patients* assigned to validation.
        seed: Reproducible random seed.
        patient_col: Patient identifier column.
        label_col: Binary label column used for stratification.

    Returns:
        DataFrame with the ``split`` column updated (train/val/test).
    """
    df = df.copy()
    train_mask = df["split"] == "train"
    train_patients = df.loc[train_mask, patient_col].dropna().unique()
    if len(train_patients) == 0:
        return df

    train_frame = df.loc[train_mask]
    patient_labels = (
        train_frame.groupby(patient_col)[label_col]
        .max()
        .reindex(train_patients)
        .fillna(0)
        .astype(int)
    )

    n_val = int(round(len(train_patients) * val_ratio))
    n_val = min(max(1, n_val), len(train_patients) - 1) if len(train_patients) > 1 else 0

    val_patients: List[str] = []
    if n_val > 0:
        stratify_labels = patient_labels.to_numpy()
        if "data_source" in train_frame.columns:
            patient_sources = (
                train_frame.groupby(patient_col)["data_source"]
                .agg(lambda values: values.astype(str).mode().iloc[0])
                .reindex(train_patients)
            )
            source_label_strata = (
                patient_sources.astype(str) + "::" + patient_labels.astype(str)
            )
            source_counts = source_label_strata.value_counts()
            n_train = len(train_patients) - n_val
            if (
                not source_counts.empty
                and source_counts.min() >= 2
                and n_val >= len(source_counts)
                and n_train >= len(source_counts)
            ):
                stratify_labels = source_label_strata.to_numpy()
            else:
                source_counts = patient_sources.value_counts()
                if (
                    not source_counts.empty
                    and source_counts.min() >= 2
                    and n_val >= len(source_counts)
                    and n_train >= len(source_counts)
                ):
                    stratify_labels = patient_sources.to_numpy()
        try:
            train_pids, val_pids = train_test_split(
                patient_labels.index.to_numpy(),
                test_size=n_val,
                random_state=seed,
                stratify=stratify_labels,
            )
            val_patients = list(val_pids)
        except ValueError:
            rng = np.random.default_rng(seed)
            val_patients = list(rng.choice(patient_labels.index.to_numpy(), size=n_val, replace=False))

    df.loc[train_mask & df[patient_col].isin(val_patients), "split"] = "val"
    return df


def load_covid_dataframe(
    covid_dir: str,
    split_dirs: Optional[Sequence[str]] = None,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> pd.DataFrame:
    """Loads Head C data from COVIDx CXR-4 manifests or legacy split CSV.

    Args:
        covid_dir: Resolved COVID dataset directory.
        split_dirs: Candidate directories containing ``covid_splits.csv``.
        val_ratio: Patient-stratified validation fraction of the train split.
        seed: Reproducible random seed.

    Returns:
        DataFrame with ``patient_id``, ``filename``, ``Image Index``, ``label``
        and ``split`` columns.

    Raises:
        FileNotFoundError: If neither COVIDx manifests nor a split CSV exist.
    """
    train_txt, test_txt = find_covidx_manifests(covid_dir)
    if train_txt and test_txt:
        records = _read_covidx_manifest(train_txt, "train") + _read_covidx_manifest(test_txt, "test")
        df = pd.DataFrame(records).drop_duplicates(subset=["filename"], keep="first")

        train_patients = set(df.loc[df["split"] == "train", "patient_id"])
        test_patients = set(df.loc[df["split"] == "test", "patient_id"])
        leaked_patients = train_patients & test_patients
        if leaked_patients:
            print(
                f"[!] COVIDx patient overlap between official train/test: "
                f"{len(leaked_patients)} patient(s). Removing them from train."
            )
            df = df[~((df["split"] == "train") & df["patient_id"].isin(leaked_patients))]

        df = make_patient_stratified_split(df, val_ratio=val_ratio, seed=seed)

        split_patients = {
            name: set(df.loc[df["split"] == name, "patient_id"]) for name in ("train", "val", "test")
        }
        assert split_patients["train"].isdisjoint(split_patients["val"])
        assert split_patients["train"].isdisjoint(split_patients["test"])
        assert split_patients["val"].isdisjoint(split_patients["test"])

        counts = df["split"].value_counts().to_dict()
        positive_counts = df.groupby("split")["label"].sum().to_dict()
        print(
            "[OK] COVIDx CXR-4 manifests: "
            f"Train={counts.get('train', 0):,d} (pos={int(positive_counts.get('train', 0)):,d}), "
            f"Val={counts.get('val', 0):,d} (pos={int(positive_counts.get('val', 0)):,d}), "
            f"Test={counts.get('test', 0):,d} (pos={int(positive_counts.get('test', 0)):,d})"
        )
        return df

    candidates = list(split_dirs or [])
    candidates.extend(
        [
            os.path.join(_project_root(), "dataset", "splits"),
            os.path.join(os.getcwd(), "dataset", "splits"),
        ]
    )
    covid_split_csv = locate_file("covid_splits.csv", candidates)
    if not covid_split_csv:
        raise FileNotFoundError(
            f"[LungRay] Neither COVIDx train.txt/test.txt nor covid_splits.csv was found in "
            f"'{covid_dir}' or split directories {candidates}."
        )

    print(f"[Splits Loaded] COVID legacy split CSV: {covid_split_csv}")
    df = pd.read_csv(covid_split_csv)
    if "filename" not in df.columns:
        df["filename"] = df["Image Index"] if "Image Index" in df.columns else df.iloc[:, 0]
    if "Image Index" not in df.columns:
        df["Image Index"] = df["filename"]
    if "patient_id" not in df.columns:
        df["patient_id"] = df["filename"].astype(str).map(lambda name: os.path.splitext(name)[0])
    if "label" in df.columns:
        df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    return df


def audit_split_coverage(
    df: pd.DataFrame,
    file_map: Dict[str, str],
    name: str,
    image_cols: Sequence[str] = ("Image Index", "filename"),
) -> Tuple[int, int, float]:
    """Audits that split rows resolve to files indexed on disk.

    Args:
        df: Split DataFrame.
        file_map: Basename-to-path index built from the dataset root.
        name: Human-readable dataset name for logging.
        image_cols: Candidate image-name columns, in priority order.

    Returns:
        ``(matched, total, coverage_percent)``.
    """
    if not file_map:
        print(f"[{name}] File map is empty (dataset root not indexed).")
        return 0, len(df), 0.0

    image_col = next((column for column in image_cols if column in df.columns), None)
    if image_col is None:
        print(f"[{name}] No image filename column found in {list(df.columns)}.")
        return 0, len(df), 0.0

    matched = sum(1 for image_name in df[image_col].astype(str) if image_name in file_map)
    total = len(df)
    coverage = (matched / total * 100.0) if total else 0.0
    print(f"[{name}] Matched: {matched:,d} / {total:,d} images ({coverage:.2f}%)")
    return matched, total, coverage
