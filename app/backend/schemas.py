"""Pydantic request/response schemas for the LungRay FastAPI backend."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    device: str = Field(..., description="torch device used for inference")
    version: str = Field(..., description="API version")


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


class ExplainResponse(BaseModel):
    heatmap_base64: str = Field(..., description="Base64-encoded Grad-CAM heatmap PNG")
    overlay_base64: str = Field(..., description="Base64-encoded heatmap overlay PNG")
    target_head: str = Field(..., description="Head used for explanation")
    target_class: int = Field(..., description="Class index used for explanation")


class AuditResponse(BaseModel):
    in_lung_energy_ratio: float = Field(..., ge=0.0, le=1.0)
    pass_80_percent: bool = Field(..., description="Whether the in-lung ratio meets the 80% threshold")
    lung_mask_base64: str = Field(..., description="Base64-encoded lung mask PNG")
