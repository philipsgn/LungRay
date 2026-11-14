"""
tests/test_dense_unet_and_asl.py
================================
Unit tests for:
1. DenseUNet architecture (Dubey et al. BMC Infectious Diseases 2026, Dice 0.9848)
2. Dilated soft anatomical masking
3. Asymmetric Focal Loss (ASL) for multi-label imbalance
"""
import numpy as np
import pytest
import torch

from src.explainability.shortcut_audit import LungSegmenter
from src.models.asymmetric_loss import AsymmetricFocalLoss
from src.models.dense_unet import (
    CombinedSegmentationLoss,
    DenseUNet,
    DiceLoss,
    apply_dilated_soft_mask,
    apply_dilated_soft_mask_tensor,
    compute_segmentation_metrics,
)


def test_dense_unet_forward_shape():
    """DenseUNet returns binary mask of exact same spatial dimensions (H, W)."""
    model = DenseUNet(pretrained=False, in_channels=3)
    model.eval()

    # Test with 256x256
    x256 = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        out256 = model(x256)
    assert out256.shape == (1, 1, 256, 256)
    assert (out256 >= 0.0).all() and (out256 <= 1.0).all()

    # Test with 512x512
    x512 = torch.randn(1, 3, 512, 512)
    with torch.no_grad():
        out512 = model(x512)
    assert out512.shape == (1, 1, 512, 512)
    assert (out512 >= 0.0).all() and (out512 <= 1.0).all()


def test_dense_unet_predict_mask():
    """predict_mask returns uint8 array with binary values {0, 255}."""
    model = DenseUNet(pretrained=False)
    x = torch.randn(1, 3, 128, 128)
    mask = model.predict_mask(x, threshold=0.5)

    assert isinstance(mask, np.ndarray)
    assert mask.shape == (128, 128)
    assert mask.dtype == np.uint8
    unique_vals = set(np.unique(mask))
    assert unique_vals.issubset({0, 255})


def test_apply_dilated_soft_mask():
    """Dilated soft masking preserves lung fields and attenuates outer background by 90%."""
    # Synthetic 512x512 image (uniform intensity 200)
    img = np.full((512, 512, 3), 200, dtype=np.uint8)

    # Synthetic lung mask: two rectangles in left and right chest
    binary_mask = np.zeros((512, 512), dtype=np.uint8)
    binary_mask[100:400, 80:200] = 255   # Right lung
    binary_mask[100:400, 312:432] = 255  # Left lung

    grounded = apply_dilated_soft_mask(
        image_np=img,
        binary_mask=binary_mask,
        dilation_margin_pct=0.06,
        background_attenuation=0.10,
    )

    assert grounded.shape == img.shape
    assert grounded.dtype == np.uint8

    # Inside the lung: intensity should be preserved (~200)
    center_lung_val = grounded[250, 140, 0]
    assert center_lung_val >= 190

    # Far outside (e.g. at corner [10, 10] where R/L marker would be):
    # Intensity should be attenuated by ~90% (200 * 0.10 = 20)
    corner_val = grounded[10, 10, 0]
    assert corner_val <= 30


def test_asymmetric_focal_loss_computation():
    """ASL calculates valid scalar loss for multi-label classification."""
    loss_fn = AsymmetricFocalLoss(gamma_neg=4.0, gamma_pos=0.0, clip=0.05)
    logits = torch.randn(4, 14)
    targets = torch.randint(0, 2, (4, 14)).float()

    loss = loss_fn(logits, targets)
    assert isinstance(loss, torch.Tensor)
    assert loss.ndim == 0  # Scalar
    assert torch.isfinite(loss)
    assert loss.item() >= 0.0


def test_asymmetric_focal_loss_easy_negative_suppression():
    """Easy negative samples (pred < clip) produce near-zero loss compared to hard negatives."""
    loss_fn = AsymmetricFocalLoss(gamma_neg=4.0, gamma_pos=0.0, clip=0.05)

    # Easy negative: target=0, logit=-5.0 (prob=0.0067 < clip=0.05)
    easy_neg_logits = torch.tensor([[-5.0]])
    target_zero = torch.tensor([[0.0]])
    easy_loss = loss_fn(easy_neg_logits, target_zero)

    # Hard negative: target=0, logit=1.0 (prob=0.73 > clip=0.05)
    hard_neg_logits = torch.tensor([[1.0]])
    hard_loss = loss_fn(hard_neg_logits, target_zero)

    # Easy negative loss should be virtually 0 (< 1e-4) while hard negative is substantial (> 0.20)
    assert easy_loss.item() < 1e-4
    assert hard_loss.item() > 0.20
    assert hard_loss.item() > easy_loss.item() * 1000


