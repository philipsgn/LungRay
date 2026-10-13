"""
LungRay Source-Stratified Split Generator for COVID-19 (src/data/make_covid_splits.py)
======================================================================================
Inviolable Constraint (Ràng buộc 3 - Anti-Shortcut Learning):
- COVID-19 Radiography Database aggregates multiple disparate sources:
  * COVID-19: BIMCV (Spain), GitHub (Cohen et al.), Eurorad, SIRM (Italy).
  * Normal & Lung Opacity: RSNA Pneumonia Detection Challenge.
  * Viral Pneumonia: Kermany Pediatric Dataset.
- Simple random split creates severe shortcut learning vulnerability.
- Mandatory: Perform Stratified Split based on (class_name, source) to guarantee
  balanced representation of each source across Train (70%), Val (10%), and Test (20%).
"""
import os
import re
import argparse
from typing import Dict, List
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def extract_source_from_url(url: str) -> str:
    """Extracts original clinical repository source from image URL."""
    u = str(url).lower()
    if "bimcv" in u:
        return "BIMCV"
    elif "github" in u:
        return "GitHub_Cohen"
    elif "eurorad" in u:
        return "Eurorad"
    elif "sirm" in u:
        return "SIRM"
    elif "rsna" in u:
        return "RSNA"
    elif "chest-xray-pneumonia" in u or "mooney" in u or "kermany" in u:
        return "Kermany_Pediatric"
    elif "padchest" in u:
        return "PadChest"
    else:
        return "Other"


def generate_covid_stratified_split(
    meta_dir: str = "dataset/covid19_meta/COVID-19_Radiography_Dataset",
    output_csv: str = "dataset/splits/covid_splits.csv",
    seed: int = 42
) -> pd.DataFrame:
    """
    Parses all metadata excel files, assigns clinical sources, and executes Source-Stratified Split.
    """
    class_files = {
        "COVID": ("COVID.metadata.xlsx", 0),
        "Normal": ("Normal.metadata.xlsx", 1),
        "Lung_Opacity": ("Lung_Opacity.metadata.xlsx", 2),
        "Viral_Pneumonia": ("Viral Pneumonia.metadata.xlsx", 3),
    }

    all_records = []

    for class_name, (filename, label_idx) in class_files.items():
        filepath = os.path.join(meta_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Metadata file not found: {filepath}")

        df_class = pd.read_excel(filepath)
        print(f"Loaded {class_name}: {len(df_class)} records.")

        for _, row in df_class.iterrows():
            file_name = str(row["FILE NAME"]).strip()
            # Standardize file extension
            if not file_name.lower().endswith(".png"):
                file_name = f"{file_name}.png"

            url = row.get("URL", "")
            source = extract_source_from_url(url)

            all_records.append({
                "Image Index": file_name,
                "class_name": class_name,
                "label": label_idx,
                "source": source,
                "original_size": str(row.get("SIZE", "")),
                "url": str(url)
            })

    full_df = pd.DataFrame(all_records)
    print(f"\nTotal COVID-19 Radiography Database images: {len(full_df)}")

    # Composite stratum key: class + source
    full_df["stratum"] = full_df["class_name"] + "_" + full_df["source"]
    print("\nSource distribution per class:")
    print(full_df["stratum"].value_counts())

    # Filter singletons if any (stratum with < 3 samples cannot be split into 3 sets)
    stratum_counts = full_df["stratum"].value_counts()
    valid_strata = stratum_counts[stratum_counts >= 3].index
    
    # Handle rare cases by merging into general class stratum
    full_df.loc[~full_df["stratum"].isin(valid_strata), "stratum"] = full_df["class_name"]

    # Step 1: Split Train (70%) vs Temp (30%)
    train_df, temp_df = train_test_split(
        full_df,
        test_size=0.30,
        random_state=seed,
        stratify=full_df["stratum"]
    )

    # Step 2: Split Temp into Val (10%) and Test (20%)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.6667,  # 0.20 / 0.30 = 2/3
        random_state=seed,
        stratify=temp_df["stratum"]
    )

    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()

    train_df["split"] = "train"
    val_df["split"] = "val"
    test_df["split"] = "test"

    out_df = pd.concat([train_df, val_df, test_df]).sort_index()

    # Verify source stratification consistency
    print("\nSource distribution across splits:")
    for split_name in ["train", "val", "test"]:
        sub = out_df[out_df["split"] == split_name]
        pct = len(sub) / len(out_df) * 100
        print(f"  - {split_name.upper()}: {pct:.2f}% ({len(sub)} images)")

    # Check deviation across sources in COVID class
    covid_train = out_df[(out_df["split"] == "train") & (out_df["class_name"] == "COVID")]
    covid_test = out_df[(out_df["split"] == "test") & (out_df["class_name"] == "COVID")]
    print("\nCOVID class source distribution (Train vs Test):")
    train_dist = covid_train["source"].value_counts(normalize=True)
    test_dist = covid_test["source"].value_counts(normalize=True)
    for src in train_dist.index:
        diff = abs(train_dist.get(src, 0) - test_dist.get(src, 0)) * 100
        print(f"  Source '{src}': Train {train_dist.get(src, 0)*100:.2f}% vs Test {test_dist.get(src, 0)*100:.2f}% (Deviation: {diff:.2f}%)")
        assert diff <= 3.0, f"Source distribution deviation > 3% for {src}"

    print("[PASS] Source-Stratified Split verified! Shortcut Learning mitigated.")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    print(f"Saved: {output_csv}")
    return out_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta_dir", type=str, default="dataset/covid19_meta/COVID-19_Radiography_Dataset")
    parser.add_argument("--output_csv", type=str, default="dataset/splits/covid_splits.csv")
    args = parser.parse_args()
    generate_covid_stratified_split(meta_dir=args.meta_dir, output_csv=args.output_csv)
