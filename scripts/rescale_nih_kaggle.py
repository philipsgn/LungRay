"""
LungRay - NIH ChestX-ray14 High-Throughput 512x512 Rescaling Script
===================================================================
Executes on Kaggle Cloud to downscale 112,120 images from 1024x1024
to 512x512 using cv2.INTER_AREA and multi-process parallelism.

Outputs a clean production folder ready to be saved as Kaggle Dataset:
'lungray-nih-512' (~12-14 GB).
"""
import os
import sys
import shutil
import glob
import time
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Optional
import cv2
import pandas as pd
from tqdm import tqdm


TARGET_SIZE = (512, 512)
PNG_COMPRESSION = 4


def find_nih_root() -> Tuple[str, str]:
    """Finds NIH image directory and Data_Entry_2017.csv on Kaggle or local."""
    potential_roots = [
        "/kaggle/input/datasets/nih-chest-xrays/data",
        "/kaggle/input/datasets/nih-chest-xrays",
        "/kaggle/input/nih-chest-xrays/data",
        "/kaggle/input/nih-chest-xrays",
        "/kaggle/input/data",
        "dataset/nih-chestXray-14",
        "dataset/nih-chestXray-14/data"
    ]
    img_dir = ""
    csv_path = ""

    for root in potential_roots:
        if os.path.exists(root):
            # Check for chunks or images/
            chunks = glob.glob(os.path.join(root, "images_*", "images"))
            if not chunks:
                chunks = glob.glob(os.path.join(root, "*", "images_*", "images"))
            if not chunks and os.path.exists(os.path.join(root, "images")):
                chunks = [os.path.join(root, "images")]
            
            if chunks:
                img_dir = root
                break

    for root in potential_roots:
        cand_csv = os.path.join(root, "Data_Entry_2017.csv")
        if os.path.exists(cand_csv):
            csv_path = cand_csv
            break
        cand_csv_upper = os.path.join(os.path.dirname(root), "Data_Entry_2017.csv")
        if os.path.exists(cand_csv_upper):
            csv_path = cand_csv_upper
            break

    return img_dir, csv_path


def resize_single_image(args: Tuple[str, str]) -> bool:
    """Worker function for multiprocessing."""
    src_path, dst_path = args
    if os.path.exists(dst_path):
        return True
    try:
        img = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return False
        # If color image or grayscale, INTER_AREA is optimal for downsampling
        resized = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)
        cv2.imwrite(dst_path, resized, [cv2.IMWRITE_PNG_COMPRESSION, PNG_COMPRESSION])
        return True
    except Exception as e:
        return False


def main():
    print("=" * 70)
    print("🩺 LUNGRAY NIH CHESTX-RAY14 RESCALING ENGINE (512x512)")
    print("=" * 70)

    nih_root, csv_path = find_nih_root()
    if not nih_root:
        print("[ERROR] NIH ChestX-ray14 directory not found! Ensure dataset is mounted.")
        sys.exit(1)

    output_root = "/kaggle/working/nih_512" if os.path.exists("/kaggle") else "data/processed/nih_512"
    output_images_dir = os.path.join(output_root, "images")
    os.makedirs(output_images_dir, exist_ok=True)

    print(f"[*] Detected NIH Root: {nih_root}")
    print(f"[*] Metadata CSV: {csv_path or 'Not found'}")
    print(f"[*] Output Directory: {output_images_dir}")

    # Index all input images
    print("[*] Scanning NIH input images across all chunks...")
    input_files = []
    for root, _, files in os.walk(nih_root):
        for f in files:
            if f.lower().endswith(".png"):
                input_files.append(os.path.join(root, f))

    total_images = len(input_files)
    print(f"[OK] Found {total_images:,} images to process.")
    if total_images == 0:
        print("[ERROR] No images found!")
        sys.exit(1)

    # Prepare job list
    jobs = []
    for src in input_files:
        fname = os.path.basename(src)
        dst = os.path.join(output_images_dir, fname)
        jobs.append((src, dst))

    # Multiprocessing execution
    num_workers = min(os.cpu_count() or 4, 8)
    print(f"[*] Launching ProcessPoolExecutor with {num_workers} workers...")
    start_time = time.time()
    success_count = 0

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for result in tqdm(executor.map(resize_single_image, jobs, chunksize=100), total=len(jobs), desc="Rescaling NIH 512x512"):
            if result:
                success_count += 1

    elapsed = time.time() - start_time
    print(f"\n[OK] Rescaling completed in {elapsed/60:.2f} minutes ({total_images/max(elapsed, 1):.1f} img/s).")
    print(f"[OK] Successfully saved: {success_count:,} / {total_images:,} images.")

    # Copy metadata and splits
    if csv_path and os.path.exists(csv_path):
        dst_csv = os.path.join(output_root, "Data_Entry_2017.csv")
        shutil.copy2(csv_path, dst_csv)
        print(f"[OK] Copied {os.path.basename(csv_path)} -> {dst_csv}")

    splits_cand = "data/splits/patient_splits.csv"
    if os.path.exists(splits_cand):
        dst_splits = os.path.join(output_root, "patient_splits.csv")
        shutil.copy2(splits_cand, dst_splits)
        print(f"[OK] Copied patient_splits.csv -> {dst_splits}")

    # Report size
    total_size_gb = sum(os.path.getsize(os.path.join(output_images_dir, f)) for f in os.listdir(output_images_dir)) / (1024**3)
    print(f"[SUMMARY] Total Output Size: {total_size_gb:.2f} GB")
    print("\n[NEXT STEP ON KAGGLE]:")
    print("1. Go to Kaggle Notebook Output pane.")
    print("2. Click '+ Save Version' -> 'Quick Save' or 'Save & Run All'.")
    print("3. In the right pane under Output, click the three dots '...' on 'nih_512' and select 'Create New Dataset'.")
    print("4. Set dataset title: 'lungray-nih-512' and make it Public or Private.")
    print("=" * 70)


if __name__ == "__main__":
    main()
