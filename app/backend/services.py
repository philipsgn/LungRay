"""Core inference/explanation/audit service for the LungRay FastAPI backend."""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from src.data.transforms import get_val_transforms
from src.explainability import GradCAMExplainer, LungSegmenter, ShortcutAuditEngine
from src.models.multi_task_net import MultiTaskChestXrayNet

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
        self.version = "v4.0"
        self.img_size = 512
        self.thresholds = self._load_thresholds()
        self.model = self._load_model()
        self.transform = get_val_transforms(img_size=self.img_size)
        self.segmenter = LungSegmenter()
        self.audit_engine = ShortcutAuditEngine(self.segmenter)
        self._initialized = True

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

    def _load_model(self) -> MultiTaskChestXrayNet:
        model = MultiTaskChestXrayNet(
            backbone_name="densenet121",
            pretrained=False,
            img_size=self.img_size,
            num_classes_a=14,
            num_classes_b=1,
            num_classes_c=1,
        )

        checkpoint_path = "checkpoints/best_model.pth"
        if os.path.exists(checkpoint_path):
            logger.info("Loading checkpoint from %s", checkpoint_path)
            state = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            if isinstance(state, dict) and "model_state_dict" in state:
                state = state["model_state_dict"]
            elif isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            model.load_state_dict(state)
        else:
            logger.warning(
                "No checkpoint found at %s; using randomly-initialized weights.",
                checkpoint_path,
            )

        model.to(self.device)
        model.eval()
        return model

    def preprocess(self, image_bytes: bytes) -> torch.Tensor:
        """Convert raw image bytes to a batched (1, 3, 512, 512) tensor."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as exc:
            raise ValueError(f"Cannot decode uploaded image: {exc}") from exc

        image = image.convert("RGB")
        image_np = np.array(image)
        transformed = self.transform(image=image_np)["image"]
        return transformed.unsqueeze(0).to(self.device)

    def predict(self, image_bytes: bytes) -> dict[str, Any]:
        tensor = self.preprocess(image_bytes)

        start = time.perf_counter()
        with torch.no_grad():
            outputs = self.model.predict(tensor)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        prob_a = outputs["head_a"][0].cpu().numpy()
        prob_b = float(outputs["head_b"][0].item())
        prob_c = float(outputs["head_c"][0].item())

        head_a = {disease: float(prob_a[i]) for i, disease in enumerate(NIH_14_DISEASES)}

        tb_threshold = self.thresholds.get("head_b_tb", {}).get("threshold", 0.5)
        covid_threshold = self.thresholds.get("head_c_covid", {}).get("threshold", 0.5)

        return {
            "head_a_prediction": head_a,
            "head_b_tb_screening": {
                "tb_probability": prob_b,
                "is_positive": prob_b >= tb_threshold,
            },
            "head_c_covidx": {
                "covid_probability": prob_c,
                "is_positive": prob_c >= covid_threshold,
            },
            "inference_time_ms": round(elapsed_ms, 2),
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
    ) -> dict[str, Any]:
        tensor = self.preprocess(image_bytes)

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

        explainer = GradCAMExplainer(self.model)
        try:
            raw_heatmap = explainer.generate(
                tensor,
                head_name=target_head,
                target_class_idx=target_class,
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

        return {
            "heatmap_base64": self._image_to_base64(heatmap_color),
            "overlay_base64": self._image_to_base64(overlay),
            "target_head": target_head,
            "target_class": target_class,
            "target_disease_name": target_disease_name,
            "in_lung_energy_ratio": round(float(in_lung_ratio), 4),
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
