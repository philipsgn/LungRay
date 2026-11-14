"""
src/models/asymmetric_loss.py - Asymmetric Focal Loss for Multi-Label CXR
========================================================================
Based on:
Ridnik et al., "Asymmetric Loss For Multi-Label Classification" (ICCV 2021)

Problem Addressed:
In multi-label Chest X-ray classification (e.g. NIH ChestX-ray14), negative labels
account for > 95% of all label instances. Standard BCE or symmetric Focal Loss
accumulates excessive gradient from millions of easy negative pixels/labels,
diluting gradients for rare pathologies like Hernia, Fibrosis, and Pneumonia.

Asymmetric Loss (ASL) Formulation:
- Decouples gamma_pos and gamma_neg:
    gamma_pos = 0 or 1 (preserves gradient for true positive lesions)
    gamma_neg = 4 (exponentially suppresses easy negative examples)
- Shifts negative probabilities by margin m:
    p_neg_shifted = max(p - m, 0)
    This discards easy negatives whose predicted probability is below m.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class AsymmetricFocalLoss(nn.Module):
    """
    Asymmetric Focal Loss (ASL) for extreme multi-label class imbalance.

    Args:
        gamma_neg: Focusing parameter for negative samples (higher -> more suppression of easy negatives).
        gamma_pos: Focusing parameter for positive samples (lower -> preserves gradients for true positives).
        clip: Margin shift for negative samples (p_neg_shifted = clamp(p - clip, min=0)).
        eps: Epsilon for numerical stability.
        reduction: 'mean', 'sum', or 'none'.
    """

    def __init__(
        self,
        gamma_neg: float = 4.0,
        gamma_pos: float = 0.0,
        clip: float = 0.05,
        eps: float = 1e-7,
        reduction: str = "mean",
    ):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps
        self.reduction = reduction

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Args:
            logits: Predicted raw logits of shape (B, C).
            targets: Binary ground truth labels of shape (B, C) in [0, 1].
            mask: Optional binary mask of shape (B, C) or (B,) indicating valid tasks.

        Returns:
            Scalar loss (if reduction=='mean') or tensor of losses.
        """
        # FP32 computation: under AMP autocast the sigmoid/log path would run in
        # FP16, where `eps` (1e-7) underflows to 0 and log(0) yields NaN.
        logits = logits.float()
        targets = targets.float()
        probs = torch.sigmoid(logits)

        # 1. Positive Loss: - targets * (1 - p)^gamma_pos * log(p)
        p_pos = probs.clamp(min=self.eps, max=1.0 - self.eps)
        loss_pos = -targets * torch.pow(1.0 - p_pos, self.gamma_pos) * torch.log(p_pos)

        # 2. Negative Loss with Asymmetric Margin Shift:
        # p_shifted = max(probs - clip, 0)
        # loss_neg = - (1 - targets) * (p_shifted)^gamma_neg * log(1 - p_shifted)
        if self.clip > 0:
            p_neg = (probs - self.clip).clamp(min=0.0, max=1.0 - self.eps)
        else:
            p_neg = probs.clamp(min=self.eps, max=1.0 - self.eps)

        loss_neg = -(1.0 - targets) * torch.pow(p_neg, self.gamma_neg) * torch.log((1.0 - p_neg).clamp(min=self.eps))

        total_loss = loss_pos + loss_neg

        # Optional validity mask ((B,) per sample or (B, C) per element). The mask
        # is broadcast to the loss shape and the mean is taken over VALID ELEMENTS
        # only, i.e. sum(masked) / sum(mask). This is consistent for both (B,) and
        # (B, C) masks and avoids the previous off-by-C scaling error.
        if mask is not None:
            if mask.ndim == 1:
                mask = mask.unsqueeze(-1)
            mask = mask.float().expand_as(total_loss)
            total_loss = total_loss * mask
            if self.reduction == "mean":
                return total_loss.sum() / mask.sum().clamp(min=1.0)
            if self.reduction == "sum":
                return total_loss.sum()
            return total_loss

        if self.reduction == "mean":
            return total_loss.mean()
        elif self.reduction == "sum":
            return total_loss.sum()
        return total_loss
