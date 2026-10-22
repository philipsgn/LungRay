"""
LungRay Unit Tests: Grad-CAM / Grad-CAM++ and Shortcut Learning Audit
=====================================================================
Coverage:
1. Forward/backward hook registration and heatmap generation.
2. Grad-CAM++ higher-order path and first-order fallback.
3. Multi-head explainability for Head A, Head B, and Head C.
4. Hook cleanup and idempotent teardown.
5. Morphological lung segmentation and in-lung energy ratio edge cases.
6. End-to-end shortcut audit sample.
"""
import cv2
import numpy as np
import pytest
import torch
import torch.nn as nn

from src.explainability import GradCAMExplainer, LungSegmenter, ShortcutAuditEngine
from src.explainability.grad_cam import GradCAMExplainer as GradCAMExplainerDirect
from src.explainability.shortcut_audit import (
    LungSegmenter as LungSegmenterDirect,
    ShortcutAuditEngine as ShortcutAuditEngineDirect,
)
from src.models.multi_task_net import MultiTaskChestXrayNet


@pytest.fixture(scope="module")
def dummy_model():
    torch.manual_seed(7)
    model = MultiTaskChestXrayNet(
        backbone_name="densenet121",
        pretrained=False,
        img_size=512,
        dropout_rate=0.2,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=1,
    )
    model.eval()
    return model


@pytest.fixture(scope="module")
def synthetic_cxr():
    image = np.zeros((256, 256), dtype=np.uint8)
    cv2.ellipse(image, (128, 128), (112, 120), 0, 0, 360, 180, -1)
    cv2.ellipse(image, (86, 132), (34, 72), 0, 0, 360, 20, -1)
    cv2.ellipse(image, (170, 132), (34, 72), 0, 0, 360, 20, -1)
    return image


def test_explainability_exports():
    assert GradCAMExplainer is GradCAMExplainerDirect
    assert LungSegmenter is LungSegmenterDirect
    assert ShortcutAuditEngine is ShortcutAuditEngineDirect


def test_gradcam_forward_backward(dummy_model):
    image = torch.randn(1, 3, 512, 512)
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    try:
        heatmap = explainer.generate(image, head_name="head_c", target_class_idx=0)

        assert heatmap.shape == (512, 512)
        assert heatmap.dtype == np.float32
        assert np.isfinite(heatmap).all()
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
        assert heatmap.max() > 0.0
        assert explainer.is_attached
        assert all(parameter.grad is None for parameter in dummy_model.parameters())
    finally:
        explainer.remove_hooks()


def test_gradcam_plus_plus(dummy_model):
    image = torch.randn(1, 3, 256, 256)
    explainer = GradCAMExplainer(dummy_model, method="gradcam++")
    try:
        heatmap = explainer.generate(image, head_name="head_c", target_class_idx=0)

        assert heatmap.shape == (256, 256)
        assert heatmap.dtype == np.float32
        assert np.isfinite(heatmap).all()
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
        assert heatmap.max() > 0.0
    finally:
        explainer.remove_hooks()


def test_gradcam_plus_plus_alias(dummy_model):
    image = torch.randn(1, 3, 128, 128)
    explainer = GradCAMExplainer(dummy_model, method="grad-cam++")
    try:
        heatmap = explainer.generate(image, head_name="head_b")
        assert heatmap.shape == (128, 128)
        assert np.isfinite(heatmap).all()
    finally:
        explainer.remove_hooks()


def test_multi_head_explainability(dummy_model):
    image = torch.randn(1, 3, 256, 256)
    cases = [
        ("head_a", 0),
        ("head_a", 13),
        ("head_b", 0),
        ("head_c", 0),
    ]
    for head_name, target_class_idx in cases:
        explainer = GradCAMExplainer(dummy_model, method="gradcam")
        try:
            heatmap = explainer.generate(
                image,
                head_name=head_name,
                target_class_idx=target_class_idx,
            )
            assert heatmap.shape == (256, 256), head_name
            assert np.isfinite(heatmap).all(), head_name
            assert 0.0 <= float(heatmap.min()) <= float(heatmap.max()) <= 1.0
        finally:
            explainer.remove_hooks()


