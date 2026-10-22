# -*- coding: utf-8 -*-
"""Unit tests for the threshold tuning engine and masked loss upgrades."""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch
from sklearn.metrics import f1_score

from src.models.losses import FocalLoss, MaskedMultiTaskLoss
from src.utils.threshold_tuning import (
    NIH_PATHOLOGY_NAMES,
    apply_thresholds,
    find_best_threshold_f1,
    find_best_threshold_youden,
    load_thresholds_json,
    save_thresholds_json,
    tune_multilabel_thresholds,
)


def _binary_tensors(
    batch_size: int = 3,
    device: torch.device = torch.device("cpu"),
):
    """Creates fresh logits tensors with gradients enabled."""
    return {
        "head_a": torch.randn(
            batch_size, 14, device=device, requires_grad=True
        ),
        "head_b": torch.randn(
            batch_size, 1, device=device, requires_grad=True
        ),
        "head_c": torch.randn(
            batch_size, 1, device=device, requires_grad=True
        ),
    }


def test_find_best_threshold_youden_separable():
    """Youden's J should recover a threshold between well-separated modes."""
    rng = np.random.default_rng(42)
    y_true = np.array([0] * 100 + [1] * 100)
    y_prob = np.concatenate(
        [
            rng.normal(0.2, 0.05, 100),
            rng.normal(0.8, 0.05, 100),
        ]
    )
    y_prob = np.clip(y_prob, 0.0, 1.0)

    best_thresh, best_j = find_best_threshold_youden(y_true, y_prob)

    assert 0.30 <= best_thresh <= 0.70
    assert best_j > 0.95


def test_find_best_threshold_f1_imbalanced():
    """F1 maximization should handle a rare-positive distribution."""
    rng = np.random.default_rng(42)
    y_true = np.array([0] * 190 + [1] * 10)
    y_prob = np.concatenate(
        [
            rng.normal(0.15, 0.08, 190),
            rng.normal(0.70, 0.10, 10),
        ]
    )
    y_prob = np.clip(y_prob, 0.0, 1.0)

    best_thresh, best_f1 = find_best_threshold_f1(y_true, y_prob)

    assert 0.10 <= best_thresh <= 0.90
    assert best_f1 > 0.60
    predicted = (y_prob >= best_thresh).astype(np.int32)
    assert f1_score(y_true, predicted, zero_division=0) == pytest.approx(
        best_f1
    )


def test_f1_grid_mode_matches_bruteforce():
    """The vectorized grid mode must match a naive sklearn F1 sweep."""
    rng = np.random.default_rng(7)
    y_true = rng.integers(0, 2, size=80)
    y_prob = rng.uniform(0.0, 1.0, size=80)

    best_thresh, best_f1 = find_best_threshold_f1(
        y_true, y_prob, num_thresholds=25
    )

    grid = np.linspace(0.02, 0.98, 25)
    scores = [
        f1_score(
            y_true,
            (y_prob >= threshold).astype(np.int32),
            zero_division=0,
        )
        for threshold in grid
    ]
    assert best_f1 == pytest.approx(float(np.max(scores)))
    predicted = (y_prob >= best_thresh).astype(np.int32)
    assert f1_score(y_true, predicted, zero_division=0) == pytest.approx(
        best_f1
    )


def test_f1_exact_mode_handles_saturated_probabilities():
    """A threshold of exactly 0.0 must remain valid for all-zero scores."""
    y_true = np.array([0, 1], dtype=np.int32)
    y_prob = np.zeros(2, dtype=np.float32)

    best_thresh, best_f1 = find_best_threshold_f1(y_true, y_prob)

    assert best_thresh == pytest.approx(0.0)
    assert best_f1 == pytest.approx(2.0 / 3.0)


@pytest.mark.parametrize("positive", [0, 1])
def test_mono_class_fallback(positive):
    """Mono-class labels must return the fallback threshold and zero metric."""
    y_true = np.full(50, positive, dtype=np.int32)
    y_prob = np.linspace(0.1, 0.9, 50)

    t_youden, j_youden = find_best_threshold_youden(
        y_true, y_prob, fallback_threshold=0.37
    )
    t_f1, f1_value = find_best_threshold_f1(
        y_true, y_prob, fallback_threshold=0.37
    )

    assert t_youden == pytest.approx(0.37)
    assert j_youden == pytest.approx(0.0)
    assert t_f1 == pytest.approx(0.37)
    assert f1_value == pytest.approx(0.0)


