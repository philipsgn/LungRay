"""Verify published atlas dimensions against real CPU model forwards."""
from pathlib import Path

import torch

from src.models.dense_unet import DenseUNet
from src.models.multi_task_net import MultiTaskChestXrayNet


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "app/frontend/public/pipeline-atlas.html"


def _forward_shapes(model, modules, size):
    shapes = {}
    handles = []
    for name, module in modules.items():
        def capture(_module, _inputs, output, key=name):
            shapes[key] = tuple(output.shape[1:])
        handles.append(module.register_forward_hook(capture))
    previous_threads = torch.get_num_threads()
    try:
        torch.set_num_threads(2)
        with torch.inference_mode():
            output = model(torch.zeros(1, 3, size, size))
    finally:
        for handle in handles:
            handle.remove()
        torch.set_num_threads(previous_threads)
    return shapes, output


def test_atlas_densenet_dimensions_and_exact_checkpoint_size():
    html = ATLAS.read_text(encoding="utf-8")
    model = MultiTaskChestXrayNet(pretrained=False).eval()
    checkpoint = ROOT / "checkpoints/best_model_20_11.pth"
    if checkpoint.exists():
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        model.load_state_dict(payload["model_state_dict"], strict=True)
        assert payload["architecture"]["img_size"] == 256
        assert f"{checkpoint.stat().st_size / 1024**2:.2f} MiB" in html
    assert f"{sum(p.numel() for p in model.parameters()):,} params" in html
    features = model.backbone.features
    names = ("pool0", "transition1", "transition2", "denseblock3", "transition3", "denseblock4")
    shapes, output = _forward_shapes(model, {n: getattr(features, n) for n in names}, 512)
    for shape in shapes.values():
        assert " × ".join(map(str, shape)) in html
    assert [tuple(t.shape) for t in output.values()] == [(1, 14), (1, 1), (1, 1)]
    assert not model.feature_norm.elementwise_affine
    assert model.dropout.p == 0.2


def test_atlas_denseunet_decoder_channels_and_spatial_shapes():
    html = ATLAS.read_text(encoding="utf-8")
    model = DenseUNet(pretrained=False).eval()
    names = ("bridge", "dec4", "dec3", "dec2", "dec1")
    shapes, output = _forward_shapes(model, {n: getattr(model, n) for n in names}, 256)
    for channels, height, width in shapes.values():
        assert height == width
        assert f"{channels}×{height}²" in html
    assert tuple(output.shape) == (1, 1, 256, 256)
    assert "ConvTranspose2d(32→16, k=2, s=2)" in html
    assert (model.final_upsample.in_channels, model.final_upsample.out_channels) == (32, 16)
    assert "Conv1×1(16→1)" in html
    assert (model.final_conv[-1].in_channels, model.final_conv[-1].out_channels) == (16, 1)
