# -*- coding: utf-8 -*-
"""Unit tests for the TASK-013 loss engine upgrades.

Covers:
- Focal Loss with dynamic per-class ``pos_weight`` and per-class ``alpha``.
- Asymmetric Loss (ASL) suppression of easy negatives.
- Masked multi-task routing with focal/ASL/weighted-CE heads.
- Strict gradient isolation for the new criteria.
"""
import pytest
import torch
import torch.nn as nn

from src.models.losses import AsymmetricLoss, FocalLoss, MaskedMultiTaskLoss


def _logits(batch_size: int = 2) -> dict:
    """Creates fresh per-head logits with gradients enabled."""
    return {
        "head_a": torch.randn(batch_size, 14, requires_grad=True),
        "head_b": torch.randn(batch_size, 1, requires_grad=True),
        "head_c": torch.randn(batch_size, 1, requires_grad=True),
    }


def test_focal_loss_pos_weight_upweights_rare_positive():
    """A large pos_weight must increase the loss on positive labels."""
    logits = torch.zeros(2, 3)
    targets = torch.tensor([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    base = FocalLoss(alpha=0.25, gamma=2.0)(logits, targets)
    weighted = FocalLoss(
        alpha=0.25,
        gamma=2.0,
        pos_weight=torch.tensor([10.0, 1.0, 1.0]),
    )(logits, targets)

    assert weighted.item() > base.item()


def test_focal_loss_per_class_alpha_broadcasting():
    """Per-class alpha must broadcast over (B, C) and reject wrong lengths."""
    logits = torch.zeros(2, 3)
    targets = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    per_class = FocalLoss(alpha=torch.tensor([0.9, 0.1, 0.1]))(logits, targets)
    scalar = FocalLoss(alpha=0.25)(logits, targets)

    assert torch.isfinite(per_class)
    assert per_class.item() > 0.0
    assert per_class.item() != pytest.approx(scalar.item())

    with pytest.raises(ValueError, match="alpha"):
        FocalLoss(alpha=torch.ones(2))(logits, targets)


def test_focal_loss_pos_weight_validation():
    """Invalid or mis-sized positive weights must fail loudly."""
    with pytest.raises(ValueError, match="pos_weight"):
        FocalLoss(pos_weight=-1.0)
    with pytest.raises(ValueError, match="pos_weight"):
        FocalLoss(pos_weight=float("nan"))

    logits = torch.zeros(2, 3)
    targets = torch.zeros(2, 3)
    with pytest.raises(ValueError, match="pos_weight"):
        FocalLoss(pos_weight=torch.ones(2))(logits, targets)


def test_asymmetric_loss_suppresses_easy_negatives():
    """ASL must drive sub-clip negatives to zero while BCE keeps penalizing them."""
    logits = torch.tensor([[-8.0], [-8.0]])
    targets = torch.zeros(2, 1)

    asl_loss = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05)(logits, targets)
    bce_loss = nn.BCEWithLogitsLoss()(logits, targets)

    assert asl_loss.item() == pytest.approx(0.0, abs=1e-7)
    assert bce_loss.item() > 0.0
    assert bce_loss.item() > asl_loss.item()


def test_asymmetric_loss_preserves_hard_positive_signal():
    """Rare hard positives must still contribute gradient under ASL."""
    logits = torch.tensor([[-2.0]])
    targets = torch.ones(1, 1)

    loss = AsymmetricLoss(gamma_neg=4.0, gamma_pos=1.0, clip=0.05)(logits, targets)

    assert loss.item() > 0.05


def test_asymmetric_loss_validation_and_reductions():
    """ASL hyperparameters and reduction modes must be validated."""
    with pytest.raises(ValueError, match="gamma_neg"):
        AsymmetricLoss(gamma_neg=-1.0)
    with pytest.raises(ValueError, match="gamma_pos"):
        AsymmetricLoss(gamma_pos=-1.0)
    with pytest.raises(ValueError, match="clip"):
        AsymmetricLoss(clip=1.0)
    with pytest.raises(ValueError, match="eps"):
        AsymmetricLoss(eps=0.0)
    with pytest.raises(ValueError, match="reduction"):
        AsymmetricLoss(reduction="median")

    logits = torch.randn(3, 4)
    targets = torch.randint(0, 2, (3, 4)).float()

    assert AsymmetricLoss(reduction="none")(logits, targets).shape == logits.shape
    assert AsymmetricLoss(reduction="sum")(logits, targets).item() > 0.0
    with pytest.raises(ValueError, match="identical shapes"):
        AsymmetricLoss()(logits, targets[:, :1])


def test_masked_loss_asl_gradient_isolation():
    """ASL heads must keep the zero-gradient contract for inactive heads."""
    criterion = MaskedMultiTaskLoss(
        head_a_criterion="asl", head_c_criterion="asl"
    )
    logits = _logits(batch_size=2)
    targets = [torch.ones(14), torch.zeros(14)]
    task_ids = torch.tensor([0, 0], dtype=torch.long)

    loss, metrics = criterion(logits, targets, task_ids)

    assert metrics["loss_a"] > 0.0
    assert metrics["loss_b"] == 0.0
    assert metrics["loss_c"] == 0.0

    loss.backward()
    assert logits["head_a"].grad is not None
    assert logits["head_b"].grad is None
    assert logits["head_c"].grad is None


def test_masked_loss_focal_with_dynamic_pos_weight():
    """FocalLoss inside the masked engine must honor focal_pos_weight_a."""
    logits = {
        "head_a": torch.zeros(2, 14),
        "head_b": torch.zeros(2, 1),
        "head_c": torch.zeros(2, 1),
    }
    targets = [torch.ones(14), torch.ones(14)]
    task_ids = torch.tensor([0, 0], dtype=torch.long)

    weighted = MaskedMultiTaskLoss(
        head_a_criterion="focal",
        focal_pos_weight_a=torch.full((14,), 10.0),
    )
    plain = MaskedMultiTaskLoss(head_a_criterion="focal")

    loss_weighted, _ = weighted(logits, targets, task_ids)
    loss_plain, _ = plain(logits, targets, task_ids)

    assert weighted.criterion_a.pos_weight is not None
    assert loss_weighted.item() > loss_plain.item()


def test_masked_loss_rejects_mismatched_criterion_options():
    """Criterion-specific options must not be silently ignored."""
    with pytest.raises(ValueError, match="focal_pos_weight_a"):
        MaskedMultiTaskLoss(
            head_a_criterion="bce", focal_pos_weight_a=torch.ones(14)
        )
    with pytest.raises(ValueError, match="focal_pos_weight_a"):
        MaskedMultiTaskLoss(
            head_a_criterion="asl", focal_pos_weight_a=torch.ones(14)
        )
    with pytest.raises(ValueError, match="ce_weight_c"):
        MaskedMultiTaskLoss(
            head_c_criterion="focal", ce_weight_c=[1.0, 2.0, 1.0]
        )


def test_masked_loss_weighted_cross_entropy():
    """Class-weighted CE must route Head C gradients and validate weight size."""
    criterion = MaskedMultiTaskLoss(
        head_c_criterion="ce", ce_weight_c=[1.0, 5.0, 1.0]
    )
    logits = {
        "head_a": torch.zeros(2, 14),
        "head_b": torch.zeros(2, 1),
        "head_c": torch.randn(2, 3, requires_grad=True),
    }
    targets = [torch.tensor([1]), torch.tensor([1])]
    task_ids = torch.tensor([2, 2], dtype=torch.long)

    loss, metrics = criterion(logits, targets, task_ids)

    assert metrics["loss_c"] > 0.0
    loss.backward()
    assert logits["head_c"].grad is not None

    with pytest.raises(ValueError, match="ce_weight_c"):
        mismatched = MaskedMultiTaskLoss(
            head_c_criterion="ce", ce_weight_c=[1.0, 2.0]
        )
        mismatched(logits, targets, task_ids)
