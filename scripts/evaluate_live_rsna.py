#!/usr/bin/env python3
"""
scripts/evaluate_live_rsna.py - Live WSOL Box-IoU Benchmark on Real RSNA Pneumonia
=============================================================================
Inviolable Constraint 4 (Ràng buộc sống còn số 4):
- Bounding Box annotations from RSNA Pneumonia Detection are STRICTLY used for
  quantitative evaluation (IoU), NEVER for training.

Inviolable Constraint 7 (Ràng buộc sống còn số 7):
- 100% Live Inference: Streams real DICOM images directly from
  dataset/rsna-pneumonia-detection-challenge.zip, runs MultiScaleGradCAMPlusPlus
  on the requested checkpoint (default checkpoints/best_model.pth), and computes
  authentic geometric Box-IoU vs RSNA radiologist annotations. Zero simulation.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
import zipfile
from typing import Any, Dict, List

import cv2
import numpy as np
import pandas as pd
import pydicom
import torch
from PIL import Image

# Force UTF-8 terminal encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data.transforms import get_val_transforms
from src.explainability import (
    MultiScaleGradCAMPlusPlus,
    LungSegmenter,
    ShortcutAuditEngine,
    compute_box_iou,
    compute_mask_iou,
    extract_bboxes_from_mask,
    adaptive_binarize,
    rasterize_bboxes,
)
from src.models.multi_task_net import MultiTaskChestXrayNet

# RSNA Pneumonia Detection maps onto Head A "Pneumonia" (NIH index 6).
RSNA_NIH_DISEASE = "Pneumonia"
RSNA_NIH_IDX = 6

# Original RSNA DICOM resolution (bounding boxes live in this space).
RSNA_ORIG_SIZE = 1024.0


def load_model(
    weights_path: str = "checkpoints/best_model.pth",
    device: torch.device = torch.device("cpu"),
) -> MultiTaskChestXrayNet:
    model = MultiTaskChestXrayNet(
        backbone_name="densenet121",
        pretrained=False,
        img_size=512,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=1,
    )
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"Không tìm thấy checkpoint tại {weights_path}")
    print(f"[*] Nạp trọng số mô hình từ {weights_path}...")
    state = torch.load(weights_path, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model_state_dict" in state:
        state = state["model_state_dict"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state)

    model.to(device)
    model.eval()
    return model


def sample_rsna_positive_cases(
    zip_path: str, target_total: int = 100, seed: int = 42
) -> List[Dict[str, Any]]:
    """Reads stage_2_train_labels.csv and selects positive pneumonia cases with boxes."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open("stage_2_train_labels.csv") as f:
            df = pd.read_csv(f)

    pos_df = df[df["Target"] == 1].dropna(subset=["x", "y", "width", "height"])
    patient_ids = sorted(pos_df["patientId"].unique())
    np.random.seed(seed)
    np.random.shuffle(patient_ids)
    patient_ids = patient_ids[:target_total]

    samples: List[Dict[str, Any]] = []
    for pid in patient_ids:
        rows = pos_df[pos_df["patientId"] == pid]
        boxes = [
            [float(r["x"]), float(r["y"]), float(r["x"]) + float(r["width"]), float(r["y"]) + float(r["height"])]
            for _, r in rows.iterrows()
        ]
        samples.append({"patient_id": pid, "gt_boxes": boxes})

    print(f"[*] Đã chọn {len(samples)} ca dương tính Viêm phổi (Pneumonia) từ RSNA.")
    return samples


