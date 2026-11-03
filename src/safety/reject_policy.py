"""
LungRay Fail-Safe Decision Policy (Reject Policy)
================================================
Evaluates computed energy and entropy against calibrated clinical thresholds.
Enforces the safety invariant:
    REJECT if Energy < tau_E OR Entropy > tau_H.
"""
from dataclasses import dataclass, field
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default empirical safety thresholds calibrated on NIH test holdout
DEFAULT_ENERGY_THRESHOLD = 9.50
DEFAULT_ENTROPY_THRESHOLD = 0.42


@dataclass
class SafetyDecision:
    """Dataclass holding safety evaluation result."""
    decision: str  # "ACCEPT" or "REJECT"
    is_safe: bool
    energy_score: float
    entropy_score: float
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "is_safe": self.is_safe,
            "energy_score": round(float(self.energy_score), 4),
            "entropy_score": round(float(self.entropy_score), 4),
            "rejection_reasons": self.rejection_reasons,
        }


class SafetyPolicy:
    """
    Evaluates OOD scores and enforces the clinical reject policy.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        energy_threshold: Optional[float] = None,
        entropy_threshold: Optional[float] = None,
    ):
        self.config_path = config_path or os.path.join("configs", "ood_thresholds.json")
        self.energy_threshold = DEFAULT_ENERGY_THRESHOLD
        self.entropy_threshold = DEFAULT_ENTROPY_THRESHOLD
        self._load_config()
        if energy_threshold is not None:
            self.energy_threshold = energy_threshold
        if entropy_threshold is not None:
            self.entropy_threshold = entropy_threshold

    def _load_config(self) -> None:
        """Loads thresholds from JSON config if available."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as fh:
                    cfg = json.load(fh)
                if "energy_score" in cfg and "threshold" in cfg["energy_score"]:
                    self.energy_threshold = float(cfg["energy_score"]["threshold"])
                if "entropy_score" in cfg and "threshold" in cfg["entropy_score"]:
                    self.entropy_threshold = float(cfg["entropy_score"]["threshold"])
                logger.info(
                    "Loaded OOD thresholds from %s (Energy: %.2f, Entropy: %.2f)",
                    self.config_path,
                    self.energy_threshold,
                    self.entropy_threshold,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to parse %s (%s); using defaults (Energy: %.2f, Entropy: %.2f)",
                    self.config_path,
                    exc,
                    self.energy_threshold,
                    self.entropy_threshold,
                )

    def evaluate(self, energy_score: float, entropy_score: float) -> SafetyDecision:
        """
        Evaluates energy and entropy against calibrated safety thresholds.

        Reject criteria:
        1. Energy < tau_E: Image feature distribution deviates significantly from
           valid adult frontal CXR patterns (e.g. noise, inverted, lateral, CT, natural images).
        2. Entropy > tau_H: Multi-label probability distribution exhibits excessive
           predictive ambiguity / conflict.
        """
        reasons: List[str] = []

        if energy_score < self.energy_threshold:
            reasons.append(
                f"Điểm số năng lượng thấp ({energy_score:.2f} < {self.energy_threshold:.2f}): "
                "Hình ảnh có dấu hiệu ngoài phân phối chuẩn (Out-of-Distribution/CXR không chuẩn tư thế)."
            )

        if entropy_score > self.entropy_threshold:
            reasons.append(
                f"Độ hỗn loạn thông tin cao ({entropy_score:.2f} > {self.entropy_threshold:.2f}): "
                "Mức độ bất định dự đoán vượt ngưỡng an toàn lâm sàng cho phép."
            )

        is_safe = len(reasons) == 0
        decision = "ACCEPT" if is_safe else "REJECT"

        return SafetyDecision(
            decision=decision,
            is_safe=is_safe,
            energy_score=float(energy_score),
            entropy_score=float(entropy_score),
            rejection_reasons=reasons,
        )
