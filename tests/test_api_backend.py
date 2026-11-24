"""Integration tests for the LungRay FastAPI backend endpoints."""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import asyncio
import httpx
import numpy as np
import pytest
from PIL import Image
import torch

from app.backend.main import app
from app.backend.services import LungRayService


def test_explain_covid_probability_uses_correct_activation() -> None:
    assert LungRayService._covid_prob_from_logits(torch.tensor([[0.0]])) == pytest.approx(0.5)
    expected = torch.softmax(torch.tensor([[0.0, 1.0, 2.0]]), dim=-1)[0, 2].item()
    assert LungRayService._covid_prob_from_logits(torch.tensor([[0.0, 1.0, 2.0]])) == pytest.approx(expected)


def test_heatmap_restores_landscape_and_portrait_letterbox() -> None:
    landscape = np.zeros((100, 100), dtype=np.float32)
    landscape[25:75, :] = 1.0
    portrait = np.zeros((100, 100), dtype=np.float32)
    portrait[:, 25:75] = 1.0
    assert np.allclose(LungRayService._restore_letterboxed_heatmap(landscape, 50, 100), 1.0)
    assert np.allclose(LungRayService._restore_letterboxed_heatmap(portrait, 100, 50), 1.0)


def test_explain_discloses_fallback_for_empty_lung_mask(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.backend.main import service

    if service.dense_unet is None:
        pytest.skip("Dense-UNet checkpoint unavailable.")
    monkeypatch.setattr(service.segmenter, "_dense_predict_masks", lambda images: [np.zeros(image.shape[:2], dtype=np.uint8) for image in images])

    def approximate_mask(image: np.ndarray) -> np.ndarray:
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        h, w = mask.shape
        mask[h // 4:3 * h // 4, w // 4:3 * w // 4] = 1
        return mask

    monkeypatch.setattr(service.segmenter, "_morphology_predict_mask", approximate_mask)
    response = client.post(
        "/api/v1/explain",
        files={"file": ("sample.png", _make_image_bytes(), "image/png")},
        data={"target_head": "head_a", "target_class": 0, "target_disease_name": "Atelectasis"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["mask_source"] == "morphology_fallback"
    assert result["mask_warning"]
    assert result["audit_pass"] is None


def test_ag_mtcnet_predict_returns_all_three_heads(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predict?model=ag_mtcnet&tta_enabled=false",
        files={"file": ("sample.png", _make_image_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["head_a_prediction"]) == 14
    assert "tb_probability" in result["head_b_tb_screening"]
    assert result["head_c_covidx"]["available"] is True
    assert result["head_c_covidx"]["status"] == "EXPLORATORY"
    assert result["head_c_covidx"]["threshold"] == pytest.approx(0.6123412, abs=1e-5)
    assert 0.0 <= result["head_c_covidx"]["covid_probability"] <= 1.0
    assert result["inference_time_ms"] >= 0.0


def test_explain_ag_mtcnet_head_c_is_available(client: TestClient) -> None:
    response = client.post(
        "/api/v1/explain",
        files={"file": ("sample.png", _make_image_bytes(), "image/png")},
        data={"target_head": "head_c", "target_class": 0, "model": "ag_mtcnet"},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["target_head"] == "head_c"
    assert result["target_threshold"] == pytest.approx(0.6123, abs=1e-5)
    assert 0.0 <= result["target_probability"] <= 1.0


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


def _rsna_dicom_sample() -> tuple[str, bytes]:
    sample_dir = Path(__file__).resolve().parents[1] / "test_samples" / "04_rsna_pneumonia"
    sample_path = next(sample_dir.glob("*.dcm"), None)
    if sample_path is None:
        pytest.skip("No RSNA DICOM sample is available for the integration check.")
    return sample_path.name, sample_path.read_bytes()


def test_predict_endpoint_accepts_rsna_dicom(client: TestClient) -> None:
    filename, dicom_bytes = _rsna_dicom_sample()
    response = client.post(
        "/api/v1/predict",
        files={"file": (filename, dicom_bytes, "application/dicom")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["head_a_prediction"]) == 14
    assert 0.0 <= payload["head_b_tb_screening"]["tb_probability"] <= 1.0
    assert "head_c_covidx" in payload


def test_explain_endpoint_accepts_rsna_dicom(client: TestClient) -> None:
    filename, dicom_bytes = _rsna_dicom_sample()
    response = client.post(
        "/api/v1/explain",
        files={"file": (filename, dicom_bytes, "application/dicom")},
        data={
            "target_head": "head_a",
            "target_class": 2,
            "target_disease_name": "Effusion",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["target_head"] == "head_a"
    assert _is_base64_png(payload["heatmap_base64"])
    assert _is_base64_png(payload["overlay_base64"])
    with Image.open(io.BytesIO(base64.b64decode(payload["heatmap_rgba_base64"]))) as rgba:
        assert rgba.mode == "RGBA"
        alpha = np.asarray(rgba)[:, :, 3]
        assert payload["heatmap_has_activation"] == bool(np.any(alpha))
    if payload["mask_source"] != "dense_unet":
        assert payload["mask_warning"]
        assert payload["audit_pass"] is None


def test_audit_endpoint_accepts_rsna_dicom(client: TestClient) -> None:
    filename, dicom_bytes = _rsna_dicom_sample()
    response = client.post(
        "/api/v1/audit",
        files={"file": (filename, dicom_bytes, "application/dicom")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert 0.0 <= payload["in_lung_energy_ratio"] <= 1.0
    assert isinstance(payload["pass_80_percent"], bool)
    assert _is_base64_png(payload["lung_mask_base64"])


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
    assert set(model_ids) == {"standard", "wsol", "resnet50", "ensemble", "ag_mtcnet"}
    by_id = {model["id"]: model for model in models}
    assert by_id["standard"]["checkpoint"] == "checkpoints/best_model_20_11.pth"
    assert by_id["ag_mtcnet"]["checkpoint"] == "checkpoints/ag_mtcnet_best.pth"
    assert by_id["ag_mtcnet"]["metrics"]["head_c_status"] == "exploratory"


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


def test_predict_with_ensemble_model(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/predict?model=ensemble",
        files={"file": ("cxr.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_model"] == "ensemble"
    assert "Consensus" in payload["model_display_name"]
    assert payload["ensemble_agreement"] is not None
    assert 0.0 <= payload["ensemble_agreement"] <= 1.0
    assert len(payload["ensemble_models"]) >= 2
    assert "individual_model_predictions" in payload
    assert "densenet121_standard" in payload["individual_model_predictions"]
    assert "head_a_prediction" in payload
    assert "safety" in payload


def test_explain_with_ensemble_model(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/explain",
        files={"file": ("cxr.png", image_bytes, "image/png")},
        data={
            "target_head": "head_b",
            "target_class": 0,
            "clinical_grounding": "true",
            "target_disease_name": "Tuberculosis",
            "model": "ensemble",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_disease_name"] == "Tuberculosis"
    assert payload["heatmap_base64"] != ""


def test_predict_with_automatic_tta(client: TestClient) -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/api/v1/predict",
        files={"file": ("cxr.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tta_enabled"] is True
    assert payload["passes_executed"] == 3
    assert payload["calibration_temperature"] == 1.20
    assert "head_a_prediction" in payload
    assert "head_b_tb_screening" in payload
    assert "head_c_covidx" in payload


def test_predict_can_disable_tta(client: TestClient) -> None:
    response = client.post(
        "/api/v1/predict?tta_enabled=false",
        files={"file": ("cxr.png", _make_image_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tta_enabled"] is False
    assert payload["passes_executed"] == 1


def test_hot_reload_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/models/reload")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "active_models" in payload
    assert "triple_consensus_ready" in payload



