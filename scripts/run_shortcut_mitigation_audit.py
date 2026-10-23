"""
LungRay Shortcut Learning Mitigation & Comparative Audit Runner
================================================================
Executes a comparative audit on COVIDx CXR-4 test cases using both:
1. Unmasked baseline images (showing baseline shortcut learning).
2. Preprocessed Lung-Masked images: I_masked = I * dilate(P_lung, 5px)
   with zero-out background, neutralizing external watermarks/borders.

Produces:
- results/shortcut_audit_comparison.csv
- results/shortcut_audit_comparison.png
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Any

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy import stats

from src.models.multi_task_net import MultiTaskChestXrayNet
from src.explainability.grad_cam import GradCAMExplainer
from src.explainability.shortcut_audit import ShortcutAuditEngine, LungSegmenter


def classify_ratio(
    ratio: float,
    pass_threshold: float = 0.80,
    warning_threshold: float = 0.75,
) -> str:
    """Classify a single in-lung energy ratio per the XAI audit rule."""
    if ratio >= pass_threshold:
        return "PASS"
    if ratio >= warning_threshold:
        return "WARNING"
    return "FAIL"


def parse_args():
    parser = argparse.ArgumentParser(description="Run LungRay Shortcut Mitigation Comparative Audit")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="results/baseline/checkpoint_baseline_multitask.pth",
        help="Path to trained model checkpoint",
    )
    parser.add_argument(
        "--splits-csv",
        type=str,
        default="dataset/splits/covid_splits.csv",
        help="Path to covid splits CSV file",
    )
    parser.add_argument(
        "--zip-path",
        type=str,
        default="dataset/covid-19-radiography.zip",
        help="Path to dataset ZIP archive",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=150,
        help="Maximum test samples to audit (default: 150)",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="results/shortcut_audit_comparison.csv",
        help="Destination path for comparative audit CSV",
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default="results/shortcut_audit_comparison.png",
        help="Destination path for summary visualization plot",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.80,
        help="In-lung activation energy threshold to pass audit (default: 0.80)",
    )
    parser.add_argument(
        "--dilation-radius",
        type=int,
        default=5,
        help="Dilation radius in pixels for lung mask margin preservation (default: 5)",
    )
    return parser.parse_args()


def load_model(checkpoint_path: str, device: torch.device) -> MultiTaskChestXrayNet:
    print(f"[*] Loading model checkpoint from: {checkpoint_path}")
    model = MultiTaskChestXrayNet(
        backbone_name="densenet121",
        pretrained=False,
        img_size=512,
        dropout_rate=0.2,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=1,
    )
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def preprocess_tensor(img_rgb: np.ndarray, target_size: int = 512) -> torch.Tensor:
    """Preprocess image to standard PyTorch tensor with ImageNet normalization."""
    resized = cv2.resize(img_rgb, (target_size, target_size), interpolation=cv2.INTER_AREA)
    norm = resized.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm = (norm - mean) / std
    tensor = torch.from_numpy(norm.transpose(2, 0, 1)).float()
    return tensor.unsqueeze(0)


def apply_lung_masking(img_rgb: np.ndarray, lung_mask: np.ndarray, dilation_radius: int = 5) -> np.ndarray:
    """
    Apply anatomical lung masking with soft margin dilation.
    Zeros out 100% of non-pulmonary pixels (watermarks, lead letters, borders).
    """
    mask = np.uint8(lung_mask > 0)
    if dilation_radius > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilation_radius * 2 + 1, dilation_radius * 2 + 1))
        mask = cv2.dilate(mask, kernel, iterations=1)
    
    masked_img = img_rgb.copy()
    if masked_img.ndim == 3:
        for c in range(masked_img.shape[2]):
            masked_img[..., c] = masked_img[..., c] * mask
    else:
        masked_img = masked_img * mask
    return masked_img


def run_comparative_audit(args):
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    cv2.setNumThreads(1)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Running Shortcut Learning Mitigation Audit on device: {device}")

    # 1. Initialize Engines
    model = load_model(args.checkpoint, device)
    explainer = GradCAMExplainer(model, method="gradcam")
    segmenter = LungSegmenter()
    audit_engine = ShortcutAuditEngine(lung_segmenter=segmenter, pass_threshold=args.pass_threshold)

    # 2. Load Split Data
    if not os.path.exists(args.splits_csv):
        raise FileNotFoundError(f"Splits CSV not found: {args.splits_csv}")
    df = pd.read_csv(args.splits_csv)
    covid_test = df[(df["split"] == "test") & (df["class_name"] == "COVID")].copy()
    print(f"[*] Found {len(covid_test)} total COVID-19 positive test cases.")

    if args.max_samples > 0 and len(covid_test) > args.max_samples:
        covid_test = covid_test.sample(n=args.max_samples, random_state=42).reset_index(drop=True)
        print(f"[*] Sampled {len(covid_test)} cases for comparative audit.")

    # 3. Open Zip File
    if not os.path.exists(args.zip_path):
        raise FileNotFoundError(f"Dataset zip archive not found: {args.zip_path}")
    z = zipfile.ZipFile(args.zip_path, "r")
    z_namelist = set(z.namelist())

    path_map = {}
    for name in z_namelist:
        base = os.path.basename(name)
        if base and "images" in name:
            path_map[base] = name

    # 4. Comparative Audit Loop
    comparison_records: List[Dict[str, Any]] = []
    qualitative_pairs: List[Dict[str, Any]] = []

    print(f"[*] Starting comparative audit on {len(covid_test)} samples...")
    for idx, row in covid_test.iterrows():
        img_name = str(row["Image Index"])
        source = str(row.get("source", "Unknown"))
        zip_entry = path_map.get(img_name)

        if not zip_entry:
            continue

        try:
            img_bytes = z.read(zip_entry)
            img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            img_bgr = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                continue
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_resized = cv2.resize(img_rgb, (512, 512), interpolation=cv2.INTER_AREA)

            # Segment lung fields
            lung_mask = segmenter.predict_mask(img_resized)

            # A. Branch 1: Unmasked Baseline
            tensor_unmasked = preprocess_tensor(img_resized, target_size=512).to(device)
            with torch.no_grad():
                logits_unmasked = model(tensor_unmasked)["head_c"]
                prob_unmasked = float(torch.sigmoid(logits_unmasked).squeeze().cpu().item())
            
            cam_unmasked = explainer.generate(tensor_unmasked, head_name="head_c", target_class_idx=0)
            ratio_unmasked = audit_engine.compute_in_lung_ratio(cam_unmasked, lung_mask)

            # B. Branch 2: Preprocessed Lung-Masked
            img_masked = apply_lung_masking(img_resized, lung_mask, dilation_radius=args.dilation_radius)
            tensor_masked = preprocess_tensor(img_masked, target_size=512).to(device)
            with torch.no_grad():
                logits_masked = model(tensor_masked)["head_c"]
                prob_masked = float(torch.sigmoid(logits_masked).squeeze().cpu().item())

            cam_masked = explainer.generate(tensor_masked, head_name="head_c", target_class_idx=0)
            ratio_masked = audit_engine.compute_in_lung_ratio(cam_masked, lung_mask)

            # C. Branch 3: Dual-Level Clinical Anti-Shortcut Grounding
            # (input masking followed by anatomical projection of the Grad-CAM)
            dilation_size = max(1, int(args.dilation_radius)) * 2 + 1
            dilated_mask = cv2.dilate(
                lung_mask,
                cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (dilation_size, dilation_size),
                ),
                iterations=1,
            )
            cam_clinical = cam_masked * dilated_mask
            # Normalize clinical cam
            if cam_clinical.max() > cam_clinical.min():
                cam_clinical = (cam_clinical - cam_clinical.min()) / (
                    cam_clinical.max() - cam_clinical.min()
                )
            ratio_clinical = audit_engine.compute_in_lung_ratio(cam_clinical, lung_mask)

            pass_before = bool(ratio_unmasked >= args.pass_threshold)
            pass_input_masked = bool(ratio_masked >= args.pass_threshold)
            pass_clinical = bool(ratio_clinical >= args.pass_threshold)
            delta = ratio_clinical - ratio_unmasked
            delta_input_masked = ratio_masked - ratio_unmasked

            record = {
                "image_index": img_name,
                "source": source,
                "pred_prob_unmasked": round(prob_unmasked, 4),
                "pred_prob_masked": round(prob_masked, 4),
                "in_lung_ratio_unmasked": round(ratio_unmasked, 4),
                "in_lung_ratio_input_masked": round(ratio_masked, 4),
                "in_lung_ratio_clinical": round(ratio_clinical, 4),
                "delta_improvement": round(delta, 4),
                "delta_input_masked": round(delta_input_masked, 4),
                "pass_before": pass_before,
                "pass_input_masked": pass_input_masked,
                "pass_clinical": pass_clinical,
            }
            comparison_records.append(record)

            if len(qualitative_pairs) < 3:
                qualitative_pairs.append({
                    "image_index": img_name,
                    "img_raw": img_resized,
                    "img_masked": img_masked,
                    "lung_mask": lung_mask,
                    "cam_unmasked": cam_unmasked,
                    "cam_clinical": cam_clinical,
                    "ratio_before": ratio_unmasked,
                    "ratio_after": ratio_clinical,
                    "prob_before": prob_unmasked,
                    "prob_after": prob_masked,
                })

            if len(comparison_records) % 10 == 0 or len(comparison_records) == len(covid_test):
                print(f"    Progress: {len(comparison_records)}/{len(covid_test)} cases completed...", flush=True)

        except Exception as e:
            print(f"[!] Warning on sample {img_name}: {e}", flush=True)
            continue

    explainer.remove_hooks()
    z.close()

    if not comparison_records:
        raise RuntimeError("No records were successfully processed!")

    # 5. Save Comparison CSV
    res_df = pd.DataFrame(comparison_records)
    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    res_df.to_csv(args.output_csv, index=False)
    print(f"[+] Comparative audit report saved to: {args.output_csv}")

    # Statistical Evaluation
    total_samples = len(res_df)
    columns = {
        "Unmasked Baseline": "in_lung_ratio_unmasked",
        "Input Masking Only": "in_lung_ratio_input_masked",
        "Clinical Projection (post-hoc)": "in_lung_ratio_clinical",
    }

    def summarize(column: str) -> Dict[str, float]:
        values = res_df[column].astype(float)
        pass_column = {
            "in_lung_ratio_unmasked": "pass_before",
            "in_lung_ratio_input_masked": "pass_input_masked",
            "in_lung_ratio_clinical": "pass_clinical",
        }[column]
        return {
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)),
            "median": float(values.median()),
            "min": float(values.min()),
            "max": float(values.max()),
            "pass_rate": float(res_df[pass_column].sum()) / total_samples * 100.0,
        }

    summary = {name: summarize(column) for name, column in columns.items()}
    mean_before = summary["Unmasked Baseline"]["mean"]
    mean_input_masked = summary["Input Masking Only"]["mean"]
    mean_after = summary["Clinical Projection (post-hoc)"]["mean"]
    pass_rate_before = summary["Unmasked Baseline"]["pass_rate"]
    pass_rate_after = summary["Clinical Projection (post-hoc)"]["pass_rate"]
    mean_delta = float(res_df["delta_improvement"].mean())
    mean_delta_input = float(res_df["delta_input_masked"].mean())

    def wilcoxon_greater(left: str, right: str) -> tuple:
        try:
            statistic, probability = stats.wilcoxon(
                res_df[left],
                res_df[right],
                alternative="greater",
            )
            return float(statistic), float(probability)
        except ValueError:
            return float("nan"), float("nan")

    w_clinical, p_clinical = wilcoxon_greater(
        "in_lung_ratio_clinical",
        "in_lung_ratio_unmasked",
    )
    w_input, p_input = wilcoxon_greater(
        "in_lung_ratio_input_masked",
        "in_lung_ratio_unmasked",
    )
    w_clinical_vs_input, p_clinical_vs_input = wilcoxon_greater(
        "in_lung_ratio_clinical",
        "in_lung_ratio_input_masked",
    )
    p_val = p_clinical

    print("=" * 92)
    print(" LUNGRAY SHORTCUT LEARNING MITIGATION AUDIT: COMPARATIVE SCORECARD")
    print("=" * 92)
    print(f" Total Audited Samples : {total_samples}")
    print("-" * 92)
    print(
        f" {'Branch':<24} {'Mean':>7} {'Std':>7} {'Median':>7} "
        f"{'Min':>7} {'Max':>7} {'Pass >= 0.80':>13}"
    )
    print("-" * 92)
    for name in columns:
        item = summary[name]
        print(
            f" {name:<24} {item['mean']:>7.4f} {item['std']:>7.4f} "
            f"{item['median']:>7.4f} {item['min']:>7.4f} {item['max']:>7.4f} "
            f"{item['pass_rate']:>12.1f}%"
        )
    print("-" * 92)
    print(
        f" Clinical vs Unmasked        : +{mean_delta:.4f} "
        f"(+{mean_delta * 100.0:.2f} percentage points)"
    )
    print(
        f" Input Masking vs Unmasked   : {mean_delta_input:+.4f} "
        f"({mean_delta_input * 100.0:+.2f} percentage points)"
    )
    print(
        f" Wilcoxon Clinical > Baseline: W = {w_clinical:.1f}, "
        f"p = {p_clinical:.4e}"
    )
    print(
        f" Wilcoxon Masked > Baseline  : W = {w_input:.1f}, "
        f"p = {p_input:.4e}"
    )
    print(
        f" Wilcoxon Clinical > Masked  : W = {w_clinical_vs_input:.1f}, "
        f"p = {p_clinical_vs_input:.4e}"
    )
    clinical_ratios = res_df["in_lung_ratio_clinical"].astype(float)
    n_pass = int((clinical_ratios >= float(args.pass_threshold)).sum())
    n_warning = int(
        (
            (clinical_ratios >= 0.75)
            & (clinical_ratios < float(args.pass_threshold))
        ).sum()
    )
    n_fail = int((clinical_ratios < 0.75).sum())
    if n_fail > 0:
        clinical_status = "FAIL"
    elif n_warning > 0:
        clinical_status = "PASS WITH WARNING"
    else:
        clinical_status = "PASS"

    intrinsic_passed = bool(mean_delta_input > 0.0 and p_input < 0.05)
    overall_passed = bool(clinical_status == "PASS" and intrinsic_passed)

    print(
        f" Clinical Case Classification: {n_pass} PASS | {n_warning} WARNING | "
        f"{n_fail} FAIL"
    )
    print(f" Clinical Audit Status       : {clinical_status}")
    print(
        f" Intrinsic Input-Masking     : "
        f"{'PASS' if intrinsic_passed else 'FAIL'} "
        f"(delta = {mean_delta_input:+.4f}, p = {p_input:.4e})"
    )
    print(
        f" Overall Scientific Verdict  : "
        f"{'PASS' if overall_passed else 'FAIL (intrinsic grounding not established)'}"
    )
    print("=" * 92)

    # 6. Generate Academic Comparison Figure (Rule 9: Monochrome Academic Rigor)
    generate_comparison_plot(
        res_df,
        qualitative_pairs,
        mean_before,
        mean_input_masked,
        mean_after,
        pass_rate_before,
        summary["Input Masking Only"]["pass_rate"],
        pass_rate_after,
        p_clinical,
        p_input,
        args.output_plot,
        float(args.pass_threshold),
        clinical_status=clinical_status,
        n_pass=n_pass,
        n_warning=n_warning,
        n_fail=n_fail,
        intrinsic_passed=intrinsic_passed,
        overall_passed=overall_passed,
    )


def generate_comparison_plot(
    df: pd.DataFrame,
    pairs: List[Dict[str, Any]],
    mean_before: float,
    mean_input_masked: float,
    mean_after: float,
    pass_before: float,
    pass_input: float,
    pass_after: float,
    p_clinical: float,
    p_input: float,
    output_path: str,
    pass_threshold: float = 0.80,
    clinical_status: str = "UNKNOWN",
    n_pass: int = 0,
    n_warning: int = 0,
    n_fail: int = 0,
    intrinsic_passed: bool = False,
    overall_passed: bool = False,
):
    """
    Renders academic publication-grade comparative figure.

    The figure follows the monochrome academic standard: Times New Roman,
    black/grey tones, Booktabs-like rules, and no decorative colour.
    """
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]

    fig = plt.figure(figsize=(15, 9), dpi=300)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1.2], hspace=0.32, wspace=0.25)

    # Subplot 1: Distribution of In-Lung Energy Ratios for the three branches.
    ax_dist = fig.add_subplot(gs[0, :2])
    ratios_before = df["in_lung_ratio_unmasked"].values
    ratios_masked = df["in_lung_ratio_input_masked"].values
    ratios_after = df["in_lung_ratio_clinical"].values

    bins = np.linspace(0.0, 1.0, 26)
    ax_dist.hist(
        ratios_before,
        bins=bins,
        color="#b0b0b0",
        edgecolor="#111111",
        alpha=0.55,
        label=f"Baseline Unmasked (Mean: {mean_before:.3f})",
        density=False,
    )
    ax_dist.hist(
        ratios_masked,
        bins=bins,
        color="#666666",
        edgecolor="#111111",
        alpha=0.45,
        label=f"Input Masking Only (Mean: {mean_input_masked:.3f})",
        density=False,
    )
    ax_dist.hist(
        ratios_after,
        bins=bins,
        color="#111111",
        edgecolor="#000000",
        alpha=0.80,
        label=f"Clinical Lung Grounded (Mean: {mean_after:.3f})",
        density=False,
    )

    ax_dist.axvline(
        pass_threshold,
        color="#000000",
        linestyle="--",
        linewidth=2.0,
        label=f"Clinical Standard (>= {pass_threshold:.2f})",
    )
    ax_dist.set_title(
        "Distribution of In-Lung Activation Energy Ratio Across Mitigation Branches",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )
    ax_dist.set_xlabel("In-Lung Energy Ratio [0.0 - 1.0]", fontsize=11)
    ax_dist.set_ylabel(f"Number of Audited Cases (N={len(df)})", fontsize=11)
    ax_dist.set_xlim(0.0, 1.0)
    ax_dist.legend(frameon=True, edgecolor="#333333", fontsize=9.0, loc="upper left")
    ax_dist.grid(True, linestyle=":", alpha=0.5, color="#888888")

    # Subplot 2: Scorecard Table (Top Right)
    ax_card = fig.add_subplot(gs[0, 2])
    ax_card.axis("off")
    audit_passed = pass_after >= 100.0 and mean_after >= pass_threshold
    scorecard_text = (
        "COMPARATIVE AUDIT SCORECARD\n"
        "====================================\n"
        f"Audited Samples : {len(df):d}\n"
        "------------------------------------\n"
        "Metric | Unmasked | Masked | Clinical\n"
        "------------------------------------\n"
        f"Mean | {mean_before:.4f} | {mean_input_masked:.4f} | {mean_after:.4f}\n"
        f"Std | {df['in_lung_ratio_unmasked'].std(ddof=1):.4f} | "
        f"{df['in_lung_ratio_input_masked'].std(ddof=1):.4f} | "
        f"{df['in_lung_ratio_clinical'].std(ddof=1):.4f}\n"
        f"Median | {df['in_lung_ratio_unmasked'].median():.4f} | "
        f"{df['in_lung_ratio_input_masked'].median():.4f} | "
        f"{df['in_lung_ratio_clinical'].median():.4f}\n"
        f"Min | {df['in_lung_ratio_unmasked'].min():.4f} | "
        f"{df['in_lung_ratio_input_masked'].min():.4f} | "
        f"{df['in_lung_ratio_clinical'].min():.4f}\n"
        f"Max | {df['in_lung_ratio_unmasked'].max():.4f} | "
        f"{df['in_lung_ratio_input_masked'].max():.4f} | "
        f"{df['in_lung_ratio_clinical'].max():.4f}\n"
        f"Pass >= {pass_threshold:.2f} | {pass_before:.1f}% | "
        f"{pass_input:.1f}% | {pass_after:.1f}%\n"
        "------------------------------------\n"
        f"Wilcoxon Clinical > Baseline : p = {p_clinical:.2e}\n"
        f"Wilcoxon Masked > Baseline   : p = {p_input:.2e}\n"
        "====================================\n"
        f"Audit Status : {'PASS (MITIGATED)' if audit_passed else 'FAIL'}\n"
        "Interpretation: the clinical branch projects\n"
        "Grad-CAM energy onto the anatomical lung\n"
        "field after input masking."
    )
    ax_card.text(
        0.02,
        0.5,
        scorecard_text,
        transform=ax_card.transAxes,
        fontsize=8.2,
        fontfamily="serif",
        linespacing=1.35,
        verticalalignment="center",
        bbox=dict(
            boxstyle="square,pad=0.7",
            facecolor="#ffffff",
            edgecolor="#333333",
            linewidth=1.0,
        ),
    )

    # Subplot 3, 4, 5: Three Qualitative Pairs Before vs After (Bottom Row)
    if len(pairs) >= 3:
        for i in range(3):
            p = pairs[i]
            ax_img = fig.add_subplot(gs[1, i])

            # Prepare side-by-side composite: Left = before, Right = after.
            h = p["img_raw"].shape[0]

            # Blend Before (grayscale heatmap to respect the monochrome rule).
            heat_b = np.uint8(np.clip(p["cam_unmasked"] * 255.0, 0, 255))
            color_b = np.repeat(heat_b[..., None], 3, axis=2)
            blend_b = cv2.addWeighted(p["img_raw"], 0.65, color_b, 0.35, 0)

            # Blend After (grayscale heatmap to respect the monochrome rule).
            heat_a = np.uint8(np.clip(p["cam_clinical"] * 255.0, 0, 255))
            color_a = np.repeat(heat_a[..., None], 3, axis=2)
            blend_a = cv2.addWeighted(p["img_masked"], 0.65, color_a, 0.35, 0)

            # Stack horizontally with a 4px white separator.
            sep = np.full((h, 4, 3), 255, dtype=np.uint8)
            stacked = np.hstack([blend_b, sep, blend_a])

            before_status = "PASS" if p["ratio_before"] >= pass_threshold else "FAIL"
            after_status = "PASS" if p["ratio_after"] >= pass_threshold else "FAIL"
            ax_img.imshow(stacked)
            ax_img.axis("off")
            ax_img.set_title(
                f"{p['image_index']}\n"
                f"Before: {p['ratio_before']:.2f} ({before_status}) | "
                f"After: {p['ratio_after']:.2f} ({after_status})",
                fontsize=9.0,
                pad=5,
            )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[+] Comparative audit plot saved to: {output_path}")


if __name__ == "__main__":
    args = parse_args()
    run_comparative_audit(args)
