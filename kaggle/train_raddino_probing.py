"""Frozen RAD-DINO, three linear heads; validation-only comparative study.

Usage (offline Hugging Face snapshot attached to Kaggle):
    python kaggle/train_raddino_probing.py --model-dir /kaggle/input/rad-dino/snapshot
Install the optional `probing` dependencies first. No random encoder fallback.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "kaggle"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from train_multitask_kaggle import calibrate_thresholds, collect_probabilities  # noqa: E402
import train_kaggle  # noqa: E402
from src.data.ingestion import resolve_dataset_paths  # noqa: E402
from src.models.losses import MaskedMultiTaskLoss  # noqa: E402
from src.models.trainer import MultiTaskTrainer  # noqa: E402
from src.utils.threshold_tuning import save_thresholds_json  # noqa: E402


class RadDinoTransform:
    """Use the checkpoint's resize/crop/normalization, not ImageNet transforms."""
    def __init__(self, processor):
        self.processor = processor

    def __call__(self, image):
        return {"image": self.processor(images=image, return_tensors="pt")["pixel_values"][0]}


class RadDinoLinearProbe(nn.Module):
    def __init__(self, encoder):
        super().__init__()
        self.backbone = encoder
        self.backbone_name = "microsoft/rad-dino"
        self.num_classes_c = 1
        self.img_size = getattr(encoder.config, "image_size", 518)
        if encoder.config.hidden_size != 768:
            raise ValueError("RAD-DINO probing requires a 768-dimensional encoder")
        self.backbone.requires_grad_(False)
        self.backbone.eval()
        self.head_a = nn.Linear(768, 14)
        self.head_b = nn.Linear(768, 1)
        self.head_c = nn.Linear(768, 1)

    def train(self, mode=True):
        super().train(mode)
        self.backbone.eval()
        return self

    def forward(self, images):
        with torch.no_grad():
            features = self.backbone(pixel_values=images).last_hidden_state[:, 0, :]
        return {name: getattr(self, name)(features) for name in ("head_a", "head_b", "head_c")}

    @torch.no_grad()
    def predict(self, images):
        return {name: torch.sigmoid(value) for name, value in self(images).items()}


def load_encoder(model_dir=None, allow_download=False):
    from transformers import AutoImageProcessor, AutoModel
    candidates = [str(model_dir)] if model_dir else ["microsoft/rad-dino"]
    if model_dir is None and Path("/kaggle/input").exists():
        candidates = [str(path.parent) for path in Path("/kaggle/input").rglob("config.json")
                      if "rad-dino" in str(path).lower() or "raddino" in str(path).lower()] + candidates
    errors = []
    for source in candidates:
        try:
            processor = AutoImageProcessor.from_pretrained(source, local_files_only=not allow_download)
            encoder = AutoModel.from_pretrained(source, local_files_only=not allow_download)
            return processor, encoder, source
        except (OSError, ValueError) as error:
            errors.append(f"{source}: {error}")
    raise RuntimeError("Attach a complete RAD-DINO snapshot (config, processor and weights). Checked: " + " | ".join(errors))


def export_validation_metrics(model, loaders, device, directory):
    rows = []
    for head, key in (("head_a", "val_loader_a"), ("head_b", "val_loader_b"), ("head_c", "val_loader_c")):
        probs, labels = collect_probabilities(model, loaders[key], head, device)
        labels = labels.reshape(len(labels), -1)
        probs = probs.reshape(len(probs), -1)
        eligible = [index for index in range(labels.shape[1]) if len(np.unique(labels[:, index])) == 2]
        scores = [roc_auc_score(labels[:, index], probs[:, index]) for index in eligible]
        rows.append(dict(split="validation", head=head, samples=len(labels), eligible_classes=len(eligible),
                         total_classes=labels.shape[1], auroc=float(np.mean(scores)) if scores else float("nan")))
        np.savez_compressed(directory / f"validation_{head}_predictions.npz", probabilities=probs, labels=labels)
    pd.DataFrame(rows).to_csv(directory / "raddino_validation_auroc.csv", index=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--allow-download", action="store_true", help="Enable Hugging Face network downloads")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-batches", type=int, default=0, help="0 means a full training epoch")
    args = parser.parse_args(argv)
    if args.epochs < 1 or args.batch_size < 3:
        raise ValueError("epochs must be positive; batch-size must include three tasks")
    if os.path.isdir("/kaggle") and not torch.cuda.is_available():
        raise RuntimeError("Enable Kaggle GPU before starting RAD-DINO probing")
    processor, encoder, source = load_encoder(args.model_dir, args.allow_download)
    model = RadDinoLinearProbe(encoder)
    paths = resolve_dataset_paths()
    output = Path(paths["output_dir"]) / "raddino_probing"
    results = Path(paths["results_dir"]) / "raddino_probing"
    results.mkdir(parents=True, exist_ok=True)
    loaders = train_kaggle.build_dataloaders(paths, args.batch_size, False,
        train_transform=RadDinoTransform(processor), val_transform=RadDinoTransform(processor))
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad),
                                  lr=args.lr, weight_decay=1e-2)
    trainer = MultiTaskTrainer(model, MaskedMultiTaskLoss(head_a_criterion="bce", head_c_criterion="bce"),
        optimizer=optimizer, mixed_precision=True, early_stopping_patience=args.epochs + 1,
        checkpoint_dir=str(output), results_dir=str(results),
        max_batches_per_epoch=args.max_batches or None)
    manifest = dict(model_source=source, processor=processor.to_dict(), encoder_frozen=True,
                    epochs=args.epochs, batch_size=args.batch_size, max_batches=args.max_batches,
                    evaluation_split="validation", independent_test_evaluated=False)
    (results / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    trainer.fit(loaders["train_loader"], loaders["val_loader_a"], loaders["val_loader_b"],
                loaders["val_loader_c"], epochs=args.epochs, save_name="best_raddino_probing.pth")
    best = torch.load(output / "best_raddino_probing.pth", map_location=trainer.device, weights_only=False)
    model.load_state_dict(best["model_state_dict"], strict=True)
    export_validation_metrics(model, loaders, trainer.device, results)
    thresholds = calibrate_thresholds(model, loaders, trainer.device)
    thresholds["calibration_split"] = "validation_all"
    save_thresholds_json(thresholds, results / "optimal_thresholds_raddino.json")


if __name__ == "__main__":
    main()
