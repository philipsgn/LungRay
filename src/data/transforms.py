"""
LungRay Medical Image Transforms & Augmentations
===============================================
Defines clinically safe transformations using Albumentations.

Rules & Inviolable Constraints:
- Mandatory input spatial resolution: 512x512.
- Interpolation: cv2.INTER_AREA for downsampling.
- STRICTLY PROHIBITED: Vertical flip (violates thoracic anatomical gravity/structure).
- Allowed augmentations: Horizontal flip (heart position accounted for in symmetric pathologies),
  subtle rotation (+-10 degrees), subtle scaling (+-5%), subtle brightness/contrast.
"""
from typing import Tuple
import cv2
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def get_train_transforms(img_size: int = 512) -> A.Compose:
    """
    Returns training transformations with safe medical augmentations.
    """
    return A.Compose([
        A.Resize(
            height=img_size,
            width=img_size,
            interpolation=cv2.INTER_AREA
        ),
        A.HorizontalFlip(p=0.5),
        A.ShiftScaleRotate(
            shift_limit=0.05,
            scale_limit=0.05,
            rotate_limit=10,
            border_mode=cv2.BORDER_CONSTANT,
            value=0,
            p=0.5
        ),
        A.RandomBrightnessContrast(
            brightness_limit=0.10,
            contrast_limit=0.10,
            p=0.4
        ),
        A.Normalize(
            mean=IMAGENET_MEAN,
            std=IMAGENET_STD,
            max_pixel_value=255.0
        ),
        ToTensorV2()
    ])


def get_val_transforms(img_size: int = 512) -> A.Compose:
    """
    Returns validation and test deterministic transformations (resize + normalize only).
    """
    return A.Compose([
        A.Resize(
            height=img_size,
            width=img_size,
            interpolation=cv2.INTER_AREA
        ),
        A.Normalize(
            mean=IMAGENET_MEAN,
            std=IMAGENET_STD,
            max_pixel_value=255.0
        ),
        ToTensorV2()
    ])
