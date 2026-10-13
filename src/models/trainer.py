"""
LungRay Multi-Task Training & Evaluation Engine (src/models/trainer.py)
======================================================================
Coordinates multi-task model optimization with:
- PyTorch Mixed Precision (AMP FP16)
- Gradient isolation per head via MaskedMultiTaskLoss
- Per-head validation (Macro AUROC for NIH 14 diseases, AUROC for TB, Macro OvR AUROC for COVID-19)
- Multi-task weighted validation checkpointing:
    S_val = 0.40 * AUC_A + 0.30 * AUC_B + 0.30 * AUC_C
- Early Stopping and Cosine Annealing LR scheduling
"""
import os
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score, f1_score

from src.models.multi_task_net import MultiTaskChestXrayNet
from src.models.losses import MaskedMultiTaskLoss


def multitask_collate_fn(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Collate function capable of packing samples of heterogeneous tasks into a unified batch.
    """
    images = torch.stack([item["image"] for item in batch], dim=0)
    task_ids = torch.stack([item["task_id"] for item in batch], dim=0)
    labels = [item["labels"] for item in batch]
    image_ids = [item.get("image_id", "") for item in batch]

    return {
        "images": images,
        "task_ids": task_ids,
        "labels": labels,
        "image_ids": image_ids,
    }


class MultiTaskTrainer:
    """
    Production-grade Multi-Task Trainer for LungRay 3-Head CADx platform.
    """

    def __init__(
        self,
        model: MultiTaskChestXrayNet,
        criterion: MaskedMultiTaskLoss,
        optimizer: Optional[torch.optim.Optimizer] = None,
        lr_scheduler: Optional[Any] = None,
        device: Optional[torch.device] = None,
        mixed_precision: bool = True,
        early_stopping_patience: int = 5,
        checkpoint_dir: str = "checkpoints",
        results_dir: str = "results",
        metric_weights: Optional[Dict[str, float]] = None,
    ):
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.model = model.to(self.device)
        self.criterion = criterion.to(self.device)

        # Optimizer: Default to AdamW
        self.optimizer = optimizer or torch.optim.AdamW(
            self.model.parameters(),
            lr=1e-4,
            weight_decay=1e-5
        )
        self.lr_scheduler = lr_scheduler

        self.mixed_precision = mixed_precision and (self.device.type == "cuda")
        self.scaler = torch.cuda.amp.GradScaler(enabled=self.mixed_precision)

        self.early_stopping_patience = early_stopping_patience
        self.checkpoint_dir = checkpoint_dir
        self.results_dir = results_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)

        self.metric_weights = metric_weights or {
            "auc_a": 0.40,
            "auc_b": 0.30,
            "auc_c": 0.30,
        }

        self.best_val_score = -1.0
        self.patience_counter = 0
        self.history: List[Dict[str, Any]] = []

    def train_step(self, batch: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Executes a single forward-backward optimization step.
        """
        self.model.train()
        images = batch["images"].to(self.device)
        task_ids = batch["task_ids"].to(self.device)
        targets = batch["labels"]

        self.optimizer.zero_grad()

        if self.mixed_precision:
            with torch.cuda.amp.autocast():
                logits = self.model(images)
                loss, metrics = self.criterion(logits, targets, task_ids)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            logits = self.model(images)
            loss, metrics = self.criterion(logits, targets, task_ids)
            loss.backward()
            self.optimizer.step()

        return float(loss.detach().item()), metrics

    def train_epoch(self, train_loader: DataLoader, epoch: int) -> Dict[str, float]:
        """
        Runs one complete training epoch over train_loader.
        """
        self.model.train()
        total_loss = 0.0
        head_losses = {"loss_a": 0.0, "loss_b": 0.0, "loss_c": 0.0}
        counts = {"loss_a": 0, "loss_b": 0, "loss_c": 0}
        num_batches = len(train_loader)

        start_time = time.time()
        for batch_idx, batch in enumerate(train_loader):
            loss_val, metrics = self.train_step(batch)
            total_loss += loss_val

            for k in head_losses:
                if metrics.get(k, 0.0) > 0.0:
                    head_losses[k] += metrics[k]
                    counts[k] += 1

        elapsed = time.time() - start_time
        avg_loss = total_loss / max(1, num_batches)
        summary = {
            "train_loss": avg_loss,
            "train_loss_a": head_losses["loss_a"] / max(1, counts["loss_a"]),
            "train_loss_b": head_losses["loss_b"] / max(1, counts["loss_b"]),
            "train_loss_c": head_losses["loss_c"] / max(1, counts["loss_c"]),
            "train_time_sec": elapsed,
        }
        return summary

    @torch.no_grad()
    def validate_loaders(
        self,
        val_loader_a: Optional[DataLoader] = None,
        val_loader_b: Optional[DataLoader] = None,
        val_loader_c: Optional[DataLoader] = None,
    ) -> Dict[str, float]:
        """
        Validates model performance on separate task validation DataLoaders.
        Computes AUROC metrics independently for each head:
        - Head A: Macro AUROC across 14 NIH pathologies.
        - Head B: Binary AUROC for TB.
        - Head C: Macro OvR AUROC for COVID-19 4-class.
        """
        self.model.eval()
        metrics: Dict[str, float] = {
            "val_auc_a": 0.50,
            "val_auc_b": 0.50,
            "val_auc_c": 0.50,
            "val_combined_score": 0.50,
        }

        # 1. Evaluate Head A
        if val_loader_a is not None and len(val_loader_a) > 0:
            all_preds_a, all_targets_a = [], []
            for batch in val_loader_a:
                images = batch["images"].to(self.device) if isinstance(batch, dict) else batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                preds = self.model.predict(images)["head_a"].cpu().numpy()
                all_preds_a.append(preds)
                if isinstance(targets, list):
                    all_targets_a.append(torch.stack(targets).cpu().numpy())
                else:
                    all_targets_a.append(targets.cpu().numpy())

            if all_preds_a:
                y_pred = np.concatenate(all_preds_a, axis=0)
                y_true = np.concatenate(all_targets_a, axis=0)
                aucs = []
                for c in range(y_true.shape[1]):
                    # Compute AUROC if both positive and negative samples exist
                    if len(np.unique(y_true[:, c])) > 1:
                        aucs.append(roc_auc_score(y_true[:, c], y_pred[:, c]))
                metrics["val_auc_a"] = float(np.mean(aucs)) if aucs else 0.50

        # 2. Evaluate Head B
        if val_loader_b is not None and len(val_loader_b) > 0:
            all_preds_b, all_targets_b = [], []
            for batch in val_loader_b:
                images = batch["images"].to(self.device) if isinstance(batch, dict) else batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                preds = self.model.predict(images)["head_b"].cpu().numpy().squeeze()
                all_preds_b.append(preds)
                if isinstance(targets, list):
                    all_targets_b.append(torch.stack(targets).cpu().numpy().squeeze())
                else:
                    all_targets_b.append(targets.cpu().numpy().squeeze())

            if all_preds_b:
                y_pred = np.concatenate(all_preds_b, axis=0)
                y_true = np.concatenate(all_targets_b, axis=0)
                if len(np.unique(y_true)) > 1:
                    metrics["val_auc_b"] = float(roc_auc_score(y_true, y_pred))

        # 3. Evaluate Head C
        if val_loader_c is not None and len(val_loader_c) > 0:
            all_preds_c, all_targets_c = [], []
            for batch in val_loader_c:
                images = batch["images"].to(self.device) if isinstance(batch, dict) else batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                preds = self.model.predict(images)["head_c"].cpu().numpy()
                all_preds_c.append(preds)
                if isinstance(targets, list):
                    all_targets_c.append(torch.stack(targets).cpu().numpy().squeeze())
                else:
                    all_targets_c.append(targets.cpu().numpy().squeeze())

            if all_preds_c:
                y_pred = np.concatenate(all_preds_c, axis=0)
                y_true = np.concatenate(all_targets_c, axis=0)
                if len(np.unique(y_true)) > 1:
                    try:
                        metrics["val_auc_c"] = float(
                            roc_auc_score(y_true, y_pred, multi_class="ovr", average="macro")
                        )
                    except Exception:
                        metrics["val_auc_c"] = 0.50

        # Calculate weighted combined validation score
        w_a = self.metric_weights.get("auc_a", 0.40)
        w_b = self.metric_weights.get("auc_b", 0.30)
        w_c = self.metric_weights.get("auc_c", 0.30)
        score = (
            w_a * metrics["val_auc_a"] +
            w_b * metrics["val_auc_b"] +
            w_c * metrics["val_auc_c"]
        )
        metrics["val_combined_score"] = float(score)
        return metrics

    def fit(
        self,
        train_loader: DataLoader,
        val_loader_a: Optional[DataLoader] = None,
        val_loader_b: Optional[DataLoader] = None,
        val_loader_c: Optional[DataLoader] = None,
        epochs: int = 25,
        save_name: str = "best_model.pth"
    ) -> pd.DataFrame:
        """
        Runs full training loop with validation, early stopping and checkpointing.
        """
        for epoch in range(1, epochs + 1):
            train_metrics = self.train_epoch(train_loader, epoch)
            val_metrics = self.validate_loaders(val_loader_a, val_loader_b, val_loader_c)

            if self.lr_scheduler is not None:
                self.lr_scheduler.step()

            current_score = val_metrics["val_combined_score"]
            record = {
                "epoch": epoch,
                **train_metrics,
                **val_metrics,
                "lr": float(self.optimizer.param_groups[0]["lr"]),
            }
            self.history.append(record)

            print(
                f"[Epoch {epoch:02d}/{epochs:02d}] "
                f"Train Loss: {train_metrics['train_loss']:.4f} | "
                f"Val Score: {current_score:.4f} (AUC_A: {val_metrics['val_auc_a']:.3f}, "
                f"AUC_B: {val_metrics['val_auc_b']:.3f}, AUC_C: {val_metrics['val_auc_c']:.3f})"
            )

            # Checkpoint saving on improvement
            if current_score > self.best_val_score:
                self.best_val_score = current_score
                self.patience_counter = 0
                checkpoint_path = os.path.join(self.checkpoint_dir, save_name)
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": self.model.state_dict(),
                        "optimizer_state_dict": self.optimizer.state_dict(),
                        "best_val_score": self.best_val_score,
                        "val_metrics": val_metrics,
                    },
                    checkpoint_path
                )
                print(f" -> Checkpoint saved to {checkpoint_path} (Best Score: {self.best_val_score:.4f})")
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.early_stopping_patience:
                    print(f"[Early Stopping] Triggered after {epoch} epochs without improvement.")
                    break

        history_df = pd.DataFrame(self.history)
        history_path = os.path.join(self.results_dir, "training_history.csv")
        history_df.to_csv(history_path, index=False)
        return history_df
