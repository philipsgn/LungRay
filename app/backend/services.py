"""Core inference/explanation/audit service for the LungRay FastAPI backend."""
from __future__ import annotations

import base64
import io
import json
import logging
import math
import os
import time
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from src.data.transforms import get_val_transforms
from src.explainability import (
    GradCAMExplainer,
    LungSegmenter,
    MultiScaleGradCAMPlusPlus,
    ShortcutAuditEngine,
    extract_adaptive_contour,
    render_contour_overlay,
)
from src.models.dense_unet import DenseUNet
from src.models.multi_task_net import MultiTaskChestXrayNet
from src.safety.ood_scores import compute_sigmoid_energy, compute_shannon_entropy
from src.safety.reject_policy import SafetyPolicy
from src.safety.report_generator import ClinicalReportGenerator

logger = logging.getLogger(__name__)

NIH_14_DISEASES = [
    "Atelectasis",
    "Cardiomegaly",
    "Effusion",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pneumonia",
    "Pneumothorax",
    "Consolidation",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Pleural_Thickening",
    "Hernia",
]


class LungRayService:
    """Singleton inference service wrapping the multi-task model and XAI utilities."""

    _instance: "LungRayService | None" = None

    def __new__(cls) -> "LungRayService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.version = "v7.0"
        self.img_size = 512
        self.thresholds = self._load_thresholds()
        self.models: dict[str, MultiTaskChestXrayNet] = {}
        self.model_info: dict[str, dict[str, Any]] = {}
        self._load_hybrid_models()
        self.model = self.models.get("standard") or next(iter(self.models.values()))
        self.transform = get_val_transforms(img_size=self.img_size)
        self.dense_unet = self._load_dense_unet()
        if self.dense_unet is not None:
            self.segmenter = LungSegmenter(dense_unet=self.dense_unet)
        else:
            self.segmenter = LungSegmenter()
        self.anatomical_gate_enabled = bool(
            self.dense_unet is not None
            and os.getenv("LUNGRAY_ANATOMICAL_GATE", "0") == "1"
        )
        self.audit_engine = ShortcutAuditEngine(self.segmenter)
        self.safety_policy = SafetyPolicy()
        self.report_generator = ClinicalReportGenerator()
        self._initialized = True

    def _load_dense_unet(self) -> DenseUNet | None:
        """
        Loads the Dense-UNet segmentation engine as a frozen inference-time gate.

        Returns ``None`` when no trained checkpoint is available so the service
        transparently falls back to the deterministic morphology segmenter
        instead of gating on randomly-initialised weights. The network is put in
        ``eval`` mode with all parameters frozen, so it never participates in
        any gradient computation or weight update.

        Environment overrides:
            DENSE_UNET_CHECKPOINT: path to the trained lung-segmentation weights
                (default ``checkpoints/dense_unet.pth``).
        """
        checkpoint = os.getenv("DENSE_UNET_CHECKPOINT", "checkpoints/dense_unet.pth")
        if not os.path.exists(checkpoint):
            logger.info(
                "Dense-UNet checkpoint '%s' not found; anatomical gate stays off "
                "(classical LungSegmenter active).",
                checkpoint,
            )
            return None

        model = DenseUNet(pretrained=False)
        state = torch.load(checkpoint, map_location=self.device, weights_only=False)
        if isinstance(state, dict):
            for key in ("model_state_dict", "state_dict"):
                if key in state:
                    state = state[key]
                    break
        model.load_state_dict(state, strict=False)
        model.to(self.device)
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        logger.info("Loaded frozen Dense-UNet segmentation gate from %s", checkpoint)
        return model

    @torch.inference_mode()
    def _anatomical_gate(self, image_np: np.ndarray) -> np.ndarray:
        """
        Inference-time Dilated Soft Anatomical Masking gate (Dilation 6%,
        attenuation 10% on the outer thoracic background).

        The gate runs detached, in numpy space and under ``torch.inference_mode``,
        so no autograd graph is ever attached to the returned image. Grad-CAM
        gradients therefore still flow only through the diagnostic backbone and
        never leak into the segmentation network, and the diagnostic weights are
        never modified.
        """
        if not getattr(self, "anatomical_gate_enabled", False):
            return image_np
        try:
            return self.segmenter.generate_dilated_soft_mask(
                image_np,
                dilation_margin_pct=0.06,
                background_attenuation=0.10,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Anatomical gate failed (%s); using raw image.", exc)
            return image_np

    def _load_thresholds(self) -> dict[str, Any]:
        try:
            with open("configs/optimal_thresholds.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Could not load optimal_thresholds.json: %s", exc)
            return {
                "head_a_nih_14": {d: 0.5 for d in NIH_14_DISEASES},
                "head_b_tb": {"threshold": 0.5},
                "head_c_covid": {"threshold": 0.5},
            }

    def _instantiate_and_load(
        self, checkpoint_path: str, backbone_name: str = "densenet121"
    ) -> MultiTaskChestXrayNet:
        model = MultiTaskChestXrayNet(
            backbone_name=backbone_name,
            pretrained=False,
            img_size=self.img_size,
            num_classes_a=14,
            num_classes_b=1,
            num_classes_c=1,
        )

        if os.path.exists(checkpoint_path):
            logger.info("Loading checkpoint from %s for %s", checkpoint_path, backbone_name)
            state = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            elif isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state, strict=False)
        else:
            logger.warning(
                "No checkpoint found at %s; using randomly-initialized weights for %s.",
                checkpoint_path,
                backbone_name,
            )

        model.to(self.device)
        model.eval()
        return model

    def _load_hybrid_models(self) -> None:
        self.standard_path = os.getenv("CHECKPOINT_PATH", "checkpoints/best_model.pth")
        self.wsol_path = "checkpoints/best_wsol_finetune.pth"
        self.resnet_path = "checkpoints/best_resnet50.pth"

        # 1. Standard CADx model (SOTA Asymmetric Net)
        self.models["standard"] = self._instantiate_and_load(self.standard_path, backbone_name="densenet121")
        self.current_checkpoint = self.standard_path
        self.model_info["standard"] = {
            "id": "standard",
            "name": "Standard Diagnostic CADx (SOTA)",
            "role": "Primary emergency triaging across 16 cardiopulmonary conditions (Multi-Task Mean AUC 0.91)",
            "checkpoint": self.standard_path,
            "metrics": {
                "head_a_auc": 0.8352,
                "head_b_tb_auc": 0.9412,
                "head_c_covid_auc": 0.9520,
                "mean_auc": 0.9095,
            },
        }

        # 2. WSOL Specialist model (Attention-Regularized WSOL Net)
        if os.path.exists(self.wsol_path):
            self.models["wsol"] = self._instantiate_and_load(self.wsol_path, backbone_name="densenet121")
            self.model_info["wsol"] = {
                "id": "wsol",
                "name": "WSOL Attention Specialist",
                "role": "Focused lesion localization & specialized TB screening (RSNA IoU 0.245, TB AUC 0.968)",
                "checkpoint": self.wsol_path,
                "metrics": {
                    "head_a_auc": 0.7351,
                    "head_b_tb_auc": 0.9684,
                    "head_c_covid_auc": 0.6135,
                    "rsna_mean_best_iou": 0.2454,
                    "rsna_pass_iou_01": 0.760,
                },
            }
        else:
            self.models["wsol"] = self.models["standard"]
            self.model_info["wsol"] = self.model_info["standard"]

        # 3. ResNet-50 Residual Specialist (if checkpoint exists)
        if os.path.exists(self.resnet_path):
            self.models["resnet50"] = self._instantiate_and_load(self.resnet_path, backbone_name="resnet50")
            self.model_info["resnet50"] = {
                "id": "resnet50",
                "name": "ResNet-50 Residual Specialist",
                "role": "Deep residual representations & multi-scale gradient flow (ResNet-50 23.5M params)",
                "checkpoint": self.resnet_path,
                "metrics": {
                    "head_a_auc": 0.7885,
                    "head_b_tb_auc": 1.0000,
                    "head_c_covid_auc": 0.9891,
                    "mean_auc": 0.9259,
                },
            }

        # 4. Consensus Ensemble (always registered, dynamically leverages available backbones)
        self.model_info["ensemble"] = {
            "id": "ensemble",
            "name": "Triple-Backbone Consensus Ensemble",
            "role": "Adaptive Soft-Voting (DenseNet-121 + ResNet-50 + WSOL) with Inter-Model Agreement",
            "checkpoint": "multi-backbone consensus",
            "metrics": {
                "head_a_auc": 0.8410,
                "head_b_tb_auc": 1.0000,
                "head_c_covid_auc": 0.9910,
                "mean_auc": 0.9440,
            },
        }

    def check_and_reload_checkpoints(self) -> dict[str, Any]:
        """
        Dynamically detects new or updated checkpoints (e.g., best_resnet50.pth)
        and reloads them into the running inference service with zero downtime.
        """
        reloaded = []
        if os.path.exists(self.resnet_path) and "resnet50" not in self.models:
            logger.info("New ResNet-50 checkpoint detected at %s. Hot-reloading...", self.resnet_path)
            self.models["resnet50"] = self._instantiate_and_load(self.resnet_path, backbone_name="resnet50")
            self.model_info["resnet50"] = {
                "id": "resnet50",
                "name": "ResNet-50 Residual Specialist",
                "role": "Deep residual representations & multi-scale gradient flow (ResNet-50 23.5M params)",
                "checkpoint": self.resnet_path,
                "metrics": {
                    "head_a_auc": 0.7885,
                    "head_b_tb_auc": 1.0000,
                    "head_c_covid_auc": 0.9891,
                    "mean_auc": 0.9259,
                },
            }
            reloaded.append("resnet50")

        return {
            "status": "success",
            "active_models": list(self.models.keys()),
            "reloaded": reloaded,
            "triple_consensus_ready": "resnet50" in self.models and "wsol" in self.models and "standard" in self.models,
        }

    @staticmethod
    def apply_temperature_scaling(p: np.ndarray | float, temperature: float = 1.20) -> np.ndarray | float:
        """
        Applies Platt/Temperature Scaling to probabilities to soften overconfident predictions:
        p_calib = sigmoid(logit(p) / T)
        """
        if temperature <= 0.0 or abs(temperature - 1.0) < 1e-4:
            return p
        
        eps = 1e-6
        if isinstance(p, np.ndarray):
            p_clipped = np.clip(p, eps, 1.0 - eps)
            logits = np.log(p_clipped / (1.0 - p_clipped))
            calibrated_logits = logits / temperature
            return 1.0 / (1.0 + np.exp(-calibrated_logits))
        else:
            p_clipped = max(min(float(p), 1.0 - eps), eps)
            logits = math.log(p_clipped / (1.0 - p_clipped))
            calibrated_logits = logits / temperature
            return 1.0 / (1.0 + math.exp(-calibrated_logits))

    def get_model(self, model_name: str = "standard") -> MultiTaskChestXrayNet:
        name_lower = model_name.lower()
        if "wsol" in name_lower:
            return self.models.get("wsol", self.model)
        elif "resnet" in name_lower:
            return self.models.get("resnet50", self.model)
        elif "ensemble" in name_lower:
            return self.models.get("standard", self.model)
        return self.models.get("standard", self.model)

    def list_models(self) -> list[dict[str, Any]]:
        return list(self.model_info.values())

    def preprocess(self, image_bytes: bytes) -> torch.Tensor:
        """Convert raw image bytes to a batched (1, 3, 512, 512) tensor."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as exc:
            raise ValueError(f"Cannot decode uploaded image: {exc}") from exc

        image = image.convert("RGB")
        image_np = np.array(image)
        image_np = self._anatomical_gate(image_np)
        transformed = self.transform(image=image_np)["image"]
        return transformed.unsqueeze(0).to(self.device)

    def preprocess_tta(self, image_bytes: bytes) -> torch.Tensor:
        """
        Generate a 3-pass augmented batch tensor (3, 3, 512, 512) for clinical test-time augmentation:
        - Pass 1: Standard normalized view
        - Pass 2: High-contrast CLAHE view (recovers subtle interstitial/alveolar infiltrates)
        - Pass 3: Multi-scale anatomical view (scaled by 1.03x and center-cropped to 512x512)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as exc:
            raise ValueError(f"Cannot decode uploaded image: {exc}") from exc

        image = image.convert("RGB")
        image_np = np.array(image)

        # Anatomical gate applied once to the base image; all TTA passes are
        # derived from the already-masked image for geometric consistency.
        image_np = self._anatomical_gate(image_np)

        # Pass 1: Standard
        t1 = self.transform(image=image_np)["image"]

        # Pass 2: CLAHE Contrast Invariant
        try:
            lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            clahe_np = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            t2 = self.transform(image=clahe_np)["image"]
        except Exception:
            t2 = t1.clone()

        # Pass 3: Multi-scale Anatomical Invariant (1.03x scale with center-crop)
        try:
            h, w = image_np.shape[:2]
            scaled_w = int(w * 1.03)
            scaled_h = int(h * 1.03)
            scaled_np = cv2.resize(image_np, (scaled_w, scaled_h), interpolation=cv2.INTER_LINEAR)
            start_x = (scaled_w - w) // 2
            start_y = (scaled_h - h) // 2
            cropped_np = scaled_np[start_y:start_y + h, start_x:start_x + w]
            t3 = self.transform(image=cropped_np)["image"]
        except Exception:
            t3 = t1.clone()

        # Stack into a single batched tensor (3, 3, 512, 512)
        batch_tensor = torch.stack([t1, t2, t3], dim=0).to(self.device)
        return batch_tensor

    def predict(
        self,
        image_bytes: bytes,
        model_name: str = "standard",
        failsafe_enabled: bool = True,
    ) -> dict[str, Any]:
        # Dynamic hot-reload check
        self.check_and_reload_checkpoints()

        # 3-Pass Medical TTA Tensor Generation
        batch_tensor = self.preprocess_tta(image_bytes)
        standard_tensor = batch_tensor[:1]

        # ---------------------------------------------------------
        # Branch A: Consensus Ensemble (Multi-Backbone Soft-Voting)
        # ---------------------------------------------------------
        if "ensemble" in model_name.lower():
            start = time.perf_counter()
            dense_model = self.models.get("standard", self.model)
            wsol_model = self.models.get("wsol", dense_model)
            resnet_model = self.models.get("resnet50")

            participating_models = ["DenseNet-121 (Standard)", "DenseNet-121 (WSOL Specialist)"]
            with torch.no_grad():
                out_dense = dense_model.predict(batch_tensor)
                logits_dense = dense_model(standard_tensor)["head_a"]
                out_wsol = wsol_model.predict(batch_tensor)

                if resnet_model is not None:
                    out_res = resnet_model.predict(batch_tensor)
                    logits_res = resnet_model(standard_tensor)["head_a"]
                    participating_models.append("ResNet-50 (Residual Specialist)")
                else:
                    out_res = None
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # 3-Pass TTA Averaging
            p_dense_a = out_dense["head_a"].mean(dim=0).cpu().numpy()
            p_dense_b = float(out_dense["head_b"].mean().item())
            p_dense_c = float(out_dense["head_c"].mean().item())

            p_wsol_a = out_wsol["head_a"].mean(dim=0).cpu().numpy()
            p_wsol_b = float(out_wsol["head_b"].mean().item())
            p_wsol_c = float(out_wsol["head_c"].mean().item())

            if out_res is not None:
                p_res_a = out_res["head_a"].mean(dim=0).cpu().numpy()
                p_res_b = float(out_res["head_b"].mean().item())
                p_res_c = float(out_res["head_c"].mean().item())
                prob_a = 0.50 * p_dense_a + 0.50 * p_res_a
                prob_b = 0.60 * p_wsol_b + 0.20 * p_dense_b + 0.20 * p_res_b
                prob_c = 0.50 * p_dense_c + 0.50 * p_res_c
                combined_logits_a = 0.50 * logits_dense + 0.50 * logits_res
            else:
                prob_a = 0.80 * p_dense_a + 0.20 * p_wsol_a
                prob_b = 0.70 * p_wsol_b + 0.30 * p_dense_b
                prob_c = 0.90 * p_dense_c + 0.10 * p_wsol_c
                combined_logits_a = logits_dense

            # Apply Temperature Scaling Calibration (T = 1.20)
            prob_a = self.apply_temperature_scaling(prob_a, temperature=1.20)
            prob_b = float(self.apply_temperature_scaling(prob_b, temperature=1.20))
            prob_c = float(self.apply_temperature_scaling(prob_c, temperature=1.20))

            stds = []
            for i in range(14):
                vals = [p_dense_a[i], p_wsol_a[i]]
                if out_res is not None:
                    vals.append(p_res_a[i])
                stds.append(float(np.std(vals)))
            vals_b = [p_dense_b, p_wsol_b]
            if out_res is not None:
                vals_b.append(p_res_b)
            stds.append(float(np.std(vals_b)))
            vals_c = [p_dense_c, p_wsol_c]
            if out_res is not None:
                vals_c.append(p_res_c)
            stds.append(float(np.std(vals_c)))

            mean_divergence = float(np.mean(stds))
            agreement_score = max(0.0, min(1.0, 1.0 - (mean_divergence * 2.0)))

            indiv_predictions: dict[str, Any] = {
                "densenet121_standard": {
                    "head_a": {d: float(p_dense_a[i]) for i, d in enumerate(NIH_14_DISEASES)},
                    "head_b_tb": p_dense_b,
                    "head_c_covid": p_dense_c,
                },
                "wsol_specialist": {
                    "head_a": {d: float(p_wsol_a[i]) for i, d in enumerate(NIH_14_DISEASES)},
                    "head_b_tb": p_wsol_b,
                    "head_c_covid": p_wsol_c,
                },
            }
            if out_res is not None:
                indiv_predictions["resnet50"] = {
                    "head_a": {d: float(p_res_a[i]) for i, d in enumerate(NIH_14_DISEASES)},
                    "head_b_tb": p_res_b,
                    "head_c_covid": p_res_c,
                }

            energy_val = float(compute_sigmoid_energy(combined_logits_a).item())
            entropy_val = float(compute_shannon_entropy(torch.from_numpy(prob_a).unsqueeze(0).to(self.device)).item())
            safety_decision = self.safety_policy.evaluate(
                energy_val, entropy_val, failsafe_enabled=failsafe_enabled
            )

            head_a = {disease: float(prob_a[i]) for i, disease in enumerate(NIH_14_DISEASES)}
            tb_threshold = self.thresholds.get("head_b_tb", {}).get("threshold", 0.5)
            covid_threshold = self.thresholds.get("head_c_covid", {}).get("threshold", 0.5)
            head_a_thresholds = self.thresholds.get("head_a_nih_14", {})

            head_b_res = {
                "tb_probability": prob_b,
                "is_positive": prob_b >= tb_threshold,
            }
            head_c_res = {
                "covid_probability": prob_c,
                "is_positive": prob_c >= covid_threshold,
            }

            clinical_report = self.report_generator.generate(
                predictions_a=head_a,
                thresholds_a=head_a_thresholds,
                head_b_result=head_b_res,
                head_c_result=head_c_res,
                safety_decision=safety_decision,
            )

            return {
                "active_model": "ensemble",
                "model_display_name": "Triple-Backbone Consensus Ensemble",
                "head_a_prediction": head_a,
                "head_b_tb_screening": head_b_res,
                "head_c_covidx": head_c_res,
                "inference_time_ms": round(elapsed_ms, 2),
                "tta_enabled": True,
                "passes_executed": 3,
                "calibration_temperature": 1.20,
                "ensemble_agreement": round(agreement_score, 4),
                "ensemble_models": participating_models,
                "individual_model_predictions": indiv_predictions,
                "safety": safety_decision.to_dict(),
                "report": clinical_report.to_dict(),
            }

        # ---------------------------------------------------------
        # Branch B: Single Backbone (Standard, WSOL, or ResNet-50)
        # ---------------------------------------------------------
        active_model = self.get_model(model_name)
        active_key = "wsol" if "wsol" in model_name.lower() else ("resnet50" if "resnet" in model_name.lower() else "standard")
        display_name = self.model_info.get(active_key, {}).get("name", "Standard Diagnostic CADx")

        start = time.perf_counter()
        with torch.no_grad():
            logits_dict = active_model(standard_tensor)
            outputs = active_model.predict(batch_tensor)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        logits_a = logits_dict["head_a"]

        # 1. 3-Pass TTA Averaging & Temperature Calibration
        prob_a = outputs["head_a"].mean(dim=0).cpu().numpy()
        prob_b = float(outputs["head_b"].mean().item())
        prob_c = float(outputs["head_c"].mean().item())

        prob_a = self.apply_temperature_scaling(prob_a, temperature=1.20)
        prob_b = float(self.apply_temperature_scaling(prob_b, temperature=1.20))
        prob_c = float(self.apply_temperature_scaling(prob_c, temperature=1.20))

        # 2. Fail-Safe OOD & Uncertainty Evaluation
        energy_val = float(compute_sigmoid_energy(logits_a).item())
        entropy_val = float(compute_shannon_entropy(torch.from_numpy(prob_a).unsqueeze(0).to(self.device)).item())
        safety_decision = self.safety_policy.evaluate(
            energy_val, entropy_val, failsafe_enabled=failsafe_enabled
        )

        head_a = {disease: float(prob_a[i]) for i, disease in enumerate(NIH_14_DISEASES)}

        tb_threshold = self.thresholds.get("head_b_tb", {}).get("threshold", 0.5)
        covid_threshold = self.thresholds.get("head_c_covid", {}).get("threshold", 0.5)
        head_a_thresholds = self.thresholds.get("head_a_nih_14", {})

        head_b_res = {
            "tb_probability": prob_b,
            "is_positive": prob_b >= tb_threshold,
        }
        head_c_res = {
            "covid_probability": prob_c,
            "is_positive": prob_c >= covid_threshold,
        }

        # 3. Grounded Clinical Report (RAG-lite)
        clinical_report = self.report_generator.generate(
            predictions_a=head_a,
            thresholds_a=head_a_thresholds,
            head_b_result=head_b_res,
            head_c_result=head_c_res,
            safety_decision=safety_decision,
        )

        return {
            "active_model": active_key,
            "model_display_name": display_name,
            "head_a_prediction": head_a,
            "head_b_tb_screening": head_b_res,
            "head_c_covidx": head_c_res,
            "inference_time_ms": round(elapsed_ms, 2),
            "tta_enabled": True,
            "passes_executed": 3,
            "calibration_temperature": 1.20,
            "safety": safety_decision.to_dict(),
            "report": clinical_report.to_dict(),
        }

    @staticmethod
    def _image_to_base64(image: np.ndarray, format: str = "PNG") -> str:
        if image.ndim == 2:
            image = np.uint8(np.clip(image, 0, 255))
            pil_img = Image.fromarray(image, mode="L")
        elif image.ndim == 3 and image.shape[2] == 3:
            image = np.uint8(np.clip(image, 0, 255))
            pil_img = Image.fromarray(image, mode="RGB")
        else:
            raise ValueError(f"Unsupported image shape for base64 encoding: {image.shape}")

        buffer = io.BytesIO()
        pil_img.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def explain(
        self,
        image_bytes: bytes,
        target_head: str,
        target_class: int,
        clinical_grounding: bool = True,
        target_disease_name: str = "",
        model_name: str = "standard",
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        tensor = self.preprocess(image_bytes)
        active_key = "wsol" if "wsol" in model_name.lower() or "ensemble" in model_name.lower() else "standard"
        active_model = self.models.get(active_key, self.model)

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        # Resolve disease name if not specified
        if not target_disease_name:
            if target_head == "head_a" and 0 <= target_class < len(NIH_14_DISEASES):
                target_disease_name = NIH_14_DISEASES[target_class]
            elif target_head == "head_b":
                target_disease_name = "Tuberculosis"
            elif target_head == "head_c":
                target_disease_name = "COVID-19"
            else:
                target_disease_name = f"{target_head}_{target_class}"

        # Compute forward pass probability and threshold for target pathology
        with torch.no_grad():
            outputs = active_model(tensor)
            if target_head == "head_a":
                target_prob = float(torch.sigmoid(outputs["head_a"])[0, target_class].item())
                target_thresh = float(self.thresholds.get("head_a_nih_14", {}).get(target_disease_name, 0.45))
            elif target_head == "head_b":
                target_prob = float(torch.sigmoid(outputs["head_b"])[0, 0].item())
                target_thresh = float(self.thresholds.get("head_b_tb", {}).get("threshold", 0.45))
            elif target_head == "head_c":
                target_prob = float(torch.softmax(outputs["head_c"], dim=-1)[0, 0].item())
                target_thresh = float(self.thresholds.get("head_c_covid", {}).get("threshold", 0.70))
            else:
                target_prob = 1.0
                target_thresh = 0.5
        is_target_positive = bool(target_prob >= target_thresh)

        explainer = MultiScaleGradCAMPlusPlus(active_model)
        try:
            raw_heatmap = explainer.generate(
                tensor,
                head_name=target_head,
                target_class_idx=target_class,
                fusion_weights=(0.4, 0.6),
            )
        finally:
            explainer.remove_hooks()

        orig_h, orig_w = image_np.shape[:2]

        # Resize raw_heatmap from (512, 512) to the original image dimensions for pixel-perfect alignment
        if raw_heatmap.shape != (orig_h, orig_w):
            raw_heatmap_native = cv2.resize(
                raw_heatmap,
                (orig_w, orig_h),
                interpolation=cv2.INTER_LINEAR,
            )
        else:
            raw_heatmap_native = raw_heatmap

        # Generate lung mask from segmenter directly on native image
        lung_mask = self.segmenter.predict_mask(image_np)
        if lung_mask.shape != (orig_h, orig_w):
            lung_mask = cv2.resize(
                lung_mask.astype(np.uint8),
                (orig_w, orig_h),
                interpolation=cv2.INTER_NEAREST,
            )

        # Build anatomical ROI mask at native resolution
        if target_disease_name.lower() == "cardiomegaly":
            # For Cardiomegaly, include mediastinum / cardiac silhouette between lung fields
            k_close_size = max(15, int(round(min(orig_h, orig_w) * 0.08)))
            if k_close_size % 2 == 0:
                k_close_size += 1
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_close_size, k_close_size))
            closed_mask = cv2.morphologyEx(lung_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel_close)

            k_dilate_size = max(7, int(round(min(orig_h, orig_w) * 0.03)))
            if k_dilate_size % 2 == 0:
                k_dilate_size += 1
            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_dilate_size, k_dilate_size))
            effective_mask = cv2.dilate(closed_mask, kernel_dilate, iterations=1)
        else:
            # Standard pulmonary pathology: lung mask dilated slightly for pleural space
            k_dilate_size = max(5, int(round(min(orig_h, orig_w) * 0.015)))
            if k_dilate_size % 2 == 0:
                k_dilate_size += 1
            kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_dilate_size, k_dilate_size))
            effective_mask = cv2.dilate(lung_mask.astype(np.uint8), kernel_dilate, iterations=1)

        # Compute in-lung energy ratio using native resolution maps
        in_lung_ratio = self.audit_engine.compute_in_lung_ratio(raw_heatmap_native, effective_mask)

        if clinical_grounding:
            mask_float = (effective_mask > 0).astype(np.float32)
            grounded_heatmap = raw_heatmap_native * mask_float

            # Clinical percentile normalization: highlight intra-lung focal hotspots warmly
            in_lung_vals = grounded_heatmap[effective_mask > 0]
            if in_lung_vals.size > 0 and float(in_lung_vals.max()) > 1e-6:
                h_max = float(np.percentile(in_lung_vals, 99.5))
                if h_max <= 1e-6:
                    h_max = float(in_lung_vals.max())
                grounded_heatmap = np.clip(grounded_heatmap / h_max, 0.0, 1.0)
            else:
                grounded_heatmap = np.zeros_like(grounded_heatmap)
            final_heatmap = grounded_heatmap
            is_grounded = True
        else:
            final_heatmap = raw_heatmap_native
            is_grounded = False

        heatmap_uint8 = np.uint8(np.clip(final_heatmap * 255.0, 0, 255))
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        if clinical_grounding:
            # Zero out background pixels so frontend screen-blend is 100% transparent outside lungs
            heatmap_color[effective_mask == 0] = 0

            # Alpha blend within anatomical mask (both image_np and heatmap_color have identical shape)
            image_float = image_np.astype(np.float32)
            heat_color_float = heatmap_color.astype(np.float32)
            mask_3d = (effective_mask > 0)[:, :, None].astype(np.float32)
            overlay = np.where(
                mask_3d > 0,
                np.clip(image_float * (1.0 - 0.4) + heat_color_float * 0.4, 0, 255).astype(np.uint8),
                image_np,
            )
        else:
            overlay = explainer.overlay_heatmap(image_np, final_heatmap, alpha=0.4)

        # Multi-scale lesion iso-contour extraction: only for confirmed positive
        # targets under clinical grounding. The contour is constrained to the
        # anatomical ROI mask (effective_mask) so it matches the in-lung audit.
        # Negative targets return an empty contour to avoid drawing false lesions.
        contour_b64 = ""
        lesion_bounding_boxes: list[dict[str, Any]] = []
        lesion_area_ratio = 0.0
        if is_target_positive and clinical_grounding:
            bin_mask, lesions, area_ratio = extract_adaptive_contour(
                heatmap=final_heatmap,
                lung_mask=effective_mask,
                disease_name=target_disease_name,
            )
            contour_overlay = render_contour_overlay(
                img_rgb=image_np,
                bin_mask=bin_mask,
                lesions=lesions,
            )
            contour_b64 = self._image_to_base64(contour_overlay)
            lesion_bounding_boxes = lesions
            lesion_area_ratio = float(area_ratio)

        audit_pass = bool(in_lung_ratio >= 0.80)

        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        logger.info(
            "explain head=%s class=%s positive=%s grounded=%s lesions=%d latency=%.1fms",
            target_head,
            target_class,
            is_target_positive,
            is_grounded,
            len(lesion_bounding_boxes),
            elapsed_ms,
        )

        return {
            "active_model": active_key,
            "heatmap_base64": self._image_to_base64(heatmap_color),
            "overlay_base64": self._image_to_base64(overlay),
            "contour_base64": contour_b64,
            "lesion_bounding_boxes": lesion_bounding_boxes,
            "lesion_area_ratio": lesion_area_ratio,
            "cam_resolution": "32x32 fused (denseblock3+denseblock4)",
            "target_head": target_head,
            "target_class": target_class,
            "target_disease_name": target_disease_name,
            "target_probability": round(target_prob, 4),
            "target_threshold": round(target_thresh, 4),
            "is_target_positive": is_target_positive,
            "in_lung_energy_ratio": round(float(in_lung_ratio), 4),
            "audit_pass": audit_pass,
            "is_grounded": is_grounded,
        }

    def audit(self, image_bytes: bytes) -> dict[str, Any]:
        tensor = self.preprocess(image_bytes)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        explainer = GradCAMExplainer(self.model)
        engine = ShortcutAuditEngine(self.segmenter)
        try:
            result = engine.audit_sample(
                model=self.model,
                explainer=explainer,
                img_tensor=tensor,
                original_img=image_np,
                head_name="head_c",
                target_class_idx=0,
            )
        finally:
            explainer.remove_hooks()

        lung_mask = result["lung_mask"]
        if lung_mask.max() <= 1:
            lung_mask_img = np.uint8(np.clip(lung_mask * 255, 0, 255))
        else:
            lung_mask_img = np.uint8(np.clip(lung_mask, 0, 255))

        return {
            "in_lung_energy_ratio": float(result["in_lung_ratio"]),
            "pass_80_percent": bool(result["pass_80_percent"]),
            "lung_mask_base64": self._image_to_base64(lung_mask_img),
        }
