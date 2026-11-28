"""Regression checks for OOD, anatomy, TTA, reporting, and checkpoint safety."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from app.backend.main import service
from src.models.dense_unet import apply_mask_coverage_failsafe
from src.safety.report_generator import ClinicalReportGenerator


def _png_bytes(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(array.astype(np.uint8), mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def test_tier1_ood_guard_rejects_white_noise_and_solid_images() -> None:
    random_image = np.random.default_rng(42).integers(0, 256, (512, 512, 3), dtype=np.uint8)
    solid_image = np.full((512, 512, 3), 127, dtype=np.uint8)

    for name, image in (("random_noise.png", random_image), ("solid.png", solid_image)):
        result = service.predict(_png_bytes(image), model_name="ag_mtcnet")
        assert result["safety"]["decision"] == "REJECT", name
        assert result["safety"]["is_safe"] is False, name
        assert result["report"]["is_blocked"] is True, name


def test_tier2_anatomical_mask_is_binary_at_512_and_whiteout_fails_open() -> None:
    model = service.dense_unet
    if model is None:
        pytest.skip("Trained Dense-UNet checkpoint is unavailable.")

    original_forward = model.forward

    def deterministic_mask(images: torch.Tensor) -> torch.Tensor:
        batch, _, height, width = images.shape
        probabilities = torch.zeros((batch, 1, height, width), device=images.device)
        probabilities[..., height // 4:3 * height // 4, width // 4:3 * width // 4] = 0.9
        return probabilities

    model.forward = deterministic_mask  # type: ignore[method-assign]
    try:
        sample = torch.zeros((1, 3, 512, 512), dtype=torch.float32, device=service.device)
        mask = model.predict_mask_batch(sample, threshold=0.5, as_tensor=True)
    finally:
        model.forward = original_forward  # type: ignore[method-assign]

    assert mask.shape == (1, 1, 512, 512)
    assert set(torch.unique(mask).tolist()) == {0.0, 1.0}
    tiny_lung = torch.zeros((1, 1, 512, 512), dtype=torch.float32)
    tiny_lung[..., 250:350, 250:350] = 1.0  # 3.81% coverage.
    assert torch.all(apply_mask_coverage_failsafe(tiny_lung, min_coverage=0.05) == 1.0)


def test_tier3_tta_builds_original_flip_and_clahe_views(monkeypatch: pytest.MonkeyPatch) -> None:
    y, x = np.mgrid[0:512, 0:512]
    gray = np.clip((x * 0.35 + y * 0.18) % 256, 0, 255).astype(np.uint8)
    image = np.stack((gray, gray, gray), axis=-1)
    monkeypatch.setattr(service, "_anatomical_gate", lambda source, force=False: source)

    batch = service.preprocess_tta(_png_bytes(image), force_gate=False)
    assert batch.shape == (3, 3, 512, 512)
    assert torch.isfinite(batch).all()
    assert not torch.allclose(batch[0], batch[1])
    assert not torch.allclose(batch[0], batch[2])


def test_tier4_clinical_report_downgrades_unsupported_covid_suspicion() -> None:
    report = ClinicalReportGenerator().generate(
        predictions_a={"Infiltration": 0.10, "Consolidation": 0.10, "Pneumonia": 0.10},
        thresholds_a={"Infiltration": 0.5, "Consolidation": 0.5, "Pneumonia": 0.5},
        head_c_result={
            "model_is_positive": True,
            "is_positive": False,
            "clinical_suspicion": False,
        },
        guardrail_reasons=[
            "Only 65% of COVID heatmap energy is within the lung mask (<80%).",
            "Head A has no threshold-positive parenchymal finding.",
        ],
        in_lung_ratio=0.65,
    )

    assert report.is_blocked is False
    assert any("cờ nghi ngờ lâm sàng đã được hạ" in finding for finding in report.findings)
    assert any("<80%" in finding for finding in report.findings)
    assert report.recommendations[0].startswith("Bác sĩ cần đối chiếu")


def test_tier5_checkpoint_registry_uses_current_artifacts() -> None:
    project = Path(__file__).resolve().parents[1]
    registry = {model["id"]: model for model in service.list_models()}
    assert set(registry) == {"standard", "wsol", "resnet50", "ensemble", "ag_mtcnet"}
    assert registry["standard"]["checkpoint"] == "checkpoints/best_model_20_11.pth"
    assert registry["ag_mtcnet"]["checkpoint"] == "checkpoints/ag_mtcnet_best.pth"
    assert (project / registry["standard"]["checkpoint"]).is_file()
    assert (project / registry["ag_mtcnet"]["checkpoint"]).is_file()
    assert registry["ag_mtcnet"]["metrics"]["resolution"] == [512, 512]
    assert registry["ag_mtcnet"]["metrics"]["head_c_test_auc_checkpoint_metadata"] == pytest.approx(0.6004)
    assert "demo_head_c_disabled" not in registry["ag_mtcnet"]["metrics"]


@pytest.mark.parametrize("disease,code", [("Tuberculosis", "A16.2"), ("Effusion", "J90"), ("Mass", "R91"), ("COVID-19", "U07.1")])
def test_rag_retrieves_reference_cards(disease: str, code: str) -> None:
    from src.safety.rag_knowledge import query_clinical_rag
    result = query_clinical_rag("Tiêu chuẩn hình ảnh?", [disease], [])
    card = result["retrieved_cards"][0]
    assert card["icd10"] == code
    assert card["hallmarks"] and card["followup"]
    assert any("WHO ICD-10" in citation for citation in result["citations"])
    assert query_clinical_rag("Tiêu chuẩn hình ảnh?", [disease], []) == result


def test_rag_ood_lock_precedes_all_retrieval() -> None:
    from src.safety.rag_knowledge import query_clinical_rag
    result = query_clinical_rag("COVID-19", ["Tuberculosis"], ["left lung"], is_safe=False)
    assert result["status"] == "BLOCKED_OOD"
    assert result["retrieved_cards"] == result["citations"] == []


def test_rag_no_match_and_low_energy_context() -> None:
    from src.safety.rag_knowledge import query_clinical_rag
    assert query_clinical_rag("unrelated topic", [], [])["status"] == "NO_MATCH"
    result = query_clinical_rag("Giải thích độ tin cậy & vùng giải phẫu?", ["Effusion"], [], in_lung_ratio=0.65)
    assert "65.0%" in result["answer"] and "< 80%" in result["answer"]
    assert "unverified localization" in result["answer"]
    # A named question is reference knowledge, not an additional positive finding.
    result = query_clinical_rag("tràn khí màng phổi", ["Effusion"], [])
    assert [card["disease"] for card in result["retrieved_cards"]] == ["Pneumothorax"]


def test_rag_endpoint_contract_and_validation() -> None:
    import asyncio
    import httpx
    from app.backend.main import app
    def post(payload):
        async def request():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                return await client.post("/api/v1/rag-query", json=payload)
        return asyncio.run(request())
    payload = dict(question="Hướng xử trí?", active_findings=["Tuberculosis"], anatomical_locations=[], is_safe=True)
    response = post(payload)
    assert response.status_code == 200
    assert response.json()["retrieved_cards"][0]["icd10"] == "A16.2"
    payload["is_safe"] = False
    blocked = post(payload).json()
    assert blocked["status"] == "BLOCKED_OOD" and blocked["retrieved_cards"] == []
    payload["in_lung_ratio"] = 1.5
    assert post(payload).status_code == 422
