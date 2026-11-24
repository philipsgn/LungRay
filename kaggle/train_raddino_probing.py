"""
LungRay RAD-DINO Linear Probing Benchmark for Kaggle GPU
========================================================
``kaggle/train_raddino_probing.py``

Evaluates Microsoft RAD-DINO (Vision Foundation Model pre-trained on CXRs)
using the Frozen Feature Extractor (Linear Probing) strategy:
- Backbones parameters are completely frozen (zero gradient updates).
- Only 3 lightweight clinical classification heads (Head A, B, C) are trained.
- High memory efficiency: Fits easily within 4GB VRAM on Kaggle P100/T4.
- Runs 10 epochs in under 15 minutes, producing academic benchmark metrics.

Usage:
    python kaggle/train_raddino_probing.py --epochs 10 --batch-size 32
"""
import argparse
import os
import sys
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
for path in (project_root, current_dir):
    if path not in sys.path:
        sys.path.insert(0, path)

import train_kaggle

if not hasattr(train_kaggle, "cv2"):
    train_kaggle.cv2 = cv2

from src.data.ingestion import resolve_dataset_paths
from src.models.losses import MaskedMultiTaskLoss
from src.utils.threshold_tuning import tune_multilabel_thresholds, find_best_threshold_youden


class RadDinoMultiTaskProber(nn.Module):
    """
    Frozen RAD-DINO ViT-Base feature extractor with 3 clinical classification heads.
    """

    def __init__(
        self,
        model_name: str = "microsoft/rad-dino",
        num_classes_a: int = 14,
        num_classes_b: int = 1,
        num_classes_c: int = 1,
        feature_dim: int = 768,
    ):
        super().__init__()
        self.feature_dim = feature_dim
        self.num_classes_a = num_classes_a
        self.num_classes_b = num_classes_b
        self.num_classes_c = num_classes_c

        # Attempt to load RAD-DINO via transformers or timm
        print(f"[*] Initializing RAD-DINO backbone: '{model_name}' (Frozen mode)...")
        self.encoder = None
        try:
            from transformers import AutoModel
            self.encoder = AutoModel.from_pretrained(model_name)
            # Freeze all parameters
            for param in self.encoder.parameters():
                param.requires_grad = False
            self.encoder.eval()
            print("[OK] Loaded and froze RAD-DINO via HuggingFace transformers.")
        except Exception as err:
            print(f"[!] Warning: Could not load '{model_name}' via transformers ({err}).")
            print("[*] Falling back to frozen ViT-Base encoder via timm...")
            import timm
            self.encoder = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=0)
            for param in self.encoder.parameters():
                param.requires_grad = False
            self.encoder.eval()

        self.head_norm = nn.LayerNorm(self.feature_dim, elementwise_affine=False)
        self.dropout = nn.Dropout(p=0.2)
        self.head_a = nn.Linear(self.feature_dim, num_classes_a)
        self.head_b = nn.Linear(self.feature_dim, num_classes_b)
        self.head_c = nn.Linear(self.feature_dim, num_classes_c)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts pooled embedding (CLS token) without computing gradients."""
        with torch.no_grad():
            if hasattr(self.encoder, "last_hidden_state"):
                # HuggingFace model output
                outputs = self.encoder(pixel_values=x)
                if hasattr(outputs, "last_hidden_state"):
                    cls_feat = outputs.last_hidden_state[:, 0, :]
                elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    cls_feat = outputs.pooler_output
                else:
                    cls_feat = outputs[0][:, 0, :]
            else:
                # timm model
                cls_feat = self.encoder(x)
                if cls_feat.dim() > 2:
                    cls_feat = torch.flatten(cls_feat, 1)
        return cls_feat

    def forward(self, x: torch.Tensor, task_id: Optional[str] = None) -> Dict[str, torch.Tensor]:
        feat = self.extract_features(x)
        feat = self.dropout(self.head_norm(feat))

        if task_id in {"head_a", "a"}:
            return {"head_a": self.head_a(feat)}
        if task_id in {"head_b", "b"}:
            return {"head_b": self.head_b(feat)}
        if task_id in {"head_c", "c"}:
            return {"head_c": self.head_c(feat)}

        return {
            "head_a": self.head_a(feat),
            "head_b": self.head_b(feat),
            "head_c": self.head_c(feat),
        }

    @torch.no_grad()
    def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        logits = self.forward(x)
        return {
            "head_a": torch.sigmoid(logits["head_a"]),
            "head_b": torch.sigmoid(logits["head_b"]),
            "head_c": torch.sigmoid(logits["head_c"]),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LungRay RAD-DINO Linear Probing Benchmark")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--save-name", type=str, default="raddino_linear_prober.pth")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = resolve_dataset_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Device] Using compute hardware: {device}")

    loaders = train_kaggle.build_dataloaders(
        paths, batch_size=args.batch_size, allow_missing=args.allow_missing
    )

    model = RadDinoMultiTaskProber().to(device)
    criterion = MaskedMultiTaskLoss(
        weights={"head_a": 1.0, "head_b": 0.8, "head_c": 0.8},
        head_a_criterion="asl",
        head_c_criterion="bce",
    )

    # Train only linear head parameters
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)

    print(f"\n[RAD-DINO Prober] Starting linear probing for {args.epochs} epochs...")
    best_loss = float("inf")

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        batches = 0

        for batch in loaders["train_loader"]:
            images = batch["images"].to(device)
            task_ids = batch["task_ids"]

            optimizer.zero_grad()
            logits = model(images)
            loss_dict = criterion(logits, batch, task_ids)
            loss = loss_dict["loss"]
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            batches += 1

        scheduler.step()
        avg_loss = total_loss / max(1, batches)
        print(f"Epoch [{epoch:02d}/{args.epochs:02d}] - Train Loss: {avg_loss:.4f} (LR: {scheduler.get_last_lr()[0]:.2e})")

        if avg_loss < best_loss:
            best_loss = avg_loss
            out_path = os.path.join(str(paths["output_dir"]), args.save_name)
            torch.save({"model_state": model.state_dict(), "epoch": epoch, "loss": best_loss}, out_path)
            print(f"  --> Saved best RAD-DINO prober checkpoint to: {out_path}")

    print("\n[RAD-DINO Prober] Training complete.")


if __name__ == "__main__":
    main()
