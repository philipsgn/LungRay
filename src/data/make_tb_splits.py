"""
LungRay Stratified Split Generator for Tuberculosis (TB) (src/data/make_tb_splits.py)
===================================================================================
Generates tb_splits.csv with 70% Train, 10% Val, 20% Test stratified by diagnosis (TB vs Normal).
"""
import os
import argparse
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def generate_tb_split(
    meta_dir: str = "dataset/tb_meta/TB_Chest_Radiography_Database",
    output_csv: str = "dataset/splits/tb_splits.csv",
    seed: int = 42
) -> pd.DataFrame:
    tb_path = os.path.join(meta_dir, "Tuberculosis.metadata.xlsx")
    norm_path = os.path.join(meta_dir, "Normal.metadata.xlsx")

    records = []
    if os.path.exists(tb_path):
        df_tb = pd.read_excel(tb_path)
        for _, row in df_tb.iterrows():
            name = str(row["FILE NAME"]).strip()
            if not name.lower().endswith(".png"):
                name = f"{name}.png"
            records.append({"Image Index": name, "label": 1, "diagnosis": "Tuberculosis"})

    if os.path.exists(norm_path):
        df_norm = pd.read_excel(norm_path)
        for _, row in df_norm.iterrows():
            name = str(row["FILE NAME"]).strip()
            if not name.lower().endswith(".png"):
                name = f"{name}.png"
            records.append({"Image Index": name, "label": 0, "diagnosis": "Normal"})

    df = pd.DataFrame(records)
    print(f"Total TB Database images: {len(df)}")
    print(df["diagnosis"].value_counts())

    # Stratified split: Train (70%), Temp (30%)
    train_df, temp_df = train_test_split(df, test_size=0.30, random_state=seed, stratify=df["label"])
    val_df, test_df = train_test_split(temp_df, test_size=0.6667, random_state=seed, stratify=temp_df["label"])

    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()

    train_df["split"] = "train"
    val_df["split"] = "val"
    test_df["split"] = "test"

    out_df = pd.concat([train_df, val_df, test_df]).sort_index()

    for s in ["train", "val", "test"]:
        sub = out_df[out_df["split"] == s]
        tb_pct = (sub["label"] == 1).mean() * 100
        print(f"  - {s.upper()}: {len(sub)} images ({tb_pct:.1f}% TB positive)")

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    out_df.to_csv(output_csv, index=False)
    print(f"[PASS] Saved: {output_csv}")
    return out_df


if __name__ == "__main__":
    generate_tb_split()
