"""Integration tests for the LungRay FastAPI backend endpoints."""
from __future__ import annotations

import base64
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _make_image_bytes(size: tuple[int, int] = (512, 512)) -> bytes:
    array = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
    image = Image.fromarray(array, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()


def _is_base64_png(data: str) -> bool:
    try:
        decoded = base64.b64decode(data)
        return decoded[:4] == b"\x89PNG"
    except Exception:
        return False


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "v4.0"
    assert payload["device"] in ("cpu", "cuda")


def test_predict_endpoint(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/predict",
        files={"file": ("cxr.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "head_a_prediction" in payload
    assert "head_b_tb_screening" in payload
    assert "head_c_covidx" in payload
    assert "inference_time_ms" in payload

    assert len(payload["head_a_prediction"]) == 14
    assert 0.0 <= payload["head_b_tb_screening"]["tb_probability"] <= 1.0
    assert isinstance(payload["head_b_tb_screening"]["is_positive"], bool)
    assert 0.0 <= payload["head_c_covidx"]["covid_probability"] <= 1.0
    assert isinstance(payload["head_c_covidx"]["is_positive"], bool)
    assert payload["inference_time_ms"] >= 0.0


def test_explain_endpoint_default_grounded(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/explain",
        files={"file": ("cxr.png", image_bytes, "image/png")},
        data={"target_head": "head_c", "target_class": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "heatmap_base64" in payload
    assert "overlay_base64" in payload
    assert payload["target_head"] == "head_c"
    assert payload["target_class"] == 0
    assert payload["target_disease_name"] == "COVID-19"
    assert payload["is_grounded"] is True
    assert 0.0 <= payload["in_lung_energy_ratio"] <= 1.0
    assert _is_base64_png(payload["heatmap_base64"])
    assert _is_base64_png(payload["overlay_base64"])


def test_explain_endpoint_raw_attention_mode(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/explain",
        files={"file": ("cxr.png", image_bytes, "image/png")},
        data={
            "target_head": "head_c",
            "target_class": 0,
            "clinical_grounding": "false",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_grounded"] is False
    assert payload["target_disease_name"] == "COVID-19"
    assert 0.0 <= payload["in_lung_energy_ratio"] <= 1.0


def test_explain_endpoint_cardiomegaly_head_a(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/explain",
        files={"file": ("cxr.png", image_bytes, "image/png")},
        data={
            "target_head": "head_a",
            "target_class": 1,
            "target_disease_name": "Cardiomegaly",
            "clinical_grounding": "true",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_head"] == "head_a"
    assert payload["target_class"] == 1
    assert payload["target_disease_name"] == "Cardiomegaly"
    assert payload["is_grounded"] is True


def test_audit_endpoint(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/audit",
        files={"file": ("cxr.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "in_lung_energy_ratio" in payload
    assert "pass_80_percent" in payload
    assert "lung_mask_base64" in payload
    assert 0.0 <= payload["in_lung_energy_ratio"] <= 1.0
    assert isinstance(payload["pass_80_percent"], bool)
    assert _is_base64_png(payload["lung_mask_base64"])


def test_corrupted_image_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predict",
        files={"file": ("bad.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/explain",
        files={"file": ("bad.png", b"not-an-image", "image/png")},
        data={"target_head": "head_c", "target_class": 0},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/audit",
        files={"file": ("bad.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 422