def test_lung_segmenter_with_dense_unet():
    """LungSegmenter integrates Dense-UNet and provides generate_dilated_soft_mask."""
    dense_unet = DenseUNet(pretrained=False)
    segmenter = LungSegmenter(dense_unet=dense_unet)

    img = np.full((256, 256, 3), 150, dtype=np.uint8)
    mask = segmenter.predict_mask(img)
    assert mask.shape == (256, 256)
    assert set(np.unique(mask)).issubset({0, 1})

    grounded = segmenter.generate_dilated_soft_mask(img)
    assert grounded.shape == img.shape
    assert grounded.dtype == np.uint8


def test_generate_dilated_soft_mask_attenuates_background(monkeypatch):
    """The dilated soft gate dims the non-lung background while preserving lung intensity."""
    segmenter = LungSegmenter(refine_with_grabcut=False)
    img = np.full((512, 512, 3), 200, dtype=np.uint8)

    fixed_mask = np.zeros((512, 512), dtype=np.uint8)
    fixed_mask[100:400, 80:200] = 1   # right lung
    fixed_mask[100:400, 312:432] = 1  # left lung
    monkeypatch.setattr(segmenter, "predict_mask", lambda _img: fixed_mask)

    grounded = segmenter.generate_dilated_soft_mask(
        img, dilation_margin_pct=0.06, background_attenuation=0.10
    )

    assert grounded.shape == img.shape
    assert grounded.dtype == np.uint8
    inner = float(grounded[250, 140].mean())
    outer = float(grounded[10, 10].mean())
    assert inner >= 190.0
    assert outer <= 30.0
    assert outer < inner * 0.2


def test_anatomical_gate_disabled_returns_input_unchanged():
    """With the gate off, the service pre-processing is a strict no-op."""
    from app.backend.services import LungRayService

    class _StubService:
        anatomical_gate_enabled = False

    img = np.full((64, 64, 3), 180, dtype=np.uint8)
    out = LungRayService._anatomical_gate(_StubService(), img)
    assert out is img or np.array_equal(out, img)


def test_anatomical_gate_enabled_delegates_to_segmenter():
    """With the gate on, the service routes the image through the soft-mask segmenter."""
    from app.backend.services import LungRayService

    class _StubSegmenter:
        def generate_dilated_soft_mask(
            self, img, dilation_margin_pct=0.06, background_attenuation=0.10
        ):
            assert dilation_margin_pct == 0.06
            assert background_attenuation == 0.10
            return np.zeros_like(img)

    class _StubService:
        anatomical_gate_enabled = True
        segmenter = _StubSegmenter()

    img = np.full((64, 64, 3), 180, dtype=np.uint8)
    out = LungRayService._anatomical_gate(_StubService(), img)
    assert out.shape == img.shape
    assert int(out.max()) == 0


def test_dense_unet_predict_mask_batch_shape():
    """Batch inference returns one binary (H, W) mask per image in a single forward."""
    model = DenseUNet(pretrained=False)
    model.eval()
    batch = torch.randn(3, 3, 128, 128)
    masks = model.predict_mask_batch(batch, threshold=0.5)

    assert masks.shape == (3, 128, 128)
    assert masks.dtype == np.uint8
    assert set(np.unique(masks)).issubset({0, 255})


def test_lung_segmenter_predict_masks_preserves_native_shape():
    """predict_masks returns one mask per image at its native spatial resolution."""
    segmenter = LungSegmenter()
    images = [
        np.full((128, 128, 3), 150, dtype=np.uint8),
        np.full((96, 64, 3), 150, dtype=np.uint8),
    ]
    masks = segmenter.predict_masks(images)

    assert len(masks) == 2
    assert masks[0].shape == (128, 128)
    assert masks[1].shape == (96, 64)
    for mask in masks:
        assert set(np.unique(mask)).issubset({0, 1})


def test_dice_loss_and_combined_segmentation_loss():
    """CombinedSegmentationLoss computes valid scalar loss bounded between 0 and 1."""
    dice_loss_fn = DiceLoss()
    combined_loss_fn = CombinedSegmentationLoss(alpha=0.50)

    # Identical predictions and targets -> Loss near 0
    pred_perfect = torch.ones(2, 1, 64, 64)
    target_perfect = torch.ones(2, 1, 64, 64)
    d_loss = dice_loss_fn(pred_perfect, target_perfect)
    c_loss = combined_loss_fn(pred_perfect, target_perfect)
    assert d_loss.item() < 0.05
    assert c_loss.item() < 0.05

    # Opposites -> Dice loss near 1
    pred_zero = torch.zeros(2, 1, 64, 64)
    target_one = torch.ones(2, 1, 64, 64)
    d_loss_high = dice_loss_fn(pred_zero, target_one)
    assert d_loss_high.item() > 0.95


