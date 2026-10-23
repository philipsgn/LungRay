"""LungRay FastAPI microservice backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.backend.schemas import (
    AuditResponse,
    ExplainResponse,
    HealthResponse,
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
    )


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    try:
        image_bytes = await file.read()
        result = service.predict(image_bytes)
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
) -> ExplainResponse:
    try:
        image_bytes = await file.read()
        result = service.explain(image_bytes, target_head=target_head, target_class=target_class)
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
