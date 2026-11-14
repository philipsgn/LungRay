"""
src/models/dense_unet.py - Dense-UNet Lung Segmentation Architecture
====================================================================
Based on SOTA comparative evaluation in:
Dubey et al. BMC Infectious Diseases (2026) 26:922
"Comparative evaluation of deep learning models for lung segmentation in chest X-rays:
applications in infectious disease screening"
https://doi.org/10.1186/s12879-026-13041-y

Key Benchmark Highlights:
- Dice Coefficient: 0.9848 (#1 out of 10 evaluated architectures)
- IoU (Jaccard Index): 0.9700 (#1)
- Hausdorff Distance: 12.2417 (lowest surface boundary error)
- ASSD: 1.5279 (lowest symmetric distance)

Architecture:
- Encoder: DenseNet-121 backbone extracting hierarchical dense representations
  (denseblock1, denseblock2, denseblock3, denseblock4)
- Decoder: Transposed convolution upsampling with dense skip connections
- Output: 1-channel binary segmentation mask with Sigmoid activation
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class DecoderBlock(nn.Module):
    """
    Decoder block with transposed convolution upsampling,
    concatenation with skip connection, and double convolution with BatchNorm and ReLU.
    """

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.upsample = nn.ConvTranspose2d(
            in_channels, in_channels // 2, kernel_size=2, stride=2
        )
        total_in = (in_channels // 2) + skip_channels
        self.conv = nn.Sequential(
            nn.Conv2d(total_in, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.upsample(x)
        # Handle spatial dimension mismatch if needed
        if x.shape[2:] != skip.shape[2:]:
            x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class DenseUNet(nn.Module):
    """
    Dense-UNet for high-precision lung field segmentation in Chest X-rays.
    Employs DenseNet-121 as contracting path for superior feature reuse and gradient flow.
    """

    def __init__(self, pretrained: bool = False, in_channels: int = 3):
        super().__init__()
        densenet = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT if pretrained else None)

        # Handle grayscale input if needed
        if in_channels != 3:
            self.init_conv = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        else:
            self.init_conv = densenet.features.conv0

        self.init_bn = densenet.features.norm0
        self.init_relu = densenet.features.relu0
        self.init_pool = densenet.features.pool0

        # Dense Blocks & Transition Layers
        self.denseblock1 = densenet.features.denseblock1  # 256 channels
        self.transition1 = densenet.features.transition1  # 128 channels

        self.denseblock2 = densenet.features.denseblock2  # 512 channels
        self.transition2 = densenet.features.transition2  # 256 channels

        self.denseblock3 = densenet.features.denseblock3  # 1024 channels
        self.transition3 = densenet.features.transition3  # 512 channels

        self.denseblock4 = densenet.features.denseblock4  # 1024 channels
        self.norm5 = densenet.features.norm5

        # Bottleneck bridge (1024 channels -> 512 channels)
        self.bridge = nn.Sequential(
            nn.Conv2d(1024, 512, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )

        # Decoder Stages (Symmetric expansion with skip connections)
        # Stage 4: from bridge (512) + skip denseblock3 (1024) -> 256
        self.dec4 = DecoderBlock(in_channels=512, skip_channels=1024, out_channels=256)
        # Stage 3: from dec4 (256) + skip denseblock2 (512) -> 128
        self.dec3 = DecoderBlock(in_channels=256, skip_channels=512, out_channels=128)
        # Stage 2: from dec3 (128) + skip denseblock1 (256) -> 64
        self.dec2 = DecoderBlock(in_channels=128, skip_channels=256, out_channels=64)
        # Stage 1: from dec2 (64) + skip init_relu (64) -> 32
        self.dec1 = DecoderBlock(in_channels=64, skip_channels=64, out_channels=32)

        # Final Upsampling to original image resolution (e.g. 512x512)
        self.final_upsample = nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2)
        self.final_conv = nn.Sequential(
            nn.Conv2d(16, 16, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 1, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_size = x.shape[2:]

        # Encoder
        x0 = self.init_conv(x)
        x0 = self.init_bn(x0)
        s0 = self.init_relu(x0)  # Skip 0: 64 channels, H/2, W/2
        p0 = self.init_pool(s0)  # H/4, W/4

        d1 = self.denseblock1(p0)  # Skip 1: 256 channels, H/4, W/4
        t1 = self.transition1(d1)  # H/8, W/8

        d2 = self.denseblock2(t1)  # Skip 2: 512 channels, H/8, W/8
        t2 = self.transition2(d2)  # H/16, W/16

        d3 = self.denseblock3(t2)  # Skip 3: 1024 channels, H/16, W/16
        t3 = self.transition3(d3)  # H/32, W/32

        d4 = self.denseblock4(t3)  # 1024 channels, H/32, W/32
        d4 = self.norm5(d4)

        # Bridge
        b = self.bridge(d4)  # 512 channels, H/32, W/32

        # Decoder with skip connections
        u4 = self.dec4(b, d3)   # H/16, W/16
        u3 = self.dec3(u4, d2)  # H/8, W/8
        u2 = self.dec2(u3, d1)  # H/4, W/4
        u1 = self.dec1(u2, s0)  # H/2, W/2

        out = self.final_upsample(u1)  # H, W
        if out.shape[2:] != input_size:
            out = F.interpolate(out, size=input_size, mode="bilinear", align_corners=False)
        logits = self.final_conv(out)
        return torch.sigmoid(logits)

    @torch.no_grad()
    def predict_mask(
        self,
        image_tensor: torch.Tensor,
        threshold: float = 0.50,
    ) -> np.ndarray:
        """
        Runs inference on a (1, 3, H, W) or (3, H, W) tensor and returns a (H, W) uint8 binary mask (0 or 255).
        """
        self.eval()
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        device = next(self.parameters()).device
        image_tensor = image_tensor.to(device)
        prob_mask = self.forward(image_tensor)
        mask_np = (prob_mask.squeeze().cpu().numpy() >= threshold).astype(np.uint8) * 255
        return mask_np

    @torch.no_grad()
    def predict_mask_batch(
        self,
        image_tensor: torch.Tensor,
        threshold: float = 0.50,
    ) -> np.ndarray:
        """
        Runs batched inference on an ``(N, 3, H, W)`` tensor (or a single
        ``(3, H, W)`` image) and returns an ``(N, H, W)`` uint8 mask in {0, 255}.

        A single forward pass over the whole batch keeps per-image latency low
        when the Dense-UNet gate is applied to several views or images at once.
        """
        self.eval()
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        if image_tensor.ndim != 4:
            raise ValueError(
                f"image_tensor must have shape (N, 3, H, W) or (3, H, W), got {tuple(image_tensor.shape)}."
            )
        device = next(self.parameters()).device
        image_tensor = image_tensor.to(device)
        prob_mask = self.forward(image_tensor)
        return (prob_mask.squeeze(1).cpu().numpy() >= threshold).astype(np.uint8) * 255


def apply_dilated_soft_mask(
    image_np: np.ndarray,
    binary_mask: np.ndarray,
    dilation_margin_pct: float = 0.06,
    background_attenuation: float = 0.10,
    min_lung_coverage: float = 0.18,
    min_symmetry_ratio: float = 0.20,
) -> np.ndarray:
    """
    Applies an anatomically-dilated soft mask to a chest X-ray image:
    1. Clinical Fail-Safe Check (White-out Lung & Massive Effusion Safeguard):
       Evaluates lung coverage and hemithoracic symmetry. Normal adult lungs cover
       22-38% of the CXR field. If coverage < min_lung_coverage (18%) or if one
       hemithorax is severely diminished (symmetry < 20% with low coverage), gating
       is bypassed to prevent catastrophic 90% attenuation of radiopaque pathologies.
    2. Dilates the lung mask by dilation_margin_pct (5-8%) to preserve:
       - Costophrenic recesses (critical for Pleural Effusion)
       - Lateral thoracic pleura (critical for Pneumothorax & Pleural Thickening)
       - Mediastinal/cardiac border (critical for Cardiomegaly)
    3. Blurs mask edges with Gaussian filter to prevent hard boundary artifacts.
    4. Softly attenuates the outer thoracic background to background_attenuation (default: 10%),
       dimming letters like 'R', 'L', and scanner borders by 90% without hard cutoff.
    """
    h, w = image_np.shape[:2]
    if binary_mask.shape[:2] != (h, w):
        binary_mask = cv2.resize(binary_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Normalise any {0, 1} or {0, 255} mask convention to a 0/255 raster before
    # the /255 softening below, otherwise a {0, 1} lung mask would collapse every
    # weight to ~0 and dim the entire radiograph to the background attenuation.
    binary_mask = (np.asarray(binary_mask) > 0).astype(np.uint8) * 255

    # Clinical Fail-Safe: evaluate total coverage and bilateral hemithorax symmetry
    total_pixels = float(h * w)
    lung_pixels = float(np.count_nonzero(binary_mask))
    coverage = lung_pixels / max(total_pixels, 1.0)

    mid_x = w // 2
    left_lung_px = float(np.count_nonzero(binary_mask[:, :mid_x]))
    right_lung_px = float(np.count_nonzero(binary_mask[:, mid_x:]))
    max_side = max(left_lung_px, right_lung_px)
    min_side = min(left_lung_px, right_lung_px)
    symmetry_ratio = (min_side / max_side) if max_side > 0.0 else 0.0

    if coverage < min_lung_coverage or (symmetry_ratio < min_symmetry_ratio and coverage < 0.25):
        # Suspected white-out lung, massive pleural effusion, or segmentation distortion.
        # Bypass gate and preserve 100% of native radiograph.
        return np.asarray(image_np)

    # 1. Morphological Dilation
    kernel_size = max(5, int(min(h, w) * dilation_margin_pct))
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated_mask = cv2.dilate(binary_mask, kernel, iterations=1)

    # 2. Gaussian Edge Softening
    blur_ksize = max(7, kernel_size // 2 * 2 + 1)
    soft_weight = cv2.GaussianBlur(dilated_mask.astype(np.float32) / 255.0, (blur_ksize, blur_ksize), 0)

    # Scale weight between background_attenuation and 1.0
    alpha = background_attenuation + (1.0 - background_attenuation) * soft_weight

    # 3. Soft Attenuation
    if image_np.ndim == 3:
        alpha_3d = np.expand_dims(alpha, axis=-1)
        grounded = (image_np.astype(np.float32) * alpha_3d).clip(0, 255).astype(np.uint8)
    else:
        grounded = (image_np.astype(np.float32) * alpha).clip(0, 255).astype(np.uint8)

    return grounded


class DiceLoss(nn.Module):
    """
    Soft Dice Loss for medical image binary segmentation.

    Computed PER SAMPLE and then averaged over the batch (rather than a single
    global Dice over the whole batch), so a large or empty mask in one image
    cannot dominate the batch gradient.

    Loss = 1 - mean_b [ (2 * intersection_b + eps) / (card + eps) ].
    """

    def __init__(self, eps: float = 1e-6):
        super().__init__()
        self.eps = eps

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred = pred.float()
        target = target.float()
        if pred.dim() < 3:
            pred = pred.reshape(1, -1)
            target = target.reshape(1, -1)
        else:
            pred = pred.reshape(pred.shape[0], -1)
            target = target.reshape(target.shape[0], -1)
        intersection = (pred * target).sum(dim=1)
        dice = (2.0 * intersection + self.eps) / (
            pred.sum(dim=1) + target.sum(dim=1) + self.eps
        )
        return 1.0 - dice.mean()


class CombinedSegmentationLoss(nn.Module):
    """
    Combined BCE + Dice Loss for robust lung boundary segmentation (Dubey et al. BMC 2026).
    Loss = alpha * BCE + (1 - alpha) * DiceLoss.

    All terms are forced to FP32 and the probabilities are clamped away from the
    0/1 boundary before the BCE log terms, so the loss never evaluates to NaN
    (a real hazard under AMP FP16, where sigmoid saturates to exactly 0.0/1.0).
    """

    def __init__(self, alpha: float = 0.50, eps: float = 1e-7):
        super().__init__()
        if not 0.0 <= float(alpha) <= 1.0:
            raise ValueError(f"alpha must be in [0, 1], got {alpha!r}.")
        self.alpha = float(alpha)
        self.eps = float(eps)
        self.dice = DiceLoss(eps=eps)

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred = pred.float().clamp(min=self.eps, max=1.0 - self.eps)
        target = target.float()
        # Direct analytical BCE in FP32: avoids PyTorch's torch.cuda.amp runtime assertion
        # against torch.nn.functional.binary_cross_entropy while remaining 100% mathematically exact
        bce_loss = -(target * torch.log(pred) + (1.0 - target) * torch.log(1.0 - pred)).mean()
        dice_loss = self.dice(pred, target)
        return self.alpha * bce_loss + (1.0 - self.alpha) * dice_loss


def apply_dilated_soft_mask_tensor(
    images: torch.Tensor,
    masks: torch.Tensor,
    dilation_margin_pct: float = 0.06,
    background_attenuation: float = 0.10,
    min_lung_coverage: float = 0.18,
    min_symmetry_ratio: float = 0.20,
) -> torch.Tensor:
    """
    GPU tensor implementation of the Dilated Soft Anatomical Masking gate with
    Clinical Fail-Safe Protocol (White-out Lung & Massive Effusion Safeguard).

    Suitable for on-the-fly gating inside a training loop: the dilation is a
    max-pool and the soft edge an average-pool, running entirely on GPU.
    If a sample's segmented lung field has coverage < min_lung_coverage or extreme
    bilateral asymmetry (< min_symmetry_ratio), gating for that sample is bypassed
    to prevent attenuating dense radiopaque pathologies.

    Args:
        images: ``(B, C, H, W)`` or ``(C, H, W)`` float tensor.
        masks: ``(B, 1, H, W)``, ``(B, H, W)``, or ``(H, W)`` binary tensor.
        dilation_margin_pct: Dilation kernel size as a fraction of ``min(H, W)``.
        background_attenuation: Multiplicative weight applied to the background.
        min_lung_coverage: Minimum fractional lung field area to qualify for gating.
        min_symmetry_ratio: Minimum ratio between left and right hemithorax areas.

    Returns:
        Gated images with the same shape as ``images``.
    """
    was_3d = False
    if images.dim() == 3:
        images = images.unsqueeze(0)
        was_3d = True

    if masks.dim() == 2:
        masks = masks.unsqueeze(0).unsqueeze(0)
    elif masks.dim() == 3:
        masks = masks.unsqueeze(1)

    height, width = int(images.shape[-2]), int(images.shape[-1])
    kernel = max(5, int(round(min(height, width) * dilation_margin_pct)))
    if kernel % 2 == 0:
        kernel += 1
    pad = kernel // 2
    binary = (masks > 0.5).float()

    # 1. Clinical Fail-Safe Evaluation per sample in batch
    total_px = float(height * width)
    coverage = binary.sum(dim=(-2, -1)) / total_px  # (B, 1)

    mid_x = width // 2
    left_px = binary[..., :mid_x].sum(dim=(-2, -1))
    right_px = binary[..., mid_x:].sum(dim=(-2, -1))
    max_side = torch.maximum(left_px, right_px)
    min_side = torch.minimum(left_px, right_px)
    symmetry_ratio = torch.where(max_side > 0.0, min_side / max_side.clamp(min=1.0), torch.zeros_like(max_side))

    fail_coverage = coverage < min_lung_coverage
    fail_symmetry = (symmetry_ratio < min_symmetry_ratio) & (coverage < 0.25)
    bypass_mask = fail_coverage | fail_symmetry  # (B, 1)

    # 2. Dilation & Softening
    dilated = F.max_pool2d(binary, kernel_size=kernel, stride=1, padding=pad)
    soft = F.avg_pool2d(dilated, kernel_size=kernel, stride=1, padding=pad)
    alpha = background_attenuation + (1.0 - background_attenuation) * soft  # (B, 1, H, W)

    if bypass_mask.any():
        bypass_expanded = bypass_mask.view(-1, 1, 1, 1).expand_as(alpha)
        alpha = torch.where(bypass_expanded, torch.ones_like(alpha), alpha)

    out = images * alpha
    return out.squeeze(0) if was_3d else out


def compute_segmentation_metrics(
    pred_mask: np.ndarray, target_mask: np.ndarray, eps: float = 1e-6
) -> dict[str, float]:
    """
    Computes Dice coefficient and IoU (Jaccard Index) between binary masks.
    """
    p = (pred_mask > 0).astype(np.float32).flatten()
    t = (target_mask > 0).astype(np.float32).flatten()
    intersection = (p * t).sum()
    dice = (2.0 * intersection + eps) / (p.sum() + t.sum() + eps)
    union = p.sum() + t.sum() - intersection
    iou = (intersection + eps) / (union + eps)
    return {"dice": float(dice), "iou": float(iou)}

