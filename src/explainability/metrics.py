"""
LungRay WSOL Grounding & Quantitative IoU Metrics (src/explainability/metrics.py)
================================================================================
Inviolable Constraint 4 (Ràng buộc sống còn số 4):
- Bounding Box CHỈ được sử dụng ở tập đánh giá để đo đạc định lượng chỉ số IoU
  (VinDr-CXR, RSNA Pneumonia Detection).
- Tuyệt đối không dùng Bounding Box để giám sát hoặc huấn luyện mô hình.

Features:
1. compute_box_iou: Geometric Intersection-over-Union between two bounding boxes.
2. compute_mask_iou: Pixel-wise Intersection-over-Union between two binary masks.
3. extract_bboxes_from_mask: Connected component contour extraction to bounding boxes.
4. adaptive_binarize: Anatomically constrained adaptive thresholding (Heatmap * LungMask).
5. rasterize_bboxes: Converts bounding box lists into 2D binary raster masks.
6. evaluate_wsol_sample: Dual-metric evaluation computing Box-IoU and Mask-IoU.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np


def compute_box_iou(
    box_a: Union[List[float], Tuple[float, float, float, float], np.ndarray],
    box_b: Union[List[float], Tuple[float, float, float, float], np.ndarray],
) -> float:
    """
    Computes geometric Intersection over Union (IoU) between two bounding boxes.
    Boxes are in format [x1, y1, x2, y2].

    Args:
        box_a: Bounding box [x1, y1, x2, y2].
        box_b: Bounding box [x1, y1, x2, y2].

    Returns:
        float IoU value in [0.0, 1.0].
    """
    x1_a, y1_a, x2_a, y2_a = float(box_a[0]), float(box_a[1]), float(box_a[2]), float(box_a[3])
    x1_b, y1_b, x2_b, y2_b = float(box_b[0]), float(box_b[1]), float(box_b[2]), float(box_b[3])

    # Canonicalize coordinates
    x1_a, x2_a = min(x1_a, x2_a), max(x1_a, x2_a)
    y1_a, y2_a = min(y1_a, y2_a), max(y1_a, y2_a)
    x1_b, x2_b = min(x1_b, x2_b), max(x1_b, x2_b)
    y1_b, y2_b = min(y1_b, y2_b), max(y1_b, y2_b)

    # Intersection rectangle
    x_left = max(x1_a, x1_b)
    y_top = max(y1_a, y1_b)
    x_right = min(x2_a, x2_b)
    y_bottom = min(y2_a, y2_b)

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area_a = (x2_a - x1_a) * (y2_a - y1_a)
    area_b = (x2_b - x1_b) * (y2_b - y1_b)
    union_area = area_a + area_b - intersection_area

    if union_area <= 0.0:
        return 0.0

    iou = float(intersection_area / union_area)
    return float(np.clip(iou, 0.0, 1.0))


def compute_mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """
    Computes pixel-level Intersection over Union (IoU) between two 2D binary masks.

    Args:
        mask_a: 2D binary array or boolean array.
        mask_b: 2D binary array or boolean array.

    Returns:
        float IoU value in [0.0, 1.0].
    """
    if mask_a.ndim != 2 or mask_b.ndim != 2:
        raise ValueError(f"Masks must be 2D, got shapes {mask_a.shape} and {mask_b.shape}")

    if mask_a.shape != mask_b.shape:
        mask_b = cv2.resize(
            mask_b.astype(np.uint8),
            (mask_a.shape[1], mask_a.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

    bin_a = mask_a > 0
    bin_b = mask_b > 0

    intersection = np.logical_and(bin_a, bin_b).sum()
    union = np.logical_or(bin_a, bin_b).sum()

    if union == 0:
        return 1.0 if (intersection == 0 and bin_a.sum() == 0 and bin_b.sum() == 0) else 0.0

    iou = float(intersection / union)
    return float(np.clip(iou, 0.0, 1.0))


def extract_bboxes_from_mask(
    binary_mask: np.ndarray,
    min_area_ratio: float = 0.005,
    max_boxes: int = 5,
) -> List[Tuple[int, int, int, int]]:
    """
    Extracts bounding boxes [x1, y1, x2, y2] from connected components in a binary mask.

    Args:
        binary_mask: 2D binary array (values 0 and >0).
        min_area_ratio: Minimum component area relative to total mask area.
        max_boxes: Maximum number of bounding boxes to return (sorted by area desc).

    Returns:
        List of [x1, y1, x2, y2] coordinates (integers).
    """
    if binary_mask.ndim != 2 or binary_mask.sum() == 0:
        return []

    u8_mask = (binary_mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(u8_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return []

    h, w = binary_mask.shape[:2]
    total_area = float(h * w)
    min_area = total_area * min_area_ratio

    boxes = []
    contour_areas = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            boxes.append((int(x), int(y), int(x + bw), int(y + bh)))
            contour_areas.append(area)

    if not boxes and contours:
        # Fallback: Pick the single largest contour even if below min_area_ratio
        largest_cnt = max(contours, key=cv2.contourArea)
        x, y, bw, bh = cv2.boundingRect(largest_cnt)
        if bw > 0 and bh > 0:
            return [(int(x), int(y), int(x + bw), int(y + bh))]
        return []

    # Sort boxes by contour area descending
    sorted_indices = np.argsort(contour_areas)[::-1]
    sorted_boxes = [boxes[i] for i in sorted_indices[:max_boxes]]
    return sorted_boxes


def adaptive_binarize(
    heatmap: np.ndarray,
    lung_mask: Optional[np.ndarray] = None,
    alpha: float = 0.5,
    method: str = "ratio",
) -> np.ndarray:
    """
    Anatomically constrained adaptive binarization of continuous activation heatmap.
    Applies Clinical Pulmonary Masking (M_clean = Heatmap * LungMask) to suppress
    all non-thoracic artifacts before thresholding.

    Args:
        heatmap: 2D numpy array with values in [0.0, 1.0].
        lung_mask: Optional 2D binary array of lung parenchyma (values 0 or >0).
        alpha: Adaptive threshold coefficient in [0.0, 1.0].
        method: 'ratio' (alpha * max) or 'otsu' (Otsu threshold on clean region).

    Returns:
        2D binary numpy array of shape matching heatmap (0 or 1).
    """
    if heatmap.ndim != 2:
        raise ValueError(f"Heatmap must be 2D, got shape {heatmap.shape}")

    clean = heatmap.astype(np.float32)

    if lung_mask is not None:
        if lung_mask.shape != heatmap.shape:
            lung_mask_resized = cv2.resize(
                (lung_mask > 0).astype(np.uint8),
                (heatmap.shape[1], heatmap.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
        else:
            lung_mask_resized = (lung_mask > 0).astype(np.uint8)
        clean = clean * lung_mask_resized.astype(np.float32)

    max_val = float(clean.max())
    if max_val <= 1e-7:
        return np.zeros_like(heatmap, dtype=np.uint8)

    if method == "ratio":
        threshold = float(alpha) * max_val
        binary = (clean >= threshold).astype(np.uint8)
        return binary

    elif method == "otsu":
        u8 = np.clip((clean / max_val) * 255.0, 0, 255).astype(np.uint8)
        # Apply Otsu on positive activation pixels
        pos_mask = u8 > 0
        if pos_mask.sum() > 10:
            otsu_thresh, _ = cv2.threshold(u8[pos_mask], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binary = (u8 >= otsu_thresh).astype(np.uint8)
        else:
            binary = (u8 >= int(alpha * 255.0)).astype(np.uint8)
        return binary

    else:
        raise ValueError(f"Unsupported binarization method: {method!r}. Choose 'ratio' or 'otsu'.")


def rasterize_bboxes(
    boxes: List[Union[Tuple[float, float, float, float], List[float]]],
    shape: Tuple[int, int],
) -> np.ndarray:
    """
    Renders a list of [x1, y1, x2, y2] bounding boxes into a 2D binary raster mask.

    Args:
        boxes: List of bounding boxes [x1, y1, x2, y2].
        shape: Output mask shape (height, width).

    Returns:
        2D binary uint8 mask of shape (height, width).
    """
    h, w = shape
    mask = np.zeros((h, w), dtype=np.uint8)
    for box in boxes:
        x1, y1, x2, y2 = [int(round(float(v))) for v in box]
        x1 = max(0, min(w, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h, y1))
        y2 = max(0, min(h, y2))
        if x2 > x1 and y2 > y1:
            mask[y1:y2, x1:x2] = 1
    return mask


def evaluate_wsol_sample(
    heatmap: np.ndarray,
    gt_boxes: List[Union[Tuple[float, float, float, float], List[float]]],
    lung_mask: Optional[np.ndarray] = None,
    alpha: float = 0.5,
    binarize_method: str = "ratio",
    iou_thresholds: Tuple[float, ...] = (0.1, 0.3, 0.5),
) -> Dict[str, Any]:
    """
    Evaluates a single WSOL sample against Ground-Truth Bounding Boxes.
    Provides Dual-Metric Evaluation:
    - Box-level IoU: Best IoU between predicted boxes and ground-truth boxes.
    - Mask-level IoU: Pixel-level IoU between binarized heatmap and rasterized GT boxes.

    Args:
        heatmap: 2D continuous activation map in [0.0, 1.0].
        gt_boxes: List of ground-truth bounding boxes [[x1, y1, x2, y2], ...].
        lung_mask: Optional 2D binary lung parenchyma mask.
        alpha: Adaptive binarization parameter.
        binarize_method: 'ratio' or 'otsu'.
        iou_thresholds: Success thresholds to report (e.g. 0.1, 0.3, 0.5).

    Returns:
        Dictionary containing quantitative metrics:
        - 'best_box_iou': float
        - 'mean_box_iou': float
        - 'mask_iou': float
        - 'pred_boxes': list of predicted boxes
        - 'num_pred_boxes': int
        - 'num_gt_boxes': int
        - 'pass_thresholds': dict of bools mapping threshold to pass/fail
        - 'binary_mask': 2D binary mask
    """
    h, w = heatmap.shape[:2]
    binary_pred = adaptive_binarize(
        heatmap=heatmap,
        lung_mask=lung_mask,
        alpha=alpha,
        method=binarize_method,
    )

    pred_boxes = extract_bboxes_from_mask(binary_pred)

    if not gt_boxes:
        return {
            "best_box_iou": 0.0,
            "mean_box_iou": 0.0,
            "mask_iou": 0.0,
            "pred_boxes": pred_boxes,
            "num_pred_boxes": len(pred_boxes),
            "num_gt_boxes": 0,
            "pass_thresholds": {th: False for th in iou_thresholds},
            "binary_mask": binary_pred,
        }

    # 1. Box-level IoU matrix
    if pred_boxes:
        all_box_ious = []
        for p_box in pred_boxes:
            for g_box in gt_boxes:
                iou_val = compute_box_iou(p_box, g_box)
                all_box_ious.append(iou_val)
        best_box_iou = float(max(all_box_ious)) if all_box_ious else 0.0
        mean_box_iou = float(np.mean(all_box_ious)) if all_box_ious else 0.0
    else:
        best_box_iou = 0.0
        mean_box_iou = 0.0

    # 2. Mask-level IoU
    gt_raster_mask = rasterize_bboxes(gt_boxes, shape=(h, w))
    mask_iou = compute_mask_iou(binary_pred, gt_raster_mask)

    pass_thresholds = {
        float(th): bool(best_box_iou >= th) for th in iou_thresholds
    }

    return {
        "best_box_iou": round(best_box_iou, 4),
        "mean_box_iou": round(mean_box_iou, 4),
        "mask_iou": round(mask_iou, 4),
        "pred_boxes": pred_boxes,
        "num_pred_boxes": len(pred_boxes),
        "num_gt_boxes": len(gt_boxes),
        "pass_thresholds": pass_thresholds,
        "binary_mask": binary_pred,
    }
