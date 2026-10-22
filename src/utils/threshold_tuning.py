# -*- coding: utf-8 -*-
"""Threshold Tuning Engine for Multi-Task Chest X-ray CADx.

Implements Youden's J statistic and F1-score maximization for optimal clinical
decision thresholds per pathology, with strict input validation.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.metrics import roc_curve


NIH_PATHOLOGY_NAMES: List[str] = [
    "Atelectasis",
    "Cardiomegaly",
    "Effusion",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pneumonia",
    "Pneumothorax",
    "Consolidation",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Pleural_Thickening",
    "Hernia",
]

_THRESHOLD_MIN = 0.01
_THRESHOLD_MAX = 0.99
_FALLBACK_THRESHOLD = 0.50


def _validate_threshold(value: float, name: str = "threshold") -> float:
    """Validates that a threshold is a finite scalar in [0, 1]."""
    try:
        threshold = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a numeric scalar, got {value!r}.") from exc
    if not np.isfinite(threshold):
        raise ValueError(f"{name} must be finite, got {threshold!r}.")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {threshold!r}.")
    return threshold


def _validate_binary_inputs(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Validates and flattens binary labels and probabilities."""
    y_true_arr = np.asarray(y_true)
    y_prob_arr = np.asarray(y_prob, dtype=np.float64)

    if y_true_arr.size == 0 or y_prob_arr.size == 0:
        raise ValueError("y_true and y_prob must not be empty.")
    if y_true_arr.size != y_prob_arr.size:
        raise ValueError(
            f"y_true and y_prob must have the same number of elements, "
            f"got {y_true_arr.size} and {y_prob_arr.size}."
        )

    y_true_arr = y_true_arr.astype(np.int32).ravel()
    y_prob_arr = y_prob_arr.ravel()

    if not np.all(np.isin(y_true_arr, (0, 1))):
        raise ValueError("y_true must contain only binary labels {0, 1}.")
    if not np.all(np.isfinite(y_prob_arr)):
        raise ValueError("y_prob must contain only finite values.")
    if np.any((y_prob_arr < 0.0) | (y_prob_arr > 1.0)):
        raise ValueError("y_prob must contain probabilities in [0, 1].")

    return y_true_arr, y_prob_arr


