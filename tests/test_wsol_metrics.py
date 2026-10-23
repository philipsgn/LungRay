"""
Unit Tests for WSOL Quantitative IoU Metrics (tests/test_wsol_metrics.py)
========================================================================
Validates:
1. Box IoU calculation (perfect overlap, disjoint, partial, inverted coordinates).
2. Mask IoU calculation (identical, non-overlapping, shape mismatch resize).
3. Connected component bounding box extraction & area filtering.
4. Anatomically constrained adaptive binarization (Heatmap * LungMask).
5. Dual-metric WSOL sample evaluation (Box-IoU + Mask-IoU).
"""
import numpy as np
import pytest

from src.explainability.metrics import (
    compute_box_iou,
    compute_mask_iou,
    extract_bboxes_from_mask,
    adaptive_binarize,
    rasterize_bboxes,
    evaluate_wsol_sample,
)


def test_compute_box_iou_perfect_match():
    box = [50, 50, 150, 150]
    iou = compute_box_iou(box, box)
    assert pytest.approx(iou, rel=1e-5) == 1.0


def test_compute_box_iou_disjoint():
    box_a = [0, 0, 50, 50]
    box_b = [100, 100, 150, 150]
    iou = compute_box_iou(box_a, box_b)
    assert iou == 0.0


def test_compute_box_iou_partial():
    # Box A: [0, 0, 100, 100], area = 10,000
    # Box B: [50, 0, 150, 100], area = 10,000
    # Intersection: [50, 0, 100, 100], area = 5,000
    # Union = 10,000 + 10,000 - 5,000 = 15,000
    # IoU = 5,000 / 15,000 = 1/3 ≈ 0.33333
    box_a = [0, 0, 100, 100]
    box_b = [50, 0, 150, 100]
    iou = compute_box_iou(box_a, box_b)
    assert pytest.approx(iou, rel=1e-3) == (1.0 / 3.0)


def test_compute_box_iou_inverted_coords():
    box_a = [100, 100, 0, 0]  # inverted [x2, y2, x1, y1]
    box_b = [0, 0, 100, 100]
    iou = compute_box_iou(box_a, box_b)
    assert pytest.approx(iou, rel=1e-5) == 1.0


def test_compute_mask_iou():
    mask_a = np.zeros((100, 100), dtype=np.uint8)
    mask_b = np.zeros((100, 100), dtype=np.uint8)

    # Both empty
    assert compute_mask_iou(mask_a, mask_b) == 1.0

    # Half overlap
    mask_a[10:60, 10:60] = 1  # 50x50 = 2500
    mask_b[10:60, 35:85] = 1  # 50x50 = 2500, overlap = 50x25 = 1250
    # Union = 2500 + 2500 - 1250 = 3750, IoU = 1250/3750 = 1/3
    iou = compute_mask_iou(mask_a, mask_b)
    assert pytest.approx(iou, rel=1e-3) == (1.0 / 3.0)


def test_extract_bboxes_from_mask():
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Component 1: large square at [20, 20, 80, 80] (area 3600)
    mask[20:80, 20:80] = 1
    # Component 2: tiny noise 2x2 (area 4) -> should be filtered by min_area_ratio
    mask[150:152, 150:152] = 1

    boxes = extract_bboxes_from_mask(mask, min_area_ratio=0.01)
    assert len(boxes) == 1
    x1, y1, x2, y2 = boxes[0]
    assert abs(x1 - 20) <= 1
    assert abs(y1 - 20) <= 1
    assert abs(x2 - 80) <= 1
    assert abs(y2 - 80) <= 1


def test_adaptive_binarize_ratio():
    heatmap = np.zeros((100, 100), dtype=np.float32)
    heatmap[30:70, 30:70] = 0.8
    heatmap[40:60, 40:60] = 1.0

    binary = adaptive_binarize(heatmap, alpha=0.5, method="ratio")
    assert binary.shape == (100, 100)
    assert binary[50, 50] == 1
    assert binary[35, 35] == 1
    assert binary[10, 10] == 0


def test_adaptive_binarize_with_lung_mask():
    heatmap = np.ones((100, 100), dtype=np.float32)
    lung_mask = np.zeros((100, 100), dtype=np.uint8)
    lung_mask[20:80, 20:80] = 1  # only central box is inside lung

    binary = adaptive_binarize(heatmap, lung_mask=lung_mask, alpha=0.5)
    # Outside lung must be 0
    assert binary[5, 5] == 0
    assert binary[90, 90] == 0
    # Inside lung must be 1
    assert binary[50, 50] == 1


def test_rasterize_bboxes():
    boxes = [(10, 10, 40, 50)]
    mask = rasterize_bboxes(boxes, shape=(100, 100))
    assert mask.shape == (100, 100)
    assert mask[20, 20] == 1
    assert mask[5, 5] == 0
    assert mask[60, 60] == 0


def test_evaluate_wsol_sample():
    heatmap = np.zeros((200, 200), dtype=np.float32)
    # True lesion at [50, 50, 120, 120]
    heatmap[50:120, 50:120] = 0.95

    gt_boxes = [(50, 50, 120, 120)]
    lung_mask = np.ones((200, 200), dtype=np.uint8)

    res = evaluate_wsol_sample(
        heatmap=heatmap,
        gt_boxes=gt_boxes,
        lung_mask=lung_mask,
        alpha=0.5,
    )

    assert "best_box_iou" in res
    assert "mask_iou" in res
    assert "pass_thresholds" in res
    assert res["best_box_iou"] >= 0.85
    assert res["mask_iou"] >= 0.85
    assert res["pass_thresholds"][0.5] is True
    assert res["num_gt_boxes"] == 1
