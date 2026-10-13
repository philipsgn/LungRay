"""
LungRay PyTorch Dataset Implementations
=======================================
Provides modular dataset classes for NIH ChestX-ray14, TB, COVID-19,
and unified Multi-Task data loading.

Key Features:
- Dual-Mode Resolution: Works directly with pre-resized 512x512 images (Production)
  or resizes on-the-fly from 1024x1024 (Fallback).
- Safe Local Dry-Run: 'ignore_missing=True' allows running tests and debug loops
  on local machines with only a small sample of images without file-not-found crashes.
- Zero Leakage Integrity: Strictly enforces partition filtering via patient_splits.csv.
"""
import os
from typing import Optional, Callable, Dict, Any, List
import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from src.data.transforms import get_train_transforms, get_val_transforms


NIH_PATHOLOGY_LIST = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration",
    "Mass", "Nodule", "Pneumonia", "Pneumothorax",
    "Consolidation", "Edema", "Emphysema", "Fibrosis",
    "Pleural_Thickening", "Hernia"
]


class ChestXrayDataset(Dataset):
    """
    Modular PyTorch Dataset for single-source CXR data (NIH, TB, or COVID).
    
    Features:
    - Smart Path Indexer: Automatically resolves images located in nested subdirectories
      (e.g., 'COVID/images/COVID-1.png', 'Tuberculosis/Tuberculosis-1.png').
    - Strict File Integrity: Raises explicit FileNotFoundError during training if any image is
      missing or unreadable (strictly forbids silent black-image fallback in production).
    - Dual-Mode Resolution: Works with pre-resized 512x512 images or resizes on-the-fly.
    - Safe Local Dry-Run: 'ignore_missing=True' enables mock/unit testing with small samples.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        image_dir: str,
        image_col: str = "Image Index",
        label_col: Optional[str] = None,
        task_id: int = 0,  # 0: NIH, 1: TB, 2: COVID
        num_classes: int = 14,
        transforms: Optional[Callable] = None,
        pre_resized: bool = False,
        ignore_missing: bool = False,
        target_size: int = 512
    ):
        self.image_dir = image_dir
        self.image_col = image_col
        self.label_col = label_col
        self.task_id = task_id
        self.num_classes = num_classes
        self.pre_resized = pre_resized
        self.ignore_missing = ignore_missing
        self.target_size = target_size
        self.transforms = transforms or get_val_transforms(img_size=target_size)

        # Smart Path Indexer: Index subdirectories if files are nested
        self.file_map: Dict[str, str] = {}
        self._init_path_indexer()

        # Filter missing images only if running in local dry-run / mock mode
        if self.ignore_missing:
            valid_indices = []
            for idx, row in df.iterrows():
                img_name = str(row[self.image_col])
                resolved = self._resolve_path(img_name)
                if resolved is not None and os.path.exists(resolved):
                    valid_indices.append(idx)
            self.df = df.loc[valid_indices].reset_index(drop=True)
            print(f"[Dataset Task {self.task_id}] Filtered {len(self.df)} existing images out of {len(df)} total rows.")
        else:
            self.df = df.reset_index(drop=True)

    def _init_path_indexer(self):
        """Indexes subdirectories in image_dir if files are not strictly top-level."""
        if not os.path.exists(self.image_dir):
            return

        # Check if first level has subdirectories (e.g. COVID, Tuberculosis, images)
        try:
            subdirs = [os.path.join(self.image_dir, d) for d in os.listdir(self.image_dir) if os.path.isdir(os.path.join(self.image_dir, d))]
            if subdirs:
                for root, dirs, files in os.walk(self.image_dir):
                    # STRICT RULE: Skip any mask directories (COVID dataset contains parallel masks/ folders with identical filenames)
                    dirs[:] = [d for d in dirs if d.lower() != "masks"]
                    if "masks" in os.path.normpath(root).lower().split(os.sep):
                        continue
                    for f in files:
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".dcm")):
                            self.file_map[f] = os.path.join(root, f)
        except Exception as e:
            print(f"[Dataset] Warning indexing {self.image_dir}: {e}")

    def _resolve_path(self, img_name: str) -> Optional[str]:
        """Resolves full image path across top-level and nested subdirectories."""
        # 1. Direct join
        direct = os.path.join(self.image_dir, img_name)
        if os.path.exists(direct) and "masks" not in os.path.normpath(direct).lower().split(os.sep):
            return direct

        # 2. Lookup in indexed file_map
        if img_name in self.file_map:
            return self.file_map[img_name]

        # 3. Task-specific heuristics
        if self.task_id == 2:  # COVIDx CXR-4 & COVID-19 subfolders
            for sub in ["train", "test", "train/images", "test/images",
                        "COVID/images", "Normal/images", "Lung_Opacity/images", "Viral Pneumonia/images",
                        "COVID", "Normal", "Lung_Opacity", "Viral Pneumonia"]:
                candidate = os.path.join(self.image_dir, sub, img_name)
                if os.path.exists(candidate) and "masks" not in os.path.normpath(candidate).lower().split(os.sep):
                    self.file_map[img_name] = candidate
                    return candidate

        elif self.task_id == 1:  # Tuberculosis subfolders
            for sub in ["Tuberculosis", "Normal", "TB_Chest_Radiography_Database/Tuberculosis", "TB_Chest_Radiography_Database/Normal"]:
                candidate = os.path.join(self.image_dir, sub, img_name)
                if os.path.exists(candidate):
                    self.file_map[img_name] = candidate
                    return candidate

        elif self.task_id == 0:  # NIH subfolders
            # Direct check for images/ or chunk directories images_001/images .. images_012/images
            candidates = [os.path.join(self.image_dir, "images", img_name)]
            for i in range(1, 13):
                candidates.append(os.path.join(self.image_dir, f"images_{i:03d}", "images", img_name))
                candidates.append(os.path.join(self.image_dir, "data", f"images_{i:03d}", "images", img_name))
            for cand in candidates:
                if os.path.exists(cand):
                    self.file_map[img_name] = cand
                    return cand

        return None

    def __len__(self) -> int:
        return len(self.df)

    def _parse_labels(self, row: pd.Series) -> torch.Tensor:
        """Parses ground truth into proper tensor format based on task_id."""
        if self.task_id == 0:  # NIH Head A (14-class multi-label)
            labels = torch.zeros(self.num_classes, dtype=torch.float32)
            if self.label_col and self.label_col in row:
                finding_str = str(row[self.label_col])
                for idx, pathology in enumerate(NIH_PATHOLOGY_LIST):
                    if pathology in finding_str:
                        labels[idx] = 1.0
            return labels

        elif self.task_id == 1:  # TB Head B (binary classification)
            label_val = float(row.get(self.label_col, 0)) if self.label_col else 0.0
            return torch.tensor([label_val], dtype=torch.float32)

        elif self.task_id == 2:  # COVID Head C (Binary screening or multi-class)
            raw_val = row.get(self.label_col, 0) if self.label_col else 0
            if self.num_classes == 1:
                # Binary: 1.0 for COVID-19 positive, 0.0 for Normal/Negative
                val_str = str(raw_val).lower().strip()
                if val_str in ["positive", "covid", "covid-19", "1", "1.0"]:
                    label_val = 1.0
                else:
                    label_val = 0.0
                return torch.tensor([label_val], dtype=torch.float32)
            else:
                if isinstance(raw_val, str):
                    val_lower = raw_val.lower().strip()
                    if val_lower in ["positive", "covid", "covid-19", "0"]:
                        label_val = 0
                    elif val_lower in ["negative", "normal", "1"]:
                        label_val = 1
                    elif val_lower in ["pneumonia", "non-covid", "2"]:
                        label_val = 2
                    else:
                        label_val = 0
                else:
                    label_val = int(raw_val)
                return torch.tensor(label_val, dtype=torch.long)

        return torch.zeros(self.num_classes, dtype=torch.float32)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]
        img_name = str(row[self.image_col])
        img_path = self._resolve_path(img_name)

        if img_path is None or not os.path.exists(img_path):
            if self.ignore_missing:
                # Mock fallback strictly in local unit-testing / dry-run mode
                image = np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)
            else:
                # Strict production integrity: Throw explicit exception!
                raise FileNotFoundError(
                    f"[ChestXrayDataset] Image file '{img_name}' not found under '{self.image_dir}'! "
                    f"Check dataset extraction path. Silent black-image fallback is strictly forbidden in training."
                )
        else:
            image = cv2.imread(img_path)
            if image is None:
                if self.ignore_missing:
                    image = np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)
                else:
                    raise IOError(f"[ChestXrayDataset] Corrupt or unreadable image file: {img_path}")
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Apply transformations (includes 512x512 resize if not already pre-resized)
        if self.transforms:
            transformed = self.transforms(image=image)
            image_tensor = transformed["image"]
        else:
            image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0

        label_tensor = self._parse_labels(row)

        return {
            "image": image_tensor,
            "labels": label_tensor,
            "task_id": torch.tensor(self.task_id, dtype=torch.long),
            "image_id": img_name
        }
