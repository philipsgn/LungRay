#!/usr/bin/env python3
"""
scripts/evaluate_live_vindr.py - Live WSOL Box-IoU Benchmark on Real VinDr-CXR
=============================================================================
Inviolable Constraint 4 (Ràng buộc sống còn số 4):
- Bounding Box annotations from VinDr-CXR are STRICTLY used for quantitative
  evaluation (IoU), NEVER for training.

Inviolable Constraint 7 (Ràng buộc sống còn số 7):
- 100% Live Inference: Streams real images directly from dataset/vinbigdata.zip,
  runs MultiScaleGradCAMPlusPlus on checkpoints/best_model.pth, and computes
  authentic geometric Box-IoU vs Vietnamese radiologist annotations. Zero simulation.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
import zipfile
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
import pandas as pd
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

VINDR_TO_NIH: Dict[str, Tuple[str, int]] = {
    "Cardiomegaly": ("Cardiomegaly", 1),
    "Pleural effusion": ("Effusion", 2),
    "Infiltration": ("Infiltration", 3),
    "Pneumothorax": ("Pneumothorax", 7),
    "Consolidation": ("Consolidation", 8),
    "Atelectasis": ("Atelectasis", 0),
    "Pulmonary fibrosis": ("Fibrosis", 11),
    "Pleural thickening": ("Pleural_Thickening", 12),
}


def load_model(weights_path: str = "checkpoints/best_model.pth", device: torch.device = torch.device("cpu")) -> MultiTaskChestXrayNet:
    model = MultiTaskChestXrayNet(
        backbone_name="densenet121",
        pretrained=False,
        img_size=512,
        num_classes_a=14,
        num_classes_b=1,
        num_classes_c=1,
    )
    if os.path.exists(weights_path):
        print(f"[*] Nạp trọng số mô hình từ {weights_path}...")
        state = torch.load(weights_path, map_location=device, weights_only=False)
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        elif isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        model.load_state_dict(state)
    else:
        raise FileNotFoundError(f"Không tìm thấy checkpoint tại {weights_path}")

    model.to(device)
    model.eval()
    return model


def sample_vindr_positive_cases(zf: zipfile.ZipFile, target_total: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """Reads train.csv and selects a balanced sample of verified positive cases."""
    print("[*] Đang đọc siêu dữ liệu vinbigdata/train.csv từ zip...")
    with zf.open("vinbigdata/train.csv") as f:
        df = pd.read_csv(f)

    # Filter to supported classes with valid bounding boxes
    valid_df = df[df["class_name"].isin(VINDR_TO_NIH.keys())].copy()
    valid_df = valid_df.dropna(subset=["x_min", "y_min", "x_max", "y_max"])

    # Group annotations by image_id and class_name
    grouped = valid_df.groupby(["image_id", "class_name"])
    unique_cases = list(grouped.groups.keys())

    np.random.seed(seed)
    np.random.shuffle(unique_cases)

    # Stratified selection
    per_class_limit = max(5, target_total // len(VINDR_TO_NIH) + 2)
    selected_cases: List[Tuple[str, str]] = []
    class_counts: Dict[str, int] = {c: 0 for c in VINDR_TO_NIH.keys()}

    for img_id, cname in unique_cases:
        if class_counts[cname] < per_class_limit and len(selected_cases) < target_total:
            selected_cases.append((img_id, cname))
            class_counts[cname] += 1

    # If still below target, fill with any remaining cases
    if len(selected_cases) < target_total:
        for img_id, cname in unique_cases:
            if (img_id, cname) not in selected_cases and len(selected_cases) < target_total:
                selected_cases.append((img_id, cname))

    print(f"[*] Đã chọn {len(selected_cases)} ca dương tính phân tầng:")
    for cname, cnt in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"    - {cname:<20}: {cnt} ca")

    samples: List[Dict[str, Any]] = []
    for img_id, cname in selected_cases:
        sub_df = valid_df[(valid_df["image_id"] == img_id) & (valid_df["class_name"] == cname)]
        nih_disease, nih_idx = VINDR_TO_NIH[cname]
        orig_w = float(sub_df["width"].iloc[0])
        orig_h = float(sub_df["height"].iloc[0])

        boxes = []
        for _, row in sub_df.iterrows():
            boxes.append([float(row["x_min"]), float(row["y_min"]), float(row["x_max"]), float(row["y_max"])])

        samples.append({
            "image_id": img_id,
            "vindr_class": cname,
            "nih_disease": nih_disease,
            "nih_idx": nih_idx,
            "orig_width": orig_w,
            "orig_height": orig_h,
            "gt_boxes": boxes,
        })

    return samples


def run_live_vindr_benchmark(
    zip_path: str = "dataset/vinbigdata.zip",
    n_samples: int = 100,
    out_csv: str = "results/live_vindr_iou_benchmark.csv",
    seed: int = 42,
) -> pd.DataFrame:
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Không tìm thấy file zip VinDr tại {zip_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Sử dụng thiết bị tính toán: {device}")

    model = load_model("checkpoints/best_model.pth", device=device)
    explainer = MultiScaleGradCAMPlusPlus(model)
    segmenter = LungSegmenter()
    audit_engine = ShortcutAuditEngine(segmenter)
    transform = get_val_transforms(img_size=512)

    with zipfile.ZipFile(zip_path, "r") as zf:
        samples = sample_vindr_positive_cases(zf, target_total=n_samples, seed=seed)

        records: List[Dict[str, Any]] = []
        start_time = time.time()
        print(f"\n[*] BẮT ĐẦU CHẠY SUY LUẬN SỐNG TRÊN {len(samples)} MẪU VINDR-CXR (100% REAL IMAGES)...")
        print("=" * 85)
        print(f"{'STT':<4} | {'Disease':<16} | {'Prob':<6} | {'Best IoU':<9} | {'Mean IoU':<9} | {'In-Lung':<8} | {'Latency':<8}")
        print("=" * 85)

        for idx, sample in enumerate(samples, 1):
            t0 = time.time()
            img_id = sample["image_id"]
            cname = sample["vindr_class"]
            nih_disease = sample["nih_disease"]
            nih_idx = sample["nih_idx"]
            orig_w = sample["orig_width"]
            orig_h = sample["orig_height"]
            gt_boxes = sample["gt_boxes"]

            zip_internal_path = f"vinbigdata/train/{img_id}.png"
            img_bytes = zf.read(zip_internal_path)
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(pil_img)

            # Preprocess tensor (1, 3, 512, 512)
            transformed = transform(image=img_np)["image"]
            tensor = transformed.unsqueeze(0).to(device)

            # Model prediction
            with torch.no_grad():
                logits = model(tensor, task_id="head_a")["head_a"]
                prob = float(torch.sigmoid(logits)[0, nih_idx].item())

            # Real Multi-Scale Grad-CAM++
            raw_heatmap = explainer.generate(
                tensor,
                head_name="head_a",
                target_class_idx=nih_idx,
                fusion_weights=(0.4, 0.6),
            )

            # Generate anatomical lung mask
            lung_mask = segmenter.predict_mask(img_np)
            if lung_mask.shape != (512, 512):
                lung_mask = cv2.resize(lung_mask.astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST)

            if nih_disease.lower() == "cardiomegaly":
                kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
                closed_mask = cv2.morphologyEx(lung_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel_close)
                kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
                effective_mask = cv2.dilate(closed_mask, kernel_dilate, iterations=1)
            else:
                kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
                effective_mask = cv2.dilate(lung_mask.astype(np.uint8), kernel_dilate, iterations=1)

            in_lung_ratio = audit_engine.compute_in_lung_ratio(raw_heatmap, effective_mask)

            # Scale GT boxes from original resolution to 512x512
            gt_scaled = []
            for b in gt_boxes:
                gx1 = (b[0] / orig_w) * 512.0
                gy1 = (b[1] / orig_h) * 512.0
                gx2 = (b[2] / orig_w) * 512.0
                gy2 = (b[3] / orig_h) * 512.0
                gt_scaled.append([gx1, gy1, gx2, gy2])

            # Adaptive Binarization & Box Extraction
            bin_mask = adaptive_binarize(raw_heatmap, lung_mask=effective_mask, alpha=0.45)
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
            records.append({
                "sample_idx": idx,
                "image_id": img_id,
                "vindr_class": cname,
                "nih_disease": nih_disease,
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
            })

            print(
                f"{idx:<4} | {nih_disease:<16} | {prob*100:>5.1f}% | {best_box_iou:>8.4f}  | {mean_box_iou:>8.4f}  | {in_lung_ratio*100:>6.1f}% | {elapsed_ms:>6.0f}ms"
            )

    explainer.remove_hooks()
    total_time = time.time() - start_time

    df_res = pd.DataFrame(records)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df_res.to_csv(out_csv, index=False)

    print("\n" + "=" * 85)
    print("📊 TỔNG HỢP KẾT QUẢ KIỂM ĐỊNH THỰC NGHIỆM SỐNG TRÊN VINDR-CXR (N = %d):" % len(df_res))
    print(f"  • Tổng thời gian thực thi:    {total_time:.1f}s ({total_time/len(df_res)*1000:.0f} ms/ảnh)")
    print(f"  • Mean Best Box-IoU:         {df_res['best_box_iou'].mean():.4f}")
    print(f"  • Mean Box-IoU:              {df_res['mean_box_iou'].mean():.4f}")
    print(f"  • Mean Pixel Mask-IoU:       {df_res['mask_iou'].mean():.4f}")
    print(f"  • Tỷ lệ định vị IoU >= 0.10: {df_res['pass_iou_01'].mean()*100:.1f}%")
    print(f"  • Tỷ lệ định vị IoU >= 0.30: {df_res['pass_iou_03'].mean()*100:.1f}%")
    print(f"  • Tỷ lệ định vị IoU >= 0.50: {df_res['pass_iou_05'].mean()*100:.1f}%")
    print(f"  • Năng lượng trong phổi TB:   {df_res['in_lung_energy'].mean()*100:.2f}%")
    print(f"  • Đã lưu kết quả chi tiết:    {out_csv}")
    print("=" * 85)

    # Per-disease breakdown
    print("\n📈 CHI TIẾT THEO TỪNG BỆNH LÝ TRÊN PHIM X-QUANG VIỆT NAM:")
    grouped_df = df_res.groupby("nih_disease").agg({
        "best_box_iou": ["count", "mean"],
        "pass_iou_03": "mean",
        "in_lung_energy": "mean",
    })
    grouped_df.columns = ["Số ca", "Mean Best-IoU", "Tỷ lệ IoU>=0.3", "In-Lung Energy"]
    grouped_df["Tỷ lệ IoU>=0.3"] = grouped_df["Tỷ lệ IoU>=0.3"] * 100.0
    grouped_df["In-Lung Energy"] = grouped_df["In-Lung Energy"] * 100.0
    print(grouped_df.round(3).to_string())
    print("\n")

    return df_res


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live WSOL Box-IoU Benchmark on Real VinDr-CXR")
    parser.add_argument("--zip-path", type=str, default="dataset/vinbigdata.zip")
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--out-csv", type=str, default="results/live_vindr_iou_benchmark.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_live_vindr_benchmark(
        zip_path=args.zip_path,
        n_samples=args.n_samples,
        out_csv=args.out_csv,
        seed=args.seed,
    )