def test_compute_segmentation_metrics():
    """compute_segmentation_metrics accurately computes Dice and IoU coefficients."""
    # Perfect overlap
    mask_a = np.ones((50, 50), dtype=np.uint8) * 255
    mask_b = np.ones((50, 50), dtype=np.uint8) * 255
    res = compute_segmentation_metrics(mask_a, mask_b)
    assert pytest.approx(res["dice"], 0.01) == 1.0
    assert pytest.approx(res["iou"], 0.01) == 1.0

    # Half overlap: 50x50 vs 50x25
    mask_c = np.zeros((50, 50), dtype=np.uint8)
    mask_c[:, :25] = 255
    res_half = compute_segmentation_metrics(mask_a, mask_c)
    # Intersection = 1250, Sum = 2500 + 1250 = 3750 -> Dice = 2*1250/3750 = 2/3 = 0.667
    assert pytest.approx(res_half["dice"], 0.01) == 0.667
    # IoU = 1250 / 2500 = 0.50
    assert pytest.approx(res_half["iou"], 0.01) == 0.50


def test_apply_dilated_soft_mask_white_out_failsafe():
    """
    White-Out Lung & Massive Effusion Safeguard:
    When segmented lung coverage < 18% or hemithoracic asymmetry is extreme,
    apply_dilated_soft_mask bypasses gating and returns the original image unattenuated.
    """
    img = np.full((512, 512, 3), 200, dtype=np.uint8)

    # 1. Severely small lung coverage (e.g. 5% coverage due to massive bilateral white-out)
    low_cov_mask = np.zeros((512, 512), dtype=np.uint8)
    low_cov_mask[200:250, 200:250] = 255  # 50x50 / 512x512 = 0.95%

    out_low = apply_dilated_soft_mask(img, low_cov_mask, min_lung_coverage=0.18)
    # Fail-safe triggered -> returns unattenuated original image
    assert np.array_equal(out_low, img)
    assert out_low[10, 10, 0] == 200

    # 2. Extreme unilateral asymmetry (e.g. unilateral complete white-out / massive pleural effusion)
    # Right lung normal (12% of total image), Left lung 0% -> asymmetry ratio 0.0, total 12% < 25%
    unilateral_mask = np.zeros((512, 512), dtype=np.uint8)
    unilateral_mask[100:400, 80:180] = 255  # Right hemithorax only

    out_unilateral = apply_dilated_soft_mask(img, unilateral_mask, min_symmetry_ratio=0.20)
    assert np.array_equal(out_unilateral, img)
    assert out_unilateral[10, 10, 0] == 200


def test_apply_dilated_soft_mask_tensor_failsafe_batch():
    """
    GPU tensor batch gating evaluates fail-safe per sample:
    Sample 0 (normal lung, ~27% coverage) gets soft-attenuated outer background.
    Sample 1 (white-out lung, ~2% coverage) triggers fail-safe and remains 100% unattenuated.
    """
    batch_img = torch.full((2, 3, 256, 256), 200.0)
    batch_mask = torch.zeros((2, 1, 256, 256))

    # Sample 0: Normal bilateral lungs (50:200, 40:100) and (50:200, 156:216) -> 150*60*2 = 18000 / 65536 = 27.5%
    batch_mask[0, 0, 50:200, 40:100] = 1.0
    batch_mask[0, 0, 50:200, 156:216] = 1.0

    # Sample 1: White-out lung (only 30x30 spot = 900 / 65536 = 1.4% coverage)
    batch_mask[1, 0, 100:130, 100:130] = 1.0

    gated = apply_dilated_soft_mask_tensor(
        batch_img,
        batch_mask,
        dilation_margin_pct=0.06,
        background_attenuation=0.10,
        min_lung_coverage=0.18,
    )

    # Sample 0: Corner (10, 10) is attenuated by 90% (200 * 0.10 = 20)
    assert gated[0, :, 10, 10].mean().item() <= 30.0
    # Sample 0: Inside lung is preserved (~200)
    assert gated[0, :, 100, 70].mean().item() >= 190.0

    # Sample 1: Fail-safe triggered -> Corner (10, 10) stays unattenuated at 200
    assert pytest.approx(gated[1, :, 10, 10].mean().item(), abs=1e-2) == 200.0
    assert pytest.approx(gated[1].mean().item(), abs=1e-2) == 200.0


def test_dense_unet_grayscale_in_channels():
    """DenseUNet supports arbitrary in_channels (e.g. single-channel grayscale CXR)."""
    model_gray = DenseUNet(pretrained=False, in_channels=1)
    model_gray.eval()
    x1 = torch.randn(1, 1, 128, 128)
    with torch.no_grad():
        out1 = model_gray(x1)
    assert out1.shape == (1, 1, 128, 128)
    assert (out1 >= 0.0).all() and (out1 <= 1.0).all()


