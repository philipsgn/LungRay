"""
scripts/resize_to_512.py - Dedicated Preprocessing & High-Speed Batch Resizer to 512x512
========================================================================================
Designed for Chest X-ray Datasets (Shenzhen, Montgomery, NIH, COVIDx):
1. Resizes raw high-res radiographs (1024x1024, 2048x2048) to 512x512 using cv2.INTER_AREA.
2. If masks exist, resizes them with cv2.INTER_NEAREST to preserve crisp binary {0, 255} values.
3. Automatically merges Montgomery separate leftMask + rightMask into a complete bilateral lung mask.
4. Uses multi-threading (ThreadPoolExecutor) for maximum I/O throughput.
5. Works seamlessly both locally and inside Kaggle environments (/kaggle/input -> /kaggle/working).

Usage:
    python scripts/resize_to_512.py --input_dir /kaggle/input/chest-x-ray-dataset-montgomery-and-shenzhen --output_dir /kaggle/working/data_512
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np


def find_image_files(input_dir: Path) -> list[Path]:
    """Recursively finds all image files in input directory."""
    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    files = [p for p in input_dir.rglob("*") if p.suffix.lower() in extensions]
    return files


def process_single_image(img_path: Path, output_dir: Path, target_size: int = 512) -> bool:
    """Reads, resizes and writes a single radiograph."""
    try:
        # Determine relative path structure or filename
        img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return False

        # Use INTER_AREA for high-quality downsampling without aliasing
        h, w = img.shape[:2]
        if (h, w) != (target_size, target_size):
            resized = cv2.resize(img, (target_size, target_size), interpolation=cv2.INTER_AREA)
        else:
            resized = img

        out_path = output_dir / "images" / f"{img_path.stem}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), resized)
        return True
    except Exception as exc:
        print(f"[!] Error processing {img_path}: {exc}")
        return False


def process_montgomery_masks(montgomery_dir: Path, output_dir: Path, target_size: int = 512) -> int:
    """
    Finds and merges Montgomery leftMask and rightMask pairs into unified lung masks.
    Example: MCUCXR_0001_0_leftMask.png + MCUCXR_0001_0_rightMask.png -> MCUCXR_0001_0.png
    """
    masks_out = output_dir / "masks"
    masks_out.mkdir(parents=True, exist_ok=True)
    count = 0

    left_masks = list(montgomery_dir.rglob("*leftMask.png"))
    for left_p in left_masks:
        stem_base = left_p.name.replace("_leftMask.png", "")
        right_p = left_p.parent / f"{stem_base}_rightMask.png"
        if not right_p.exists():
            # Try searching anywhere in parent directory
            matches = list(montgomery_dir.rglob(f"{stem_base}_rightMask.png"))
            if matches:
                right_p = matches[0]

        left_img = cv2.imread(str(left_p), cv2.IMREAD_GRAYSCALE)
        if left_img is None:
            continue

        if right_p.exists():
            right_img = cv2.imread(str(right_p), cv2.IMREAD_GRAYSCALE)
            merged = cv2.bitwise_or(left_img, right_img)
        else:
            merged = left_img

        # Resize mask using NEAREST interpolation to preserve strictly binary edges
        merged_resized = cv2.resize(merged, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
        merged_bin = ((merged_resized > 127).astype(np.uint8)) * 255

        out_file = masks_out / f"{stem_base}.png"
        cv2.imwrite(str(out_file), merged_bin)
        count += 1

    return count


def process_dataset(input_dir: str | Path, output_dir: str | Path, target_size: int = 512, workers: int = 4):
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    images_out = output_path / "images"
    images_out.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" LUNGRAY DATASET RESIZER (Target: 512x512)")
    print(f" Input : {input_path}")
    print(f" Output: {output_path}")
    print("=" * 70)

    # 1. Collect all CXR image files (exclude masks)
    all_files = find_image_files(input_path)
    cxr_files = [
        f for f in all_files
        if not any(k in f.name.lower() for k in ["mask", "leftmask", "rightmask"])
    ]

    print(f"[*] Found {len(cxr_files)} raw radiographs to resize.")
    if not cxr_files:
        print("[!] No image files found! Check your input_dir path.")
        return

    # 2. Resize CXR images in parallel
    success_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_single_image, f, output_path, target_size)
            for f in cxr_files
        ]
        for idx, f in enumerate(futures):
            if f.result():
                success_count += 1
            if (idx + 1) % 100 == 0 or (idx + 1) == len(cxr_files):
                print(f"    Resized [{idx + 1}/{len(cxr_files)}] images...")

    print(f"[✓] Successfully resized {success_count}/{len(cxr_files)} CXR images to {target_size}x{target_size}.")

    # 3. Check and process masks if present
    mask_files = [f for f in all_files if "mask" in f.name.lower()]
    if mask_files:
        print(f"[*] Found {len(mask_files)} mask files. Processing binary masks...")
        montgomery_count = process_montgomery_masks(input_path, output_path, target_size)
        if montgomery_count > 0:
            print(f"[✓] Merged & resized {montgomery_count} Montgomery bilateral lung masks.")

        # Also copy/resize standard single masks (e.g. Shenzhen manual masks)
        single_masks = [
            f for f in mask_files
            if not f.name.endswith("_leftMask.png") and not f.name.endswith("_rightMask.png")
        ]
        masks_out = output_path / "masks"
        masks_out.mkdir(parents=True, exist_ok=True)
        single_count = 0
        for m_path in single_masks:
            m_img = cv2.imread(str(m_path), cv2.IMREAD_GRAYSCALE)
            if m_img is not None:
                m_res = cv2.resize(m_img, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
                m_bin = ((m_res > 127).astype(np.uint8)) * 255
                # Normalise name (remove _mask suffix if present to match image stem)
                target_stem = m_path.stem.replace("_mask", "")
                cv2.imwrite(str(masks_out / f"{target_stem}.png"), m_bin)
                single_count += 1
        if single_count > 0:
            print(f"[✓] Processed & resized {single_count} single lung masks.")

    print(f"\n[✓] Done! 512x512 dataset ready at: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Batch resize Chest X-ray dataset to 512x512")
    parser.add_argument("--input_dir", type=str, default="/kaggle/input", help="Source dataset path")
    parser.add_argument("--output_dir", type=str, default="/kaggle/working/data_512", help="Target output path")
    parser.add_argument("--size", type=int, default=512, help="Target spatial resolution (default 512)")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel worker threads")
    
    # Use parse_known_args() to safely ignore Colab/Jupyter kernel flags (-f, --HistoryManager, etc.)
    args, unknown = parser.parse_known_args()

    # Auto-detect if input_dir doesn't exist directly (common in Kaggle/Colab)
    in_path = Path(args.input_dir)
    if not in_path.exists():
        # Check /content for Colab or search /kaggle/input
        alternatives = [
            Path("/content"),
            Path("/kaggle/input"),
            Path("data"),
        ]
        for alt in alternatives:
            if alt.exists():
                matches = list(alt.glob("*montgomery*")) + list(alt.glob("*shenzhen*"))
                if matches:
                    in_path = matches[0]
                    print(f"[*] Auto-detected input dataset at: {in_path}")
                    break

    process_dataset(in_path, args.output_dir, target_size=args.size, workers=args.workers)


if __name__ == "__main__":
    main()