def test_single_image_and_batch_inputs(dummy_model):
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    try:
        single = explainer.generate(torch.randn(3, 128, 128), head_name="head_b")
        assert single.shape == (128, 128)
        batch = explainer.generate(torch.randn(3, 3, 128, 128), head_name="head_b")
        assert batch.shape == (128, 128)
    finally:
        explainer.remove_hooks()


def test_hook_cleanup(dummy_model):
    target_layer = dummy_model.get_last_conv_layer()
    initial_forward_hooks = len(target_layer._forward_hooks)
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    assert explainer.is_attached
    assert len(target_layer._forward_hooks) == initial_forward_hooks + 1
    assert len(target_layer._backward_hooks) == 1

    explainer.remove_hooks()
    assert not explainer.is_attached
    assert len(target_layer._forward_hooks) == initial_forward_hooks
    assert len(target_layer._backward_hooks) == 0

    explainer.remove_hooks()
    with pytest.raises(RuntimeError, match="Hooks have been removed"):
        explainer.generate(torch.randn(1, 3, 64, 64), head_name="head_c")


def test_explicit_target_layer(dummy_model):
    target_layer = dummy_model.get_last_conv_layer()
    explainer = GradCAMExplainer(
        dummy_model,
        target_layer=target_layer,
        method="gradcam",
    )
    try:
        heatmap = explainer.generate(torch.randn(1, 3, 64, 64), head_name="head_c")
        assert heatmap.shape == (64, 64)
    finally:
        explainer.remove_hooks()


def test_invalid_explainer_configuration(dummy_model):
    with pytest.raises(ValueError, match="convolutional target layer"):
        GradCAMExplainer(dummy_model, target_layer=object(), method="gradcam")

    with pytest.raises(ValueError, match="method"):
        GradCAMExplainer(dummy_model, method="scorecam")


def test_missing_target_layer():
    class PlainModel(nn.Module):
        def forward(self, x):
            return {"head_c": x.mean(dim=(1, 2, 3), keepdim=True)}

    with pytest.raises(ValueError, match="get_last_conv_layer"):
        GradCAMExplainer(PlainModel())


def test_invalid_generate_arguments(dummy_model):
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    try:
        with pytest.raises(TypeError, match="floating-point"):
            explainer.generate(torch.ones(1, 3, 64, 64, dtype=torch.uint8))
        with pytest.raises(ValueError, match="shape"):
            explainer.generate(torch.randn(1, 1, 3, 64, 64))
        with pytest.raises(KeyError, match="head_name"):
            explainer.generate(torch.randn(1, 3, 64, 64), head_name="head_z")
        with pytest.raises(IndexError, match="target_class_idx"):
            explainer.generate(
                torch.randn(1, 3, 64, 64),
                head_name="head_a",
                target_class_idx=14,
            )
        with pytest.raises(IndexError, match="target_class_idx"):
            explainer.generate(
                torch.randn(1, 3, 64, 64),
                head_name="head_b",
                target_class_idx=1,
            )
    finally:
        explainer.remove_hooks()


def test_overlay_heatmap_uint8_and_float(dummy_model):
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    try:
        heatmap = np.linspace(0.0, 1.0, 64 * 64, dtype=np.float32).reshape(64, 64)
        image_uint8 = np.full((64, 64, 3), 128, dtype=np.uint8)
        overlaid = explainer.overlay_heatmap(image_uint8, heatmap, alpha=0.4)
        assert overlaid.shape == (64, 64, 3)
        assert overlaid.dtype == np.uint8
        assert overlaid.min() >= 0 and overlaid.max() <= 255

        image_float = np.full((64, 64, 3), 0.5, dtype=np.float32)
        overlaid_float = explainer.overlay_heatmap(image_float, heatmap, alpha=0.0)
        assert overlaid_float.shape == (64, 64, 3)
        assert overlaid_float.dtype == np.uint8
        assert np.allclose(overlaid_float, 127, atol=1)

        resized = explainer.overlay_heatmap(
            image_uint8,
            np.ones((8, 8), dtype=np.float32),
        )
        assert resized.shape == (64, 64, 3)
    finally:
        explainer.remove_hooks()


