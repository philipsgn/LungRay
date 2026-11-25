"""ConvNeXt spatial explainability and offline Kaggle training contracts."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch
from torch import nn

_kaggle_dir = Path(__file__).resolve().parent.parent / "kaggle"
if str(_kaggle_dir) not in sys.path:
    sys.path.insert(0, str(_kaggle_dir))

from src.models.multi_task_net import MultiTaskChestXrayNet
from src.explainability.grad_cam import GradCAMExplainer
from train_multitask_kaggle import build_optimizer, parse_args
from train_kaggle import validate_training_splits
from train_raddino_probing import RadDinoLinearProbe


@pytest.fixture(scope="module")
def convnext_model():
    torch.manual_seed(42)
    return MultiTaskChestXrayNet(backbone_name="convnext_tiny", pretrained=False).eval()


def test_convnext_initialization(convnext_model):
    assert convnext_model.feature_dim == 768
    assert convnext_model.head_a.in_features == 768


def test_convnext_forward_512(convnext_model):
    with torch.no_grad():
        result = convnext_model(torch.randn(2, 3, 512, 512))
    assert {name: tuple(value.shape) for name, value in result.items()} == {
        "head_a": (2, 14), "head_b": (2, 1), "head_c": (2, 1)}


def test_convnext_last_spatial_block_hook(convnext_model):
    layer = convnext_model.get_last_conv_layer()
    assert layer is convnext_model.backbone.stages[-1].blocks[-1]
    seen = []
    handle = layer.register_forward_hook(lambda module, inputs, output: seen.append(tuple(output.shape)))
    try:
        with torch.no_grad():
            convnext_model(torch.randn(1, 3, 512, 512))
    finally:
        handle.remove()
    assert seen == [(1, 768, 16, 16)]


def test_convnext_gradcam_plus_plus_512(convnext_model):
    explainer = GradCAMExplainer(convnext_model, method="gradcam++")
    try:
        heatmap = explainer.generate(torch.randn(1, 3, 512, 512), head_name="head_a", target_class_idx=3)
    finally:
        explainer.remove_hooks()
    assert heatmap.shape == (512, 512)
    assert np.isfinite(heatmap).all()
    assert heatmap.min() >= 0 and heatmap.max() <= 1
    assert not explainer.is_attached


def test_convnext_optimizer_keeps_groups_on_partial_override(convnext_model):
    args = parse_args([])
    assert args.backbone == "convnext_tiny" and args.batch_size == 32
    optimizer = build_optimizer(convnext_model, args)
    assert [group["lr"] for group in optimizer.param_groups] == [2e-5, 1e-4]
    assert all(group["weight_decay"] == 1e-2 for group in optimizer.param_groups)
    args.lr_heads = 3e-4
    optimizer = build_optimizer(convnext_model, args)
    assert [group["lr"] for group in optimizer.param_groups] == [2e-5, 3e-4]
    all_ids = [id(parameter) for group in optimizer.param_groups for parameter in group["params"]]
    assert len(all_ids) == len(set(all_ids)) == len(list(convnext_model.parameters()))


def test_split_preflight_rejects_patient_leak_and_missing_source():
    leaked = pd.DataFrame({"Patient ID": [1, 1, 2], "split": ["train", "val", "test"]})
    with pytest.raises(ValueError, match="leakage"):
        validate_training_splits(leaked, "NIH", ["Patient ID"])
    missing_source = pd.DataFrame({"patient_id": [1, 2, 3], "split": ["train", "val", "test"], "label": [0, 1, 0]})
    with pytest.raises(ValueError, match="data_source"):
        validate_training_splits(missing_source, "COVIDx", ["patient_id"])


def test_rad_dino_encoder_frozen_but_linear_heads_learn():
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.config = SimpleNamespace(hidden_size=768)
            self.projection = nn.Linear(3, 768)
            self.dropout = nn.Dropout(0.9)

        def forward(self, pixel_values):
            features = self.dropout(self.projection(pixel_values.mean((2, 3))))
            return SimpleNamespace(last_hidden_state=features[:, None, :])

    model = RadDinoLinearProbe(Encoder()).train()
    assert not model.backbone.training
    assert all(not parameter.requires_grad for parameter in model.backbone.parameters())
    before = {name: parameter.clone() for name, parameter in model.backbone.named_parameters()}
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=1e-3)
    head_before = model.head_a.weight.detach().clone()
    outputs = model(torch.randn(2, 3, 32, 32))
    assert outputs["head_a"].shape == (2, 14)
    assert outputs["head_b"].shape == outputs["head_c"].shape == (2, 1)
    sum(value.square().mean() for value in outputs.values()).backward()
    optimizer.step()
    assert not torch.equal(head_before, model.head_a.weight)
    assert all(parameter.grad is None and torch.equal(parameter, before[name]) for name, parameter in model.backbone.named_parameters())


def test_convnext_offline_weights_load_without_pretrained_download(convnext_model, monkeypatch, tmp_path):
    import src.models.backbones as factory
    path = tmp_path / "convnext_tiny_local.pth"
    torch.save({"model": convnext_model.backbone.state_dict()}, path)
    monkeypatch.setattr(factory, "_find_local_weights", lambda name: str(path))
    create = factory.timm.create_model
    calls = []
    def create_offline(name, **kwargs):
        calls.append(kwargs["pretrained"])
        assert kwargs["pretrained"] is False
        return create(name, **kwargs)
    monkeypatch.setattr(factory.timm, "create_model", create_offline)
    backbone, dimension = factory.build_backbone("convnext_tiny", pretrained=True)
    assert dimension == 768 and backbone.pretrained_loaded
    assert calls == [False]
    assert torch.equal(backbone.stem[0].weight, convnext_model.backbone.stem[0].weight)