def test_youden_constant_probabilities():
    """Constant probabilities cannot separate classes, but must stay finite."""
    y_true = np.array([0, 1, 0, 1], dtype=np.int32)
    y_prob = np.full(4, 0.5, dtype=np.float32)

    best_thresh, best_j = find_best_threshold_youden(y_true, y_prob)

    assert 0.01 <= best_thresh <= 0.99
    assert best_j == pytest.approx(0.0)


@pytest.mark.parametrize(
    "y_true,y_prob,match",
    [
        ([0, 1], [0.2], "same number of elements"),
        ([0, 2], [0.2, 0.8], "binary labels"),
        ([0, 1], [0.2, 1.2], r"probabilities in \[0, 1\]"),
        ([0, 1], [0.2, np.nan], "finite"),
        ([], [], "must not be empty"),
    ],
)
def test_threshold_input_validation(y_true, y_prob, match):
    """Invalid label/probability inputs must fail loudly."""
    with pytest.raises(ValueError, match=match):
        find_best_threshold_youden(np.asarray(y_true), np.asarray(y_prob))
    with pytest.raises(ValueError, match=match):
        find_best_threshold_f1(np.asarray(y_true), np.asarray(y_prob))


def test_invalid_fallback_and_num_thresholds():
    """Invalid tuning hyperparameters must raise clear errors."""
    y_true = np.array([0, 1], dtype=np.int32)
    y_prob = np.array([0.2, 0.8], dtype=np.float32)

    with pytest.raises(ValueError, match="fallback_threshold"):
        find_best_threshold_youden(y_true, y_prob, fallback_threshold=np.nan)
    with pytest.raises(ValueError, match="at least 2"):
        find_best_threshold_f1(y_true, y_prob, num_thresholds=1)


def test_tune_multilabel_thresholds():
    """Threshold calibration must cover every NIH pathology."""
    rng = np.random.default_rng(42)
    y_true = rng.integers(0, 2, size=(200, 14))
    y_true[0, :] = 0
    y_true[1, :] = 1
    y_prob = rng.uniform(0.0, 1.0, size=(200, 14))

    thresholds_dict = tune_multilabel_thresholds(
        y_true,
        y_prob,
        class_names=NIH_PATHOLOGY_NAMES,
        method="youden",
    )

    assert len(thresholds_dict) == 14
    for name in NIH_PATHOLOGY_NAMES:
        assert name in thresholds_dict
        assert 0.01 <= thresholds_dict[name] <= 0.99


def test_tune_multilabel_f1_and_validation():
    """F1 mode and all validation branches must behave deterministically."""
    rng = np.random.default_rng(11)
    y_true = rng.integers(0, 2, size=(40, 3))
    y_true[0, :] = 0
    y_true[1, :] = 1
    y_prob = rng.uniform(0.0, 1.0, size=(40, 3))

    thresholds = tune_multilabel_thresholds(
        y_true, y_prob, class_names=["A", "B", "C"], method="F1"
    )
    assert set(thresholds) == {"A", "B", "C"}

    with pytest.raises(ValueError, match="Unknown threshold method"):
        tune_multilabel_thresholds(y_true, y_prob, method="lift")
    with pytest.raises(ValueError, match="class_names"):
        tune_multilabel_thresholds(
            y_true, y_prob, class_names=["A", "B"]
        )
    with pytest.raises(ValueError, match="2-D"):
        tune_multilabel_thresholds(y_true[:, 0], y_prob[:, 0])
    with pytest.raises(ValueError, match="shapes differ"):
        tune_multilabel_thresholds(y_true, y_prob[:, :2])


def test_apply_thresholds_modes():
    """Scalar, list, and dictionary thresholds must agree where equivalent."""
    probs = np.array(
        [
            [0.2, 0.6, 0.8],
            [0.7, 0.3, 0.4],
        ]
    )
    class_names = ["A", "B", "C"]

    bin_scalar = apply_thresholds(probs, 0.5)
    assert bin_scalar.shape == probs.shape
    assert bin_scalar[0, 0] == 0 and bin_scalar[0, 1] == 1

    bin_list = apply_thresholds(probs, [0.3, 0.5, 0.7])
    assert bin_list[0, 0] == 0 and bin_list[1, 0] == 1

    thresh_dict = {"A": 0.3, "B": 0.5, "C": 0.7}
    bin_dict = apply_thresholds(probs, thresh_dict, class_names=class_names)
    np.testing.assert_array_equal(bin_list, bin_dict)


