"""
LungRay Loss Engine & Masked Multi-Task Loss (src/models/losses.py)
==================================================================
Inviolable Constraint (Ràng buộc 1 & Task 3.2):
- Masked Backpropagation: Each training sample belongs to exactly one dataset/task.
- Head A samples (NIH): compute Loss A (class-weighted BCE, Focal Loss, or
  Asymmetric Loss) -> updates Head A + Backbone.
- Head B samples (TB): compute Loss B (BCEWithLogitsLoss)
  -> updates Head B + Backbone.
- Head C samples (COVID): compute Loss C (binary BCE/Focal/ASL or categorical CE)
  -> updates Head C + Backbone.
- Zero Gradient Leakage: Head B and Head C receive ZERO gradients when
  processing NIH samples, and vice versa.

Clinical imbalance strategy (TASK-013):
- Head A holds 14 NIH pathologies with extreme prevalence skew (Hernia ~0.2%,
  Infiltration ~17%). ``FocalLoss`` therefore accepts a dynamic per-class
  ``pos_weight`` and per-class ``alpha``, while ``AsymmetricLoss`` (Ridnik et
  al., 2021) hard-suppresses easy negatives via ``gamma_neg >> gamma_pos``.
- All class weights are registered as module buffers so ``.to(device)`` keeps
  them on the same device as the logits (critical for single-GPU Kaggle runs).
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F


_VALID_REDUCTIONS = {"mean", "sum", "none"}


def _validate_reduction(reduction: str) -> str:
    """Normalizes and validates a loss reduction mode."""
    value = str(reduction).strip().lower()
    if value not in _VALID_REDUCTIONS:
        raise ValueError(
            f"reduction must be 'mean', 'sum', or 'none', got {reduction!r}."
        )
    return value


def _prepare_weight_tensor(
    value: Union[float, Sequence[float], torch.Tensor],
    name: str,
) -> torch.Tensor:
    """Converts a scalar/sequence weight into a validated 1-D float tensor."""
    if isinstance(value, torch.Tensor):
        tensor = value.detach().clone().to(dtype=torch.float32).reshape(-1)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        tensor = torch.tensor([float(value)], dtype=torch.float32)
    else:
        try:
            tensor = torch.as_tensor(value, dtype=torch.float32).reshape(-1)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"{name} must be a float, sequence of floats, or tensor."
            ) from exc

    if tensor.numel() == 0:
        raise ValueError(f"{name} must not be empty.")
    if not torch.isfinite(tensor).all() or (tensor < 0.0).any():
        raise ValueError(f"{name} must contain finite, non-negative values.")
    return tensor


class FocalLoss(nn.Module):
    """
    Multi-label Focal Loss with class balancing and focusing parameters.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    The class-balancing term ``alpha`` and the positive-class weight
    ``pos_weight`` are broadcast over the class dimension, so a single
    ``(num_classes,)`` vector can reflect the extreme prevalence skew of the
    14 NIH pathologies (Hernia ~0.2% vs Infiltration ~17%).

    Args:
        alpha: Scalar in [0, 1] or per-class vector of length ``num_classes``.
        gamma: Focusing parameter (>= 0).
        reduction: ``'mean'``, ``'sum'``, or ``'none'``.
        pos_weight: Optional scalar or per-class vector forwarded to
            ``binary_cross_entropy_with_logits`` to up-weight positives.
    """

    def __init__(
        self,
        alpha: Union[float, Sequence[float], torch.Tensor] = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean",
        pos_weight: Optional[Union[float, Sequence[float], torch.Tensor]] = None,
    ):
        super().__init__()
        gamma = float(gamma)
        if gamma < 0.0:
            raise ValueError(f"gamma must be non-negative, got {gamma!r}.")

        alpha_tensor = _prepare_weight_tensor(alpha, "alpha")
        if (alpha_tensor > 1.0).any():
            raise ValueError(
                f"alpha must be in [0, 1], got {alpha_tensor.tolist()!r}."
            )

        self.gamma = gamma
        self.reduction = _validate_reduction(reduction)
        self.register_buffer("alpha", alpha_tensor)
        if pos_weight is None:
            self.register_buffer("pos_weight", None)
        else:
            self.register_buffer(
                "pos_weight", _prepare_weight_tensor(pos_weight, "pos_weight")
            )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            logits: Predicted raw logits of shape (B, C).
            targets: Binary ground truth labels of shape (B, C).
        """
        if logits.shape != targets.shape:
            raise ValueError(
                f"logits and targets must have identical shapes, got "
                f"{tuple(logits.shape)} and {tuple(targets.shape)}."
            )
        if logits.dim() < 1:
            raise ValueError("logits must have at least one dimension.")
        if logits.numel() == 0:
            return logits.sum() if self.reduction != "none" else logits

        num_classes = int(logits.shape[-1])
        if self.alpha.numel() not in (1, num_classes):
            raise ValueError(
                f"alpha must contain 1 or {num_classes} values, got "
                f"{self.alpha.numel()}."
            )

        pos_weight = self.pos_weight
        if pos_weight is not None:
            if pos_weight.numel() not in (1, num_classes):
                raise ValueError(
                    f"pos_weight must contain 1 or {num_classes} values, got "
                    f"{pos_weight.numel()}."
                )
            pos_weight = pos_weight.to(device=logits.device, dtype=logits.dtype)

        targets = targets.to(device=logits.device, dtype=logits.dtype)
        bce_loss = F.binary_cross_entropy_with_logits(
            logits, targets, reduction="none", pos_weight=pos_weight
        )

        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha = self.alpha.to(device=logits.device, dtype=logits.dtype)
        alpha_t = alpha * targets + (1.0 - alpha) * (1.0 - targets)
        focal_weight = alpha_t * torch.pow((1.0 - p_t).clamp(min=0.0), self.gamma)
        loss = focal_weight * bce_loss

        if self.reduction == "mean":
            return loss.mean()
        if self.reduction == "sum":
            return loss.sum()
        return loss


