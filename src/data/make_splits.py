"""
LungRay Patient-Level Split Generator (src/data/make_splits.py)
==============================================================
Generates patient_splits.csv for NIH ChestX-ray14 strictly based on Patient ID.

Inviolable Rule (Ràng buộc 2 - Zero Data Leakage):
- Train / Val / Test sets MUST be partitioned strictly by unique Patient ID (70/10/20).
- Random image-level split is STRICTLY FORBIDDEN.
- Assert: Train_patients & Val_patients == empty, Train_patients & Test_patients == empty.
"""
import os
import argparse
from typing import Tuple, List, Set
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def split_nih_by_patient_id(
    df: pd.DataFrame,
    patient_col: str = "Patient ID",
    train_ratio: float = 0.70,
    val_ratio: float = 0.10,
    test_ratio: float = 0.20,
    seed: int = 42
) -> pd.DataFrame:
    """
    Partitions NIH ChestX-ray14 metadata into Train, Val, and Test sets by Patient ID.
    """
    assert np.isclose(train_ratio + val_ratio + test_ratio, 1.0), "Ratios must sum to 1.0"

    unique_patients = df[patient_col].unique()
    print(f"Total unique patients: {len(unique_patients)}")
    print(f"Total total images: {len(df)}")

    # Step 1: Split train vs temp (val + test)
    temp_ratio = val_ratio + test_ratio
    train_patients, temp_patients = train_test_split(
        unique_patients,
        test_size=temp_ratio,
        random_state=seed
    )

    # Step 2: Split temp into val and test
    relative_test_ratio = test_ratio / temp_ratio
    val_patients, test_patients = train_test_split(
        temp_patients,
        test_size=relative_test_ratio,
        random_state=seed
    )

    train_set: Set = set(train_patients)
    val_set: Set = set(val_patients)
    test_set: Set = set(test_patients)

    # Zero Data Leakage Verification
    assert len(train_set & val_set) == 0, "[CRITICAL] Patient leakage detected between Train and Val!"
    assert len(train_set & test_set) == 0, "[CRITICAL] Patient leakage detected between Train and Test!"
    assert len(val_set & test_set) == 0, "[CRITICAL] Patient leakage detected between Val and Test!"
    print("[PASS] Zero Data Leakage verified: No patient ID overlap across any splits.")

    # Assign split column
    patient_to_split = {}
    for p in train_set:
        patient_to_split[p] = "train"
    for p in val_set:
        patient_to_split[p] = "val"
    for p in test_set:
        patient_to_split[p] = "test"

    df_out = df.copy()
    df_out["split"] = df_out[patient_col].map(patient_to_split)

    split_counts = df_out["split"].value_counts(normalize=True)
    print("Image distribution across splits:")
    for split_name, pct in split_counts.items():
        print(f"  - {split_name.upper()}: {pct*100:.2f}% ({len(df_out[df_out['split'] == split_name])} images)")

    return df_out


def main():
    parser = argparse.ArgumentParser(description="Generate Zero-Leakage Patient-Level Split for NIH ChestX-ray14")
    parser.add_argument("--metadata_csv", type=str, default="dataset/Data_Entry_2017.csv", help="Path to Data_Entry_2017.csv")
    parser.add_argument("--output_csv", type=str, default="dataset/splits/patient_splits.csv", help="Output split CSV path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)

    if not os.path.exists(args.metadata_csv):
        print(f"Warning: Metadata file '{args.metadata_csv}' not found.")
        print("Creating mock metadata file with 1,000 synthetic records to demonstrate split logic...")
        # Create reproducible synthetic metadata for testing
        np.random.seed(args.seed)
        synthetic_patients = [f"P_{i:05d}" for i in range(1, 301)]
        records = []
        for img_idx in range(1, 1001):
            records.append({
                "Image Index": f"{img_idx:08d}.png",
                "Finding Labels": "No Finding" if img_idx % 2 == 0 else "Effusion|Infiltration",
                "Patient ID": np.random.choice(synthetic_patients),
                "Patient Age": 45,
                "Patient Gender": "M"
            })
        df = pd.DataFrame(records)
    else:
        print(f"Loading metadata from {args.metadata_csv}...")
        df = pd.read_csv(args.metadata_csv)

    df_split = split_nih_by_patient_id(df, seed=args.seed)
    df_split.to_csv(args.output_csv, index=False)
    print(f"Split file successfully written to: {args.output_csv}")


if __name__ == "__main__":
    main()