def test_apply_thresholds_one_dimensional_dict():
    """1-D dictionaries must be resolved without arbitrary key selection."""
    probs = np.array([0.2, 0.8])

    bin_single = apply_thresholds(probs, {"COVID-19": 0.5})
    np.testing.assert_array_equal(bin_single, [0, 1])

    bin_named = apply_thresholds(
        probs, {"threshold": 0.5, "metadata": 1}, class_names=["threshold"]
    )
    np.testing.assert_array_equal(bin_named, bin_single)

    bin_metadata = apply_thresholds(
        probs, {"threshold": 0.5, "metadata": 1}
    )
    np.testing.assert_array_equal(bin_metadata, bin_single)

    with pytest.raises(ValueError, match="requires class_names"):
        apply_thresholds(probs, {"A": 0.3, "B": 0.7})


@pytest.mark.parametrize(
    "thresholds,match",
    [
        ([0.3, 0.7], "Number of thresholds"),
        ([0.3, 0.5, np.nan], "finite"),
        (1.2, r"\[0, 1\]"),
    ],
)
def test_apply_thresholds_invalid(thresholds, match):
    """Invalid threshold arrays/scalars must raise."""
    probs = np.array([[0.2, 0.6, 0.8]])
    with pytest.raises(ValueError, match=match):
        apply_thresholds(probs, thresholds)


def test_apply_thresholds_invalid_probabilities_and_names():
    """Probability and class-name validation must be strict."""
    with pytest.raises(ValueError, match="finite"):
        apply_thresholds(np.array([0.2, np.nan]), 0.5)
    with pytest.raises(ValueError, match="probabilities"):
        apply_thresholds(np.array([0.2, 1.5]), 0.5)
    with pytest.raises(ValueError, match="class_names"):
        apply_thresholds(
            np.array([[0.2, 0.8]]),
            {"a": 0.3, "b": 0.7},
            class_names=["only_one"],
        )


def test_json_save_and_load():
    """Serialization must round-trip nested threshold metadata."""
    test_data = {
        "head_a": {"Cardiomegaly": 0.42, "Effusion": 0.38},
        "head_b": {"threshold": 0.50},
        "head_c": {"threshold": 0.50},
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "test_thresholds.json")
        save_thresholds_json(test_data, json_path)
        assert os.path.exists(json_path)

        with open(json_path, "r", encoding="utf-8") as handle:
            assert json.load(handle) == test_data

        loaded = load_thresholds_json(json_path)
        assert loaded == test_data


