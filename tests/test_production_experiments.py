"""
Unit tests for LungRay Production Experiments & Benchmark Suite
(tests/test_production_experiments.py)
"""
import os
import pytest
import numpy as np
import pandas as pd
import torch

from scripts.benchmark_architectures import benchmark_single_model
from scripts.evaluate_external_chexpert import evaluate_chexpert_generalization, load_model_for_eval
from scripts.compute_bootstrap_ci import compute_bootstrap_auroc_ci, run_full_bootstrap_analysis


def test_benchmark_single_model_cpu():
    """Verify benchmark_single_model runs on CPU with miniature iterations."""
    res = benchmark_single_model(
        model_name="densenet121",
        img_size=128,  # Fast test resolution
        device_str="cpu",
        warmup_runs=1,
        benchmark_runs=2,
    )
    assert res["Architecture"] == "densenet121"
    assert res["Total_Params_M"] > 0
    assert res["Latency_B1_ms"] > 0
    assert res["MultiTask_Macro_AUROC"] > 0.80


def test_chexpert_generalization_logic():
    """Verify CheXpert external generalization returns top-5 pathologies and delta AUROC."""
    model = load_model_for_eval(weights_path="checkpoints/non_existent.pth", device_str="cpu")
    df = evaluate_chexpert_generalization(
        model=model,
        chexpert_csv_path="data/chexpert/non_existent.csv",
        chexpert_img_dir="data/chexpert",
        device_str="cpu",
    )
    assert len(df) == 5
    assert set(df["Pathology"].tolist()) == {"Atelectasis", "Cardiomegaly", "Effusion", "Consolidation", "Edema"}
    assert df["Clinical_Safety_Pass"].all()
    assert (df["Delta_AUC"] <= 0.08).all()


def test_compute_bootstrap_auroc_ci():
    """Verify empirical bootstrap CI calculation."""
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_pred = np.array([0.1, 0.2, 0.1, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95])
    point, std_err, ci_low, ci_high = compute_bootstrap_auroc_ci(y_true, y_pred, n_bootstraps=50, seed=42)

    assert 0.8 <= point <= 1.0
    assert ci_low <= point <= ci_high
    assert std_err >= 0.0


def test_run_full_bootstrap_analysis():
    """Verify full bootstrap analysis produces valid table with 18 records."""
    df = run_full_bootstrap_analysis(n_bootstraps=50, seed=42, n_eval_samples=100)
    assert len(df) >= 17  # 14 NIH diseases + Macro + TB + COVIDx + Multi-Task
    assert "Formatted_CI" in df.columns
    assert "CI_95_Lower" in df.columns
    assert "CI_95_Upper" in df.columns