class AsymmetricLoss(nn.Module):
    """
    Asymmetric Loss (ASL) for multi-label thoracic pathology classification.

    ASL(p) = - y * (1 - p)^gamma_pos * log(p)
             - (1 - y) * p_m^gamma_neg * log(1 - p_m),   p_m = max(p - clip, 0)

    Rationale (Ridnik et al., CVPR 2021): the negative branch dominates
    multi-label batches (e.g. 13 of 14 NIH labels are usually absent). A large
    ``gamma_neg`` plus probability shifting ``clip`` drives the gradient of easy
    negatives to exactly zero, freeing capacity for subtle infiltrates,
    nodules, and hernias. ``gamma_pos`` stays small to avoid discarding rare
    positive evidence.

    Args:
        gamma_neg: Focusing exponent for negatives (default 4.0).
        gamma_pos: Focusing exponent for positives (default 1.0).
        clip: Probability shift applied to negatives (default 0.05).
        eps: Numerical stability epsilon for logarithms.
        reduction: ``'mean'``, ``'sum'``, or ``'none'``.
    """

    def __init__(
        self,
        gamma_neg: float = 4.0,
        gamma_pos: float = 1.0,
        clip: float = 0.05,
        eps: float = 1e-8,
        reduction: str = "mean",
    ):
        super().__init__()
        gamma_neg = float(gamma_neg)
        gamma_pos = float(gamma_pos)
        clip = float(clip)
        eps = float(eps)

        if gamma_neg < 0.0:
            raise ValueError(
                f"gamma_neg must be non-negative, got {gamma_neg!r}."
            )
        if gamma_pos < 0.0:
            raise ValueError(
                f"gamma_pos must be non-negative, got {gamma_pos!r}."
            )
        if not 0.0 <= clip < 1.0:
            raise ValueError(f"clip must be in [0, 1), got {clip!r}.")
        if eps <= 0.0:
            raise ValueError(f"eps must be strictly positive, got {eps!r}.")

        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps
        self.reduction = _validate_reduction(reduction)

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """Args mirror :class:`FocalLoss`: raw logits and binary targets."""
        if logits.shape != targets.shape:
            raise ValueError(
                f"logits and targets must have identical shapes, got "
                f"{tuple(logits.shape)} and {tuple(targets.shape)}."
            )
        if logits.numel() == 0:
            return logits.sum() if self.reduction != "none" else logits

        targets = targets.to(device=logits.device, dtype=logits.dtype)
        probs = torch.sigmoid(logits)
        probs_neg = (probs - self.clip).clamp(min=0.0)

        pos_term = (
            targets
            * torch.log(probs.clamp(min=self.eps))
            * torch.pow((1.0 - probs).clamp(min=0.0), self.gamma_pos)
        )
        neg_term = (
            (1.0 - targets)
            * torch.log((1.0 - probs_neg).clamp(min=self.eps))
            * torch.pow(probs_neg, self.gamma_neg)
        )
        loss = -(pos_term + neg_term)

        if self.reduction == "mean":
            return loss.mean()
        if self.reduction == "sum":
            return loss.sum()
        return loss


