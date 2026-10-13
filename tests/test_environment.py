"""
Test environment and module structure for LungRay platform.
"""
import sys
import importlib


def test_python_version():
    """Verify Python version is 3.10+."""
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version_info}"


def test_core_dependencies():
    """Verify core packages can be imported."""
    for pkg in ["torch", "torchvision", "numpy", "pandas"]:
        module = importlib.import_module(pkg)
        assert module is not None, f"Failed to import {pkg}"


def test_lungray_package_structure():
    """Verify internal LungRay package modules exist."""
    import src
    import src.data
    import src.models
    import src.explainability
    import src.utils

    assert src.__version__ == "0.1.0"


def test_standard_512_resolution_fixture(dummy_cxr_tensor):
    """Verify standard input resolution fixture is 512x512."""
    assert dummy_cxr_tensor.shape == (2, 3, 512, 512), f"Expected 512x512 shape, got {dummy_cxr_tensor.shape}"


def test_backbones_module_import():
    """Verify backbones builder with 512x512 resolution utilities can be imported."""
    from src.models.backbones import build_backbone, interpolate_vit_pos_embed_for_512
    assert callable(build_backbone)
    assert callable(interpolate_vit_pos_embed_for_512)

