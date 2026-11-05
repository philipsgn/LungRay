"""Pydantic request/response schemas for the LungRay FastAPI backend."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    device: str = Field(..., description="torch device used for inference")
    version: str = Field(..., description="API version")
    ood_failsafe_enabled: bool = Field(default=True, description="Whether OOD Fail-Safe policy is active")
    active_checkpoint: str = Field(default="checkpoints/best_model.pth", description="Active checkpoint path")


class SafetyDecisionSchema(BaseModel):
    decision: str = Field(..., description="ACCEPT or REJECT")
    is_safe: bool = Field(..., description="True if accepted, False if rejected")
    energy_score: float = Field(..., description="Sigmoid energy score")
    entropy_score: float = Field(..., description="Mean Shannon entropy")
    rejection_reasons: list[str] = Field(default_factory=list, description="List of rejection reasons")


class ReportResponse(BaseModel):
    status: str = Field(..., description="GENERATED or BLOCKED")
    is_blocked: bool = Field(..., description="Whether report was blocked by safety fail-safe")
    findings: list[str] = Field(default_factory=list)
    anatomical_locations: list[str] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    impression: str = Field(default="")
    recommendations: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default="")


class PredictionResponse(BaseModel):
    head_a_prediction: dict[str, float] = Field(
        ..., description="Map of 14 NIH pathology names to predicted probabilities"
    )
    head_b_tb_screening: dict = Field(
        ..., description="TB screening result with probability and binary flag"
    )
    head_c_covidx: dict = Field(
        ..., description="COVID-19 screening result with probability and binary flag"
    )
    inference_time_ms: float = Field(..., ge=0.0, description="Pure inference latency in ms")
    safety: SafetyDecisionSchema = Field(
        ..., description="OOD Fail-Safe evaluation and rejection decision"
    )
    report: ReportResponse = Field(
        ..., description="Preliminary grounded clinical report"
    )


class ExplainResponse(BaseModel):
    heatmap_base64: str = Field(..., description="Base64-encoded Grad-CAM heatmap PNG")
    overlay_base64: str = Field(..., description="Base64-encoded heatmap overlay PNG")
    contour_base64: str = Field(default="", description="Base64-encoded clinical lesion iso-contour overlay PNG")
    lesion_bounding_boxes: list[dict] = Field(default_factory=list, description="Detected lesion bounding boxes and centroids")
    lesion_area_ratio: float = Field(default=0.0, description="Ratio of detected lesion area to total pulmonary field")
    cam_resolution: str = Field(default="", description="Spatial resolution of multi-scale CAM")
    target_head: str = Field(..., description="Head used for explanation")
    target_class: int = Field(..., description="Class index used for explanation")
    target_disease_name: str = Field(default="", description="Name of the pathology explained")
    target_probability: float = Field(default=1.0, ge=0.0, le=1.0, description="Model predicted probability for target")
    target_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Decision threshold for target")
    is_target_positive: bool = Field(default=True, description="Whether target probability exceeds decision threshold")
    in_lung_energy_ratio: float = Field(default=1.0, ge=0.0, le=1.0, description="Activation energy inside anatomy ratio [0, 1]")
    audit_pass: bool = Field(default=True, description="Whether in-lung energy ratio is >= 80%")
    is_grounded: bool = Field(default=True, description="Whether clinical anatomical grounding was applied")


class AuditResponse(BaseModel):
    in_lung_energy_ratio: float = Field(..., ge=0.0, le=1.0)
    pass_80_percent: bool = Field(..., description="Whether the in-lung ratio meets the 80% threshold")
    lung_mask_base64: str = Field(..., description="Base64-encoded lung mask PNG")