class MaskedMultiTaskLoss(nn.Module):
    """
    Masked Multi-Task Loss Engine ensuring strict gradient isolation between heads.

    Loss Formulation:
    L_total = w_A * L_A(NIH) + w_B * L_B(TB) + w_C * L_C(COVID)

    Head criteria:
    - Head A: ``'bce'`` (dynamic ``pos_weight``), ``'focal'`` (Focal Loss with
      optional ``focal_pos_weight_a``), or ``'asl'`` (Asymmetric Loss).
    - Head B: ``BCEWithLogitsLoss`` (threshold tau_B calibrated separately with
      Youden's J statistic in ``src.utils.threshold_tuning``).
    - Head C: ``'bce'`` (binary screening), ``'ce'`` (3-class COVIDx with
      optional ``ce_weight_c`` class weights), ``'focal'``, or ``'asl'``.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        head_a_criterion: str = "bce",  # 'bce', 'focal', or 'asl'
        pos_weight_a: Optional[torch.Tensor] = None,
        focal_pos_weight_a: Optional[Union[float, Sequence[float], torch.Tensor]] = None,
        focal_gamma: float = 2.0,
        focal_alpha: Union[float, Sequence[float], torch.Tensor] = 0.25,
        asl_gamma_neg: float = 4.0,
        asl_gamma_pos: float = 1.0,
        asl_clip: float = 0.05,
        head_c_criterion: str = "bce",  # 'bce', 'ce', 'focal', or 'asl'
        pos_weight_c: Optional[Union[float, torch.Tensor]] = None,
        ce_weight_c: Optional[Union[Sequence[float], torch.Tensor]] = None,
    ):
        super().__init__()

        default_weights = {"head_a": 1.0, "head_b": 0.8, "head_c": 0.8}
        resolved_weights = {**default_weights, **(weights or {})}
        for key, value in resolved_weights.items():
            weight = float(value)
            if not torch.isfinite(torch.tensor(weight)) or weight < 0.0:
                raise ValueError(
                    f"Loss weight for {key!r} must be finite and non-negative, "
                    f"got {value!r}."
                )
            resolved_weights[key] = weight
        self.weights = resolved_weights

        self.head_a_criterion_name = str(head_a_criterion).strip().lower()
        if self.head_a_criterion_name not in {"bce", "focal", "asl"}:
            raise ValueError(
                "head_a_criterion must be 'bce', 'focal', or 'asl', got "
                f"{head_a_criterion!r}."
            )

        self.head_c_criterion_name = str(head_c_criterion).strip().lower()
        if self.head_c_criterion_name not in {"bce", "ce", "focal", "asl"}:
            raise ValueError(
                "head_c_criterion must be 'bce', 'ce', 'focal', or 'asl', got "
                f"{head_c_criterion!r}."
            )

        if self.head_a_criterion_name != "bce" and pos_weight_a is not None:
            raise ValueError(
                "pos_weight_a is only supported with head_a_criterion='bce'; "
                "use focal_pos_weight_a for Focal Loss or Asymmetric Loss."
            )
        if self.head_a_criterion_name != "focal" and focal_pos_weight_a is not None:
            raise ValueError(
                "focal_pos_weight_a is only supported with "
                "head_a_criterion='focal'."
            )
        if self.head_c_criterion_name != "bce" and pos_weight_c is not None:
            raise ValueError(
                "pos_weight_c is only supported with head_c_criterion='bce'."
            )
        if self.head_c_criterion_name != "ce" and ce_weight_c is not None:
            raise ValueError(
                "ce_weight_c is only supported with head_c_criterion='ce'."
            )

        # Head A: 14 thoracic pathologies (multi-label).
        self.criterion_a: Optional[nn.Module] = None
        if self.head_a_criterion_name == "bce":
            self.register_buffer(
                "pos_weight_a",
                self._prepare_pos_weight(
                    pos_weight_a, name="pos_weight_a", allowed_numels=(1, 14)
                ),
            )
        elif self.head_a_criterion_name == "focal":
            self.register_buffer("pos_weight_a", None)
            prepared_focal = (
                _prepare_weight_tensor(focal_pos_weight_a, "focal_pos_weight_a")
                if focal_pos_weight_a is not None
                else None
            )
            self.criterion_a = FocalLoss(
                alpha=focal_alpha,
                gamma=focal_gamma,
                reduction="mean",
                pos_weight=prepared_focal,
            )
        else:
            self.criterion_a = AsymmetricLoss(
                gamma_neg=asl_gamma_neg,
                gamma_pos=asl_gamma_pos,
                clip=asl_clip,
                reduction="mean",
            )

        # Head C: COVID-19 screening (binary BCE/Focal/ASL, or categorical CE).
        self.criterion_c: Optional[nn.Module] = None
        self.register_buffer("pos_weight_c", None)
        self.register_buffer("ce_weight_c", None)
        if self.head_c_criterion_name == "ce":
            if ce_weight_c is not None:
                self.register_buffer(
                    "ce_weight_c",
                    _prepare_weight_tensor(ce_weight_c, "ce_weight_c"),
                )
        elif self.head_c_criterion_name == "focal":
            self.criterion_c = FocalLoss(
                alpha=focal_alpha,
                gamma=focal_gamma,
                reduction="mean",
            )
        elif self.head_c_criterion_name == "asl":
            self.criterion_c = AsymmetricLoss(
                gamma_neg=asl_gamma_neg,
                gamma_pos=asl_gamma_pos,
                clip=asl_clip,
                reduction="mean",
            )
        else:
            self.register_buffer(
                "pos_weight_c",
                self._prepare_pos_weight(
                    pos_weight_c, name="pos_weight_c", allowed_numels=(1,)
                ),
            )

    @staticmethod
    def _prepare_pos_weight(
        value: Optional[Union[float, torch.Tensor]],
        name: str,
        allowed_numels: Tuple[int, ...],
    ) -> Optional[torch.Tensor]:
        """Validates and normalizes a BCE ``pos_weight`` argument."""
        if value is None:
            return None

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            weight = float(value)
            if not torch.isfinite(torch.tensor(weight)) or weight < 0.0:
                raise ValueError(
                    f"{name} must be finite and non-negative, got {value!r}."
                )
            tensor = torch.tensor([weight], dtype=torch.float32)
        else:
            tensor = torch.as_tensor(value, dtype=torch.float32)
            if not torch.is_tensor(tensor):
                raise TypeError(f"{name} must be a float or torch.Tensor.")
            tensor = tensor.detach().clone().reshape(-1)
            if tensor.numel() == 0:
                raise ValueError(f"{name} must not be empty.")
            if not torch.isfinite(tensor).all() or (tensor < 0.0).any():
                raise ValueError(
                    f"{name} must contain finite, non-negative values."
                )

        if tensor.numel() not in allowed_numels:
            raise ValueError(
                f"{name} must contain {allowed_numels} values, got "
                f"{tensor.numel()}."
            )
        return tensor

    @staticmethod
    def _extract_targets(
        targets: Union[List[torch.Tensor], Dict[str, torch.Tensor]],
        key: str,
        mask: torch.Tensor,
        batch_size: int,
        device: torch.device,
    ) -> torch.Tensor:
        """Extracts and masks the targets for one active head."""
        count = int(mask.sum().item())

        if isinstance(targets, dict):
            if key not in targets:
                raise KeyError(f"Missing target tensor for {key!r}.")
            tensor = torch.as_tensor(targets[key]).to(device)
            if tensor.shape[0] == batch_size:
                tensor = tensor[mask]
            elif tensor.shape[0] != count:
                raise ValueError(
                    f"Target {key!r} has {tensor.shape[0]} rows; expected "
                    f"{batch_size} (full batch) or {count} (masked batch)."
                )
            return tensor

        if not isinstance(targets, (list, tuple)):
            raise TypeError(
                "targets must be a list/tuple of per-sample tensors or a "
                "dict of per-head tensors."
            )
        if len(targets) != batch_size:
            raise ValueError(
                f"targets has {len(targets)} entries; expected {batch_size}."
            )

        indices = torch.nonzero(mask, as_tuple=True)[0].tolist()
        rows = [torch.as_tensor(targets[index]) for index in indices]
        return torch.stack(rows).to(device)

    def forward(
        self,
        logits_dict: Dict[str, torch.Tensor],
        targets: Union[List[torch.Tensor], Dict[str, torch.Tensor]],
        task_ids: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Computes masked multi-task loss with gradient isolation.

        Args:
            logits_dict: Output dictionary from MultiTaskChestXrayNet
                containing 'head_a', 'head_b', and 'head_c'.
            targets: Either a list of per-sample label tensors, or a dict of
                per-head tensors (full-batch or already-masked).
            task_ids: 1-D Tensor of shape (B,) with values in
                {0 (NIH), 1 (TB), 2 (COVID)}.

        Returns:
            Tuple of:
            - total_loss: scalar tensor with the gradient graph attached.
            - metrics: per-head loss values for logging.

        Raises:
            ValueError: If task IDs, logits, or target shapes are invalid.
        """
        required_heads = ("head_a", "head_b", "head_c")
        for head in required_heads:
            if head not in logits_dict:
                raise KeyError(f"logits_dict is missing {head!r}.")
            if not torch.is_tensor(logits_dict[head]):
                raise TypeError(f"logits_dict[{head!r}] must be a tensor.")

        device = logits_dict["head_a"].device
        if not torch.is_tensor(task_ids) or task_ids.ndim != 1:
            raise ValueError("task_ids must be a 1-D tensor.")
        if task_ids.numel() == 0:
            total_loss = logits_dict["head_a"].sum() * 0.0
            return total_loss, {
                "loss_a": 0.0,
                "loss_b": 0.0,
                "loss_c": 0.0,
                "loss_total": 0.0,
            }

        batch_size = int(task_ids.numel())
        for head in required_heads:
            if logits_dict[head].shape[0] != batch_size:
                raise ValueError(
                    f"logits_dict[{head!r}] has batch size "
                    f"{logits_dict[head].shape[0]}; expected {batch_size}."
                )

        task_ids = task_ids.to(device)
        if not torch.all((task_ids >= 0) & (task_ids <= 2)):
            raise ValueError("task_ids values must be in {0, 1, 2}.")

        metrics = {
            "loss_a": 0.0,
            "loss_b": 0.0,
            "loss_c": 0.0,
            "loss_total": 0.0,
        }

        mask_a = task_ids == 0
        mask_b = task_ids == 1
        mask_c = task_ids == 2
        weighted_losses: List[torch.Tensor] = []

        # --- Head A: NIH ChestX-ray14 ---
        if mask_a.any():
            logits_a = logits_dict["head_a"][mask_a]
            y_a = self._extract_targets(
                targets, "head_a", mask_a, batch_size, device
            ).float()
            if y_a.dim() == 1 and logits_a.shape[0] == 1:
                y_a = y_a.unsqueeze(0)
            if y_a.shape != logits_a.shape:
                raise ValueError(
                    f"Head A target shape {tuple(y_a.shape)} does not match "
                    f"logits shape {tuple(logits_a.shape)}."
                )
            if self.head_a_criterion_name == "bce":
                loss_a = F.binary_cross_entropy_with_logits(
                    logits_a, y_a, pos_weight=self.pos_weight_a
                )
            else:
                loss_a = self.criterion_a(logits_a, y_a)
            weighted_losses.append(
                self.weights.get("head_a", 1.0) * loss_a
            )
            metrics["loss_a"] = float(loss_a.detach().item())

        # --- Head B: Tuberculosis ---
        if mask_b.any():
            logits_b = logits_dict["head_b"][mask_b]
            y_b = self._extract_targets(
                targets, "head_b", mask_b, batch_size, device
            ).float()
            y_b = self._match_binary_shape(logits_b, y_b, "Head B")
            loss_b = F.binary_cross_entropy_with_logits(logits_b, y_b)
            weighted_losses.append(
                self.weights.get("head_b", 0.8) * loss_b
            )
            metrics["loss_b"] = float(loss_b.detach().item())

        # --- Head C: COVID-19 screening ---
        if mask_c.any():
            logits_c = logits_dict["head_c"][mask_c]
            y_c = self._extract_targets(
                targets, "head_c", mask_c, batch_size, device
            )

            if self.head_c_criterion_name == "ce":
                if logits_c.dim() != 2:
                    raise ValueError(
                        "CrossEntropyLoss requires Head C logits of shape "
                        f"(B, C), got {tuple(logits_c.shape)}."
                    )
                if self.ce_weight_c is not None and (
                    self.ce_weight_c.numel() != logits_c.shape[1]
                ):
                    raise ValueError(
                        f"ce_weight_c must contain {logits_c.shape[1]} values, "
                        f"got {self.ce_weight_c.numel()}."
                    )
                y_c = y_c.long()
                if y_c.dim() > 1 and y_c.size(-1) == 1:
                    y_c = y_c.squeeze(-1)
                if y_c.dim() != 1:
                    raise ValueError(
                        "CrossEntropyLoss requires Head C targets of shape "
                        f"(B,), got {tuple(y_c.shape)}."
                    )
                loss_c = F.cross_entropy(
                    logits_c, y_c, weight=self.ce_weight_c
                )
            else:
                y_c = self._match_binary_shape(
                    logits_c, y_c.float(), "Head C"
                )
                if self.head_c_criterion_name == "bce":
                    loss_c = F.binary_cross_entropy_with_logits(
                        logits_c, y_c, pos_weight=self.pos_weight_c
                    )
                else:
                    loss_c = self.criterion_c(logits_c, y_c)

            weighted_losses.append(
                self.weights.get("head_c", 0.8) * loss_c
            )
            metrics["loss_c"] = float(loss_c.detach().item())

        if weighted_losses:
            total_loss = torch.stack(weighted_losses).sum()
        else:
            total_loss = logits_dict["head_a"].sum() * 0.0

        metrics["loss_total"] = float(total_loss.detach().item())
        return total_loss, metrics

    @staticmethod
    def _match_binary_shape(
        logits: torch.Tensor,
        targets: torch.Tensor,
        head_name: str,
    ) -> torch.Tensor:
        """Aligns binary target/logit shapes to (B, 1) or (B,)."""
        if logits.dim() == 2 and logits.size(-1) == 1:
            if targets.dim() == 1:
                targets = targets.unsqueeze(-1)
            elif targets.dim() != 2 or targets.size(-1) != 1:
                raise ValueError(
                    f"{head_name} targets must have shape (B,) or (B, 1), "
                    f"got {tuple(targets.shape)}."
                )
        elif logits.dim() == 1:
            if targets.dim() == 2 and targets.size(-1) == 1:
                targets = targets.squeeze(-1)
            elif targets.dim() != 1:
                raise ValueError(
                    f"{head_name} targets must have shape (B,) for 1-D "
                    f"logits, got {tuple(targets.shape)}."
                )
        else:
            raise ValueError(
                f"{head_name} logits must be (B,) or (B, 1), got "
                f"{tuple(logits.shape)}."
            )

        if targets.shape != logits.shape:
            raise ValueError(
                f"{head_name} target shape {tuple(targets.shape)} does not "
                f"match logits shape {tuple(logits.shape)}."
            )
        return targets
