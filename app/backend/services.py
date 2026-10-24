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

    def explain(self, image_bytes: bytes, target_head: str, target_class: int) -> dict[str, Any]:
        tensor = self.preprocess(image_bytes)

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        explainer = GradCAMExplainer(self.model)
        try:
            heatmap = explainer.generate(
                tensor,
                head_name=target_head,
                target_class_idx=target_class,
            )
            overlay = explainer.overlay_heatmap(image_np, heatmap, alpha=0.4)
        finally:
            explainer.remove_hooks()

        heatmap_uint8 = np.uint8(np.clip(heatmap * 255.0, 0, 255))
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        return {
            "heatmap_base64": self._image_to_base64(heatmap_color),
            "overlay_base64": self._image_to_base64(overlay),
            "target_head": target_head,
            "target_class": target_class,
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
