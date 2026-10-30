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
        max_batches_per_epoch: Optional[int] = None,
        max_val_batches_per_head: Optional[int] = None,
        log_interval: int = 50,
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
        # Modern PyTorch 2.x AMP API with backwards compatibility
        if hasattr(torch, "amp") and hasattr(torch.amp, "GradScaler"):
            self.scaler = torch.amp.GradScaler("cuda", enabled=self.mixed_precision)
        else:
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
        self.max_batches_per_epoch = max_batches_per_epoch
        self.max_val_batches_per_head = max_val_batches_per_head
        self.log_interval = max(1, log_interval)

        self.best_val_score = -1.0
        self.patience_counter = 0
        self.history: List[Dict[str, Any]] = []

    def train_step(self, batch: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Executes a single forward-backward optimization step.
        """
        self.model.train()
        # Frozen-backbone fine-tuning stages must also freeze BatchNorm
        # running statistics; requires_grad=False alone does not do that.
        backbone = getattr(self.model, "backbone", None)
        if backbone is not None and not any(
            parameter.requires_grad for parameter in backbone.parameters()
        ):
            backbone.eval()
        images = batch["images"].to(self.device)
        task_ids = batch["task_ids"].to(self.device)
        targets = batch["labels"]

        self.optimizer.zero_grad()

        if self.mixed_precision:
            autocast_ctx = (
                torch.amp.autocast("cuda")
                if hasattr(torch, "amp") and hasattr(torch.amp, "autocast")
                else torch.cuda.amp.autocast()
            )
            with autocast_ctx:
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
        max_batches = num_batches
        if self.max_batches_per_epoch is not None:
            max_batches = min(num_batches, max(1, self.max_batches_per_epoch))

        if max_batches < num_batches:
            print(
                f"[*] Epoch {epoch}: speed mode {max_batches:,d}/{num_batches:,d} batches "
                f"(set max_batches_per_epoch=None for a full epoch).",
                flush=True,
            )

        start_time = time.time()
        running_loss = 0.0
        processed = 0
        for batch_idx, batch in enumerate(train_loader):
            if batch_idx >= max_batches:
                break
            loss_val, metrics = self.train_step(batch)
            total_loss += loss_val
            running_loss += loss_val
            processed += 1

            for k in head_losses:
                if metrics.get(k, 0.0) > 0.0:
                    head_losses[k] += metrics[k]
                    counts[k] += 1

            if processed == 1 or processed % self.log_interval == 0 or processed == max_batches:
                elapsed = time.time() - start_time
                avg_running = running_loss / processed
                eta = elapsed / processed * (max_batches - processed)
                print(
                    f"  [Epoch {epoch:02d}] batch {processed:,d}/{max_batches:,d} | "
                    f"loss={avg_running:.4f} | elapsed={elapsed / 60:.1f}m | "
                    f"eta={eta / 60:.1f}m",
                    flush=True,
                )

        elapsed = time.time() - start_time
        avg_loss = total_loss / max(1, processed)
        summary = {
            "train_loss": avg_loss,
            "train_loss_a": head_losses["loss_a"] / max(1, counts["loss_a"]),
            "train_loss_b": head_losses["loss_b"] / max(1, counts["loss_b"]),
            "train_loss_c": head_losses["loss_c"] / max(1, counts["loss_c"]),
            "train_time_sec": elapsed,
        }
        return summary

    def _val_autocast(self):
        """Returns the AMP context used during validation/inference."""
        if not self.mixed_precision:
            return torch.autocast(device_type=self.device.type, enabled=False)
        if hasattr(torch, "amp") and hasattr(torch.amp, "autocast"):
            return torch.amp.autocast(device_type=self.device.type)
        return torch.cuda.amp.autocast()

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
            val_total_a = len(val_loader_a)
            if self.max_val_batches_per_head is not None:
                val_total_a = min(val_total_a, max(1, self.max_val_batches_per_head))
            print(
                f"[*] Validating Head A (NIH): {val_total_a:,d}/{len(val_loader_a):,d} batches...",
                flush=True,
            )
            val_start = time.time()
            all_preds_a, all_targets_a = [], []
            for batch_idx, batch in enumerate(val_loader_a):
                if batch_idx >= val_total_a:
                    break
                if isinstance(batch, dict):
                    images = batch["images"].to(self.device)
                else:
                    images = batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                with self._val_autocast():
                    preds = self.model.predict(images)["head_a"].cpu().numpy()
                all_preds_a.append(preds)
                if isinstance(targets, list):
                    all_targets_a.append(torch.stack(targets).cpu().numpy())
                else:
                    all_targets_a.append(targets.cpu().numpy())
                if (batch_idx + 1) % 20 == 0 or batch_idx + 1 == val_total_a:
                    print(
                        f"  [Val A] batch {batch_idx + 1:,d}/{val_total_a:,d} "
                        f"({time.time() - val_start:.1f}s)",
                        flush=True,
                    )

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
            val_total_b = len(val_loader_b)
            if self.max_val_batches_per_head is not None:
                val_total_b = min(val_total_b, max(1, self.max_val_batches_per_head))
            print(
                f"[*] Validating Head B (TB): {val_total_b:,d}/{len(val_loader_b):,d} batches...",
                flush=True,
            )
            val_start = time.time()
            all_preds_b, all_targets_b = [], []
            for batch_idx, batch in enumerate(val_loader_b):
                if batch_idx >= val_total_b:
                    break
                if isinstance(batch, dict):
                    images = batch["images"].to(self.device)
                else:
                    images = batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                with self._val_autocast():
                    preds = self.model.predict(images)["head_b"].cpu().numpy().reshape(-1)
                all_preds_b.append(preds)
                if isinstance(targets, list):
                    all_targets_b.append(torch.stack(targets).cpu().numpy().reshape(-1))
                else:
                    all_targets_b.append(targets.cpu().numpy().reshape(-1))
                if (batch_idx + 1) % 20 == 0 or batch_idx + 1 == val_total_b:
                    print(
                        f"  [Val B] batch {batch_idx + 1:,d}/{val_total_b:,d} "
                        f"({time.time() - val_start:.1f}s)",
                        flush=True,
                    )

            if all_preds_b:
                y_pred = np.concatenate(all_preds_b, axis=0)
                y_true = np.concatenate(all_targets_b, axis=0)
                if len(np.unique(y_true)) > 1:
                    metrics["val_auc_b"] = float(roc_auc_score(y_true, y_pred))

        # 3. Evaluate Head C (binary screening or multi-class benchmark)
        if val_loader_c is not None and len(val_loader_c) > 0:
            val_total_c = len(val_loader_c)
            if self.max_val_batches_per_head is not None:
                val_total_c = min(val_total_c, max(1, self.max_val_batches_per_head))
            print(
                f"[*] Validating Head C (COVIDx): {val_total_c:,d}/{len(val_loader_c):,d} batches...",
                flush=True,
            )
            val_start = time.time()
            all_preds_c, all_targets_c = [], []
            for batch_idx, batch in enumerate(val_loader_c):
                if batch_idx >= val_total_c:
                    break
                if isinstance(batch, dict):
                    images = batch["images"].to(self.device)
                else:
                    images = batch[0].to(self.device)
                targets = batch["labels"] if isinstance(batch, dict) else batch[1]
                with self._val_autocast():
                    preds = self.model.predict(images)["head_c"].cpu().numpy()
                all_preds_c.append(preds)
                if isinstance(targets, list):
                    all_targets_c.append(torch.stack(targets).cpu().numpy().reshape(-1))
                else:
                    all_targets_c.append(targets.cpu().numpy().reshape(-1))
                if (batch_idx + 1) % 20 == 0 or batch_idx + 1 == val_total_c:
                    print(
                        f"  [Val C] batch {batch_idx + 1:,d}/{val_total_c:,d} "
                        f"({time.time() - val_start:.1f}s)",
                        flush=True,
                    )

            if all_preds_c:
                y_pred = np.concatenate(all_preds_c, axis=0)
                y_true = np.concatenate(all_targets_c, axis=0).ravel()
                if y_pred.ndim > 1 and y_pred.shape[1] == 1:
                    y_pred = y_pred.ravel()
                if len(np.unique(y_true)) > 1:
                    try:
                        if y_pred.ndim == 1 or y_pred.shape[1] == 1:
                            metrics["val_auc_c"] = float(roc_auc_score(y_true, y_pred.ravel()))
                        else:
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

    def _save_checkpoint(
        self,
        path: str,
        epoch: int,
        val_metrics: Optional[Dict[str, float]],
        stage: str,
    ) -> None:
        """Atomically saves a resumable checkpoint (survives Kaggle interruptions)."""
        payload = {
            "epoch": epoch,
            "stage": stage,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scaler_state_dict": self.scaler.state_dict() if self.mixed_precision else None,
            "lr_scheduler_state_dict": (
                self.lr_scheduler.state_dict() if self.lr_scheduler is not None else None
            ),
            "best_val_score": self.best_val_score,
            "patience_counter": self.patience_counter,
            "val_metrics": val_metrics,
            "history": self.history,
        }
        tmp_path = f"{path}.tmp"
        torch.save(payload, tmp_path)
        os.replace(tmp_path, path)

    def fit(
        self,
        train_loader: DataLoader,
        val_loader_a: Optional[DataLoader] = None,
        val_loader_b: Optional[DataLoader] = None,
        val_loader_c: Optional[DataLoader] = None,
        epochs: int = 25,
        save_name: str = "best_model.pth",
        resume_from: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Runs full training loop with validation, early stopping and checkpointing.

        Args:
            resume_from: Optional ``last_model.pth`` path. Restores model,
                optimizer, scaler, scheduler and history, then continues from
                the next epoch.
        """
        start_epoch = 1
        if resume_from and os.path.isfile(resume_from):
            try:
                checkpoint = torch.load(
                    resume_from, map_location=self.device, weights_only=False
                )
            except TypeError:
                checkpoint = torch.load(resume_from, map_location=self.device)

            self.model.load_state_dict(checkpoint["model_state_dict"])
            if checkpoint.get("optimizer_state_dict"):
                self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            if self.lr_scheduler is not None and checkpoint.get("lr_scheduler_state_dict"):
                self.lr_scheduler.load_state_dict(checkpoint["lr_scheduler_state_dict"])
            if self.mixed_precision and checkpoint.get("scaler_state_dict"):
                self.scaler.load_state_dict(checkpoint["scaler_state_dict"])

            self.best_val_score = float(checkpoint.get("best_val_score", -1.0))
            self.patience_counter = int(checkpoint.get("patience_counter", 0))
            self.history = checkpoint.get("history", []) or []
            start_epoch = int(checkpoint.get("epoch", 0)) + 1
            # The "trained" checkpoint is written before validation and before
            # the scheduler step. Catch the LR schedule up on resume.
            if checkpoint.get("stage") == "trained" and self.lr_scheduler is not None:
                self.lr_scheduler.step()
            print(
                f"[Resume] Loaded {resume_from} | last epoch={start_epoch - 1} | "
                f"best={self.best_val_score:.4f} | continue from epoch {start_epoch}.",
                flush=True,
            )

        last_path = os.path.join(self.checkpoint_dir, "last_model.pth")
        history_path = os.path.join(self.results_dir, "training_history.csv")

        for epoch in range(start_epoch, epochs + 1):
            train_metrics = self.train_epoch(train_loader, epoch)
            # Save immediately after training: a validation interruption
            # must not throw away hours of optimization.
            self._save_checkpoint(last_path, epoch, None, "trained")
            print(f" -> Last checkpoint saved to {last_path} (after train).", flush=True)

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
            for group_index, param_group in enumerate(self.optimizer.param_groups):
                group_name = str(param_group.get("name", f"group_{group_index}"))
                record[f"lr_{group_name}"] = float(param_group["lr"])
            self.history.append(record)
            pd.DataFrame(self.history).to_csv(history_path, index=False)

            print(
                f"[Epoch {epoch:02d}/{epochs:02d}] "
                f"Train Loss: {train_metrics['train_loss']:.4f} | "
                f"Val Score: {current_score:.4f} (AUC_A: {val_metrics['val_auc_a']:.3f}, "
                f"AUC_B: {val_metrics['val_auc_b']:.3f}, AUC_C: {val_metrics['val_auc_c']:.3f})"
            )

            if current_score > self.best_val_score:
                self.best_val_score = current_score
                self.patience_counter = 0
                checkpoint_path = os.path.join(self.checkpoint_dir, save_name)
                self._save_checkpoint(checkpoint_path, epoch, val_metrics, "validated")
                print(
                    f" -> Best checkpoint saved to {checkpoint_path} "
                    f"(Best Score: {self.best_val_score:.4f})"
                )
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.early_stopping_patience:
                    self._save_checkpoint(last_path, epoch, val_metrics, "validated")
                    print(f"[Early Stopping] Triggered after {epoch} epochs without improvement.")
                    break

            self._save_checkpoint(last_path, epoch, val_metrics, "validated")

        history_df = pd.DataFrame(self.history)
        history_df.to_csv(history_path, index=False)
        return history_df
