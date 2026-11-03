"""
LungRay Safety Package: Fail-Safe OOD Detection and Grounded Reporting
======================================================================
"""
from src.safety.ood_scores import (
    compute_sigmoid_energy,
    compute_shannon_entropy,
    compute_max_sigmoid_confidence,
)
from src.safety.reject_policy import (
    SafetyDecision,
    SafetyPolicy,
    DEFAULT_ENERGY_THRESHOLD,
    DEFAULT_ENTROPY_THRESHOLD,
)
from src.safety.report_generator import (
    ClinicalReport,
    ClinicalReportGenerator,
    extract_anatomical_zone_from_heatmap,
)

__all__ = [
    "compute_sigmoid_energy",
    "compute_shannon_entropy",
    "compute_max_sigmoid_confidence",
    "SafetyDecision",
    "SafetyPolicy",
    "DEFAULT_ENERGY_THRESHOLD",
    "DEFAULT_ENTROPY_THRESHOLD",
    "ClinicalReport",
    "ClinicalReportGenerator",
    "extract_anatomical_zone_from_heatmap",
]
