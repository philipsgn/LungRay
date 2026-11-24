"""Checkpoint, inference-contract, and anatomical-gate regression tests."""

from pathlib import Path
import csv
import hashlib
import json

import numpy as np
import pytest
import torch

from src.models.dense_unet import (
    DenseUNet,
    apply_dilated_soft_mask_tensor,
    apply_mask_coverage_failsafe,
)

CHECKPOINT_PATH = Path(__file__).resolve().parents[1] / "checkpoints" / "dense_unet_best.pth"


@pytest.fixture(scope="module")
def trained_dense_unet():
    assert CHECKPOINT_PATH.is_file(), f"Required Dense-UNet checkpoint is missing: {CHECKPOINT_PATH}"
    payload = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    model = DenseUNet(pretrained=False, in_channels=3)
    model.load_state_dict(payload["model_state_dict"], strict=True)
    model.eval()
    return model, payload


def test_dense_unet_checkpoint_loads_strictly(trained_dense_unet):
    model, payload = trained_dense_unet
    assert not model.training
    assert payload["epoch"] == 15
    assert payload["data_mode"] == "real"
    assert payload["num_real_pairs"] == 3014
    assert payload["val_dice"] == pytest.approx(0.9630, abs=0.001)
    assert payload["val_iou"] == pytest.approx(0.9300, abs=0.001)


def test_dense_unet_manifest_and_history_exports_match_checkpoint():
    project_root = CHECKPOINT_PATH.parents[1]
    manifest_path = project_root / "configs" / "dense_unet_manifest.json"
    alias_path = project_root / "checkpoints" / "dense_unet.pth"
    history_path = project_root / "results" / "22_11_dense-unet_phase1" / "dense_unet_training_history.csv"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert CHECKPOINT_PATH.read_bytes() == alias_path.read_bytes()
    assert manifest["sha256"] == hashlib.sha256(CHECKPOINT_PATH.read_bytes()).hexdigest()
    assert manifest["resolution"] == [256, 256]
    assert manifest["pairs_count"] == 3014
    assert manifest["epoch"] == 15
    with history_path.open(newline="", encoding="utf-8") as handle:
        history = list(csv.DictReader(handle))
    assert len(history) == 15
    assert {"epoch", "train_loss", "val_loss", "val_dice", "val_iou"}.issubset(history[0])


def test_predict_mask_tensor_contract_at_512(trained_dense_unet, monkeypatch):
    model, _ = trained_dense_unet
    received = []

    def deterministic_probabilities(images):
        received.append(images.detach().cpu().clone())
        batch, _, height, width = images.shape
        probabilities = torch.zeros((batch, 1, height, width), device=images.device)
        probabilities[..., : height // 2, : width // 2] = 0.75
        return probabilities

    monkeypatch.setattr(model, "forward", deterministic_probabilities)
    normalized_batch = torch.zeros((2, 3, 512, 512), dtype=torch.float32)

    masks = model.predict_mask_batch(normalized_batch, threshold=0.5, as_tensor=True)
    assert isinstance(masks, torch.Tensor)
    assert masks.shape == (2, 1, 512, 512)
    assert masks.dtype == torch.float32
    assert set(torch.unique(masks).tolist()) == {0.0, 1.0}
    assert torch.equal(received[-1], normalized_batch)

    single_mask = model.predict_mask(normalized_batch[:1], threshold=0.5, as_tensor=True)
    assert isinstance(single_mask, torch.Tensor)
    assert single_mask.shape == (1, 1, 512, 512)
    assert set(torch.unique(single_mask).tolist()) == {0.0, 1.0}

    # The default NumPy return remains compatible with existing LungSegmenter callers.
    legacy_mask = model.predict_mask_batch(normalized_batch[:1], threshold=0.5)
    assert isinstance(legacy_mask, np.ndarray)
    assert legacy_mask.shape == (1, 512, 512)
    assert set(np.unique(legacy_mask).tolist()) == {0, 255}


def test_whiteout_coverage_failsafe_returns_all_ones_and_preserves_image():
    image = torch.full((1, 3, 512, 512), 0.4, dtype=torch.float32)
    predicted_mask = torch.zeros((1, 1, 512, 512), dtype=torch.float32)
    predicted_mask[..., 200:300, 200:300] = 1.0  # 3.81% coverage.

    safe_mask = apply_mask_coverage_failsafe(predicted_mask, min_coverage=0.05)
    assert torch.all(safe_mask == 1.0)

    gated_image = apply_dilated_soft_mask_tensor(image, predicted_mask)
    assert torch.equal(gated_image, image)


def test_dilated_soft_mask_uses_six_percent_margin_and_ten_percent_attenuation():
    image = torch.ones((1, 3, 512, 512), dtype=torch.float32)
    mask = torch.zeros((1, 1, 512, 512), dtype=torch.float32)
    mask[..., 100:400, 60:220] = 1.0
    mask[..., 100:400, 292:452] = 1.0

    grounded = apply_dilated_soft_mask_tensor(
        image,
        mask,
        dilation_margin_pct=0.06,
        background_attenuation=0.10,
    )
    assert grounded[0, :, 250, 140].mean().item() == pytest.approx(1.0, abs=1e-6)
    assert grounded[0, :, 10, 10].mean().item() == pytest.approx(0.10, abs=1e-6)
    boundary_weight = grounded[0, :, 250, 45].mean().item()
    assert 0.10 < boundary_weight < 1.0
