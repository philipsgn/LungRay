"""
LungRay: One-Time Kaggle Cloud Rescaling Utility (scripts/kaggle_rescale_512.py)
=============================================================================
Purpose:
    Rescales NIH ChestX-ray14 (and/or other raw CXR datasets) from 1024x1024 to 512x512
    directly on Kaggle Cloud using multi-processing (4 vCPUs) and cv2.INTER_AREA.
    
Usage in Kaggle Notebook:
    1. Mount raw NIH ChestX-ray14 dataset (e.g. /kaggle/input/data/images*)
    2. Run this script: python kaggle_rescale_512.py
    3. Output will be saved to: /kaggle/working/nih_chestxray14_512/
    4. Click 'Save Version' -> 'Save & Run All' -> Output creates reusable 512x512 dataset (~12GB)
"""
import os
import glob
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import cv2
from tqdm import tqdm


def process_single_image(args):
    """Reads 1024x1024 CXR, rescales to 512x512 with INTER_AREA, and writes output."""
    in_path, out_path = args
    if os.path.exists(out_path):
        return True  # Skip if already processed

    try:
        # Load grayscale
        img = cv2.imread(in_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False

        # cv2.INTER_AREA is optimal for photographic/radiographic downsampling
        resized = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)

        # Save with light compression (PNG compression level 4 for fast I/O)
        cv2.imwrite(out_path, resized, [cv2.IMWRITE_PNG_COMPRESSION, 4])
        return True
    except Exception as e:
        print(f"Error processing {in_path}: {e}")
        return False


def batch_rescale(
    input_pattern: str = "/kaggle/input/data/images*/*.png",
    output_dir: str = "/kaggle/working/nih_chestxray14_512",
    num_workers: int = 4
):
    """Dispatches image resizing across multiple CPU worker processes."""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Scanning for images with pattern: {input_pattern}")
    image_paths = glob.glob(input_pattern)
    if not image_paths:
        # Fallback patterns on Kaggle
        for alt in ["/kaggle/input/data/images*/*/*.png", "/kaggle/input/nih-chest-xrays/images*/*.png"]:
            image_paths = glob.glob(alt)
            if image_paths:
                break

    total_images = len(image_paths)
    print(f"Found {total_images} images to rescale.")
    if total_images == 0:
        print("No images found. Please verify the Kaggle input path.")
        return

    tasks = [
        (p, os.path.join(output_dir, os.path.basename(p)))
        for p in image_paths
    ]

    print(f"Starting parallel execution with {num_workers} workers...")
    start_time = time.time()
    success_count = 0

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for result in tqdm(executor.map(process_single_image, tasks, chunksize=100), total=total_images):
            if result:
                success_count += 1

    elapsed = time.time() - start_time
    print(f"\n[DONE] Successfully processed {success_count}/{total_images} images in {elapsed/60:.2f} minutes.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    batch_rescale()
