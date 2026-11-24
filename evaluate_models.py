"""Evaluate LungRay checkpoints on the curated test_samples collection.

The script mirrors the serving-time deterministic transforms and 3-pass TTA.
Metrics are explicitly exploratory because several test_samples groups have
filename-derived labels or no ground truth at all.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import logging
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import cv2
import torch
from sklearn.metrics import roc_auc_score

from app.backend.services import LungRayService, NIH_14_DISEASES
from src.data.transforms import get_val_transforms
from src.explainability.shortcut_audit import LungSegmenter
from src.models.dense_unet import DenseUNet, apply_dilated_soft_mask
from src.models.multi_task_net import MultiTaskChestXrayNet

LOGGER = logging.getLogger("lungray.evaluate")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm"}
WEIGHT_EXTENSIONS = {".pt", ".pth", ".h5", ".onnx"}
MONOCHROME = "#111111"
GRAY = "#666666"
LIGHT_GRAY = "#D9D9D9"
PALE = "#F2F2F2"

FILENAME_TO_NIH = {
    "atelectasis": "Atelectasis",
    "cardiomegaly": "Cardiomegaly",
    "effusion": "Effusion",
    "infiltration": "Infiltration",
    "mass": "Mass",
    "nodule": "Nodule",
    "pneumonia": "Pneumonia",
    "pneumothorax": "Pneumothorax",
    "consolidation": "Consolidation",
    "edema": "Edema",
    "emphysema": "Emphysema",
    "fibrosis": "Fibrosis",
    "pleural_thickening": "Pleural_Thickening",
    "hernia": "Hernia",
}

DEMO_MODEL_NAMES = {
    "standard": "Standard",
    "wsol": "WSOL",
    "resnet50": "ResNet-50",
    "ensemble": "Ensemble",
    "ag_mtcnet": "AG-MTCNet",
}


@dataclass
class Sample:
    path: Path
    sample_id: str
    dataset: str
    label_basis: str
    nih_labels: tuple[str, ...] | None = None
    tb_positive: int | None = None
    covid_positive: int | None = None
    rsna_pneumonia_positive: int | None = None


@dataclass
class Checkpoint:
    path: Path
    sha256: str
    aliases: list[Path]
    kind: str = "unknown"
    model_id: str = ""
    display_name: str = ""
    backbone: str = ""
    img_size: int = 512
    model: torch.nn.Module | None = None
    status: str = "discovered"
    notes: str = ""


def _set_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.edgecolor": MONOCHROME,
            "axes.linewidth": 0.8,
            "text.color": MONOCHROME,
            "axes.labelcolor": MONOCHROME,
            "xtick.color": MONOCHROME,
            "ytick.color": MONOCHROME,
        }
    )


def _discover_test_root(workspace: Path) -> Path:
    candidates = [workspace / "data" / "test_samples", workspace / "test_samples"]
    for candidate in candidates:
        if candidate.is_dir() and any(p.suffix.lower() in IMAGE_EXTENSIONS for p in candidate.rglob("*")):
            return candidate
    raise FileNotFoundError("Could not find images under data/test_samples/ or test_samples/.")


def _sample_from_path(path: Path, root: Path) -> Sample:
    relative = path.relative_to(root)
    folder = relative.parts[0].lower() if len(relative.parts) > 1 else ""
    stem = path.stem.lower()
    prefix = stem.split("_", 1)[0]
    sample = Sample(
        path=path,
        sample_id=relative.as_posix(),
        dataset="unlabeled",
        label_basis="no_ground_truth",
    )

    if folder.startswith("01_nih"):
        sample.dataset = "NIH ChestX-ray14"
        sample.label_basis = "filename_prefix_single_label_proxy"
        disease = FILENAME_TO_NIH.get(prefix)
        sample.nih_labels = (disease,) if disease else tuple()
    elif folder.startswith("02_tb"):
        sample.dataset = "TB Shenzhen"
        if prefix == "normal":
            sample.label_basis = "filename_prefix_class"
            sample.tb_positive = 0
        elif prefix == "tb":
            sample.label_basis = "filename_prefix_class"
            sample.tb_positive = 1
    elif folder.startswith("03_covid"):
        sample.dataset = "COVID Radiography"
        if prefix == "covid19":
            sample.label_basis = "filename_prefix_class"
            sample.covid_positive = 1
        elif prefix in {"normal", "viral"}:
            sample.label_basis = "filename_prefix_class"
            sample.covid_positive = 0
    elif folder.startswith("04_rsna"):
        sample.dataset = "RSNA Pneumonia"
        # The curated test_samples README states this folder contains positive cases only.
        sample.label_basis = "README_all_positive_one_class_only"
        sample.rsna_pneumonia_positive = 1
    elif folder.startswith("05_vindr"):
        sample.dataset = "VinDr-CXR"
    elif folder.startswith("06_chexpert"):
        sample.dataset = "CheXpert"
    return sample


def discover_samples(test_root: Path) -> list[Sample]:
    paths = sorted(
        p for p in test_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No supported image files found in {test_root}.")
    return [_sample_from_path(path, test_root) for path in paths]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def discover_checkpoints(workspace: Path) -> tuple[list[Checkpoint], list[dict[str, str]]]:
    roots = [workspace / "models", workspace / "checkpoints"]
    found: dict[str, Checkpoint] = {}
    unsupported: list[dict[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in WEIGHT_EXTENSIONS:
                continue
            sha = _sha256(path)
            if sha in found:
                found[sha].aliases.append(path)
                continue
            if path.suffix.lower() in {".h5", ".onnx"}:
                unsupported.append(
                    {
                        "path": str(path.relative_to(workspace)),
                        "status": f"unsupported_loader_for_{path.suffix.lower()}",
                    }
                )
                continue
            found[sha] = Checkpoint(path=path, sha256=sha, aliases=[path])
    checkpoints = list(found.values())
    for checkpoint in checkpoints:
        low = checkpoint.path.stem.lower()
        if "dense_unet" in low:
            checkpoint.kind = "segmentation"
            checkpoint.model_id = "dense_unet"
            checkpoint.display_name = "Dense-UNet"
        else:
            checkpoint.kind = "classifier_candidate"
            if low.startswith("ag_mtcnet"):
                checkpoint.model_id = "ag_mtcnet"
                checkpoint.display_name = DEMO_MODEL_NAMES["ag_mtcnet"]
            elif "best_model_20_11" in low or "20_11" in low:
                checkpoint.model_id = "densenet121_20_11"
                checkpoint.display_name = "DenseNet-121 (20_11 Baseline)"
            elif low == "best_model":
                checkpoint.model_id = "standard"
                checkpoint.display_name = DEMO_MODEL_NAMES["standard"]
            elif low == "best_wsol_finetune":
                checkpoint.model_id = "wsol"
                checkpoint.display_name = DEMO_MODEL_NAMES["wsol"]
            elif low == "best_resnet50":
                checkpoint.model_id = "resnet50"
                checkpoint.display_name = DEMO_MODEL_NAMES["resnet50"]
            else:
                checkpoint.model_id = f"checkpoint_{low}"
                checkpoint.display_name = f"Checkpoint: {checkpoint.path.stem}"
    return checkpoints, unsupported


def _unwrap_checkpoint(path: Path, device: torch.device) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    raw = torch.load(path, map_location=device, weights_only=False)
    if not isinstance(raw, dict):
        raise TypeError(f"Checkpoint payload is {type(raw).__name__}, expected a mapping.")
    metadata = raw
    state: Any = raw
    for key in ("model_state_dict", "state_dict", "ema_state_dict", "model"):
        value = raw.get(key)
        if isinstance(value, dict) and any(torch.is_tensor(v) for v in value.values()):
            state = value
            break
    if not isinstance(state, dict):
        raise TypeError("Checkpoint does not contain a state dictionary.")
    normalized: dict[str, torch.Tensor] = {}
    for key, value in state.items():
        if not torch.is_tensor(value):
            continue
        name = key
        for prefix in ("module.", "_orig_mod."):
            if name.startswith(prefix):
                name = name[len(prefix) :]
        normalized[name] = value
    if not normalized:
        raise ValueError("Checkpoint state dictionary contains no tensor weights.")
    return normalized, metadata


def _checkpoint_img_size(metadata: dict[str, Any], fallback: int = 512) -> int:
    for container in (metadata, metadata.get("architecture", {}), metadata.get("config", {}), metadata.get("args", {})):
        if not isinstance(container, dict):
            continue
        for key in ("img_size", "image_size", "input_size", "resolution"):
            value = container.get(key)
            if isinstance(value, int) and value > 0:
                return value
    return fallback


def load_classifier(checkpoint: Checkpoint, device: torch.device) -> torch.nn.Module:
    state, metadata = _unwrap_checkpoint(checkpoint.path, device)
    if "head_a.weight" not in state or "head_b.weight" not in state or "head_c.weight" not in state:
        raise ValueError("Missing one or more 3-head classifier weights.")
    if "backbone.conv1.weight" in state:
        backbone = "resnet50"
    elif "backbone.features.conv0.weight" in state:
        backbone = "densenet121"
    else:
        raise ValueError("Backbone could not be identified from checkpoint state keys.")
    checkpoint.backbone = backbone
    checkpoint.img_size = _checkpoint_img_size(metadata, 256 if checkpoint.model_id == "ag_mtcnet" else 512)
    model = MultiTaskChestXrayNet(
        backbone_name=backbone,
        pretrained=False,
        img_size=checkpoint.img_size,
        num_classes_a=int(state["head_a.weight"].shape[0]),
        num_classes_b=int(state["head_b.weight"].shape[0]),
        num_classes_c=int(state["head_c.weight"].shape[0]),
    )
    incompatible = model.load_state_dict(state, strict=False)
    if incompatible.missing_keys:
        raise RuntimeError(
            "Checkpoint is incomplete; missing weights: " + ", ".join(incompatible.missing_keys[:8])
        )
    if incompatible.unexpected_keys:
        LOGGER.warning(
            "%s has %d unexpected checkpoint keys; first keys: %s",
            checkpoint.path.name,
            len(incompatible.unexpected_keys),
            incompatible.unexpected_keys[:5],
        )
    model.to(device).eval()
    checkpoint.model = model
    checkpoint.status = "loaded"
    return model


def _binary_stats(y_true: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=np.int32)
    score = np.asarray(score, dtype=np.float64)
    prediction = score >= threshold
    truth = y_true.astype(bool)
    tp = int(np.sum(truth & prediction))
    tn = int(np.sum(~truth & ~prediction))
    fp = int(np.sum(~truth & prediction))
    fn = int(np.sum(truth & ~prediction))
    n = int(y_true.size)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else None
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    auc: float | None = None
    if np.unique(y_true).size == 2:
        auc = float(roc_auc_score(y_true, score))
    return {
        "n": n,
        "positive_support": int(truth.sum()),
        "negative_support": int(n - truth.sum()),
        "accuracy": (tp + tn) / n if n else None,
        "precision": precision,
        "recall": recall,
        "sensitivity": recall,
        "specificity": specificity,
        "f1": f1,
        "auroc": auc,
        "threshold": threshold,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def _metric_row(
    model_id: str,
    display_name: str,
    checkpoint_name: str,
    dataset: str,
    task: str,
    class_name: str,
    y_true: np.ndarray,
    score: np.ndarray,
    threshold: float,
    label_basis: str,
) -> dict[str, Any]:
    return {
        "model_id": model_id,
        "model_name": display_name,
        "checkpoint": checkpoint_name,
        "dataset": dataset,
        "task": task,
        "class_name": class_name,
        "label_basis": label_basis,
        **_binary_stats(y_true, score, threshold),
    }


def _metric_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for model_id in sorted({row["model_id"] for row in rows}):
        model_rows = [row for row in rows if row["model_id"] == model_id]
        for task in ("Head A", "Head B", "Head C", "Head A Pneumonia (RSNA proxy)"):
            task_rows = [r for r in model_rows if r["task"] == task]
            if not task_rows:
                continue
            if task == "Head A":
                auc_rows = [r for r in task_rows if pd.notna(r["auroc"])]
                observed_rows = [
                    r for r in task_rows
                    if r["positive_support"] > 0 and r["negative_support"] > 0
                ]
                aggregate = {
                    "model_id": model_id,
                    "model_name": task_rows[0]["model_name"],
                    "checkpoint": task_rows[0]["checkpoint"],
                    "dataset": "NIH ChestX-ray14",
                    "task": task,
                    "class_name": "Macro over classes with both labels",
                    "label_basis": "filename_prefix_single_label_proxy",
                    "n": int(task_rows[0]["n"]),
                    "positive_support": None,
                    "negative_support": None,
                    "accuracy": float(np.mean([r["accuracy"] for r in observed_rows])) if observed_rows else None,
                    "precision": float(np.mean([r["precision"] for r in observed_rows])) if observed_rows else None,
                    "recall": float(np.mean([r["recall"] for r in observed_rows])) if observed_rows else None,
                    "sensitivity": None,
                    "specificity": None,
                    "f1": float(np.mean([r["f1"] for r in observed_rows])) if observed_rows else None,
                    "auroc": float(np.mean([r["auroc"] for r in auc_rows])) if auc_rows else None,
                    "threshold": None,
                    "classes_in_macro_auc": len(auc_rows),
                    "classes_in_macro_other_metrics": len(observed_rows),
                }
            else:
                aggregate = dict(task_rows[0])
                aggregate["class_name"] = "Positive class"
                aggregate["classes_in_macro_auc"] = 1 if aggregate["auroc"] is not None else 0
            summaries.append(aggregate)
    return summaries


def _make_prediction_rows(
    samples: list[Sample],
    model_outputs: dict[str, list[dict[str, Any]]],
    checkpoints: list[Checkpoint],
) -> pd.DataFrame:
    metadata = {cp.model_id: cp for cp in checkpoints if cp.kind == "classifier_candidate"}
    output_rows: list[dict[str, Any]] = []
    for model_id, values in model_outputs.items():
        cp = metadata.get(model_id)
        for sample, prediction in zip(samples, values):
            row: dict[str, Any] = {
                "model_id": model_id,
                "model_name": DEMO_MODEL_NAMES.get(model_id, cp.display_name if cp else model_id),
                "checkpoint": cp.path.name if cp else "Derived Ensemble",
                "sample_id": sample.sample_id,
                "dataset": sample.dataset,
                "label_basis": sample.label_basis,
                "nih_filename_label": "|".join(sample.nih_labels or ()) if sample.dataset == "NIH ChestX-ray14" else "",
                "tb_ground_truth": sample.tb_positive if sample.dataset == "TB Shenzhen" else None,
                "covid_ground_truth": sample.covid_positive if sample.dataset == "COVID Radiography" else None,
                "rsna_pneumonia_ground_truth": sample.rsna_pneumonia_positive if sample.dataset == "RSNA Pneumonia" else None,
                "head_b_tb_probability": prediction.get("head_b"),
                "head_c_status": prediction.get("head_c_status", "available"),
                "head_c_covid_probability": prediction.get("head_c"),
            }
            head_a = prediction.get("head_a")
            for idx, disease in enumerate(NIH_14_DISEASES):
                row[f"head_a_{disease.lower()}"] = float(head_a[idx]) if head_a is not None else None
            output_rows.append(row)
    return pd.DataFrame(output_rows)


def evaluate_metrics(
    samples: list[Sample],
    model_outputs: dict[str, list[dict[str, Any]]],
    checkpoint_by_id: dict[str, Checkpoint],
    thresholds: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metric_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for model_id, outputs in model_outputs.items():
        model_thresholds = thresholds.get("_per_model", {}).get(
            model_id, thresholds.get("_default", thresholds)
        )
        a_thresholds = model_thresholds.get("head_a_nih_14", {})
        b_value = model_thresholds.get("head_b_tb", {})
        c_value = model_thresholds.get("head_c_covid", {})
        b_threshold = float(b_value.get("threshold", 0.5) if isinstance(b_value, dict) else b_value)
        c_threshold = float(c_value.get("threshold", 0.5) if isinstance(c_value, dict) else c_value)
        checkpoint = checkpoint_by_id.get(model_id)
        checkpoint_name = checkpoint.path.name if checkpoint else "Derived Ensemble"
        display = DEMO_MODEL_NAMES.get(model_id, checkpoint.display_name if checkpoint else model_id)

        nih_indices = [i for i, s in enumerate(samples) if s.dataset == "NIH ChestX-ray14"]
        if nih_indices:
            for class_index, disease in enumerate(NIH_14_DISEASES):
                y = np.asarray([int(disease in (samples[i].nih_labels or ())) for i in nih_indices])
                score = np.asarray([outputs[i]["head_a"][class_index] for i in nih_indices])
                threshold = float(a_thresholds.get(disease, 0.5))
                row = _metric_row(
                    model_id, display, checkpoint_name, "NIH ChestX-ray14", "Head A", disease,
                    y, score, threshold, "filename_prefix_single_label_proxy",
                )
                metric_rows.append(row)
                for local_idx, (truth, value) in enumerate(zip(y, score)):
                    predicted = int(value >= threshold)
                    if int(truth) == predicted:
                        continue
                    error_rows.append(
                        {
                            "model_id": model_id,
                            "model_name": display,
                            "sample_id": samples[nih_indices[local_idx]].sample_id,
                            "dataset": "NIH ChestX-ray14",
                            "task": "Head A",
                            "class_name": disease,
                            "error_type": "false_negative" if truth else "false_positive",
                            "ground_truth": int(truth),
                            "prediction": predicted,
                            "probability": float(value),
                            "threshold": threshold,
                            "error_confidence": float(threshold - value if truth else value - threshold),
                            "label_basis": "filename_prefix_single_label_proxy",
                        }
                    )

        tb_indices = [i for i, s in enumerate(samples) if s.tb_positive is not None]
        if tb_indices:
            y = np.asarray([samples[i].tb_positive for i in tb_indices], dtype=int)
            score = np.asarray([outputs[i]["head_b"] for i in tb_indices], dtype=float)
            row = _metric_row(
                model_id, display, checkpoint_name, "TB Shenzhen", "Head B", "Tuberculosis",
                y, score, b_threshold, "filename_prefix_class",
            )
            metric_rows.append(row)
            for local_idx, (truth, value) in enumerate(zip(y, score)):
                predicted = int(value >= b_threshold)
                if int(truth) != predicted:
                    error_rows.append(
                        {
                            "model_id": model_id, "model_name": display,
                            "sample_id": samples[tb_indices[local_idx]].sample_id,
                            "dataset": "TB Shenzhen", "task": "Head B",
                            "class_name": "Tuberculosis",
                            "error_type": "false_negative" if truth else "false_positive",
                            "ground_truth": int(truth), "prediction": predicted,
                            "probability": float(value), "threshold": b_threshold,
                            "error_confidence": float(b_threshold - value if truth else value - b_threshold),
                            "label_basis": "filename_prefix_class",
                        }
                    )

        covid_indices = [i for i, s in enumerate(samples) if s.covid_positive is not None]
        if covid_indices and model_id != "ag_mtcnet":
            y = np.asarray([samples[i].covid_positive for i in covid_indices], dtype=int)
            score = np.asarray([outputs[i]["head_c"] for i in covid_indices], dtype=float)
            row = _metric_row(
                model_id, display, checkpoint_name, "COVID Radiography", "Head C", "COVID-19",
                y, score, c_threshold, "filename_prefix_class_binary_covid_vs_non_covid",
            )
            metric_rows.append(row)
            for local_idx, (truth, value) in enumerate(zip(y, score)):
                predicted = int(value >= c_threshold)
                if int(truth) != predicted:
                    error_rows.append(
                        {
                            "model_id": model_id, "model_name": display,
                            "sample_id": samples[covid_indices[local_idx]].sample_id,
                            "dataset": "COVID Radiography", "task": "Head C",
                            "class_name": "COVID-19",
                            "error_type": "false_negative" if truth else "false_positive",
                            "ground_truth": int(truth), "prediction": predicted,
                            "probability": float(value), "threshold": c_threshold,
                            "error_confidence": float(c_threshold - value if truth else value - c_threshold),
                            "label_basis": "filename_prefix_class_binary_covid_vs_non_covid",
                        }
                    )

        rsna_indices = [i for i, s in enumerate(samples) if s.rsna_pneumonia_positive is not None]
        if rsna_indices:
            y = np.asarray([samples[i].rsna_pneumonia_positive for i in rsna_indices], dtype=int)
            score = np.asarray([outputs[i]["head_a"][6] for i in rsna_indices], dtype=float)
            threshold = float(a_thresholds.get("Pneumonia", 0.5))
            metric_rows.append(
                _metric_row(
                    model_id, display, checkpoint_name, "RSNA Pneumonia", "Head A Pneumonia (RSNA proxy)",
                    "Pneumonia", y, score, threshold, "README_all_positive_one_class_only",
                )
            )

    return metric_rows, error_rows


def _confusion(y: np.ndarray, score: np.ndarray, threshold: float) -> np.ndarray:
    prediction = np.asarray(score) >= threshold
    y = np.asarray(y).astype(bool)
    return np.asarray(
        [
            [int(np.sum(~y & ~prediction)), int(np.sum(~y & prediction))],
            [int(np.sum(y & ~prediction)), int(np.sum(y & prediction))],
        ]
    )


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_overview(
    output_dir: Path,
    summaries: list[dict[str, Any]],
    model_ids: list[str],
) -> None:
    tasks = [
        ("Head A macro AUROC", "Head A", "NIH ChestX-ray14"),
        ("Head B AUROC", "Head B", "TB Shenzhen"),
        ("Head C AUROC", "Head C", "COVID Radiography"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), sharey=True)
    for ax, (title, task, dataset) in zip(axes, tasks):
        rows = [
            next((r for r in summaries if r["model_id"] == model_id and r["task"] == task and r["dataset"] == dataset), None)
            for model_id in model_ids
        ]
        vals = [r.get("auroc") if r else None for r in rows]
        y_positions = np.arange(len(model_ids))
        for pos, value, model_id in zip(y_positions, vals, model_ids):
            if value is None or pd.isna(value):
                ax.barh(pos, 1.0, color="white", edgecolor=GRAY, hatch="///", linewidth=0.8)
                ax.text(0.5, pos, "NOT VALIDATED" if model_id == "ag_mtcnet" and task == "Head C" else "N/A", ha="center", va="center", fontsize=8)
            else:
                ax.barh(pos, value, color=MONOCHROME if model_id in DEMO_MODEL_NAMES else GRAY, edgecolor="black", height=0.62)
                ax.text(min(value + 0.015, 1.02), pos, f"{value:.3f}", va="center", fontsize=8)
        ax.set_xlim(0, 1.12)
        ax.set_xticks(np.arange(0, 1.01, 0.2))
        ax.set_xlabel("AUROC")
        ax.set_title(title, pad=10, fontweight="bold")
        ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.invert_yaxis()
        ax.set_yticks(y_positions, [DEMO_MODEL_NAMES.get(m, m.replace("checkpoint_", "")) for m in model_ids])
    fig.suptitle("Exploratory test-sample comparison", fontsize=15, fontweight="bold", y=1.02)
    sample_counts = {
        dataset: next(
            (int(r["n"]) for r in summaries if r["dataset"] == dataset),
            0,
        )
        for dataset in ("NIH ChestX-ray14", "TB Shenzhen", "COVID Radiography")
    }
    fig.text(
        0.5,
        0.01,
        f"NIH n={sample_counts['NIH ChestX-ray14']} (filename-label proxy) · TB n={sample_counts['TB Shenzhen']} · COVID n={sample_counts['COVID Radiography']} · AG-MTCNet Head C withheld",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout()
    _save_figure(fig, output_dir / "webdemo_model_overview.png")


def plot_nih_heatmap(output_dir: Path, metric_rows: list[dict[str, Any]], model_ids: list[str]) -> None:
    matrix = np.full((len(model_ids), len(NIH_14_DISEASES)), np.nan)
    support = np.zeros_like(matrix, dtype=int)
    for row in metric_rows:
        if row["task"] != "Head A" or row["model_id"] not in model_ids:
            continue
        col = NIH_14_DISEASES.index(row["class_name"])
        rr = model_ids.index(row["model_id"])
        matrix[rr, col] = row["auroc"] if row["auroc"] is not None else np.nan
        support[rr, col] = row["positive_support"]
    fig, ax = plt.subplots(figsize=(15, 5.8))
    shown = np.nan_to_num(matrix, nan=0.0)
    image = ax.imshow(shown, vmin=0.0, vmax=1.0, cmap="Greys", aspect="auto")
    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):
            if np.isnan(matrix[r, c]):
                label = "—"
            else:
                label = f"{matrix[r,c]:.2f}\n(n+={support[r,c]})"
            ax.text(c, r, label, ha="center", va="center", fontsize=7, color="white" if matrix[r, c] > 0.68 else "black")
    ax.set_xticks(np.arange(len(NIH_14_DISEASES)), [n.replace("_", "\n") for n in NIH_14_DISEASES], rotation=0)
    ax.set_yticks(np.arange(len(model_ids)), [DEMO_MODEL_NAMES.get(m, m.replace("checkpoint_", "")) for m in model_ids])
    ax.set_title("NIH filename-label proxy: per-pathology AUROC", fontweight="bold", pad=12)
    ax.set_xlabel("Classes with one or fewer positive samples are highly unstable; ‘—’ means AUROC undefined")
    fig.colorbar(image, ax=ax, label="AUROC", shrink=0.8)
    fig.tight_layout()
    _save_figure(fig, output_dir / "nih_per_class_auroc.png")


def plot_confusion_figures(
    output_dir: Path,
    samples: list[Sample],
    model_outputs: dict[str, list[dict[str, Any]]],
    thresholds: dict[str, Any],
    model_ids: list[str],
) -> None:
    a_thresholds = thresholds.get("head_a_nih_14", {})
    b_threshold = float(thresholds.get("head_b_tb", {}).get("threshold", 0.5))
    c_threshold = float(thresholds.get("head_c_covid", {}).get("threshold", 0.5))
    for model_id in model_ids:
        values = model_outputs[model_id]
        # NIH: each row is a pathology; four columns are TN, FP, FN, TP.
        indices = [i for i, s in enumerate(samples) if s.dataset == "NIH ChestX-ray14"]
        if indices:
            table = []
            for disease_idx, disease in enumerate(NIH_14_DISEASES):
                y = np.asarray([int(disease in (samples[i].nih_labels or ())) for i in indices])
                score = np.asarray([values[i]["head_a"][disease_idx] for i in indices])
                cm = _confusion(y, score, float(a_thresholds.get(disease, 0.5)))
                table.append([cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]])
            table_arr = np.asarray(table)
            fig, ax = plt.subplots(figsize=(10.8, 6.5))
            image = ax.imshow(table_arr, cmap="Greys", aspect="auto")
            for r in range(table_arr.shape[0]):
                for c in range(table_arr.shape[1]):
                    ax.text(c, r, str(table_arr[r, c]), ha="center", va="center", fontsize=8, color="white" if table_arr[r,c] > table_arr.max() * 0.58 else "black")
            ax.set_yticks(np.arange(len(NIH_14_DISEASES)), NIH_14_DISEASES)
            ax.set_xticks(range(4), ["TN", "FP", "FN", "TP"])
            ax.set_title(f"{DEMO_MODEL_NAMES.get(model_id, model_id)} · NIH confusion counts by class", fontweight="bold")
            fig.colorbar(image, ax=ax, label="Sample count", shrink=0.8)
            fig.tight_layout()
            _save_figure(fig, output_dir / f"confusion_{model_id}_nih.png")

        for dataset, task, score_key, threshold, filename in (
            ("TB Shenzhen", "Head B", "head_b", b_threshold, f"confusion_{model_id}_tb.png"),
            ("COVID Radiography", "Head C", "head_c", c_threshold, f"confusion_{model_id}_covid.png"),
            ("RSNA Pneumonia", "Head A Pneumonia", "head_a", float(a_thresholds.get("Pneumonia", 0.5)), f"confusion_{model_id}_rsna.png"),
        ):
            if dataset == "TB Shenzhen":
                indices = [i for i, s in enumerate(samples) if s.tb_positive is not None]
                y = np.asarray([samples[i].tb_positive for i in indices], dtype=int)
                scores = np.asarray([values[i][score_key] for i in indices], dtype=float)
            elif dataset == "COVID Radiography" and model_id != "ag_mtcnet":
                indices = [i for i, s in enumerate(samples) if s.covid_positive is not None]
                y = np.asarray([samples[i].covid_positive for i in indices], dtype=int)
                scores = np.asarray([values[i][score_key] for i in indices], dtype=float)
            elif dataset == "RSNA Pneumonia":
                indices = [i for i, s in enumerate(samples) if s.rsna_pneumonia_positive is not None]
                y = np.asarray([samples[i].rsna_pneumonia_positive for i in indices], dtype=int)
                scores = np.asarray([values[i]["head_a"][6] for i in indices], dtype=float)
            else:
                continue
            if not indices:
                continue
            cm = _confusion(y, scores, threshold)
            fig, ax = plt.subplots(figsize=(5.5, 4.5))
            image = ax.imshow(cm, cmap="Greys", vmin=0, vmax=max(1, int(cm.max())), aspect="equal")
            for rr in range(2):
                for cc in range(2):
                    ax.text(cc, rr, str(cm[rr, cc]), ha="center", va="center", fontsize=15, color="white" if cm[rr,cc] > cm.max() * 0.58 else "black")
            ax.set_xticks([0, 1], ["Negative", "Positive"])
            ax.set_yticks([0, 1], ["Negative", "Positive"])
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Ground truth")
            label = task + (" (proxy; positives only)" if dataset == "RSNA Pneumonia" else "")
            ax.set_title(f"{DEMO_MODEL_NAMES.get(model_id, model_id)} · {label}\n n={len(indices)}, threshold={threshold:.3f}", fontweight="bold")
            for spine in ax.spines.values():
                spine.set_color(MONOCHROME)
            fig.colorbar(image, ax=ax, label="Sample count", fraction=0.046, pad=0.04)
            fig.tight_layout()
            _save_figure(fig, output_dir / filename)


def plot_qualitative_cases(
    output_dir: Path,
    samples: list[Sample],
    model_outputs: dict[str, list[dict[str, Any]]],
    demo_model_ids: list[str],
    thresholds: dict[str, Any],
) -> None:
    case_defs = [
        ("NIH ChestX-ray14", lambda s: "Effusion" in (s.nih_labels or ()), "Effusion", 2),
        ("TB Shenzhen", lambda s: s.tb_positive == 1, "Tuberculosis", None),
        ("COVID Radiography", lambda s: s.covid_positive == 1, "COVID-19", None),
    ]
    cases = []
    for dataset, predicate, task, class_idx in case_defs:
        idx = next((i for i, s in enumerate(samples) if s.dataset == dataset and predicate(s)), None)
        if idx is not None:
            cases.append((idx, task, class_idx))
    if not cases:
        return

    fig, axes = plt.subplots(len(cases), 1 + len(demo_model_ids), figsize=(15, 3.3 * len(cases)))
    if len(cases) == 1:
        axes = np.asarray([axes])
    col_titles = ["Input sample"] + [DEMO_MODEL_NAMES.get(m, m) for m in demo_model_ids]
    for c, title in enumerate(col_titles):
        axes[0, c].set_title(title, fontweight="bold", pad=8)
    for row_idx, (sample_idx, task, class_idx) in enumerate(cases):
        sample = samples[sample_idx]
        image = LungRayService._decode_uploaded_image(sample.path.read_bytes())
        axes[row_idx, 0].imshow(image, cmap="gray")
        axes[row_idx, 0].set_ylabel(task, rotation=0, labelpad=60, fontsize=10, fontweight="bold")
        axes[row_idx, 0].set_xticks([])
        axes[row_idx, 0].set_yticks([])
        for col_idx, model_id in enumerate(demo_model_ids, start=1):
            ax = axes[row_idx, col_idx]
            if task == "COVID-19" and model_id == "ag_mtcnet":
                ax.text(0.5, 0.5, "NOT VALIDATED\nprobability withheld", ha="center", va="center", fontsize=10, fontweight="bold")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis("off")
                continue
            prediction = model_outputs[model_id][sample_idx]
            if task == "Effusion":
                probability = prediction["head_a"][class_idx]
                threshold = float(thresholds.get("head_a_nih_14", {}).get("Effusion", 0.5))
            elif task == "Tuberculosis":
                probability = prediction["head_b"]
                threshold = float(thresholds.get("head_b_tb", {}).get("threshold", 0.5))
            else:
                probability = prediction["head_c"]
                threshold = float(thresholds.get("head_c_covid", {}).get("threshold", 0.5))
            ax.barh([0], [probability], height=0.42, color=MONOCHROME if probability >= threshold else LIGHT_GRAY, edgecolor=MONOCHROME)
            ax.axvline(threshold, color=GRAY, linestyle="--", linewidth=1.2, label=f"decision threshold {threshold:.2f}")
            ax.set_xlim(0, 1)
            ax.set_yticks([])
            ax.set_xlabel("Calibrated probability")
            ax.text(min(probability + 0.02, 0.82), 0, f"{probability:.2f}", va="center", fontsize=10, fontweight="bold")
            ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.6)
            ax.set_axisbelow(True)
            ax.spines["left"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
    fig.suptitle("Representative test-sample predictions by web-demo model", fontsize=15, fontweight="bold", y=1.01)
    fig.text(0.5, 0.005, "Curated examples; filename-derived labels; probabilities are not clinical validation.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    _save_figure(fig, output_dir / "qualitative_webdemo_cases.png")


def write_report(
    output_dir: Path,
    workspace: Path,
    test_root: Path,
    samples: list[Sample],
    checkpoints: list[Checkpoint],
    unsupported: list[dict[str, str]],
    metric_rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    elapsed_seconds: float,
    device: torch.device,
    inference_protocol: str,
) -> None:
    counts = pd.Series([sample.dataset for sample in samples]).value_counts().to_dict()
    summary_map = {(row["model_id"], row["task"], row["dataset"]): row for row in summaries}
    ids = sorted({r["model_id"] for r in summaries}, key=lambda m: (m not in DEMO_MODEL_NAMES, m))
    lines = [
        "# LungRay test-sample evaluation",
        "",
        "## Scope and interpretation",
        "",
        f"- Input root: `{test_root.relative_to(workspace).as_posix()}`; {len(samples)} images were processed.",
        f"- Device: `{device}`. Runtime: {elapsed_seconds / 60:.1f} minutes.",
        f"- Unique checkpoint files evaluated as classifiers: {sum(cp.kind == 'classifier_candidate' and cp.status in {'loaded', 'loaded_from_web_demo_runtime'} for cp in checkpoints)}; duplicate hashes are listed as aliases in `model_inventory.csv`.",
        f"- Inference protocol: {inference_protocol}. Existing web-demo modes use `configs/optimal_thresholds.json`; `densenet121_20_11` uses validation-calibrated thresholds from `configs/optimal_thresholds_20_11.json` and its training-time 256-pixel CLAHE/Otsu/25-pixel morphology preprocessing. Neither threshold set was fitted to this curated sample.",
        "- This is a curated demonstration sample, not an independent clinical test set. Do not present these results as validated clinical performance.",
        "- NIH labels are filename-prefix single-label proxies; co-occurring findings are not represented. TB and COVID labels are filename prefixes. RSNA contains positive cases only according to the local README, so specificity and AUROC are undefined. VinDr and CheXpert have no image-level ground truth in `test_samples`; only predictions are recorded.",
        "- AG-MTCNet Head C is marked `NOT_VALIDATED`; its probabilities and metrics are withheld. No prior Head C metric is reused.",
        "- Dense-UNet has no reference masks in the curated sample. Its outputs are exported as foreground ratios only; no Dice/IoU is reported.",
        "",
        "## Sample coverage",
        "",
        "| Dataset | Images | Supervised use |",
        "|:---|---:|:---|",
    ]
    for dataset in ("NIH ChestX-ray14", "TB Shenzhen", "COVID Radiography", "RSNA Pneumonia", "VinDr-CXR", "CheXpert"):
        n = counts.get(dataset, 0)
        use = {
            "NIH ChestX-ray14": "Head A; filename-label proxy",
            "TB Shenzhen": "Head B; filename class labels",
            "COVID Radiography": "Head C; filename binary COVID/non-COVID labels",
            "RSNA Pneumonia": "Head A Pneumonia sensitivity only; positive-only sample",
            "VinDr-CXR": "Inference only; no ground truth included",
            "CheXpert": "Inference only; no ground truth included",
        }[dataset]
        lines.append(f"| {dataset} | {n} | {use} |")
    lines.extend(
        [
            "",
            "## Comparison of web-demo modes",
            "",
            "| Model | Head A NIH macro AUROC | Head A macro F1 | TB AUROC | TB F1 | COVID AUROC | COVID F1 | RSNA pneumonia sensitivity | Model forward ms/image |",
            "|:---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for model_id in DEMO_MODEL_NAMES:
        a = summary_map.get((model_id, "Head A", "NIH ChestX-ray14"), {})
        b = summary_map.get((model_id, "Head B", "TB Shenzhen"), {})
        c = summary_map.get((model_id, "Head C", "COVID Radiography"), {})
        r = summary_map.get((model_id, "Head A Pneumonia (RSNA proxy)", "RSNA Pneumonia"), {})
        c_auc = "NOT VALIDATED" if model_id == "ag_mtcnet" else _fmt(c.get("auroc"))
        c_f1 = "WITHHELD" if model_id == "ag_mtcnet" else _fmt(c.get("f1"))
        lines.append(
            f"| {DEMO_MODEL_NAMES[model_id]} | {_fmt(a.get('auroc'))} | {_fmt(a.get('f1'))} | {_fmt(b.get('auroc'))} | {_fmt(b.get('f1'))} | {c_auc} | {c_f1} | {_fmt(r.get('sensitivity'))} | {_fmt(a.get('inference_ms_per_image_model_forward'))} |"
        )
    lines.extend(["", "## Checkpoint-only variants", "", "| Model/checkpoint | Head A NIH macro AUROC | TB AUROC | COVID AUROC |", "|:---|---:|---:|---:|"])
    for model_id in ids:
        if model_id in DEMO_MODEL_NAMES or model_id == "ensemble":
            continue
        a = summary_map.get((model_id, "Head A", "NIH ChestX-ray14"), {})
        b = summary_map.get((model_id, "Head B", "TB Shenzhen"), {})
        c = summary_map.get((model_id, "Head C", "COVID Radiography"), {})
        checkpoint = next((cp.path.name for cp in checkpoints if cp.model_id == model_id), model_id)
        c_value = "NOT VALIDATED" if model_id == "ag_mtcnet" else _fmt(c.get("auroc"))
        lines.append(f"| `{checkpoint}` | {_fmt(a.get('auroc'))} | {_fmt(b.get('auroc'))} | {c_value} |")
    lines.extend(
        [
            "",
            "## Generated artifacts",
            "",
        "- `predictions.csv`: per-image probabilities from web-demo modes; AG-MTCNet Head C is blank and marked not validated.",
            "- `metrics_by_class.csv`: accuracy, precision, recall/sensitivity, specificity, F1, AUROC and support where labels permit.",
            "- `model_summary.csv`: macro/per-task summaries; NIH macro metrics average only classes with both positive and negative support.",
            "- `error_analysis.csv`: false negatives and false positives ranked by distance beyond the decision threshold.",
            "- `model_inventory.csv`: discovered files, aliases, architecture and load status.",
            "- `dense_unet_predictions.csv`: foreground ratios without segmentation accuracy metrics.",
            "- `figures/webdemo_model_overview.png`, `figures/nih_per_class_auroc.png`, confusion matrices and qualitative case comparison are slide-ready 300 dpi grayscale figures.",
            "",
            "## Model comparison figures",
            "",
            "![Web-demo metrics](figures/webdemo_model_overview.png)",
            "",
            "![NIH class AUROC](figures/nih_per_class_auroc.png)",
            "",
            "![Qualitative cases](figures/qualitative_webdemo_cases.png)",
            "",
        ]
    )
    if unsupported:
        lines.extend(["## Unsupported formats", ""])
        for item in unsupported:
            lines.append(f"- `{item['path']}`: {item['status']}")
        lines.append("")
    report = output_dir / "summary_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.3f}"


def _model_tta_outputs(model: torch.nn.Module, tensor: torch.Tensor, n_samples: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with torch.inference_mode():
        output = model.predict(tensor)
    n_views = tensor.shape[0] // n_samples
    a = output["head_a"].detach().cpu().numpy().reshape(n_samples, n_views, -1).mean(axis=1)
    b = output["head_b"].detach().cpu().numpy().reshape(n_samples, n_views, -1).mean(axis=1)[:, 0]
    c_matrix = output["head_c"].detach().cpu().numpy().reshape(n_samples, n_views, -1).mean(axis=1)
    c = c_matrix[:, 2] if c_matrix.shape[1] == 3 else c_matrix[:, 0]
    return a.astype(float), b.astype(float), c.astype(float)


def _calibrated(raw: np.ndarray) -> np.ndarray:
    eps = 1e-6
    clipped = np.clip(raw, eps, 1.0 - eps)
    logits = np.log(clipped / (1.0 - clipped)) / 1.20
    return (1.0 / (1.0 + np.exp(-logits))).astype(float)


def _three_view_tensor(image: np.ndarray, transform: Any) -> torch.Tensor:
    """Build the same deterministic three views used by the serving endpoint."""
    first = transform(image=image)["image"]
    try:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        contrast = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        second = transform(image=contrast)["image"]
    except Exception:
        second = first.clone()
    try:
        h, w = image.shape[:2]
        scaled_w, scaled_h = int(w * 1.03), int(h * 1.03)
        scaled = cv2.resize(image, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)
        x0, y0 = (scaled_w - w) // 2, (scaled_h - h) // 2
        crop = scaled[y0 : y0 + h, x0 : x0 + w]
        third = transform(image=crop)["image"]
    except Exception:
        third = first.clone()
    return torch.stack((first, second, third), dim=0)


def _apply_20_11_morphology_mask(image: np.ndarray, dilation_kernel: int = 25) -> np.ndarray:
    """Reproduce the training-time CLAHE/Otsu/ellipse mask for the 20_11 model."""
    image = np.asarray(image, dtype=np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_kernel, dilation_kernel))
    dilated = cv2.dilate(binary, kernel, iterations=1)
    keep = dilated > 0
    return image * keep[:, :, None].astype(image.dtype) if image.ndim == 3 else image * keep.astype(image.dtype)


def run_evaluation(args: argparse.Namespace) -> int:
    workspace = Path(__file__).resolve().parent
    test_root = Path(args.test_dir).resolve() if args.test_dir else _discover_test_root(workspace)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else workspace / "eval_results"
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _set_plot_style()

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    torch.set_num_threads(max(1, min(args.threads, os.cpu_count() or 1)))
    LOGGER.info("Device: %s", device)
    LOGGER.info("Test root: %s", test_root)
    samples = discover_samples(test_root)
    LOGGER.info("Discovered %d images.", len(samples))
    checkpoints, unsupported = discover_checkpoints(workspace)
    LOGGER.info("Discovered %d unique PyTorch checkpoints; %d unsupported-format files.", len(checkpoints), len(unsupported))

    sample_decode_errors = []
    for sample in samples:
        try:
            LungRayService._decode_uploaded_image(sample.path.read_bytes())
        except Exception as exc:
            sample_decode_errors.append({"sample_id": sample.sample_id, "error": str(exc)})
    if sample_decode_errors:
        (output_dir / "decode_errors.json").write_text(json.dumps(sample_decode_errors, indent=2), encoding="utf-8")
        raise RuntimeError(f"Could not decode {len(sample_decode_errors)} test images. See eval_results/decode_errors.json.")

    if device.type == "cpu":
        LOGGER.warning("CUDA is unavailable; full inference will run on CPU and may take several minutes.")

    service = LungRayService()
    service.device = device
    for runtime_model in service.models.values():
        runtime_model.to(device).eval()
    if service.dense_unet is not None:
        service.dense_unet.to(device).eval()
    serving_hashes: dict[str, tuple[str, torch.nn.Module]] = {}
    for key, path in (
        ("standard", service.standard_path),
        ("wsol", service.wsol_path),
        ("resnet50", service.resnet_path),
        ("ag_mtcnet", service.ag_mtcnet_path),
    ):
        if path and Path(path).is_file() and key in service.models:
            serving_hashes[_sha256(Path(path))] = (key, service.models[key])

    classifier_checkpoints = [cp for cp in checkpoints if cp.kind == "classifier_candidate"]
    segment_checkpoints = [cp for cp in checkpoints if cp.kind == "segmentation"]
    model_for_checkpoint: dict[str, torch.nn.Module] = {}
    demo_model_ids: list[str] = []
    checkpoint_by_id: dict[str, Checkpoint] = {}
    failed_loads: list[dict[str, str]] = []
    failed_inferences: list[dict[str, str]] = []

    for checkpoint in classifier_checkpoints:
        if checkpoint.model_id not in DEMO_MODEL_NAMES and checkpoint.model_id != "densenet121_20_11":
            checkpoint.status = "discovered_not_run_not_a_web_demo_mode"
            checkpoint.notes = "Inventory only; not registered for the requested evaluation pipeline."
            continue
        try:
            if checkpoint.sha256 in serving_hashes:
                serving_id, model = serving_hashes[checkpoint.sha256]
                checkpoint.model_id = serving_id
                checkpoint.display_name = DEMO_MODEL_NAMES.get(serving_id, checkpoint.display_name)
                checkpoint.status = "loaded_from_web_demo_runtime"
                checkpoint.backbone = "resnet50" if serving_id == "resnet50" else "densenet121"
                checkpoint.img_size = 256 if serving_id == "ag_mtcnet" else 512
            else:
                model = load_classifier(checkpoint, device)
            model_for_checkpoint[checkpoint.sha256] = model
            checkpoint.model = model
            checkpoint_by_id[checkpoint.model_id] = checkpoint
            if checkpoint.model_id not in demo_model_ids and checkpoint.model_id in DEMO_MODEL_NAMES and checkpoint.model_id != "ensemble":
                demo_model_ids.append(checkpoint.model_id)
        except Exception as exc:
            checkpoint.status = "load_failed"
            checkpoint.notes = str(exc)
            failed_loads.append({"path": str(checkpoint.path.relative_to(workspace)), "error": str(exc)})
            LOGGER.exception("Could not load %s", checkpoint.path.name)

    if "standard" not in demo_model_ids or "wsol" not in demo_model_ids or "resnet50" not in demo_model_ids or "ag_mtcnet" not in demo_model_ids:
        LOGGER.warning("One or more web-demo checkpoint modes were not loaded; ensemble may be unavailable.")

    model_outputs: dict[str, list[dict[str, Any]]] = {}
    inference_times: dict[str, list[float]] = {}
    dense_unet_rows: list[dict[str, Any]] = []
    usable_checkpoints = [
        cp for cp in classifier_checkpoints
        if cp.sha256 in model_for_checkpoint
    ]
    baseline_20_transform = get_val_transforms(img_size=256)
    batch_size = max(1, args.batch_size)
    total_batches = math.ceil(len(samples) / batch_size)
    start_all = time.perf_counter()

    for batch_number, start in enumerate(range(0, len(samples), batch_size), start=1):
        batch_samples = samples[start : start + batch_size]
        raw_images = [
            np.asarray(LungRayService._decode_uploaded_image(s.path.read_bytes()), dtype=np.uint8)
            for s in batch_samples
        ]
        if args.single_pass:
            standard_inputs = torch.stack(
                [service.transform(image=image)["image"] for image in raw_images], dim=0
            ).to(device)
        else:
            standard_inputs = torch.cat(
                [_three_view_tensor(image, service.transform) for image in raw_images], dim=0
            ).to(device)
        baseline_20_images = [_apply_20_11_morphology_mask(image) for image in raw_images]
        if args.single_pass:
            baseline_20_inputs = torch.stack(
                [baseline_20_transform(image=image)["image"] for image in baseline_20_images], dim=0
            ).to(device)
        else:
            baseline_20_inputs = torch.cat(
                [_three_view_tensor(image, baseline_20_transform) for image in baseline_20_images], dim=0
            ).to(device)
        masks = service.segmenter.predict_masks(raw_images)
        if service.dense_unet is not None:
            for sample, mask in zip(batch_samples, masks):
                dense_unet_rows.append(
                    {
                        "model_id": "dense_unet",
                        "sample_id": sample.sample_id,
                        "dataset": sample.dataset,
                        "foreground_fraction_at_0_5": float(np.asarray(mask, dtype=np.uint8).mean()),
                        "ground_truth_mask_available": False,
                        "dice": None,
                        "iou": None,
                    }
                )
        gated_images = [
            apply_dilated_soft_mask(
                image,
                mask,
                dilation_margin_pct=0.06,
                background_attenuation=0.10,
            )
            for image, mask in zip(raw_images, masks)
        ]
        if args.single_pass:
            ag_inputs = torch.stack(
                [service.ag_transform(image=image)["image"] for image in gated_images], dim=0
            ).to(device)
        else:
            ag_inputs = torch.cat(
                [_three_view_tensor(image, service.ag_transform) for image in gated_images], dim=0
            ).to(device)
        batch_raw: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        batch_model_times: dict[str, float] = {}

        for checkpoint in usable_checkpoints:
            model = model_for_checkpoint[checkpoint.sha256]
            model_id = checkpoint.model_id
            if model_id == "ag_mtcnet":
                inputs = ag_inputs
            elif model_id == "densenet121_20_11":
                inputs = baseline_20_inputs
            else:
                inputs = standard_inputs
            t0 = time.perf_counter()
            try:
                raw_a, raw_b, raw_c = _model_tta_outputs(model, inputs, len(batch_samples))
            except Exception as exc:
                checkpoint.status = "inference_failed"
                checkpoint.notes = str(exc)
                failed_inferences.append(
                    {"checkpoint": str(checkpoint.path.relative_to(workspace)), "error": str(exc)}
                )
                LOGGER.exception("Inference failed for %s", checkpoint.path.name)
                model_for_checkpoint.pop(checkpoint.sha256, None)
                model_outputs.pop(model_id, None)
                inference_times.pop(model_id, None)
                continue
            batch_elapsed_ms = (time.perf_counter() - t0) * 1000 / len(batch_samples)
            inference_times.setdefault(model_id, []).append(batch_elapsed_ms)
            batch_model_times[model_id] = batch_elapsed_ms
            batch_raw[model_id] = (raw_a, raw_b, raw_c)

        # The app's Ensemble is a derived mode using the same soft-voting weights as the API.
        if all(k in batch_raw for k in ("standard", "wsol", "resnet50")):
            std_a, std_b, std_c = batch_raw["standard"]
            wsol_a, wsol_b, wsol_c = batch_raw["wsol"]
            res_a, res_b, res_c = batch_raw["resnet50"]
            raw_ensemble_a = 0.5 * std_a + 0.5 * res_a
            raw_ensemble_b = 0.6 * wsol_b + 0.2 * std_b + 0.2 * res_b
            raw_ensemble_c = 0.5 * std_c + 0.5 * res_c
            batch_raw["ensemble"] = (raw_ensemble_a, raw_ensemble_b, raw_ensemble_c)
            inference_times.setdefault("ensemble", []).append(
                sum(batch_model_times.get(k, 0.0) for k in ("standard", "wsol", "resnet50"))
            )

        for model_id, (raw_a, raw_b, raw_c) in batch_raw.items():
            if model_id == "densenet121_20_11":
                calibrated_a, calibrated_b, calibrated_c = raw_a, raw_b, raw_c
            else:
                calibrated_a = _calibrated(raw_a)
                calibrated_b = _calibrated(raw_b)
                calibrated_c = None if model_id == "ag_mtcnet" else _calibrated(raw_c)
            rows = model_outputs.setdefault(model_id, [])
            for local_idx in range(len(batch_samples)):
                rows.append(
                    {
                        "head_a": calibrated_a[local_idx],
                        "head_b": float(calibrated_b[local_idx]),
                        "head_c": None if calibrated_c is None else float(calibrated_c[local_idx]),
                        "head_c_status": "NOT_VALIDATED" if model_id == "ag_mtcnet" else "available",
                        "raw_head_a": raw_a[local_idx],
                        "raw_head_b": float(raw_b[local_idx]),
                        "raw_head_c": None if model_id == "ag_mtcnet" else float(raw_c[local_idx]),
                    }
                )
        LOGGER.info("Evaluated batch %d/%d (%d/%d images).", batch_number, total_batches, start + len(batch_samples), len(samples))

    # Include an explicit model summary for the derived Ensemble selection.
    if "ensemble" in model_outputs:
        demo_model_ids.append("ensemble")

    # Dense-UNet has image masks but no mask annotations in this curated sample.
    dense_path = Path(os.getenv("DENSE_UNET_CHECKPOINT", "checkpoints/dense_unet.pth"))
    if not dense_path.is_absolute():
        dense_path = workspace / dense_path
    dense_sha = _sha256(dense_path) if dense_path.is_file() else None
    dense_checkpoint = next((cp for cp in segment_checkpoints if cp.sha256 == dense_sha), None)
    if dense_checkpoint is not None and service.dense_unet is not None:
        dense_checkpoint.status = "loaded_from_web_demo_runtime"
        dense_checkpoint.backbone = "densenet121_encoder_decoder"
        dense_checkpoint.img_size = 256
        dense_checkpoint.model = service.dense_unet
    if dense_unet_rows:
        pd.DataFrame(dense_unet_rows).to_csv(output_dir / "dense_unet_predictions.csv", index=False)

    threshold_path = workspace / "configs" / "optimal_thresholds.json"
    base_thresholds = json.loads(threshold_path.read_text(encoding="utf-8")) if threshold_path.exists() else {}
    baseline_20_threshold_path = workspace / "configs" / "optimal_thresholds_20_11.json"
    baseline_20_raw = (
        json.loads(baseline_20_threshold_path.read_text(encoding="utf-8"))
        if baseline_20_threshold_path.exists() else {}
    )
    baseline_20_thresholds = {
        "head_a_nih_14": baseline_20_raw.get("head_a", {}),
        "head_b_tb": baseline_20_raw.get("head_b_tb", 0.5),
        "head_c_covid": baseline_20_raw.get("head_c_covid_binary", 0.5),
    }
    thresholds = {
        "_default": base_thresholds,
        "_per_model": {"densenet121_20_11": baseline_20_thresholds},
    }
    metric_rows, error_rows = evaluate_metrics(samples, model_outputs, checkpoint_by_id, thresholds)
    summary_rows = _metric_summary(metric_rows)
    for row in summary_rows:
        times = inference_times.get(row["model_id"], [])
        row["inference_ms_per_image_model_forward"] = float(np.mean(times)) if times else None
    metrics_frame = pd.DataFrame(metric_rows)
    summary_frame = pd.DataFrame(summary_rows)
    metrics_frame.to_csv(output_dir / "metrics_by_class.csv", index=False)
    summary_frame.to_csv(output_dir / "model_summary.csv", index=False)
    if error_rows:
        errors = pd.DataFrame(error_rows)
        errors["error_rank"] = errors.groupby(["model_id", "task", "class_name"])['error_confidence'].rank(method="first", ascending=False)
        errors.sort_values(["error_type", "error_confidence"], ascending=[True, False]).to_csv(output_dir / "error_analysis.csv", index=False)
    else:
        pd.DataFrame(columns=["model_id", "sample_id", "task", "error_type"]).to_csv(output_dir / "error_analysis.csv", index=False)

    prediction_frame = _make_prediction_rows(samples, model_outputs, checkpoints)
    prediction_frame.to_csv(output_dir / "predictions.csv", index=False)

    inventory_rows = []
    for cp in checkpoints:
        inventory_rows.append(
            {
                "checkpoint": str(cp.path.relative_to(workspace)),
                "aliases": "|".join(str(p.relative_to(workspace)) for p in cp.aliases if p != cp.path),
                "sha256": cp.sha256,
                "kind": cp.kind,
                "model_id": cp.model_id,
                "display_name": cp.display_name,
                "backbone": cp.backbone,
                "img_size": cp.img_size,
                "parameters": sum(p.numel() for p in cp.model.parameters()) if cp.model is not None else None,
                "status": cp.status,
                "notes": cp.notes,
            }
        )
    pd.DataFrame(inventory_rows).to_csv(output_dir / "model_inventory.csv", index=False)
    if unsupported:
        pd.DataFrame(unsupported).to_csv(output_dir / "unsupported_models.csv", index=False)
    if failed_loads:
        (output_dir / "model_load_errors.json").write_text(json.dumps(failed_loads, indent=2), encoding="utf-8")

    demo_model_ids = [model for model in DEMO_MODEL_NAMES if model in model_outputs]
    all_model_ids = list(model_outputs)
    plot_overview(figures_dir, summary_rows, demo_model_ids)
    plot_nih_heatmap(figures_dir, metric_rows, demo_model_ids)
    plot_confusion_figures(figures_dir, samples, model_outputs, base_thresholds, demo_model_ids)
    plot_qualitative_cases(figures_dir, samples, model_outputs, demo_model_ids, base_thresholds)

    elapsed_seconds = time.perf_counter() - start_all
    write_report(
        output_dir, workspace, test_root, samples, checkpoints, unsupported,
        metric_rows, summary_rows, elapsed_seconds, device,
        "single-pass serving validation transform (preliminary)" if args.single_pass
        else "serving validation transform with three-pass TTA",
    )
    run_metadata = {
        "test_root": str(test_root),
        "sample_count": len(samples),
        "device": str(device),
        "models_with_predictions": all_model_ids,
        "web_demo_modes": demo_model_ids,
        "runtime_seconds": elapsed_seconds,
        "inference_protocol": "single_pass_preliminary" if args.single_pass else "three_pass_tta",
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ag_mtcnet_head_c": "NOT_VALIDATED; probabilities and metrics withheld",
        "image_decode_errors": sample_decode_errors,
        "failed_model_loads": failed_loads,
        "failed_model_inferences": failed_inferences,
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")

    print("\nEvaluation summary")
    if not summary_frame.empty:
        overview = summary_frame[summary_frame["model_id"].isin(demo_model_ids)][
            ["model_id", "task", "dataset", "auroc", "f1", "sensitivity", "specificity", "inference_ms_per_image_model_forward", "n"]
        ]
        print(overview.to_string(index=False))
    print(f"\nProcessed {len(samples)} images with {len(model_outputs)} classifier modes on {device}.")
    print(f"Artifacts: {output_dir}")
    return 0 if model_outputs and not failed_loads and not failed_inferences else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-dir", default=None, help="Test root; defaults to data/test_samples then test_samples.")
    parser.add_argument("--output-dir", default=None, help="Output directory; defaults to eval_results/.")
    parser.add_argument("--batch-size", type=int, default=4, help="Number of samples per inference batch.")
    parser.add_argument("--threads", type=int, default=4, help="Maximum PyTorch CPU thread count.")
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference even if CUDA exists.")
    parser.add_argument("--single-pass", action="store_true", help="Use one deterministic view per image for a faster preliminary run.")
    parser.add_argument("--verbose", action="store_true", help="Show debug logs.")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        return run_evaluation(args)
    except Exception as exc:
        LOGGER.exception("Evaluation stopped: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