def _validate_multilabel_inputs(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Validates 2-D multi-label label/probability matrices."""
    y_true_arr = np.asarray(y_true)
    y_prob_arr = np.asarray(y_prob, dtype=np.float64)

    if y_true_arr.ndim != 2 or y_prob_arr.ndim != 2:
        raise ValueError("y_true and y_prob must be 2-D matrices (N, C).")
    if y_true_arr.shape != y_prob_arr.shape:
        raise ValueError(
            f"y_true and y_prob shapes differ: {y_true_arr.shape} vs "
            f"{y_prob_arr.shape}."
        )
    if y_true_arr.shape[0] == 0 or y_true_arr.shape[1] == 0:
        raise ValueError("y_true and y_prob must not have empty dimensions.")
    if not np.all(np.isin(y_true_arr, (0, 1))):
        raise ValueError("y_true must contain only binary labels {0, 1}.")
    if not np.all(np.isfinite(y_prob_arr)):
        raise ValueError("y_prob must contain only finite values.")
    if np.any((y_prob_arr < 0.0) | (y_prob_arr > 1.0)):
        raise ValueError("y_prob must contain probabilities in [0, 1].")

    return y_true_arr.astype(np.int32), y_prob_arr


def _select_tie_member(values: np.ndarray) -> float:
    """Selects the upper median member of a tie set.

    The returned value is always one of the candidate thresholds, so the
    reported metric remains achievable by the returned threshold.
    """
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    return float(ordered[ordered.size // 2])


def find_best_threshold_youden(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    fallback_threshold: float = 0.50,
) -> Tuple[float, float]:
    """Finds the optimal decision threshold maximizing Youden's J statistic.

    J = Sensitivity + Specificity - 1 = TPR - FPR.

    Args:
        y_true: Binary ground-truth labels (0 or 1), shape (N,).
        y_prob: Predicted probabilities in [0, 1], shape (N,).
        fallback_threshold: Default threshold if ground-truth is mono-class.

    Returns:
        Tuple of (optimal_threshold, best_j_statistic).

    Raises:
        ValueError: If inputs are empty, mismatched, non-binary, non-finite,
            or if probabilities are outside [0, 1].
    """
    fallback = _validate_threshold(fallback_threshold, "fallback_threshold")
    y_true_arr, y_prob_arr = _validate_binary_inputs(y_true, y_prob)

    # Edge case: mono-class data (e.g. all 0s or all 1s).
    if np.unique(y_true_arr).size < 2:
        return fallback, 0.0

    fpr, tpr, thresholds = roc_curve(y_true_arr, y_prob_arr)
    j_scores = tpr - fpr

    finite_mask = np.isfinite(thresholds)
    if not np.any(finite_mask):
        return fallback, 0.0

    finite_thresholds = thresholds[finite_mask]
    finite_j_scores = j_scores[finite_mask]
    best_j = float(np.max(finite_j_scores))
    tied = finite_thresholds[np.isclose(finite_j_scores, best_j, atol=1e-12)]

    # Pick a member of the optimal tie set, never an interpolated value.
    best_threshold = _select_tie_member(tied)
    best_threshold = float(
        np.clip(best_threshold, _THRESHOLD_MIN, _THRESHOLD_MAX)
    )
    return best_threshold, best_j


def find_best_threshold_f1(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    num_thresholds: Optional[int] = None,
    fallback_threshold: float = 0.50,
) -> Tuple[float, float]:
    """Finds the optimal decision threshold maximizing binary F1-score.

    By default the search is exact over all unique probability values using a
    vectorized cumulative TP/FP computation. If ``num_thresholds`` is provided,
    a fixed grid in (0, 1) is evaluated instead for backward compatibility.

    Args:
        y_true: Binary ground-truth labels (0 or 1), shape (N,).
        y_prob: Predicted probabilities in [0, 1], shape (N,).
        num_thresholds: Optional number of grid candidates in (0, 1). If
            ``None``, evaluates every unique probability (exact search).
        fallback_threshold: Default threshold if ground-truth is mono-class.

    Returns:
        Tuple of (optimal_threshold, best_f1_score).

    Raises:
        ValueError: If inputs are invalid or ``num_thresholds`` < 2.
    """
    fallback = _validate_threshold(fallback_threshold, "fallback_threshold")
    y_true_arr, y_prob_arr = _validate_binary_inputs(y_true, y_prob)

    if num_thresholds is not None and int(num_thresholds) < 2:
        raise ValueError("num_thresholds must be at least 2 when provided.")

    # Edge case: mono-class data.
    if np.unique(y_true_arr).size < 2:
        return fallback, 0.0

    if num_thresholds is not None:
        candidates = np.linspace(
            0.02, 0.98, int(num_thresholds), dtype=np.float64
        )
        predictions = y_prob_arr[None, :] >= candidates[:, None]
        positives = predictions & (y_true_arr[None, :] == 1)
        negatives = predictions & (y_true_arr[None, :] == 0)
        tp = positives.sum(axis=1, dtype=np.float64)
        fp = negatives.sum(axis=1, dtype=np.float64)
        fn = float(np.sum(y_true_arr == 1)) - tp
        thresholds = candidates
    else:
        # Sort by descending probability; the last occurrence of each unique
        # score is the threshold that includes all tied predictions.
        order = np.argsort(-y_prob_arr, kind="mergesort")
        sorted_prob = y_prob_arr[order]
        sorted_true = y_true_arr[order]
        tp_cum = np.cumsum(sorted_true, dtype=np.float64)
        fp_cum = np.cumsum(1 - sorted_true, dtype=np.float64)
        last_index = np.r_[
            np.flatnonzero(np.diff(sorted_prob) != 0),
            sorted_prob.size - 1,
        ]
        tp = tp_cum[last_index]
        fp = fp_cum[last_index]
        fn = float(np.sum(y_true_arr == 1)) - tp
        thresholds = sorted_prob[last_index]

    denominator = 2.0 * tp + fp + fn
    f1_scores = np.divide(
        2.0 * tp,
        denominator,
        out=np.zeros_like(tp, dtype=np.float64),
        where=denominator > 0,
    )

    best_f1 = float(np.max(f1_scores))
    if best_f1 <= 0.0:
        return fallback, 0.0

    tied = thresholds[np.isclose(f1_scores, best_f1, atol=1e-12)]
    # Do not clip here: a threshold of exactly 0 or 1 can be optimal for
    # saturated probabilities, and clipping would invalidate the F1 score.
    best_threshold = _select_tie_member(tied)
    return best_threshold, best_f1


def tune_multilabel_thresholds(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_names: Optional[List[str]] = None,
    method: str = "youden",
    default_threshold: float = 0.50,
) -> Dict[str, float]:
    """Calibrates individual decision thresholds per class for multi-label tasks.

    Args:
        y_true: Ground-truth binary matrix of shape (N, num_classes).
        y_prob: Predicted probabilities matrix of shape (N, num_classes).
        class_names: Optional list of class names. Defaults to NIH 14 names.
        method: Optimization strategy, 'youden' or 'f1'.
        default_threshold: Fallback threshold for mono-class columns.

    Returns:
        Dictionary mapping class_name -> optimal_threshold.

    Raises:
        ValueError: If shapes are invalid, class names do not match, or the
            optimization method is unknown.
    """
    y_true_arr, y_prob_arr = _validate_multilabel_inputs(y_true, y_prob)
    default = _validate_threshold(default_threshold, "default_threshold")

    method_name = str(method).strip().lower()
    if method_name not in {"youden", "f1"}:
        raise ValueError(
            f"Unknown threshold method {method!r}; expected 'youden' or 'f1'."
        )

    num_classes = y_true_arr.shape[1]
    if class_names is None:
        if num_classes == len(NIH_PATHOLOGY_NAMES):
            resolved_names = list(NIH_PATHOLOGY_NAMES)
        else:
            resolved_names = [f"class_{i}" for i in range(num_classes)]
    else:
        resolved_names = [str(name) for name in class_names]

    if len(resolved_names) != num_classes:
        raise ValueError(
            f"Length of class_names ({len(resolved_names)}) does not match "
            f"num_classes ({num_classes})."
        )

    tuner_fn = (
        find_best_threshold_youden
        if method_name == "youden"
        else find_best_threshold_f1
    )
    optimal_dict: Dict[str, float] = {}

    for col_idx, name in enumerate(resolved_names):
        best_thresh, _ = tuner_fn(
            y_true_arr[:, col_idx],
            y_prob_arr[:, col_idx],
            fallback_threshold=default,
        )
        optimal_dict[name] = round(float(best_thresh), 4)

    return optimal_dict


def apply_thresholds(
    y_prob: np.ndarray,
    thresholds: Union[float, List[float], np.ndarray, Dict[str, float]],
    class_names: Optional[List[str]] = None,
) -> np.ndarray:
    """Applies class-specific thresholds to convert probabilities to binaries.

    Args:
        y_prob: Probability matrix of shape (N, num_classes) or (N,).
        thresholds: Scalar threshold, list/array of per-class thresholds,
            or dict mapping class name to threshold.
        class_names: Optional list of class names if thresholds is a dict.

    Returns:
        Binary prediction array (0 or 1) of same shape as y_prob.

    Raises:
        ValueError: If probabilities are invalid, shapes are incompatible,
            or a 1-D dictionary threshold is ambiguous.
    """
    y_prob_arr = np.asarray(y_prob, dtype=np.float64)
    if y_prob_arr.size == 0:
        raise ValueError("y_prob must not be empty.")
    if not np.all(np.isfinite(y_prob_arr)):
        raise ValueError("y_prob must contain only finite values.")
    if np.any((y_prob_arr < 0.0) | (y_prob_arr > 1.0)):
        raise ValueError("y_prob must contain probabilities in [0, 1].")
    if y_prob_arr.ndim not in (1, 2):
        raise ValueError("y_prob must be 1-D or 2-D.")

    if isinstance(thresholds, bool):
        raise TypeError("thresholds must be numeric, not bool.")

    # Scalar threshold.
    if isinstance(thresholds, (int, float, np.integer, np.floating)):
        threshold = _validate_threshold(thresholds)
        return (y_prob_arr >= threshold).astype(np.int32)

    # Dictionary threshold.
    if isinstance(thresholds, dict):
        if y_prob_arr.ndim == 1:
            if class_names:
                key = str(class_names[0])
                if key not in thresholds:
                    raise KeyError(
                        f"Missing threshold for class {key!r}."
                    )
            elif len(thresholds) == 1:
                key = next(iter(thresholds))
            elif "threshold" in thresholds:
                key = "threshold"
            else:
                raise ValueError(
                    "A 1-D y_prob with a multi-key threshold dict requires "
                    "class_names or a unique 'threshold' key."
                )
            threshold = _validate_threshold(
                thresholds[key], f"thresholds[{key!r}]"
            )
            return (y_prob_arr >= threshold).astype(np.int32)

        if class_names is None:
            if y_prob_arr.shape[1] == len(NIH_PATHOLOGY_NAMES):
                resolved_names = list(NIH_PATHOLOGY_NAMES)
            else:
                resolved_names = [
                    f"class_{i}" for i in range(y_prob_arr.shape[1])
                ]
        else:
            resolved_names = [str(name) for name in class_names]

        if len(resolved_names) != y_prob_arr.shape[1]:
            raise ValueError(
                f"Length of class_names ({len(resolved_names)}) does not "
                f"match number of columns ({y_prob_arr.shape[1]})."
            )

        thresh_arr = np.array(
            [
                _validate_threshold(
                    thresholds.get(name, _FALLBACK_THRESHOLD),
                    f"thresholds[{name!r}]",
                )
                for name in resolved_names
            ],
            dtype=np.float64,
        )
        return (y_prob_arr >= thresh_arr).astype(np.int32)

    # Array or list threshold.
    thresh_arr = np.asarray(thresholds, dtype=np.float64)
    if thresh_arr.ndim == 0:
        threshold = _validate_threshold(thresh_arr.item())
        return (y_prob_arr >= threshold).astype(np.int32)

    thresh_arr = thresh_arr.ravel()
    if not np.all(np.isfinite(thresh_arr)):
        raise ValueError("thresholds must contain only finite values.")
    if np.any((thresh_arr < 0.0) | (thresh_arr > 1.0)):
        raise ValueError("thresholds must be in [0, 1].")
    if y_prob_arr.ndim == 1 and thresh_arr.size != 1:
        raise ValueError(
            "A 1-D y_prob requires a scalar or a single-element threshold "
            "array."
        )
    if y_prob_arr.ndim == 2 and thresh_arr.size != y_prob_arr.shape[1]:
        raise ValueError(
            f"Number of thresholds ({thresh_arr.size}) does not match "
            f"number of columns ({y_prob_arr.shape[1]})."
        )

    return (y_prob_arr >= thresh_arr).astype(np.int32)


def save_thresholds_json(
    thresholds_dict: Dict[str, Any],
    filepath: str,
) -> None:
    """Saves a thresholds dictionary to a strict, formatted JSON file.

    NaN and Infinity are rejected because they are not valid JSON values.
    """
    if not isinstance(thresholds_dict, dict):
        raise TypeError("thresholds_dict must be a dictionary.")
    parent = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(parent, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as handle:
        json.dump(
            thresholds_dict,
            handle,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )


def load_thresholds_json(
    filepath: str,
) -> Dict[str, Any]:
    """Loads a thresholds dictionary from a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Thresholds file not found at: {filepath}")
    with open(filepath, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Thresholds JSON root must be an object.")
    return data
