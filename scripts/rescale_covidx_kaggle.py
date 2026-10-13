"""
LungRay - COVIDx CXR-4 Benchmark High-Throughput 512x512 Letterboxing Script
=============================================================================
Executes on Kaggle Cloud to standardize 16,400+ images from COVIDx CXR-4
to 512x512 using Medical Letterboxing (LongestMaxSize + Black Border Pad)
preserving thoracic organ geometry without anatomical stretching.

Outputs a clean production folder ready to be saved as Kaggle Dataset:
'lungray-covidx-512' (~2 GB).
"""
import os
import sys
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Tuple, List, Optional
import cv2
import pandas as pd
from tqdm import tqdm


TARGET_SIZE = 512
PNG_COMPRESSION = 4


def find_covidx_root() -> Tuple[str, str, str]:
    """Finds COVIDx CXR-4 root, train.txt and test.txt."""
    potential_roots = [
        "/kaggle/input/covidx-cxr2",
        "/kaggle/input/covidx-cxr-4",
        "dataset/covidx-cxr2"
    ]
    covid_root = ""
    train_txt = ""
    test_txt = ""

    for root in potential_roots:
        if os.path.exists(root):
            cand_train = os.path.join(root, "train.txt")
            cand_test = os.path.join(root, "test.txt")
            if os.path.exists(cand_train) and os.path.exists(cand_test):
                covid_root = root
                train_txt = cand_train
                test_txt = cand_test
                break

    return covid_root, train_txt, test_txt


def letterbox_image(img: cv2.Mat, target_size: int = 512) -> cv2.Mat:
    """Medical Letterboxing: Scales longest edge to target_size, pads with black (0)."""
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return img

    # Compute scaling factor
    scale = target_size / max(h, w)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    # Resize with INTER_AREA (optimal downsampling)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Compute padding
    pad_top = (target_size - new_h) // 2
    pad_bottom = target_size - new_h - pad_top
    pad_left = (target_size - new_w) // 2
    pad_right = target_size - new_w - pad_left

    # Symmetric constant black border
    padded = cv2.copyMakeBorder(
        resized,
        pad_top, pad_bottom, pad_left, pad_right,
        borderType=cv2.BORDER_CONSTANT,
        value=0
    )
    return padded


def process_single_image(args: Tuple[str, str]) -> bool:
    src_path, dst_path = args
    if os.path.exists(dst_path):
        return True
    try:
        img = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return False
        letterboxed = letterbox_image(img, TARGET_SIZE)
        cv2.imwrite(dst_path, letterboxed, [cv2.IMWRITE_PNG_COMPRESSION, PNG_COMPRESSION])
        return True
    except Exception:
        return False


def main():
    print("=" * 70)
    print("🩺 LUNGRAY COVIDx CXR-4 MEDICAL LETTERBOXING ENGINE (512x512)")
    print("=" * 70)

    covid_root, train_txt, test_txt = find_covidx_root()
    if not covid_root:
        print("[ERROR] COVIDx CXR-4 dataset not found! Mount 'andyczhao/covidx-cxr2'.")
        sys.exit(1)

    output_root = "/kaggle/working/covidx_512" if os.path.exists("/kaggle") else "data/processed/covidx_512"
    os.makedirs(os.path.join(output_root, "train"), exist_ok=True)
    os.makedirs(os.path.join(output_root, "test"), exist_ok=True)

    print(f"[*] Detected COVIDx Root: {covid_root}")
    print(f"[*] Output Directory: {output_root}")

    # Build job list from train.txt and test.txt
    jobs = []
    for split_name, txt_file in [("train", train_txt), ("test", test_txt)]:
        with open(txt_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    filename = parts[1]
                    # Source image can be in root/split_name/filename or root/filename
                    cand1 = os.path.join(covid_root, split_name, filename)
                    cand2 = os.path.join(covid_root, filename)
                    src = cand1 if os.path.exists(cand1) else cand2
                    dst = os.path.join(output_root, split_name, filename)
                    jobs.append((src, dst))

    total_images = len(jobs)
    print(f"[OK] Found {total_images:,} images across train and test sets.")
    if total_images == 0:
        print("[ERROR] No images resolved from txt files!")
        sys.exit(1)

    num_workers = min(os.cpu_count() or 4, 8)
    print(f"[*] Launching ProcessPoolExecutor with {num_workers} workers...")
    start_time = time.time()
    success_count = 0

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for result in tqdm(executor.map(process_single_image, jobs, chunksize=100), total=len(jobs), desc="Letterboxing COVIDx 512x512"):
            if result:
                success_count += 1

    elapsed = time.time() - start_time
    print(f"\n[OK] Letterboxing completed in {elapsed/60:.2f} minutes ({total_images/max(elapsed, 1):.1f} img/s).")
    print(f"[OK] Successfully saved: {success_count:,} / {total_images:,} images.")

    # Copy train.txt and test.txt
    shutil.copy2(train_txt, os.path.join(output_root, "train.txt"))
    shutil.copy2(test_txt, os.path.join(output_root, "test.txt"))
    print("[OK] Copied train.txt and test.txt to output.")

    # Report size
    total_size_mb = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, files in os.walk(output_root)
        for f in files
    ) / (1024**2)
    print(f"[SUMMARY] Total Output Size: {total_size_mb:.2f} MB (~{total_size_mb/1024:.2f} GB)")
    print("\n[NEXT STEP ON KAGGLE]:")
    print("1. Go to Kaggle Notebook Output pane.")
    print("2. Click '+ Save Version' -> 'Quick Save' or 'Save & Run All'.")
    print("3. Click '...' on 'covidx_512' and select 'Create New Dataset'.")
    print("4. Set dataset title: 'lungray-covidx-512'.")
    print("=" * 70)


if __name__ == "__main__":
    main()
