"""Integration tests for the LungRay FastAPI backend endpoints."""
from __future__ import annotations

import base64
import io

import asyncio
import httpx
import numpy as np
import pytest
from PIL import Image

from app.backend.main import app


import sys

# Prevent Windows Proactor event loop deadlock on localhost socketpair accept
if sys.platform == "win32":
    try:
        import asyncio.proactor_events

        class _DummySocket:
            def setblocking(self, *a): pass
            def send(self, *a): return 0
            def recv(self, *a): return b""
            def close(self): pass
            def fileno(self): return -1

        def _noop_self_pipe(self):
            self._ssock = _DummySocket()
            self._csock = _DummySocket()
            self._internal_fds = 0

        asyncio.proactor_events.BaseProactorEventLoop._make_self_pipe = _noop_self_pipe
        asyncio.proactor_events.BaseProactorEventLoop._loop_self_reading = lambda self, *a: None
    except Exception:
        pass


class TestClientSync:
    """Synchronous test client bridge using httpx.ASGITransport without anyio deadlock."""

    def __init__(self, asgi_app):
        self.app = asgi_app
        self.transport = httpx.ASGITransport(app=asgi_app)

    def get(self, url: str, **kwargs):
        async def _req():
            async with httpx.AsyncClient(transport=self.transport, base_url="http://testserver") as c:
                return await c.get(url, **kwargs)

        return asyncio.run(_req())

    def post(self, url: str, **kwargs):
        async def _req():
            async with httpx.AsyncClient(transport=self.transport, base_url="http://testserver") as c:
                return await c.post(url, **kwargs)

        return asyncio.run(_req())


TestClient = TestClientSync


@pytest.fixture(scope="module")
def client():
    yield TestClientSync(app)


def _make_image_bytes(size: tuple[int, int] = (512, 512)) -> bytes:
    h, w = size
    y = np.linspace(0, 255, h, dtype=np.uint8)[:, None]
    x = np.linspace(0, 255, w, dtype=np.uint8)[None, :]
    base = (y // 2 + x // 2).astype(np.uint8)
    array = np.stack([base, base, base], axis=-1)
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
    assert payload["version"] == "v7.0"
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
    assert "safety" in payload
    assert payload["safety"]["decision"] in ("ACCEPT", "REJECT")
    assert isinstance(payload["safety"]["is_safe"], bool)
    assert "report" in payload
    assert payload["report"]["status"] in ("GENERATED", "BLOCKED")


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


def test_explain_high_resolution_non_square_image(client: TestClient) -> None:
    # High-resolution non-square dimensions simulating real CXR (e.g. 768x920)
    image_bytes = _make_image_bytes(size=(768, 920))
    response = client.post(
        "/api/v1/explain",
        files={"file": ("hi_res.png", image_bytes, "image/png")},
        data={
            "target_head": "head_a",
            "target_class": 3,
            "target_disease_name": "Infiltration",
            "clinical_grounding": "true",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_disease_name"] == "Infiltration"
    assert payload["is_grounded"] is True
    assert _is_base64_png(payload["heatmap_base64"])
    assert _is_base64_png(payload["overlay_base64"])


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


def test_explain_multiscale_contour_contract(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/explain",
        files={"file": ("cxr.png", image_bytes, "image/png")},
        data={
            "target_head": "head_c",
            "target_class": 0,
            "clinical_grounding": "true",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload["contour_base64"], str)
    assert isinstance(payload["lesion_bounding_boxes"], list)
    assert isinstance(payload["lesion_area_ratio"], float)
    assert "fused" in payload["cam_resolution"]

    # For a confirmed positive target under grounding a rendered contour image
    # must be present; negative targets must never draw a lesion contour.
    if payload["is_target_positive"]:
        assert payload["contour_base64"] != ""
        assert _is_base64_png(payload["contour_base64"])
    else:
        assert payload["contour_base64"] == ""
        assert payload["lesion_bounding_boxes"] == []
        assert payload["lesion_area_ratio"] == 0.0


def test_explain_raw_mode_has_no_contour(client: TestClient) -> None:
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
    assert payload["contour_base64"] == ""
    assert payload["lesion_bounding_boxes"] == []
    assert payload["lesion_area_ratio"] == 0.0


def test_list_models_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    model_ids = [m["id"] for m in models]
    assert "standard" in model_ids
    assert "wsol" in model_ids


def test_predict_with_wsol_model(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/predict?model=wsol",
        files={"file": ("cxr.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_model"] == "wsol"
    assert "WSOL" in payload["model_display_name"]
    assert "head_a_prediction" in payload
    assert "head_b_tb_screening" in payload

