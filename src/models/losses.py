"""
LungRay Loss Engine & Masked Multi-Task Loss (src/models/losses.py)
==================================================================
Inviolable Constraint (Ràng buộc 1 & Task 3.2):
- Masked Backpropagation: Each training sample belongs to exactly one dataset/task.
- Head A samples (NIH): compute Loss A (BCE with pos_weight or Focal Loss) -> updates Head A + Backbone.
- Head B samples (TB): compute Loss B (BCEWithLogitsLoss) -> updates Head B + Backbone.
- Head C samples (COVID): compute Loss C (CrossEntropyLoss) -> updates Head C + Backbone.
- Zero Gradient Leakage: Head B and Head C receive ZERO gradients when processing NIH samples.
"""
from typing import Dict, Optional, Tuple, Any, List, Union
import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """
    Multi-label Focal Loss with class balancing parameter alpha and focusing parameter gamma.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean"
    ):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: Predicted raw logits of shape (B, C).
            targets: Binary ground truth labels of shape (B, C).
        """
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal_weight = alpha_t * torch.pow(1.0 - p_t, self.gamma)
        loss = focal_weight * bce_loss

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


class MaskedMultiTaskLoss(nn.Module):
    """
    Masked Multi-Task Loss Engine ensuring strict gradient isolation between heads.

    Loss Formulation:
    L_total = w_A * L_A(NIH) + w_B * L_B(TB) + w_C * L_C(COVID)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        head_a_criterion: str = "bce",  # 'bce' or 'focal'
        pos_weight_a: Optional[torch.Tensor] = None,
        focal_gamma: float = 2.0,
        focal_alpha: float = 0.25,
    ):
        super().__init__()
        self.weights = weights or {"head_a": 1.0, "head_b": 0.8, "head_c": 0.8}
        self.head_a_criterion_name = head_a_criterion

        # Head A: 14 thoracic pathologies (multi-label)
        if head_a_criterion == "focal":
            self.criterion_a = FocalLoss(alpha=focal_alpha, gamma=focal_gamma, reduction="mean")
        else:
            if pos_weight_a is not None:
                self.register_buffer("pos_weight_a", pos_weight_a.clone().detach())
                self.criterion_a = nn.BCEWithLogitsLoss(pos_weight=self.pos_weight_a)
            else:
                self.pos_weight_a = None
                self.criterion_a = nn.BCEWithLogitsLoss()

        # Head B: TB screening (binary logit)
        self.criterion_b = nn.BCEWithLogitsLoss()

        # Head C: COVID-19 screening (4-class categorical)
        self.criterion_c = nn.CrossEntropyLoss()

    def forward(
        self,
        logits_dict: Dict[str, torch.Tensor],
        targets: Union[List[torch.Tensor], Dict[str, torch.Tensor]],
        task_ids: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Computes masked multi-task loss with gradient isolation.

        Args:
            logits_dict: Output dictionary from MultiTaskChestXrayNet containing 'head_a', 'head_b', 'head_c'.
            targets: Either a list of per-sample label tensors, or a dict of per-task tensors.
            task_ids: 1D Tensor of shape (B,) with values in {0 (NIH), 1 (TB), 2 (COVID)}.

        Returns:
            Tuple of:
            - total_loss: PyTorch scalar tensor with attached gradient computational graph.
            - metrics: Dict of floating-point loss values per head for logging.
        """
        device = logits_dict["head_a"].device
        metrics = {
            "loss_a": 0.0,
            "loss_b": 0.0,
            "loss_c": 0.0,
            "loss_total": 0.0,
        }

        # Identify sample masks
        mask_a = (task_ids == 0)
        mask_b = (task_ids == 1)
        mask_c = (task_ids == 2)

        total_loss = torch.tensor(0.0, device=device, requires_grad=True)
        active_heads = 0

        # --- Head A: NIH ChestX-ray14 ---
        if mask_a.any():
            logits_a = logits_dict["head_a"][mask_a]
            if isinstance(targets, dict):
                y_a = targets["head_a"]
            else:
                # Extract and stack labels for mask_a samples
                idx_a = torch.nonzero(mask_a, as_tuple=True)[0]
                y_a = torch.stack([targets[i] for i in idx_a]).to(device).float()

            loss_a = self.criterion_a(logits_a, y_a)
            total_loss = total_loss + self.weights.get("head_a", 1.0) * loss_a
            metrics["loss_a"] = float(loss_a.detach().item())
            active_heads += 1

        # --- Head B: Tuberculosis ---
        if mask_b.any():
            logits_b = logits_dict["head_b"][mask_b]
            if isinstance(targets, dict):
                y_b = targets["head_b"]
            else:
                idx_b = torch.nonzero(mask_b, as_tuple=True)[0]
                y_b = torch.stack([targets[i] for i in idx_b]).to(device).float()
                if y_b.dim() == 1:
                    y_b = y_b.unsqueeze(-1)

            loss_b = self.criterion_b(logits_b, y_b)
            total_loss = total_loss + self.weights.get("head_b", 0.8) * loss_b
            metrics["loss_b"] = float(loss_b.detach().item())
            active_heads += 1

        # --- Head C: COVID-19 Radiography ---
        if mask_c.any():
            logits_c = logits_dict["head_c"][mask_c]
            if isinstance(targets, dict):
                y_c = targets["head_c"]
            else:
                idx_c = torch.nonzero(mask_c, as_tuple=True)[0]
                y_c = torch.stack([targets[i] for i in idx_c]).to(device).long()
                if y_c.dim() > 1 and y_c.size(-1) == 1:
                    y_c = y_c.squeeze(-1)

            loss_c = self.criterion_c(logits_c, y_c)
            total_loss = total_loss + self.weights.get("head_c", 0.8) * loss_c
            metrics["loss_c"] = float(loss_c.detach().item())
            active_heads += 1

        metrics["loss_total"] = float(total_loss.detach().item())
        return total_loss, metrics
