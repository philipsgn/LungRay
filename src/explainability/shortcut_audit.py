"""
LungRay Shortcut Learning Audit
===============================
Offline lung-field segmentation and in-lung activation energy measurement for
Head C (COVID-19).  The audit verifies that Grad-CAM energy remains inside the
pulmonary fields instead of relying on external shortcuts such as text markers,
laterality labels, or image borders.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import cv2
import numpy as np
import torch
from scipy import ndimage

from src.explainability.grad_cam import GradCAMExplainer


class LungSegmenter:
    """
    Classical morphology-based lung-field segmenter.

    The segmenter is fully offline and deterministic: Otsu thresholding inside
    an elliptical thorax region, morphological closing/opening, connected
    component filtering, and hole filling.
    """

    def __init__(
        self,
        min_area_ratio: float = 0.01,
        max_area_ratio: float = 0.85,
        max_components: int = 3,
    ) -> None:
        if not 0.0 < float(min_area_ratio) < 1.0:
            raise ValueError("min_area_ratio must be in (0, 1).")
        if not 0.0 < float(max_area_ratio) <= 1.0:
            raise ValueError("max_area_ratio must be in (0, 1].")
        if float(min_area_ratio) >= float(max_area_ratio):
            raise ValueError("min_area_ratio must be smaller than max_area_ratio.")
        if not isinstance(max_components, int) or max_components < 1:
            raise ValueError("max_components must be a positive integer.")
        self.min_area_ratio = float(min_area_ratio)
        self.max_area_ratio = float(max_area_ratio)
        self.max_components = max_components

    def predict_mask(self, img: np.ndarray) -> np.ndarray:
        """
        Extract a binary lung-field mask.

        Args:
            img: Chest X-ray of shape ``(H, W)`` or ``(H, W, 3)``.  Values may be
                ``uint8`` in ``[0, 255]`` or float in ``[0, 1]``.

        Returns:
            ``uint8`` mask of shape ``(H, W)`` with values in ``{0, 1}``.
        """
        gray = self._to_grayscale(img)
        height, width = gray.shape
        if height < 16 or width < 16:
            raise ValueError("Input image must be at least 16x16 pixels.")

        thorax = self._thorax_roi_mask(height, width)
        candidate = self._otsu_lung_candidate(gray, thorax)
        mask = self._refine_candidate(candidate, thorax)

        area_ratio = float(mask.sum()) / float(height * width)
        if not self.min_area_ratio <= area_ratio <= self.max_area_ratio:
            mask = self._fallback_lung_prior(height, width)

        return np.uint8(mask > 0)

    @staticmethod
    def _to_grayscale(img: np.ndarray) -> np.ndarray:
        array = np.asarray(img)
        if array.ndim == 2:
            gray = array
        elif array.ndim == 3 and array.shape[2] in (3, 4):
            gray = cv2.cvtColor(array[..., :3], cv2.COLOR_RGB2GRAY)
        else:
            raise ValueError("img must have shape (H, W) or (H, W, 3).")
        if gray.size == 0:
            raise ValueError("img must not be empty.")

        if gray.dtype == np.uint8:
            return gray
        gray = np.nan_to_num(
            np.asarray(gray, dtype=np.float32),
            nan=0.0,
            posinf=255.0,
            neginf=0.0,
        )
        if float(gray.max()) <= 1.0:
            gray = gray * 255.0
        return np.uint8(np.clip(gray, 0.0, 255.0))

    @staticmethod
    def _thorax_roi_mask(height: int, width: int) -> np.ndarray:
        mask = np.zeros((height, width), dtype=np.uint8)
        center = (width // 2, height // 2)
        axes = (max(1, int(round(width * 0.42))), max(1, int(round(height * 0.46))))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, thickness=-1)
        return mask

    @staticmethod
    def _otsu_lung_candidate(gray: np.ndarray, thorax: np.ndarray) -> np.ndarray:
        values = gray[thorax > 0]
        if values.size == 0:
            return np.zeros_like(gray)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        threshold, _ = cv2.threshold(
            values,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )
        if not np.isfinite(threshold):
            threshold = float(np.median(values))
        candidate = np.uint8((blurred <= threshold) & (thorax > 0))
        return candidate

    def _refine_candidate(
        self,
        candidate: np.ndarray,
        thorax: np.ndarray,
    ) -> np.ndarray:
        height, width = candidate.shape
        base = max(3, int(round(min(height, width) * 0.025)))
        kernel_size = base if base % 2 == 1 else base + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )

        mask = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = np.uint8((mask > 0) & (thorax > 0))

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )
        if num_labels <= 1:
            return np.zeros_like(mask)

        components = []
        for label in range(1, num_labels):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area <= 0:
                continue
            center_x, center_y = centroids[label]
            if not (0.0 <= center_x < width and 0.0 <= center_y < height):
                continue
            components.append((area, label))
        if not components:
            return np.zeros_like(mask)

        components.sort(key=lambda item: item[0], reverse=True)
        largest_area = components[0][0]
        min_pixels = max(
            int(round(height * width * self.min_area_ratio * 0.5)),
            int(round(largest_area * 0.12)),
        )
        selected = [
            label
            for area, label in components[: self.max_components]
            if area >= min_pixels
        ]
        if not selected:
            selected = [components[0][1]]

        refined = np.isin(labels, selected).astype(np.uint8)
        refined = ndimage.binary_fill_holes(refined).astype(np.uint8)
        refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel, iterations=2)
        refined = ndimage.binary_fill_holes(refined).astype(np.uint8)
        return np.uint8((refined > 0) & (thorax > 0))

    @staticmethod
    def _fallback_lung_prior(height: int, width: int) -> np.ndarray:
        mask = np.zeros((height, width), dtype=np.uint8)
        axis_x = max(1, int(round(width * 0.17)))
        axis_y = max(1, int(round(height * 0.31)))
        left_center = (int(round(width * 0.31)), int(round(height * 0.52)))
        right_center = (int(round(width * 0.69)), int(round(height * 0.52)))
        cv2.ellipse(mask, left_center, (axis_x, axis_y), 0, 0, 360, 255, -1)
        cv2.ellipse(mask, right_center, (axis_x, axis_y), 0, 0, 360, 255, -1)
        kernel_size = max(3, int(round(min(height, width) * 0.03)))
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        return np.uint8(mask > 0)


class ShortcutAuditEngine:
    """
    Quantify whether Grad-CAM energy is concentrated inside the lung fields.

    The audit passes when ``in_lung_ratio >= 0.80`` for positive COVID-19 cases.
    """

    def __init__(
        self,
        lung_segmenter: Optional[LungSegmenter] = None,
        pass_threshold: float = 0.80,
    ) -> None:
        if not 0.0 <= float(pass_threshold) <= 1.0:
            raise ValueError("pass_threshold must be in [0, 1].")
        self.lung_segmenter = lung_segmenter or LungSegmenter()
        if not isinstance(self.lung_segmenter, LungSegmenter):
            raise TypeError("lung_segmenter must be a LungSegmenter instance.")
        self.pass_threshold = float(pass_threshold)

    def compute_in_lung_ratio(
        self,
        heatmap: np.ndarray,
        lung_mask: np.ndarray,
    ) -> float:
        """
        Compute the fraction of heatmap energy inside ``lung_mask == 1``.

        A heatmap with zero total energy returns ``0.0``; an empty mask also
        returns ``0.0``.  Negative heatmap values are clipped to zero because
        Grad-CAM heatmaps are non-negative.
        """
        heat = np.asarray(heatmap, dtype=np.float64)
        mask = np.asarray(lung_mask)
        if heat.ndim != 2:
            raise ValueError("heatmap must be a two-dimensional array.")
        if mask.ndim != 2:
            raise ValueError("lung_mask must be a two-dimensional array.")
        if heat.shape != mask.shape:
            raise ValueError(
                f"heatmap shape {heat.shape} does not match lung_mask shape "
                f"{mask.shape}."
            )
        if heat.size == 0:
            raise ValueError("heatmap and lung_mask must not be empty.")
        if not np.isfinite(heat).all():
            raise ValueError("heatmap contains NaN or infinite values.")

        positive_heat = np.maximum(heat, 0.0)
        total_energy = float(positive_heat.sum())
        if total_energy <= 1e-12:
            return 0.0

        lung_binary = mask > 0.5
        lung_energy = float(positive_heat[lung_binary].sum()) if lung_binary.any() else 0.0
        ratio = lung_energy / total_energy
        return float(np.clip(ratio, 0.0, 1.0))

    def audit_sample(
        self,
        model: torch.nn.Module,
        explainer: GradCAMExplainer,
        img_tensor: torch.Tensor,
        original_img: np.ndarray,
        head_name: str = "head_c",
        target_class_idx: int = 0,
    ) -> Dict[str, Any]:
        """
        Run a single-sample shortcut audit.

        Returns:
            Dictionary with ``in_lung_ratio``, ``heatmap``, ``lung_mask``, and
            ``pass_80_percent``.
        """
        if not isinstance(model, torch.nn.Module):
            raise TypeError("model must be an instance of torch.nn.Module.")
        if not isinstance(explainer, GradCAMExplainer):
            raise TypeError("explainer must be a GradCAMExplainer instance.")
        heatmap = explainer.generate(
            img_tensor,
            head_name=head_name,
            target_class_idx=target_class_idx,
        )
        lung_mask = self.lung_segmenter.predict_mask(original_img)
        if lung_mask.shape != heatmap.shape:
            lung_mask = cv2.resize(
                lung_mask,
                (heatmap.shape[1], heatmap.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
            lung_mask = np.uint8(lung_mask > 0)
        ratio = self.compute_in_lung_ratio(heatmap, lung_mask)
        return {
            "in_lung_ratio": ratio,
            "heatmap": heatmap,
            "lung_mask": lung_mask,
            "pass_80_percent": bool(ratio >= self.pass_threshold),
        }