def test_overlay_heatmap_validation(dummy_model):
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    try:
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="alpha"):
            explainer.overlay_heatmap(image, np.zeros((64, 64)), alpha=1.5)
        with pytest.raises(ValueError, match="H, W, 3"):
            explainer.overlay_heatmap(np.zeros((64, 64), dtype=np.uint8), np.zeros((64, 64)))
        with pytest.raises(ValueError, match="two-dimensional"):
            explainer.overlay_heatmap(image, np.zeros((64, 64, 1)), alpha=0.4)
    finally:
        explainer.remove_hooks()


def test_lung_segmenter_and_energy_ratio(synthetic_cxr):
    segmenter = LungSegmenter()
    mask = segmenter.predict_mask(synthetic_cxr)
    assert mask.shape == synthetic_cxr.shape
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 1})
    assert 0.0 < float(mask.mean()) < 0.85

    rgb_image = cv2.cvtColor(synthetic_cxr, cv2.COLOR_GRAY2RGB)
    mask_rgb = segmenter.predict_mask(rgb_image)
    assert mask_rgb.shape == synthetic_cxr.shape
    assert set(np.unique(mask_rgb)).issubset({0, 1})

    engine = ShortcutAuditEngine(segmenter)
    uniform = np.full((256, 256), 0.5, dtype=np.float32)
    assert engine.compute_in_lung_ratio(uniform, mask) == pytest.approx(mask.mean())
    assert engine.compute_in_lung_ratio(uniform, np.ones((256, 256))) == pytest.approx(1.0)
    assert engine.compute_in_lung_ratio(uniform, np.zeros((256, 256))) == pytest.approx(0.0)
    assert engine.compute_in_lung_ratio(np.zeros((256, 256)), mask) == pytest.approx(0.0)


def test_energy_ratio_known_values():
    engine = ShortcutAuditEngine()
    heatmap = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    left_mask = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    assert engine.compute_in_lung_ratio(heatmap, left_mask) == pytest.approx(4.0 / 10.0)

    negative = np.array([[-1.0, 1.0], [-1.0, 1.0]], dtype=np.float32)
    assert engine.compute_in_lung_ratio(negative, left_mask) == pytest.approx(0.0)
    assert engine.compute_in_lung_ratio(negative, 1 - left_mask) == pytest.approx(1.0)

    with pytest.raises(ValueError, match="does not match"):
        engine.compute_in_lung_ratio(heatmap, np.zeros((3, 3)))
    with pytest.raises(ValueError, match="NaN or infinite"):
        engine.compute_in_lung_ratio(
            np.array([[np.nan, 1.0], [1.0, 1.0]]),
            left_mask,
        )


def test_lung_segmenter_fallback_and_validation():
    segmenter = LungSegmenter()
    blank = np.zeros((64, 64), dtype=np.uint8)
    mask = segmenter.predict_mask(blank)
    assert mask.shape == (64, 64)
    assert set(np.unique(mask)).issubset({0, 1})
    assert 0.0 < float(mask.mean()) < 0.85

    with pytest.raises(ValueError, match="at least 16x16"):
        segmenter.predict_mask(np.zeros((8, 8), dtype=np.uint8))
    with pytest.raises(ValueError, match="shape"):
        segmenter.predict_mask(np.zeros((64, 64, 2), dtype=np.uint8))
    with pytest.raises(ValueError, match="min_area_ratio"):
        LungSegmenter(min_area_ratio=0.9, max_area_ratio=0.8)
    with pytest.raises(ValueError, match="pass_threshold"):
        ShortcutAuditEngine(pass_threshold=1.5)


def test_audit_sample(dummy_model, synthetic_cxr):
    image_tensor = torch.randn(1, 3, 256, 256)
    explainer = GradCAMExplainer(dummy_model, method="gradcam")
    engine = ShortcutAuditEngine(LungSegmenter())
    try:
        result = engine.audit_sample(
            model=dummy_model,
            explainer=explainer,
            img_tensor=image_tensor,
            original_img=synthetic_cxr,
            head_name="head_c",
        )
        assert set(result) == {
            "in_lung_ratio",
            "heatmap",
            "lung_mask",
            "pass_80_percent",
        }
        assert result["heatmap"].shape == (256, 256)
        assert result["lung_mask"].shape == (256, 256)
        assert 0.0 <= result["in_lung_ratio"] <= 1.0
        assert isinstance(result["pass_80_percent"], bool)
        assert result["pass_80_percent"] == (result["in_lung_ratio"] >= 0.80)
    finally:
        explainer.remove_hooks()
