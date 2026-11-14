"""LungRay FastAPI microservice backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.backend.schemas import (
    AuditResponse,
    ExplainResponse,
    HealthResponse,
    ModelInfo,
    PredictionResponse,
)
from app.backend.services import LungRayService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

service = LungRayService()

app = FastAPI(
    title="LungRay FastAPI Backend",
    version=service.version,
    description="RESTful microservice for multi-task CXR inference, Grad-CAM, and shortcut audit.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        device=str(service.device),
        version=service.version,
        active_checkpoint=getattr(service, "current_checkpoint", "checkpoints/best_model.pth"),
    )


@app.get("/api/v1/models", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    return [ModelInfo(**m) for m in service.list_models()]


@app.post("/api/v1/models/reload")
async def reload_models() -> dict[str, Any]:
    try:
        return service.check_and_reload_checkpoints()
    except Exception as exc:
        logger.exception("Model hot-reloading failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    model: str = Query(default="standard", description="Model variant: 'standard' (SOTA CADx), 'wsol' (Grounding Specialist), 'resnet50' (Residual Specialist), or 'ensemble' (Consensus Multi-Backbone)"),
    failsafe_enabled: bool = Query(default=True, description="Whether OOD Fail-Safe policy is enforced"),
) -> PredictionResponse:
    try:
        image_bytes = await file.read()
        result = service.predict(image_bytes, model_name=model, failsafe_enabled=failsafe_enabled)
        return PredictionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/explain", response_model=ExplainResponse)
async def explain(
    file: UploadFile = File(...),
    target_head: str = Form(default="head_c"),
    target_class: int = Form(default=0),
    clinical_grounding: bool = Form(default=True),
    target_disease_name: str = Form(default=""),
    model: str = Form(default="standard"),
) -> ExplainResponse:
    try:
        image_bytes = await file.read()
        result = service.explain(
            image_bytes,
            target_head=target_head,
            target_class=target_class,
            clinical_grounding=clinical_grounding,
            target_disease_name=target_disease_name,
            model_name=model,
        )
        return ExplainResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Explainability failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@app.post("/api/v1/audit", response_model=AuditResponse)
async def audit(file: UploadFile = File(...)) -> AuditResponse:
    try:
        image_bytes = await file.read()
        result = service.audit(image_bytes)
        return AuditResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Shortcut audit failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