def test_json_strict_errors():
    """NaN, non-dict roots, and missing files must fail loudly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "bad.json")
        with pytest.raises(ValueError):
            save_thresholds_json({"threshold": float("nan")}, json_path)
        with pytest.raises(TypeError):
            save_thresholds_json([0.5], json_path)

        with open(json_path, "w", encoding="utf-8") as handle:
            handle.write("[0.5]")
        with pytest.raises(ValueError, match="root must be an object"):
            load_thresholds_json(json_path)

        with pytest.raises(FileNotFoundError):
            load_thresholds_json(os.path.join(tmp_dir, "missing.json"))


def test_optimal_thresholds_config_schema():
    """The production JSON must match the 14 NIH + TB + COVID schema."""
    config_path = (
        Path(__file__).resolve().parents[1]
        / "configs"
        / "optimal_thresholds.json"
    )
    text = config_path.read_text(encoding="utf-8")
    assert "NaN" not in text and "Infinity" not in text

    config = load_thresholds_json(str(config_path))
    assert config["version"]
    assert set(config["head_a_nih_14"]) == set(NIH_PATHOLOGY_NAMES)
    assert all(
        0.0 <= value <= 1.0 for value in config["head_a_nih_14"].values()
    )

    assert 0.0 <= config["head_b_tb"]["threshold"] <= 1.0
    assert config["head_b_tb"]["positive_class"] == "Tuberculosis"
    assert 0.0 <= config["head_c_covid"]["threshold"] <= 1.0
    assert config["head_c_covid"]["pos_weight_c_recommended"] > 0.0
    assert config["default_fallback_threshold"] == pytest.approx(0.50)


def test_focal_loss_validation_and_reduction():
    """FocalLoss must validate hyperparameters and support all reductions."""
    with pytest.raises(ValueError, match="alpha"):
        FocalLoss(alpha=1.5)
    with pytest.raises(ValueError, match="gamma"):
        FocalLoss(gamma=-1.0)
    with pytest.raises(ValueError, match="reduction"):
        FocalLoss(reduction="median")

    logits = torch.randn(4, 3, requires_grad=True)
    targets = torch.randint(0, 2, (4, 3)).float()

    with pytest.raises(ValueError, match="identical shapes"):
        FocalLoss()(logits, targets[:, :1])

    none_loss = FocalLoss(reduction="none")(logits, targets)
    assert none_loss.shape == logits.shape
    assert FocalLoss(reduction="sum")(logits, targets) > 0.0


def test_masked_loss_with_head_c_rebalancing():
    """Head C must accept scalar/tensor pos_weight and Focal Loss."""
    criterion_rebalanced = MaskedMultiTaskLoss(
        pos_weight_c=0.185,
        head_c_criterion="bce",
    )
    assert criterion_rebalanced.pos_weight_c is not None
    assert torch.isclose(
        criterion_rebalanced.pos_weight_c,
        torch.tensor([0.185]),
        atol=1e-3,
    )

    logits_dict = _binary_tensors()
    targets = [
        torch.zeros(14),
        torch.ones(1),
        torch.ones(1),
    ]
    task_ids = torch.tensor([0, 1, 2], dtype=torch.long)

    loss, metrics = criterion_rebalanced(logits_dict, targets, task_ids)
    assert loss.item() > 0.0
    assert "loss_a" in metrics and "loss_b" in metrics and "loss_c" in metrics

    loss.backward()
    assert logits_dict["head_c"].grad is not None

    criterion_focal = MaskedMultiTaskLoss(
        head_c_criterion="focal",
        focal_gamma=2.0,
        focal_alpha=0.25,
    )
    loss_focal, _ = criterion_focal(logits_dict, targets, task_ids)
    assert loss_focal.item() > 0.0


def test_pos_weight_validation():
    """Invalid positive-class weights must be rejected at construction."""
    with pytest.raises(ValueError, match="non-negative"):
        MaskedMultiTaskLoss(pos_weight_c=-0.1)
    with pytest.raises(ValueError, match="non-negative"):
        MaskedMultiTaskLoss(pos_weight_c=float("nan"))
    with pytest.raises(ValueError, match="must contain"):
        MaskedMultiTaskLoss(pos_weight_c=torch.tensor([0.1, 0.2]))
    with pytest.raises(ValueError, match="values"):
        MaskedMultiTaskLoss(pos_weight_a=torch.ones(5))
    with pytest.raises(ValueError, match="head_c_criterion"):
        MaskedMultiTaskLoss(head_c_criterion="mse")
    with pytest.raises(ValueError, match="head_a_criterion"):
        MaskedMultiTaskLoss(head_a_criterion="mse")
    with pytest.raises(ValueError, match="Loss weight"):
        MaskedMultiTaskLoss(weights={"head_a": -1.0})
    with pytest.raises(ValueError, match="pos_weight_a"):
        MaskedMultiTaskLoss(
            head_a_criterion="focal", pos_weight_a=torch.ones(14)
        )
    with pytest.raises(ValueError, match="pos_weight_c"):
        MaskedMultiTaskLoss(
            head_c_criterion="focal", pos_weight_c=0.185
        )


@pytest.mark.parametrize("active_task", [0, 1, 2])
def test_gradient_isolation(active_task):
    """Only the active head must receive gradients for a pure-task batch."""
    criterion = MaskedMultiTaskLoss()
    logits_dict = _binary_tensors(batch_size=2)
    label = torch.zeros(14) if active_task == 0 else torch.ones(1)
    targets = [label.clone(), label.clone()]
    task_ids = torch.full((2,), active_task, dtype=torch.long)

    loss, _ = criterion(logits_dict, targets, task_ids)
    loss.backward()

    expected = {0: "head_a", 1: "head_b", 2: "head_c"}[active_task]
    for head, tensor in logits_dict.items():
        if head == expected:
            assert tensor.grad is not None
            assert torch.isfinite(tensor.grad).all()
        else:
            assert tensor.grad is None


def test_dict_targets_are_masked_per_head():
    """Full-batch dict targets must be indexed by each task mask."""
    criterion = MaskedMultiTaskLoss()
    logits_dict = _binary_tensors(batch_size=3)
    task_ids = torch.tensor([0, 1, 2], dtype=torch.long)

    targets = {
        "head_a": torch.zeros(3, 14),
        "head_b": torch.tensor([[0.0], [1.0], [0.0]]),
        "head_c": torch.tensor([[0.0], [0.0], [1.0]]),
    }

    _, metrics = criterion(logits_dict, targets, task_ids)

    expected_a = torch.nn.BCEWithLogitsLoss()(
        logits_dict["head_a"][0:1], targets["head_a"][0:1]
    )
    expected_b = torch.nn.BCEWithLogitsLoss()(
        logits_dict["head_b"][1:2], targets["head_b"][1:2]
    )
    expected_c = torch.nn.BCEWithLogitsLoss()(
        logits_dict["head_c"][2:3], targets["head_c"][2:3]
    )

    assert metrics["loss_a"] == pytest.approx(expected_a.item(), rel=1e-5)
    assert metrics["loss_b"] == pytest.approx(expected_b.item(), rel=1e-5)
    assert metrics["loss_c"] == pytest.approx(expected_c.item(), rel=1e-5)


def test_dict_targets_match_list_targets():
    """Full-batch dict targets and per-sample lists must be equivalent."""
    torch.manual_seed(3)
    task_ids = torch.tensor([0, 1, 2, 0], dtype=torch.long)
    logits_a = torch.randn(4, 14, requires_grad=True)
    logits_b = torch.randn(4, 1, requires_grad=True)
    logits_c = torch.randn(4, 1, requires_grad=True)
    logits_dict = {"head_a": logits_a, "head_b": logits_b, "head_c": logits_c}

    labels_a = torch.randint(0, 2, (4, 14)).float()
    labels_b = torch.randint(0, 2, (4, 1)).float()
    labels_c = torch.randint(0, 2, (4, 1)).float()
    targets_dict = {
        "head_a": labels_a,
        "head_b": labels_b,
        "head_c": labels_c,
    }
    targets_list = [
        labels_a[index]
        if task_ids[index] == 0
        else labels_b[index]
        if task_ids[index] == 1
        else labels_c[index]
        for index in range(4)
    ]

    dict_loss, dict_metrics = MaskedMultiTaskLoss()(
        logits_dict, targets_dict, task_ids
    )
    list_loss, list_metrics = MaskedMultiTaskLoss()(
        logits_dict, targets_list, task_ids
    )

    assert dict_loss.item() == pytest.approx(list_loss.item(), rel=1e-6)
    for key in ("loss_a", "loss_b", "loss_c"):
        assert dict_metrics[key] == pytest.approx(
            list_metrics[key], rel=1e-6
        )


def test_head_c_cross_entropy_path():
    """Categorical Head C must squeeze singleton targets for CE."""
    criterion = MaskedMultiTaskLoss(head_c_criterion="ce")
    logits_dict = _binary_tensors(batch_size=2)
    logits_dict["head_c"] = torch.randn(2, 3, requires_grad=True)
    task_ids = torch.tensor([2, 2], dtype=torch.long)
    targets = [torch.tensor([0]), torch.tensor([2])]

    loss, metrics = criterion(logits_dict, targets, task_ids)

    assert loss.item() > 0.0
    assert metrics["loss_c"] > 0.0
    loss.backward()
    assert logits_dict["head_c"].grad is not None


def test_invalid_task_ids_and_shapes():
    """Malformed batches must fail before producing silent zero losses."""
    criterion = MaskedMultiTaskLoss()
    logits_dict = _binary_tensors(batch_size=2)
    targets = [
        torch.zeros(14),
        torch.ones(1),
    ]

    with pytest.raises(ValueError, match="task_ids values"):
        criterion(
            logits_dict,
            targets,
            torch.tensor([0, 3], dtype=torch.long),
        )
    with pytest.raises(ValueError, match="batch size"):
        criterion(
            logits_dict,
            targets,
            torch.tensor([0], dtype=torch.long),
        )
    with pytest.raises(ValueError, match="entries"):
        criterion(
            logits_dict,
            targets[:1],
            torch.tensor([0, 1], dtype=torch.long),
        )
    with pytest.raises(KeyError, match="head_c"):
        criterion(
            {"head_a": logits_dict["head_a"], "head_b": logits_dict["head_b"]},
            targets,
            torch.tensor([0, 1], dtype=torch.long),
        )
    with pytest.raises(ValueError, match="1-D"):
        criterion(logits_dict, targets, torch.tensor([[0, 1]]))


def test_empty_batch_returns_zero_loss():
    """An empty batch must return a differentiable zero scalar."""
    criterion = MaskedMultiTaskLoss()
    logits_dict = {
        "head_a": torch.zeros(0, 14, requires_grad=True),
        "head_b": torch.zeros(0, 1, requires_grad=True),
        "head_c": torch.zeros(0, 1, requires_grad=True),
    }

    loss, metrics = criterion(
        logits_dict, [], torch.empty(0, dtype=torch.long)
    )

    assert loss.item() == pytest.approx(0.0)
    assert loss.requires_grad
    assert metrics["loss_total"] == pytest.approx(0.0)
