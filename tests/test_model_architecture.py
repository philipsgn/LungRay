"""
LungRay Unit Tests: Model Architecture & Masked Multi-Task Loss Engine
======================================================================
Tests:
1. MultiTaskChestXrayNet forward shapes for 512x512 resolution.
2. Probability validity from .predict() method.
3. Strict Gradient Isolation (Zero Gradient Leakage between heads).
4. Focal Loss & Positive Class Weighting functionality.
5. MultiTaskTrainer 1-step dry run on heterogeneous batch.
"""
import pytest
import torch
import torch.nn as nn
from src.models.multi_task_net import MultiTaskChestXrayNet
from src.models.losses import MaskedMultiTaskLoss, FocalLoss
from src.models.trainer import MultiTaskTrainer, multitask_collate_fn


@pytest.fixture
def dummy_model():
    """Initializes a lightweight non-pretrained DenseNet-121 model for fast test execution."""
    return MultiTaskChestXrayNet(
        backbone_name="densenet121",
        pretrained=False,
        img_size=512,
        dropout_rate=0.2,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=3,
    )


def test_multitask_net_forward_shapes(dummy_model):
    """Verify MultiTaskChestXrayNet returns correct raw logit tensor shapes."""
    batch_size = 2
    dummy_input = torch.randn(batch_size, 3, 512, 512)

    dummy_model.eval()
    with torch.no_grad():
        outputs = dummy_model(dummy_input)

    assert "head_a" in outputs
    assert "head_b" in outputs
    assert "head_c" in outputs

    assert outputs["head_a"].shape == (batch_size, 14), f"Expected (2, 14), got {outputs['head_a'].shape}"
    assert outputs["head_b"].shape == (batch_size, 1), f"Expected (2, 1), got {outputs['head_b'].shape}"
    assert outputs["head_c"].shape == (batch_size, 3), f"Expected (2, 3), got {outputs['head_c'].shape}"


def test_multitask_net_predict_probabilities(dummy_model):
    """Verify .predict() returns valid activated probabilities within [0, 1] and softmax sums to 1.0."""
    batch_size = 2
    dummy_input = torch.randn(batch_size, 3, 512, 512)

    preds = dummy_model.predict(dummy_input)

    prob_a = preds["head_a"]
    prob_b = preds["head_b"]
    prob_c = preds["head_c"]

    # Sigmoid ranges in [0, 1]
    assert (prob_a >= 0.0).all() and (prob_a <= 1.0).all()
    assert (prob_b >= 0.0).all() and (prob_b <= 1.0).all()

    # Softmax ranges in [0, 1] and sums to 1.0
    assert (prob_c >= 0.0).all() and (prob_c <= 1.0).all()
    assert torch.allclose(prob_c.sum(dim=-1), torch.ones(batch_size), atol=1e-5)


def test_masked_loss_gradient_isolation(dummy_model):
    """
    INVIOLABLE CONSTRAINT CHECK (Task 3.2):
    Verify that backpropagating a batch containing ONLY Head A samples (NIH)
    produces non-zero gradients on Head A and Shared Backbone, but STRICTLY ZERO gradients on Head B and Head C.
    """
    dummy_model.train()
    criterion = MaskedMultiTaskLoss(head_a_criterion="bce")

    batch_size = 2
    dummy_input = torch.randn(batch_size, 3, 512, 512)
    # Only NIH task (task_id = 0)
    task_ids = torch.tensor([0, 0], dtype=torch.long)
    targets = [
        torch.zeros(14, dtype=torch.float32),
        torch.ones(14, dtype=torch.float32),
    ]

    logits = dummy_model(dummy_input)
    loss, metrics = criterion(logits, targets, task_ids)

    assert loss > 0.0
    assert metrics["loss_a"] > 0.0
    assert metrics["loss_b"] == 0.0
    assert metrics["loss_c"] == 0.0

    # Reset any previous gradients
    dummy_model.zero_grad()
    loss.backward()

    # Assert Head A has active gradients
    assert dummy_model.head_a.weight.grad is not None
    assert torch.norm(dummy_model.head_a.weight.grad).item() > 0.0

    # Assert Head B and Head C have ZERO gradients (Zero Gradient Leakage)
    assert dummy_model.head_b.weight.grad is None or torch.norm(dummy_model.head_b.weight.grad).item() == 0.0
    assert dummy_model.head_c.weight.grad is None or torch.norm(dummy_model.head_c.weight.grad).item() == 0.0


def test_focal_loss_computation():
    """Verify FocalLoss computes valid non-negative loss on multi-label targets."""
    focal = FocalLoss(alpha=0.25, gamma=2.0)
    logits = torch.randn(4, 14, requires_grad=True)
    targets = torch.randint(0, 2, (4, 14)).float()

    loss = focal(logits, targets)
    assert loss.item() > 0.0
    loss.backward()
    assert logits.grad is not None


def test_pos_weight_bce_weighting():
    """Verify MaskedMultiTaskLoss respects positive class weights pos_weight_a."""
    pos_weight = torch.ones(14) * 10.0
    criterion = MaskedMultiTaskLoss(pos_weight_a=pos_weight)

    logits = {"head_a": torch.zeros(2, 14), "head_b": torch.zeros(2, 1), "head_c": torch.zeros(2, 4)}
    targets = [torch.ones(14), torch.ones(14)]
    task_ids = torch.tensor([0, 0])

    loss_weighted, _ = criterion(logits, targets, task_ids)

    criterion_unweighted = MaskedMultiTaskLoss()
    loss_unweighted, _ = criterion_unweighted(logits, targets, task_ids)

    assert loss_weighted.item() > loss_unweighted.item()


def test_trainer_dryrun_one_step(dummy_model, tmp_path):
    """Verify MultiTaskTrainer successfully executes one complete optimization step on CPU."""
    criterion = MaskedMultiTaskLoss()
    optimizer = torch.optim.AdamW(dummy_model.parameters(), lr=1e-4)
    trainer = MultiTaskTrainer(
        model=dummy_model,
        criterion=criterion,
        optimizer=optimizer,
        device=torch.device("cpu"),
        mixed_precision=False,
        checkpoint_dir=str(tmp_path / "checkpoints"),
        results_dir=str(tmp_path / "results"),
    )

    # Heterogeneous mini-batch with 1 sample from each task: NIH, TB, COVID
    batch = {
        "images": torch.randn(3, 3, 512, 512),
        "task_ids": torch.tensor([0, 1, 2], dtype=torch.long),
        "labels": [
            torch.zeros(14, dtype=torch.float32),  # NIH
            torch.tensor([1.0], dtype=torch.float32),  # TB
            torch.tensor(2, dtype=torch.long),  # COVID (Class index 2)
        ],
        "image_ids": ["nih_01.png", "tb_01.png", "covid_01.png"],
    }

    loss_val, metrics = trainer.train_step(batch)

    assert loss_val > 0.0
    assert metrics["loss_a"] > 0.0
    assert metrics["loss_b"] > 0.0
    assert metrics["loss_c"] > 0.0
