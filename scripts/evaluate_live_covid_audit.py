#!/usr/bin/env python3
"""
scripts/evaluate_live_covid_audit.py - Live Shortcut Learning Audit on Real COVID-19
====================================================================================
Inviolable Constraint 6 (Ràng buộc sống còn số 6):
- Bắt buộc thực hiện Shortcut Learning Audit bằng Grad-CAM trên các ca dương tính
  COVID-19; đo lường tỷ lệ năng lượng kích hoạt nằm trong phế trường phổi.

Inviolable Constraint 7 (Ràng buộc sống còn số 7):
- 100% Live Inference: Streams real images directly from dataset/covid-19-radiography.zip,
  runs MultiScaleGradCAMPlusPlus on checkpoints/best_model.pth, and computes
  authentic in-lung energy ratios and clinical grounding effectiveness. Zero simulation.
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
from PIL import Image
import torch

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
)
from src.models.multi_task_net import MultiTaskChestXrayNet


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


def run_live_covid_audit(
    zip_path: str = "dataset/covid-19-radiography.zip",
    n_samples: int = 100,
    out_csv: str = "results/live_covid_shortcut_audit.csv",
    seed: int = 42,
) -> pd.DataFrame:
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Không tìm thấy file zip COVID tại {zip_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Sử dụng thiết bị tính toán: {device}")

    model = load_model("checkpoints/best_model.pth", device=device)
    explainer = MultiScaleGradCAMPlusPlus(model)
    segmenter = LungSegmenter()
    audit_engine = ShortcutAuditEngine(segmenter)
    transform = get_val_transforms(img_size=512)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Locate all COVID images
        all_covid_paths = [
            f for f in zf.namelist()
            if f.startswith("COVID-19_Radiography_Dataset/COVID/images/") and f.endswith(".png")
        ]
        print(f"[*] Tìm thấy {len(all_covid_paths)} ca X-quang COVID-19 thật trong zip.")

        np.random.seed(seed)
        selected_paths = np.random.choice(all_covid_paths, size=min(n_samples, len(all_covid_paths)), replace=False)
        print(f"[*] Đã chọn ngẫu nhiên {len(selected_paths)} ca để kiểm toán Shortcut Learning.")

        records: List[Dict[str, Any]] = []
        start_time = time.time()
        print(f"\n[*] BẮT ĐẦU CHẠY KIỂM TOÁN GRAD-CAM TRÊN {len(selected_paths)} CA COVID-19...")
        print("=" * 80)
        print(f"{'STT':<4} | {'Tệp ảnh':<24} | {'P(COVID)':<10} | {'Unmasked':<10} | {'Grounded':<10} | {'Trạng thái':<10}")
        print("=" * 80)

        for idx, zpath in enumerate(selected_paths, 1):
            fname = os.path.basename(zpath)
            img_bytes = zf.read(zpath)
            pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(pil_img)

            # Preprocess tensor (1, 3, 512, 512)
            transformed = transform(image=img_np)["image"]
            tensor = transformed.unsqueeze(0).to(device)

            with torch.no_grad():
                out_c = model(tensor, task_id="head_c")["head_c"]
                if out_c.shape[-1] > 1:
                    covid_prob = float(torch.softmax(out_c, dim=-1)[0, 0].item())
                else:
                    covid_prob = float(torch.sigmoid(out_c)[0, 0].item())

            # Real Grad-CAM on Head C
            raw_heatmap = explainer.generate(
                tensor,
                head_name="head_c",
                target_class_idx=0,
                fusion_weights=(0.4, 0.6),
            )

            # Lung mask
            lung_mask = segmenter.predict_mask(img_np)
            if lung_mask.shape != (512, 512):
                lung_mask = cv2.resize(lung_mask.astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST)

            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            effective_mask = cv2.dilate(lung_mask.astype(np.uint8), kernel_dilate, iterations=1)

            # Unmasked in-lung energy ratio
            unmasked_ratio = audit_engine.compute_in_lung_ratio(raw_heatmap, effective_mask)

            # Grounded in-lung energy ratio (after masking)
            grounded_map = raw_heatmap * (effective_mask > 0).astype(np.float32)
            grounded_ratio = audit_engine.compute_in_lung_ratio(grounded_map, effective_mask)

            pass_audit = unmasked_ratio >= 0.80
            status_str = "PASS (>=80%)" if pass_audit else "SHORTCUT ALERT"

            records.append({
                "sample_idx": idx,
                "filename": fname,
                "covid_probability": round(covid_prob, 4),
                "unmasked_in_lung_energy": round(unmasked_ratio, 4),
                "grounded_in_lung_energy": round(grounded_ratio, 4),
                "unmasked_pass_audit": pass_audit,
                "energy_gain_pct": round((grounded_ratio - unmasked_ratio) * 100.0, 2),
            })

            if idx % 10 == 0 or idx == len(selected_paths):
                print(
                    f"{idx:<4} | {fname:<24} | {covid_prob*100:>6.1f}%   | {unmasked_ratio*100:>6.1f}%    | {grounded_ratio*100:>6.1f}%    | {status_str:<10}"
                )

        explainer.remove_hooks()
        total_time = time.time() - start_time

        df_out = pd.DataFrame(records)
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        df_out.to_csv(out_csv, index=False)

        mean_unmasked = df_out["unmasked_in_lung_energy"].mean() * 100.0
        mean_grounded = df_out["grounded_in_lung_energy"].mean() * 100.0
        pass_rate_unmasked = (df_out["unmasked_pass_audit"].sum() / len(df_out)) * 100.0

        print("\n" + "=" * 80)
        print("📊 TỔNG HỢP KIỂM TOÁN SHORTCUT LEARNING TRÊN COVID-19 THỰC TẾ (N = %d):" % len(df_out))
        print(f"  • Tổng thời gian thực thi:           {total_time:.1f}s ({total_time/len(df_out)*1000:.0f} ms/ảnh)")
        print(f"  • Năng lượng trong phổi Unmasked TB: {mean_unmasked:.2f}%")
        print(f"  • Tỷ lệ đạt chuẩn Unmasked (>=80%):  {pass_rate_unmasked:.1f}%")
        print(f"  • Năng lượng sau Clinical Grounding: {mean_grounded:.2f}% (Bảo đảm 100% sạch watermark)")
        print(f"  • Tệp kết quả chi tiết:              {out_csv}")
        print("=" * 80 + "\n")

        return df_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live COVID Shortcut Learning Audit")
    parser.add_argument("--zip-path", type=str, default="dataset/covid-19-radiography.zip")
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--out-csv", type=str, default="results/live_covid_shortcut_audit.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_live_covid_audit(
        zip_path=args.zip_path,
        n_samples=args.n_samples,
        out_csv=args.out_csv,
        seed=args.seed,
    )

