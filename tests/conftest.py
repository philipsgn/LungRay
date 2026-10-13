"""
Shared PyTest fixtures for LungRay platform testing.
"""
import pytest
import torch
import numpy as np


@pytest.fixture
def dummy_cxr_tensor():
    """Generates a dummy batch of CXR images (B=2, C=3, H=512, W=512)."""
    return torch.randn(2, 3, 512, 512)


@pytest.fixture
def dummy_nih_labels():
    """Generates multi-hot ground truth for NIH Head A (14 classes)."""
    return torch.randint(0, 2, (2, 14)).float()


@pytest.fixture
def dummy_tb_labels():
    """Generates binary ground truth for TB Head B."""
    return torch.randint(0, 2, (2, 1)).float()


@pytest.fixture
def dummy_covid_labels():
    """Generates multi-class categorical ground truth for COVID Head C (4 classes)."""
    return torch.randint(0, 4, (2,))
