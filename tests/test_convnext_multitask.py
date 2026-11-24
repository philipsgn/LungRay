"""
Unit Tests for ConvNeXt Multi-Task 3-Head Network & Grad-CAM Integration
========================================================================
Validates:
1. Backbone instantiation with 'convnext_tiny'.
2. MultiTaskChestXrayNet forward pass and logits shapes.
3. Feature projection and parameter-free normalization.
4. Correct resolution of convolutional target layer for Grad-CAM.
5. GradCAMExplainer / Grad-CAM++ execution on dummy 512x512 chest X-rays.
"""
import pytest
import torch
import numpy as np

from src.models.multi_task_net import MultiTaskChestXrayNet
from src.explainability.grad_cam import GradCAMExplainer


def test_convnext_tiny_initialization():
    """Verify ConvNeXt-Tiny builds with feature_dim=768 and 3 linear heads."""
    model = MultiTaskChestXrayNet(
        backbone_name="convnext_tiny",
        pretrained=False,
        img_size=512,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=1,
        head_norm="layernorm",
    )
    assert model.feature_dim == 768
    assert model.backbone_name == "convnext_tiny"
    assert model.head_a.out_features == 14
    assert model.head_b.out_features == 1
    assert model.head_c.out_features == 1


def test_convnext_tiny_forward_shapes():
    """Verify forward pass output dictionary and logits dimensions."""
    model = MultiTaskChestXrayNet(
        backbone_name="convnext_tiny",
        pretrained=False,
        img_size=512,
    )
    model.eval()

    dummy_input = torch.randn(2, 3, 512, 512)
    with torch.no_grad():
        outputs = model(dummy_input)

    assert isinstance(outputs, dict)
    assert "head_a" in outputs
    assert "head_b" in outputs
    assert "head_c" in outputs

    assert outputs["head_a"].shape == (2, 14)
    assert outputs["head_b"].shape == (2, 1)
    assert outputs["head_c"].shape == (2, 1)


def test_convnext_tiny_single_head_forward():
    """Verify task_id selection evaluates only the requested head."""
    model = MultiTaskChestXrayNet(
        backbone_name="convnext_tiny",
        pretrained=False,
        img_size=512,
    )
    model.eval()
    dummy_input = torch.randn(2, 3, 512, 512)

    with torch.no_grad():
        out_a = model(dummy_input, task_id="head_a")
        out_b = model(dummy_input, task_id="head_b")
        out_c = model(dummy_input, task_id="head_c")

    assert list(out_a.keys()) == ["head_a"]
    assert list(out_b.keys()) == ["head_b"]
    assert list(out_c.keys()) == ["head_c"]


def test_convnext_tiny_grad_cam_target_layer():
    """Verify get_last_conv_layer returns ConvNeXt stage 4 last block."""
    model = MultiTaskChestXrayNet(
        backbone_name="convnext_tiny",
        pretrained=False,
        img_size=512,
    )
    target_layer = model.get_last_conv_layer()
    assert target_layer is not None
    assert target_layer == model.backbone.stages[-1].blocks[-1]


def test_convnext_tiny_grad_cam_generation():
    """Verify GradCAMExplainer generates valid [512, 512] heatmaps with ConvNeXt."""
    model = MultiTaskChestXrayNet(
        backbone_name="convnext_tiny",
        pretrained=False,
        img_size=512,
    )
    model.eval()

    target_layer = model.get_last_conv_layer()
    explainer = GradCAMExplainer(model=model, target_layer=target_layer, method="gradcam++")

    dummy_input = torch.randn(1, 3, 512, 512)
    heatmap = explainer.generate(
        x=dummy_input,
        head_name="head_a",
        target_class_idx=2,
    )

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (512, 512)
    assert heatmap.min() >= 0.0
    assert heatmap.max() <= 1.0 + 1e-5
