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

try:
    import pydicom
    from pydicom.pixel_data_handlers.util import (
        apply_modality_lut,
        apply_voi_lut,
        convert_color_space,
    )
except ImportError:
    pydicom = None
    apply_modality_lut = None
    apply_voi_lut = None
    convert_color_space = None

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

        self.serving_profile = os.getenv("LUNGRAY_SERVING_PROFILE", "auto")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.version = "v7.0"
        self.img_size = 512
        self.thresholds = self._load_thresholds("configs/optimal_thresholds_20_11.json")
        self.ag_thresholds = self._load_thresholds("configs/ag_mtcnet_thresholds.json") if self.serving_profile != "standard" else {}
        self.models: dict[str, MultiTaskChestXrayNet] = {}
        self.model_info: dict[str, dict[str, Any]] = {}
        self._load_hybrid_models()
        self.model = self.models.get("standard") or next(iter(self.models.values()))
        self.transform = get_val_transforms(img_size=self.img_size)
        self.ag_transform = get_val_transforms(img_size=512)
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
        if self.serving_profile == "standard":
            return None
        checkpoint = os.getenv("DENSE_UNET_CHECKPOINT", "checkpoints/dense_unet_best.pth")
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
            model.inference_size = int(state.get("img_size", 256))
            for key in ("model_state_dict", "state_dict"):
                if key in state:
                    state = state[key]
                    break
        model.load_state_dict(state, strict=True)
        model.to(self.device)
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        logger.info("Loaded frozen Dense-UNet segmentation gate from %s", checkpoint)
        return model

    @torch.inference_mode()
    def _anatomical_gate(self, image_np: np.ndarray, force: bool = False) -> np.ndarray:
        """
        Inference-time Dilated Soft Anatomical Masking gate (Dilation 6%,
        attenuation 10% on the outer thoracic background).

        The gate runs detached, in numpy space and under ``torch.inference_mode``,
        so no autograd graph is ever attached to the returned image. Grad-CAM
        gradients therefore still flow only through the diagnostic backbone and
        never leak into the segmentation network, and the diagnostic weights are
        never modified.
        """
        if not force and not getattr(self, "anatomical_gate_enabled", False):
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

    @staticmethod
    def _input_quality_reasons(image_np: np.ndarray) -> list[str]:
        """Reject only obvious blank or unstructured-noise inputs before inference."""
        image = np.asarray(image_np)
        if image.size == 0 or not np.isfinite(image).all():
            return ["Ảnh đầu vào rỗng hoặc chứa giá trị không hữu hạn."]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
        gray = gray.astype(np.float32)
        contrast = float(gray.std())
        if contrast < 2.0:
            return ["Ảnh gần như đơn sắc, không đủ tương phản để phân tích an toàn."]
        if gray.shape[0] > 1 and gray.shape[1] > 1:
            adjacent_difference = 0.5 * (
                float(np.abs(np.diff(gray, axis=0)).mean())
                + float(np.abs(np.diff(gray, axis=1)).mean())
            )
            normalized_high_frequency = adjacent_difference / max(contrast, 1e-6)
            if normalized_high_frequency > 1.05:
                return [
                    "Ảnh có biến thiên tần số cao tương thích với nhiễu ngẫu nhiên; "
                    "cần xác nhận phim X-quang gốc trước khi phân tích."
                ]
        return []

    def _audit_ag_covid_focus(
        self,
        model: MultiTaskChestXrayNet,
        tensor: torch.Tensor,
        original_image: np.ndarray,
    ) -> float:
        """Measure COVID Grad-CAM energy in a trained Dense-UNet lung mask."""
        if self.dense_unet is None:
            raise RuntimeError("Dense-UNet checkpoint unavailable; lung-energy audit cannot be validated.")
        explainer = GradCAMExplainer(model)
        try:
            audit = self.audit_engine.audit_sample(
                model=model,
                explainer=explainer,
                img_tensor=tensor,
                original_img=original_image,
                head_name="head_c",
                target_class_idx=0,
            )
            return float(audit["in_lung_ratio"])
        finally:
            explainer.remove_hooks()

    def _load_thresholds(self, path: str = "configs/optimal_thresholds.json") -> dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Could not load thresholds from %s: %s", path, exc)
            return {
                "head_a_nih_14": {d: 0.5 for d in NIH_14_DISEASES},
                "head_b_tb": {"threshold": 0.5},
                "head_c_covid": {"threshold": 0.5},
            }

    def _instantiate_and_load(
        self, checkpoint_path: str, backbone_name: str = "densenet121", strict: bool = False
    ) -> MultiTaskChestXrayNet:
        num_classes_c = 1
        state = None
        if os.path.exists(checkpoint_path):
            logger.info("Loading checkpoint from %s for %s", checkpoint_path, backbone_name)
            raw_state = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            if isinstance(raw_state, dict) and "model_state_dict" in raw_state:
                state = raw_state["model_state_dict"]
            elif isinstance(raw_state, dict) and "state_dict" in raw_state:
                state = raw_state["state_dict"]
            elif isinstance(raw_state, dict):
                state = raw_state

            if isinstance(state, dict) and "head_c.weight" in state:
                num_classes_c = int(state["head_c.weight"].shape[0])

        model = MultiTaskChestXrayNet(
            backbone_name=backbone_name,
            pretrained=False,
            img_size=self.img_size,
            num_classes_a=14,
            num_classes_b=1,
            num_classes_c=num_classes_c,
        )

        if state is not None:
            model.load_state_dict(state, strict=strict)
        elif strict:
            raise FileNotFoundError(f"Required model checkpoint was not found: {checkpoint_path}")
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
        configured_standard = os.getenv("CHECKPOINT_PATH")
        if configured_standard and os.path.isfile(configured_standard):
            self.standard_path = configured_standard
        elif os.path.isfile("checkpoints/best_model_20_11.pth"):
            self.standard_path = "checkpoints/best_model_20_11.pth"
        else:
            self.standard_path = "checkpoints/best_model.pth"
        self.wsol_path = "checkpoints/best_wsol_finetune.pth"
        self.resnet_path = "checkpoints/best_resnet50.pth"

        # 1. Standard CADx model (SOTA Asymmetric Net)
        self.models["standard"] = self._instantiate_and_load(self.standard_path, backbone_name="densenet121", strict=True)
        self.current_checkpoint = self.standard_path
        self.model_info["standard"] = {
            "id": "standard",
            "name": "Standard Diagnostic CADx (SOTA)",
            "role": "Primary emergency triaging across 16 cardiopulmonary conditions (Multi-Task Mean AUC 0.91)",
            "checkpoint": self.standard_path,
            "metrics": {
                "head_a_test_auc": 0.7508,
                "head_b_test_auc": 1.0000,
                "head_c_test_auc": 0.7692,
                "metric_source": "stored independent-test artifact; not recomputed at API startup",
            },
        }

        if self.serving_profile == "standard":
            return

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

        if "wsol" not in self.models:
            self.model_info.pop("ensemble", None)

        # 5. AG-MTCNet Flagship (Anatomically-Gated Multi-Task Network)
        candidates_ag = [
            os.getenv("AG_MTCNET_CHECKPOINT", ""),
            "checkpoints/ag_mtcnet_best.pth",
        ]
        ag_ckpt = next((p for p in candidates_ag if p and os.path.isfile(p)), None)
        if ag_ckpt is None:
            logger.info("AG-MTCNet checkpoint absent; serving available models only.")
            return
        self.ag_mtcnet_path = ag_ckpt
        self.models["ag_mtcnet"] = self._instantiate_and_load(
            ag_ckpt, backbone_name="densenet121", strict=True
        )
        self.model_info["ag_mtcnet"] = {
            "id": "ag_mtcnet",
            "name": "AG-MTCNet 512 (research candidate)",
            "role": "Exploratory 512-pixel three-head output with clinical safety review",
            "checkpoint": ag_ckpt,
            "metrics": {
                "head_a_test_auc_checkpoint_metadata": 0.6230,
                "head_b_test_auc_checkpoint_metadata": 0.9986,
                "head_c_test_auc_checkpoint_metadata": 0.6004,
                "head_c_validation_auc_checkpoint_metadata": 0.9171,
                "metric_source": "checkpoint_metadata_not_independently_recomputed",
                "head_c_status": "exploratory",
                "resolution": [512, 512],
                "clinical_use": "not_validated",
            },
        }

    def check_and_reload_checkpoints(self) -> dict[str, Any]:
        """
        Dynamically detects new or updated checkpoints (e.g., best_resnet50.pth)
        and reloads them into the running inference service with zero downtime.
        """
        if self.serving_profile == "standard":
            return {"status": "success", "active_models": ["standard"], "reloaded": [], "triple_consensus_ready": False}
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
        if model_name not in self.model_info:
            raise ValueError(f"Model unavailable: {model_name}. Select a model returned by /api/v1/models.")
        if "ag_mtcnet" in name_lower or "ag-mtcnet" in name_lower:
            return self.models.get("ag_mtcnet", self.models.get("standard", self.model))
        elif "wsol" in name_lower:
            return self.models.get("wsol", self.model)
        elif "resnet" in name_lower:
            return self.models.get("resnet50", self.model)
        elif "ensemble" in name_lower:
            return self.models.get("standard", self.model)
        return self.models.get("standard", self.model)

    def list_models(self) -> list[dict[str, Any]]:
        models = []
        for model_info in self.model_info.values():
            public_info = dict(model_info)
            public_info["metrics"] = dict(public_info.get("metrics", {}))
            models.append(public_info)
        return models

    @staticmethod
    def _dicom_to_rgb(dataset: pydicom.dataset.Dataset) -> np.ndarray:
        """Convert a DICOM pixel array to displayable RGB uint8 pixels."""
        if "PixelData" not in dataset:
            raise ValueError("DICOM file has no PixelData element.")

        try:
            pixels = np.asarray(dataset.pixel_array)
        except Exception as exc:
            raise ValueError(f"Cannot decode DICOM pixel data: {exc}") from exc

        samples_per_pixel = int(getattr(dataset, "SamplesPerPixel", 1))
        photometric = str(getattr(dataset, "PhotometricInterpretation", "MONOCHROME2"))

        # A multi-frame radiograph is treated as a single image using its first frame.
        if pixels.ndim == 4:
            pixels = pixels[0]
        elif pixels.ndim == 3 and not (
            samples_per_pixel > 1 and pixels.shape[-1] in (3, 4)
        ):
            pixels = pixels[0]

        if samples_per_pixel > 1 or (pixels.ndim == 3 and pixels.shape[-1] in (3, 4)):
            if pixels.ndim != 3 or pixels.shape[-1] not in (3, 4):
                raise ValueError(
                    f"Unsupported color DICOM pixel shape: {pixels.shape}."
                )
            if photometric.startswith("YBR"):
                try:
                    pixels = convert_color_space(pixels, photometric, "RGB")
                except Exception as exc:
                    raise ValueError(
                        f"Cannot convert DICOM color space {photometric}: {exc}"
                    ) from exc
            pixels = pixels[..., :3].astype(np.float32)
            finite = np.isfinite(pixels)
            if not finite.any():
                raise ValueError("DICOM color image contains no finite pixel values.")
            low, high = np.percentile(pixels[finite], (0.5, 99.5))
            if high <= low:
                high = low + 1.0
            scaled = np.clip((pixels - low) * (255.0 / (high - low)), 0, 255)
            return np.ascontiguousarray(scaled.astype(np.uint8))

        if pixels.ndim != 2:
            raise ValueError(f"Unsupported grayscale DICOM pixel shape: {pixels.shape}.")

        try:
            pixels = apply_modality_lut(pixels, dataset)
        except Exception as exc:
            raise ValueError(f"Cannot apply DICOM modality transform: {exc}") from exc

        if "WindowCenter" in dataset and "WindowWidth" in dataset:
            try:
                pixels = apply_voi_lut(pixels, dataset)
            except Exception as exc:
                logger.warning(
                    "DICOM VOI LUT could not be applied (%s); using robust scaling.",
                    exc,
                )

        pixels = np.asarray(pixels, dtype=np.float32)
        finite = np.isfinite(pixels)
        if not finite.any():
            raise ValueError("DICOM grayscale image contains no finite pixel values.")
        low, high = np.percentile(pixels[finite], (0.5, 99.5))
        if high <= low:
            high = low + 1.0
        scaled = np.clip((pixels - low) * (255.0 / (high - low)), 0, 255)
        if photometric == "MONOCHROME1":
            scaled = 255.0 - scaled
        gray = np.ascontiguousarray(scaled.astype(np.uint8))
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    @classmethod
    def _decode_uploaded_image(cls, image_bytes: bytes) -> Image.Image:
        """Decode standard raster images or DICOM bytes into an RGB PIL image."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                return image.convert("RGB")
        except Exception as raster_error:
            if pydicom is not None:
                try:
                    dataset = pydicom.dcmread(io.BytesIO(image_bytes), force=True)
                    rgb = cls._dicom_to_rgb(dataset)
                    return Image.fromarray(rgb)
                except Exception as dicom_error:
                    raise ValueError(
                        "Cannot decode uploaded image as PNG/JPEG or DICOM "
                        f"(raster: {raster_error}; DICOM: {dicom_error})."
                    ) from dicom_error
            raise ValueError(
                f"Cannot decode uploaded image as PNG/JPEG (error: {raster_error})."
            ) from raster_error

    def preprocess(self, image_bytes: bytes, ag_mtcnet: bool = False) -> torch.Tensor:
        """Convert uploaded raster or DICOM bytes to the selected model's input size."""
        image = self._decode_uploaded_image(image_bytes)

        image_np = np.array(image)
        image_np = self._anatomical_gate(image_np, force=ag_mtcnet)
        transform = self.ag_transform if ag_mtcnet else self.transform
        transformed = transform(image=image_np)["image"]
        return transformed.unsqueeze(0).to(self.device)

    def preprocess_tta(self, image_bytes: bytes, force_gate: bool = False) -> torch.Tensor:
        """
        Generate a 3-pass augmented batch tensor (3, 3, 512, 512) for clinical test-time augmentation:
        - Pass 1: Original normalized view
        - Pass 2: Horizontal flip
        - Pass 3: CLAHE contrast view
        """
        image = self._decode_uploaded_image(image_bytes)
        image_np = np.array(image)

        # Anatomical gate applied once to the base image; all TTA passes are
        # derived from the already-masked image for geometric consistency.
        image_np = self._anatomical_gate(image_np, force=force_gate)

        # All selected diagnostic checkpoints are served at 512 px.
        transform = self.ag_transform if force_gate else self.transform

        # Pass 1: Original
        t1 = transform(image=image_np)["image"]

        # Pass 2: Horizontal flip
        try:
            flipped_np = cv2.flip(image_np, 1)
            t2 = transform(image=flipped_np)["image"]
        except Exception:
            t2 = t1.clone()

        # Pass 3: CLAHE contrast view
        try:
            lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            clahe_np = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            t3 = transform(image=clahe_np)["image"]
        except Exception:
            t3 = t1.clone()

        # Stack into a single batched tensor (3, 3, 512, 512)
        batch_tensor = torch.stack([t1, t2, t3], dim=0).to(self.device)
        return batch_tensor

    @staticmethod
    def _extract_covid_prob(tensor: torch.Tensor) -> float:
        if tensor.ndim > 1 and tensor.shape[-1] == 3:
            # COVIDx 3-class format: index 2 corresponds to COVID-19
            return float(tensor[:, 2].mean().item())
        return float(tensor.mean().item())

    @staticmethod
    def _covid_prob_from_logits(logits: torch.Tensor) -> float:
        if logits.shape[-1] == 3:
            return float(torch.softmax(logits, dim=-1)[0, 2].item())
        return float(torch.sigmoid(logits)[0, 0].item())

    @staticmethod
    def _is_ag_mtcnet(model_name: str) -> bool:
        normalized = model_name.strip().lower().replace("-", "_")
        return "ag_mtcnet" in normalized

    @staticmethod
    def _thresholds_for_task(config: dict[str, Any], task: str) -> dict[str, Any]:
        if task == "head_a":
            value = config.get("head_a_nih_14", config.get("head_a", {}))
            return value if isinstance(value, dict) else {}
        if task == "head_b":
            value = config.get("head_b_tb", config.get("head_b", {}))
        else:
            value = config.get("head_c_covid", config.get("head_c_covid_binary", {}))
        if isinstance(value, (int, float)):
            return {"threshold": float(value)}
        if not isinstance(value, dict):
            return {}
        if "threshold" in value:
            return value
        numeric_values = [item for item in value.values() if isinstance(item, (int, float))]
        return {"threshold": float(numeric_values[0])} if len(numeric_values) == 1 else value

    def predict(
        self,
        image_bytes: bytes,
        model_name: str = "standard",
        failsafe_enabled: bool = True,
        tta_enabled: bool = True,
    ) -> dict[str, Any]:
        request_started_at = time.perf_counter()
        # Dynamic hot-reload check
        self.check_and_reload_checkpoints()

        is_ag_mtcnet = self._is_ag_mtcnet(model_name)
        active_thresholds = self.ag_thresholds if is_ag_mtcnet else self.thresholds
        selected_key = (
            "ag_mtcnet" if is_ag_mtcnet else
            "wsol" if "wsol" in model_name.lower() else
            "resnet50" if "resnet" in model_name.lower() else
            "ensemble" if "ensemble" in model_name.lower() else "standard"
        )

        if selected_key not in self.model_info:
            raise ValueError(f"Model unavailable: {selected_key}")
        source_image = np.asarray(self._decode_uploaded_image(image_bytes))
        quality_reasons = self._input_quality_reasons(source_image)
        if quality_reasons:
            # Input-quality rejects remain active even when the optional OOD
            # bypass is requested; blank/noise images never receive predictions.
            safety_decision = self.safety_policy.evaluate(0.0, 0.0, failsafe_enabled=True)
            safety_decision.rejection_reasons.extend(quality_reasons)
            head_a = {disease: 0.0 for disease in NIH_14_DISEASES}
            head_b = {"tb_probability": 0.0, "is_positive": False}
            head_c = {
                "available": True,
                "status": "REJECTED_INPUT",
                "covid_probability": 0.0,
                "threshold": self._thresholds_for_task(active_thresholds, "head_c").get("threshold", 0.5),
                "is_positive": False,
                "model_is_positive": False,
                "clinical_suspicion": False,
                "guardrail_reasons": quality_reasons,
            }
            report = self.report_generator.generate({}, {}, safety_decision=safety_decision)
            return {
                "active_model": selected_key,
                "model_display_name": self.model_info.get(selected_key, {}).get("name", selected_key),
                "head_a_prediction": head_a,
                "head_b_tb_screening": head_b,
                "head_c_covidx": head_c,
                "inference_time_ms": round((time.perf_counter() - request_started_at) * 1000.0, 2),
                "tta_enabled": False,
                "passes_executed": 0,
                "calibration_temperature": 1.20,
                "safety": safety_decision.to_dict(),
                "report": report.to_dict(),
            }

        # 3-Pass Medical TTA Tensor Generation (applies anatomical gate automatically if AG-MTCNet)
        batch_tensor = self.preprocess_tta(image_bytes, force_gate=is_ag_mtcnet)
        if not tta_enabled:
            batch_tensor = batch_tensor[:1]
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
            p_dense_c = self._extract_covid_prob(out_dense["head_c"])

            p_wsol_a = out_wsol["head_a"].mean(dim=0).cpu().numpy()
            p_wsol_b = float(out_wsol["head_b"].mean().item())
            p_wsol_c = self._extract_covid_prob(out_wsol["head_c"])

            if out_res is not None:
                p_res_a = out_res["head_a"].mean(dim=0).cpu().numpy()
                p_res_b = float(out_res["head_b"].mean().item())
                p_res_c = self._extract_covid_prob(out_res["head_c"])
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
            tb_threshold = self._thresholds_for_task(self.thresholds, "head_b").get("threshold", 0.5)
            covid_threshold = self._thresholds_for_task(self.thresholds, "head_c").get("threshold", 0.5)
            head_a_thresholds = self._thresholds_for_task(self.thresholds, "head_a")

            head_b_res = {
                "tb_probability": prob_b,
                "is_positive": prob_b >= tb_threshold,
            }
            head_c_res = {
                "available": True,
                "covid_probability": prob_c,
                "threshold": covid_threshold,
                "is_positive": prob_c >= covid_threshold,
                "model_is_positive": prob_c >= covid_threshold,
                "clinical_suspicion": prob_c >= covid_threshold,
                "status": "MODEL_THRESHOLD_RESULT",
            }

            clinical_report = self.report_generator.generate(
                predictions_a=head_a,
                thresholds_a=head_a_thresholds,
                head_b_result=head_b_res,
                head_c_result=head_c_res,
                safety_decision=safety_decision,
            )
            elapsed_ms = (time.perf_counter() - request_started_at) * 1000.0

            return {
                "active_model": "ensemble",
                "model_display_name": "Triple-Backbone Consensus Ensemble",
                "head_a_prediction": head_a,
                "head_b_tb_screening": head_b_res,
                "head_c_covidx": head_c_res,
                "inference_time_ms": round(elapsed_ms, 2),
                "tta_enabled": tta_enabled,
                "passes_executed": 3 if tta_enabled else 1,
                "calibration_temperature": 1.20,
                "ensemble_agreement": round(agreement_score, 4),
                "ensemble_models": participating_models,
                "individual_model_predictions": indiv_predictions,
                "safety": safety_decision.to_dict(),
                "report": clinical_report.to_dict(),
            }

        # ---------------------------------------------------------
        # Branch B: Single Backbone (Standard, WSOL, ResNet-50, or AG-MTCNet)
        # ---------------------------------------------------------
        active_key = "ag_mtcnet" if is_ag_mtcnet else ("wsol" if "wsol" in model_name.lower() else ("resnet50" if "resnet" in model_name.lower() else "standard"))
        active_model = self.get_model(active_key)
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
        prob_c = self._extract_covid_prob(outputs["head_c"])

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

        head_b_threshold = self._thresholds_for_task(active_thresholds, "head_b").get("threshold", 0.5)
        covid_threshold = self._thresholds_for_task(active_thresholds, "head_c").get("threshold", 0.5)
        head_a_thresholds = self._thresholds_for_task(active_thresholds, "head_a")

        head_b_res = {
            "tb_probability": prob_b,
            "is_positive": prob_b >= head_b_threshold,
        }
        model_c_positive = prob_c >= covid_threshold
        in_lung_ratio = None
        guardrail_reasons: list[str] = []
        parenchymal_positive = any(
            head_a.get(disease, 0.0) >= head_a_thresholds.get(disease, 0.45)
            for disease in ("Infiltration", "Consolidation", "Pneumonia")
        )
        if is_ag_mtcnet and model_c_positive:
            try:
                in_lung_ratio = self._audit_ag_covid_focus(
                    active_model, standard_tensor, source_image
                )
            except Exception as exc:
                logger.warning("AG-MTCNet lung-energy audit unavailable: %s", exc)
                guardrail_reasons.append("Lung-energy audit unavailable; specialist review required.")
            if in_lung_ratio is not None and in_lung_ratio < 0.80:
                guardrail_reasons.append(
                    f"Only {in_lung_ratio:.1%} of COVID heatmap energy is within the lung mask (<80%)."
                )
            if not parenchymal_positive:
                guardrail_reasons.append(
                    "Head A has no threshold-positive infiltration, consolidation, or pneumonia finding."
                )
        clinical_c_positive = model_c_positive and not guardrail_reasons
        head_c_res = {
            "available": True,
            "status": "EXPLORATORY",
            "covid_probability": prob_c,
            "threshold": covid_threshold,
            "is_positive": clinical_c_positive,
            "model_is_positive": model_c_positive,
            "clinical_suspicion": clinical_c_positive,
            "guardrail_reasons": guardrail_reasons,
            "in_lung_energy_ratio": in_lung_ratio,
        }

        # 3. Grounded Clinical Report (RAG-lite)
        clinical_report = self.report_generator.generate(
            predictions_a=head_a,
            thresholds_a=head_a_thresholds,
            head_b_result=head_b_res,
            head_c_result=head_c_res,
            safety_decision=safety_decision,
            in_lung_ratio=in_lung_ratio,
            guardrail_reasons=guardrail_reasons,
        )
        elapsed_ms = (time.perf_counter() - request_started_at) * 1000.0

        return {
            "active_model": active_key,
            "model_display_name": display_name,
            "head_a_prediction": head_a,
            "head_b_tb_screening": head_b_res,
            "head_c_covidx": head_c_res,
            "inference_time_ms": round(elapsed_ms, 2),
            "tta_enabled": tta_enabled,
            "passes_executed": 3 if tta_enabled else 1,
            "calibration_temperature": 1.20,
            "safety": safety_decision.to_dict(),
            "report": clinical_report.to_dict(),
            "in_lung_energy_ratio": in_lung_ratio,
        }

    @staticmethod
    def _image_to_base64(image: np.ndarray, format: str = "PNG") -> str:
        if image.ndim == 2:
            image = np.uint8(np.clip(image, 0, 255))
            pil_img = Image.fromarray(image, mode="L")
        elif image.ndim == 3 and image.shape[2] == 3:
            image = np.uint8(np.clip(image, 0, 255))
            pil_img = Image.fromarray(image, mode="RGB")
        elif image.ndim == 3 and image.shape[2] == 4:
            image = np.uint8(np.clip(image, 0, 255))
            pil_img = Image.fromarray(image, mode="RGBA")
        else:
            raise ValueError(f"Unsupported image shape for base64 encoding: {image.shape}")

        buffer = io.BytesIO()
        pil_img.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _restore_letterboxed_heatmap(heatmap: np.ndarray, height: int, width: int) -> np.ndarray:
        """Remove the centered validation padding before mapping CAM to the source image."""
        map_h, map_w = heatmap.shape[:2]
        scale = min(map_h / height, map_w / width)
        resized_h = max(1, min(map_h, round(height * scale)))
        resized_w = max(1, min(map_w, round(width * scale)))
        top = (map_h - resized_h) // 2
        left = (map_w - resized_w) // 2
        unpadded = heatmap[top:top + resized_h, left:left + resized_w]
        return cv2.resize(unpadded, (width, height), interpolation=cv2.INTER_LINEAR)

    def explain(
        self,
        image_bytes: bytes,
        target_head: str,
        target_class: int,
        clinical_grounding: bool = True,
        target_disease_name: str = "",
        model_name: str = "standard",
    ) -> dict[str, Any]:
        is_ag_mtcnet = self._is_ag_mtcnet(model_name)
        active_thresholds = self.ag_thresholds if is_ag_mtcnet else self.thresholds
        started_at = time.perf_counter()
        tensor = self.preprocess(image_bytes, ag_mtcnet=is_ag_mtcnet)
        if is_ag_mtcnet:
            active_key = "ag_mtcnet"
        elif "wsol" in model_name.lower() or "ensemble" in model_name.lower():
            active_key = "wsol"
        elif "resnet" in model_name.lower():
            active_key = "resnet50"
        else:
            active_key = "standard"
        active_model = self.get_model(active_key)

        image = self._decode_uploaded_image(image_bytes)
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
                target_thresh = float(self._thresholds_for_task(active_thresholds, "head_a").get(target_disease_name, 0.45))
            elif target_head == "head_b":
                target_prob = float(torch.sigmoid(outputs["head_b"])[0, 0].item())
                target_thresh = float(self._thresholds_for_task(active_thresholds, "head_b").get("threshold", 0.45))
            elif target_head == "head_c":
                target_prob = self._covid_prob_from_logits(outputs["head_c"])
                target_thresh = float(self._thresholds_for_task(active_thresholds, "head_c").get("threshold", 0.70))
            else:
                target_prob = 1.0
                target_thresh = 0.5
        is_target_positive = bool(target_prob >= target_thresh)

        explainer = MultiScaleGradCAMPlusPlus(active_model)
        try:
            cam_class = 2 if target_head == "head_c" and outputs["head_c"].shape[-1] == 3 else target_class
            raw_heatmap = explainer.generate(
                tensor,
                head_name=target_head,
                target_class_idx=cam_class,
                fusion_weights=(0.4, 0.6),
            )
        finally:
            explainer.remove_hooks()

        orig_h, orig_w = image_np.shape[:2]

        raw_heatmap_native = self._restore_letterboxed_heatmap(raw_heatmap, orig_h, orig_w)

        # Generate lung mask from segmenter directly on native image
        mask_source = "morphology"
        mask_warning = (
            "Đang dùng mặt nạ hình thái xấp xỉ. Tỷ lệ năng lượng trong phổi chỉ để tham khảo, chưa được xác thực."
        )
        if self.dense_unet is not None:
            try:
                lung_mask = self.segmenter._dense_predict_masks([image_np])[0]
                mask_source = "dense_unet"
                mask_warning = ""
            except Exception as exc:
                logger.warning("Dense-UNet segmentation failed; using approximate morphology: %s", exc)
                lung_mask = self.segmenter._morphology_predict_mask(image_np)
                mask_source = "morphology_fallback"
                mask_warning = (
                    "Không thể tạo mặt nạ Dense-UNet; đang dùng mặt nạ hình thái xấp xỉ. "
                    "Tỷ lệ năng lượng trong phổi chỉ để tham khảo, chưa được xác thực."
                )
        else:
            lung_mask = self.segmenter._morphology_predict_mask(image_np)
        if lung_mask.shape != (orig_h, orig_w):
            lung_mask = cv2.resize(
                lung_mask.astype(np.uint8),
                (orig_w, orig_h),
                interpolation=cv2.INTER_NEAREST,
            )

        mask_fraction = float(np.mean(lung_mask > 0))
        if mask_source == "dense_unet" and (mask_fraction < 0.01 or mask_fraction > 0.85):
            # An empty/full deep mask would silently erase or misrepresent the CAM.
            # The morphology fallback is approximate and is explicitly disclosed.
            lung_mask = self.segmenter._morphology_predict_mask(image_np)
            mask_source = "morphology_fallback"
            mask_warning = (
                "Mặt nạ Dense-UNet không hợp lệ; đang dùng mặt nạ hình thái xấp xỉ. "
                "Tỷ lệ năng lượng trong phổi chỉ để tham khảo, chưa được xác thực."
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

        # Alpha follows the computed activation; zero activation remains transparent.
        # The original RGB field stays available for older API clients.
        heatmap_rgba = np.dstack((heatmap_color, heatmap_uint8))

        # Multi-scale lesion iso-contour extraction: only for confirmed positive
        # targets under clinical grounding. The contour is constrained to the
        # anatomical ROI mask (effective_mask) so it matches the in-lung audit.
        # Negative targets return an empty contour to avoid drawing false lesions.
        contour_b64 = ""
        contour_rgba_b64 = ""
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
            changed = np.any(contour_overlay != image_np, axis=2).astype(np.uint8) * 255
            contour_rgba_b64 = self._image_to_base64(np.dstack((contour_overlay, changed)))
            lesion_bounding_boxes = lesions
            lesion_area_ratio = float(area_ratio)

        audit_pass = bool(in_lung_ratio >= 0.80) if mask_source == "dense_unet" else None

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
            "heatmap_rgba_base64": self._image_to_base64(heatmap_rgba),
            "heatmap_has_activation": bool(np.any(heatmap_uint8)),
            "overlay_base64": self._image_to_base64(overlay),
            "contour_base64": contour_b64,
            "contour_rgba_base64": contour_rgba_b64,
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
            "mask_source": mask_source,
            "mask_warning": mask_warning,
        }

    def audit(self, image_bytes: bytes) -> dict[str, Any]:
        tensor = self.preprocess(image_bytes)
        image = self._decode_uploaded_image(image_bytes)
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
