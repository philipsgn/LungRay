"""
LungRay Explainability & Trustworthy AI Modules
==============================================
Contains Grad-CAM / Grad-CAM++ generators, Adaptive Binarization,
IoU evaluation against VinDr-CXR, and Shortcut Learning Audit.
"""

from src.explainability.grad_cam import GradCAMExplainer
from src.explainability.shortcut_audit import LungSegmenter, ShortcutAuditEngine

__all__ = [
    "GradCAMExplainer",
    "LungSegmenter",
    "ShortcutAuditEngine",
]