def dicom_to_rgb_uint8(dcm: "pydicom.dataset.FileDataset") -> np.ndarray:
    """Decodes a RSNA DICOM into an RGB uint8 image (MONOCHROME2 convention)."""
    arr = dcm.pixel_array.astype(np.float32)
    arr = np.clip(arr, 0, np.percentile(arr, 99) * 1.01 if arr.max() > 0 else 1)
    if arr.max() > 0:
        arr = (arr / arr.max()) * 255.0
    gray = arr.astype(np.uint8)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def run_live_rsna_benchmark(
    zip_path: str = "dataset/rsna-pneumonia-detection-challenge.zip",
    n_samples: int = 100,
    out_csv: str = "results/live_rsna_iou_benchmark.csv",
    seed: int = 42,
    weights_path: str = "checkpoints/best_model.pth",
) -> pd.DataFrame:
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Không tìm thấy file zip RSNA tại {zip_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Sử dụng thiết bị tính toán: {device}")

    model = load_model(weights_path, device=device)
    explainer = MultiScaleGradCAMPlusPlus(model)
    segmenter = LungSegmenter()
    audit_engine = ShortcutAuditEngine(segmenter)
    transform = get_val_transforms(img_size=512)

    samples = sample_rsna_positive_cases(zip_path, target_total=n_samples, seed=seed)

    records: List[Dict[str, Any]] = []
    start_time = time.time()
    print(f"\n[*] BẮT ĐẦU CHẠY SUY LUẬN SỐNG TRÊN {len(samples)} MẪU RSNA (100% REAL DICOM)...")
    print("=" * 85)
    print(f"{'STT':<4} | {'Disease':<16} | {'Prob':<6} | {'Best IoU':<9} | {'Mean IoU':<9} | {'In-Lung':<8} | {'Latency':<8}")
    print("=" * 85)

    with zipfile.ZipFile(zip_path, "r") as zf:
        for idx, sample in enumerate(samples, 1):
            t0 = time.time()
            pid = sample["patient_id"]
            gt_boxes = sample["gt_boxes"]

            zip_internal_path = f"stage_2_train_images/{pid}.dcm"
            img_bytes = zf.read(zip_internal_path)
            dcm = pydicom.dcmread(io.BytesIO(img_bytes))
            img_np = dicom_to_rgb_uint8(dcm)

            # Preprocess tensor (1, 3, 512, 512)
            transformed = transform(image=img_np)["image"]
            tensor = transformed.unsqueeze(0).to(device)

            # Model prediction
            with torch.no_grad():
                logits = model(tensor, task_id="head_a")["head_a"]
                prob = float(torch.sigmoid(logits)[0, RSNA_NIH_IDX].item())

            # Real Multi-Scale Grad-CAM++
            raw_heatmap = explainer.generate(
                tensor,
                head_name="head_a",
                target_class_idx=RSNA_NIH_IDX,
                fusion_weights=(0.4, 0.6),
            )

            # Generate anatomical lung mask
            lung_mask = segmenter.predict_mask(img_np)
            if lung_mask.shape != (512, 512):
                lung_mask = cv2.resize(lung_mask.astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST)
            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            effective_mask = cv2.dilate(lung_mask.astype(np.uint8), kernel_dilate, iterations=1)

            in_lung_ratio = audit_engine.compute_in_lung_ratio(raw_heatmap, effective_mask)

            # Scale GT boxes from original 1024 resolution to 512x512
            scale = 512.0 / RSNA_ORIG_SIZE
            gt_scaled = [[b[0] * scale, b[1] * scale, b[2] * scale, b[3] * scale] for b in gt_boxes]

            # Adaptive Binarization & Box Extraction
            bin_mask = adaptive_binarize(raw_heatmap, lung_mask=effective_mask, disease_name=RSNA_NIH_DISEASE)
            pred_boxes = extract_bboxes_from_mask(bin_mask, min_area_ratio=0.005)

            # Compute IoU
            best_box_iou = 0.0
            mean_box_iou = 0.0
            if len(pred_boxes) > 0 and len(gt_scaled) > 0:
                ious_for_gt = []
                for gb in gt_scaled:
                    max_iou_for_g = max(compute_box_iou(pb, gb) for pb in pred_boxes)
                    ious_for_gt.append(max_iou_for_g)
                mean_box_iou = float(np.mean(ious_for_gt))
                best_box_iou = float(max(ious_for_gt))

            gt_raster = rasterize_bboxes(gt_scaled, shape=(512, 512))
            mask_iou = compute_mask_iou(bin_mask, gt_raster)

            elapsed_ms = (time.time() - t0) * 1000.0
            records.append(
                {
                    "sample_idx": idx,
                    "patient_id": pid,
                    "nih_disease": RSNA_NIH_DISEASE,
                    "target_probability": round(prob, 4),
                    "num_gt_boxes": len(gt_scaled),
                    "num_pred_boxes": len(pred_boxes),
                    "best_box_iou": round(best_box_iou, 4),
                    "mean_box_iou": round(mean_box_iou, 4),
                    "mask_iou": round(mask_iou, 4),
                    "in_lung_energy": round(in_lung_ratio, 4),
                    "pass_iou_01": best_box_iou >= 0.10,
                    "pass_iou_03": best_box_iou >= 0.30,
                    "pass_iou_05": best_box_iou >= 0.50,
                    "latency_ms": round(elapsed_ms, 1),
                }
            )

            print(
                f"{idx:<4} | {RSNA_NIH_DISEASE:<16} | {prob * 100:>5.1f}% | {best_box_iou:>8.4f}  | {mean_box_iou:>8.4f}  | {in_lung_ratio * 100:>6.1f}% | {elapsed_ms:>6.0f}ms"
            )

    explainer.remove_hooks()
    total_time = time.time() - start_time

    df_res = pd.DataFrame(records)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_res.to_csv(out_csv, index=False)

    print("\n" + "=" * 85)
    print(f"TỔNG HỢP KẾT QUẢ KIỂM ĐỊNH THỰC NGHIỆM SỐNG TRÊN RSNA PNEUMONIA (N = {len(df_res)}):")
    print(f"  • Checkpoint:                 {weights_path}")
    print(f"  • Tổng thời gian thực thi:   {total_time:.1f}s ({total_time / len(df_res) * 1000:.0f} ms/ảnh)")
    print(f"  • Mean Best Box-IoU:         {df_res['best_box_iou'].mean():.4f}")
    print(f"  • Mean Box-IoU:              {df_res['mean_box_iou'].mean():.4f}")
    print(f"  • Mean Pixel Mask-IoU:       {df_res['mask_iou'].mean():.4f}")
    print(f"  • Tỷ lệ định vị IoU >= 0.10: {df_res['pass_iou_01'].mean() * 100:.1f}%")
    print(f"  • Tỷ lệ định vị IoU >= 0.30: {df_res['pass_iou_03'].mean() * 100:.1f}%")
    print(f"  • Tỷ lệ định vị IoU >= 0.50: {df_res['pass_iou_05'].mean() * 100:.1f}%")
    print(f"  • Năng lượng trong phổi TB:  {df_res['in_lung_energy'].mean() * 100:.2f}%")
    print(f"  • Đã lưu kết quả chi tiết:   {out_csv}")
    print("=" * 85)
    print("\n")

    return df_res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Live WSOL Box-IoU Benchmark on Real RSNA Pneumonia (DICOM)"
    )
    parser.add_argument("--zip-path", type=str, default="dataset/rsna-pneumonia-detection-challenge.zip")
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--out-csv", type=str, default="results/live_rsna_iou_benchmark.csv")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--weights",
        type=str,
        default="checkpoints/best_model.pth",
        help="Checkpoint to benchmark (e.g. checkpoints/best_wsol_finetune.pth).",
    )
    args = parser.parse_args()

    run_live_rsna_benchmark(
        zip_path=args.zip_path,
        n_samples=args.n_samples,
        out_csv=args.out_csv,
        seed=args.seed,
        weights_path=args.weights,
    )
