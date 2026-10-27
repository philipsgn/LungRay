"""
LungRay Medical Image Transforms & Augmentations
===============================================
Defines clinically safe transformations using Albumentations.

Rules & Inviolable Constraints:
- Mandatory input spatial resolution: 512x512.
- Interpolation: cv2.INTER_AREA for downsampling.
- STRICTLY PROHIBITED: Vertical flip (violates thoracic anatomical gravity/structure:
  lung apices always superior, diaphragmatic domes always inferior).
- Allowed augmentations: Horizontal flip, subtle rotation (+-7 degrees simulating a
  supine/portable cassette tilt), subtle scale (0.96-1.04) and translation (4%),
  subtle brightness/contrast, and CLAHE for lung-field contrast.
- API compatibility: Albumentations 1.3.x through 2.x (no deprecated ``value=`` arguments).
"""
import inspect
from typing import Optional

import albumentations as A
import cv2
from albumentations.pytorch import ToTensorV2


IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Clinically safe geometric envelope (TASK-013).
MAX_ROTATION_DEGREES = 7.0
SCALE_RANGE = (0.96, 1.04)
TRANSLATE_PERCENT = 0.04


def _resolve_size(img_size: int = 512, image_size: Optional[int] = None) -> int:
    """Accepts both legacy ``image_size`` and canonical ``img_size`` arguments."""
    size = image_size if image_size is not None else img_size
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError(f"Image size must be a positive integer, got: {size!r}")
    return size


def _affine_kwargs() -> dict:
    """Returns border-mode kwargs compatible with Albumentations 1.x and 2.x."""
    params = inspect.signature(A.Affine.__init__).parameters
    kwargs = {
        "translate_percent": (-TRANSLATE_PERCENT, TRANSLATE_PERCENT),
        "scale": SCALE_RANGE,
        "rotate": (-MAX_ROTATION_DEGREES, MAX_ROTATION_DEGREES),
        "p": 0.5,
    }
    if "border_mode" in params:
        kwargs["border_mode"] = cv2.BORDER_CONSTANT
    elif "mode" in params:
        kwargs["mode"] = cv2.BORDER_CONSTANT
    return kwargs


def get_train_transforms(
    img_size: int = 512,
    anti_shortcut: bool = True,
    image_size: Optional[int] = None,
) -> A.Compose:
    """
    Returns training transformations with safe medical augmentations & anti-shortcut mechanisms.

    - Medical Letterboxing: Preserves thoracic anatomical aspect ratio without distortion.
    - CLAHE: Balances contrast distribution across multi-center imaging machines.
    - Safe Affine: Subtle +-7 deg rotation, 0.96-1.04 scale, 4% translation, constant border.
    - STRICTLY PROHIBITED: Vertical flip (violates thoracic gravity & organ topology).

    Args:
        img_size: Canonical square output resolution (default 512).
        anti_shortcut: Enables CLAHE when True.
        image_size: Legacy alias for ``img_size`` (kept for backward compatibility).

    Returns:
        Albumentations composition producing a float tensor ``(3, S, S)``.
    """
    effective_size = _resolve_size(img_size=img_size, image_size=image_size)

    aug_list = [
        A.LongestMaxSize(max_size=effective_size, interpolation=cv2.INTER_AREA),
        A.PadIfNeeded(
            min_height=effective_size,
            min_width=effective_size,
            border_mode=cv2.BORDER_CONSTANT,
        ),
    ]

    if anti_shortcut:
        aug_list.append(A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.7))

    aug_list.extend(
        [
            A.HorizontalFlip(p=0.5),
            A.Affine(**_affine_kwargs()),
            A.RandomBrightnessContrast(
                brightness_limit=0.10,
                contrast_limit=0.10,
                p=0.4,
            ),
            A.Normalize(
                mean=IMAGENET_MEAN,
                std=IMAGENET_STD,
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ]
    )

    return A.Compose(aug_list)


def get_val_transforms(
    img_size: int = 512,
    image_size: Optional[int] = None,
) -> A.Compose:
    """
    Returns validation and test deterministic transformations (letterbox + normalize only).

    Args:
        img_size: Canonical square output resolution (default 512).
        image_size: Legacy alias for ``img_size`` (kept for backward compatibility).

    Returns:
        Albumentations composition producing a float tensor ``(3, S, S)``.
    """
    effective_size = _resolve_size(img_size=img_size, image_size=image_size)

    return A.Compose(
        [
            A.LongestMaxSize(max_size=effective_size, interpolation=cv2.INTER_AREA),
            A.PadIfNeeded(
                min_height=effective_size,
                min_width=effective_size,
                border_mode=cv2.BORDER_CONSTANT,
            ),
            A.Normalize(
                mean=IMAGENET_MEAN,
                std=IMAGENET_STD,
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ]
    )
