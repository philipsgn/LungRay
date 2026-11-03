"""
LungRay Explainability & Trustworthy AI Modules
==============================================
Contains Grad-CAM / Grad-CAM++ generators, Adaptive Binarization,
WSOL quantitative IoU evaluation, and Shortcut Learning Audit.
"""

from src.explainability.grad_cam import (
    GradCAMExplainer,
    MultiScaleGradCAMPlusPlus,
    extract_adaptive_contour,
    render_contour_overlay,
)
from src.explainability.shortcut_audit import LungSegmenter, ShortcutAuditEngine
from src.explainability.metrics import (
    compute_box_iou,
    compute_mask_iou,
    extract_bboxes_from_mask,
    adaptive_binarize,
    rasterize_bboxes,
    evaluate_wsol_sample,
)

__all__ = [
    "GradCAMExplainer",
    "MultiScaleGradCAMPlusPlus",
    "extract_adaptive_contour",
    "render_contour_overlay",
    "LungSegmenter",
    "ShortcutAuditEngine",
    "compute_box_iou",
    "compute_mask_iou",
    "extract_bboxes_from_mask",
    "adaptive_binarize",
    "rasterize_bboxes",
    "evaluate_wsol_sample",
]
