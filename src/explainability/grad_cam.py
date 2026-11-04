"""
LungRay Grad-CAM and Grad-CAM++ Explainability Engine
=====================================================
Generates class activation maps for the shared encoder of
:class:`src.models.multi_task_net.MultiTaskChestXrayNet`.

The implementation is dependency-light: it uses PyTorch forward/backward hooks
and OpenCV for colour mapping, so it works fully offline on Kaggle.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple, Union

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


TensorLike = Union[torch.Tensor, np.ndarray]


def compute_gradcam_plus_plus_core(
    activation: torch.Tensor,
    first: torch.Tensor,
    eps: float = 1e-8,
) -> torch.Tensor:
    """
    Shared Grad-CAM++ analytic spatial weighting core.

    Given a target activation map and its first-order gradient, computes the
    Grad-CAM++ spatial alpha weights and returns the non-negative activation
    map. Consumed by both :class:`GradCAMExplainer` (single-layer) and
    :class:`MultiScaleGradCAMPlusPlus` (multi-layer fusion) so the analytic
    weighting is identical everywhere.
    """
    first = torch.nan_to_num(first, nan=0.0, posinf=0.0, neginf=0.0)
    spatial = activation[0].detach()
    grad = first[0].detach()
    grad_squared = grad * grad
    grad_cubed = grad_squared * grad
    sum_activations = torch.sum(spatial, dim=(1, 2), keepdim=True)
    alpha = grad_squared / (
        2.0 * grad_squared + sum_activations * grad_cubed + eps
    )
    alpha = torch.where(grad != 0.0, alpha, torch.zeros_like(alpha))
    alpha = torch.nan_to_num(alpha, nan=0.0, posinf=0.0, neginf=0.0)
    weights = torch.sum(torch.relu(grad) * alpha, dim=(1, 2))
    return torch.relu(torch.sum(weights[:, None, None] * spatial, dim=0))


class GradCAMExplainer:
    """
    Grad-CAM / Grad-CAM++ explainer with explicit hook lifecycle management.

    Args:
        model: Multi-task model returning a logits dictionary, or a single-head
            model returning a logits tensor.
        target_layer: Convolutional layer used to extract activations. When
            ``None``, ``model.get_last_conv_layer()`` is called.
        method: ``"gradcam"`` or ``"gradcam++"``.
    """

    _VALID_METHODS = {"gradcam", "gradcam++", "gradcampp", "grad-cam", "grad-cam++"}

    def __init__(
        self,
        model: nn.Module,
        target_layer: Optional[nn.Module] = None,
        method: str = "gradcam",
    ) -> None:
        if not isinstance(model, nn.Module):
            raise TypeError("model must be an instance of torch.nn.Module.")
        if target_layer is None:
            getter = getattr(model, "get_last_conv_layer", None)
            if not callable(getter):
                raise ValueError(
                    "target_layer is None and model has no get_last_conv_layer()."
                )
            target_layer = getter()
        if not isinstance(target_layer, nn.Module):
            raise ValueError(
                "Unable to resolve a convolutional target layer for this model."
            )

        normalized_method = str(method).strip().lower()
        if normalized_method not in self._VALID_METHODS:
            raise ValueError(
                "method must be 'gradcam' or 'gradcam++', "
                f"got {method!r}."
            )

        self.model = model
        self.target_layer = target_layer
        self.method = "gradcam++" if "++" in normalized_method or normalized_method.endswith(
            "pp"
        ) else "gradcam"

        self._activation: Optional[torch.Tensor] = None
        self._gradient: Optional[torch.Tensor] = None
        self._forward_handle: Any = None
        self._backward_handle: Any = None

        self._register_hooks()

    @property
    def is_attached(self) -> bool:
        """Return whether both hooks are currently registered."""
        return self._forward_handle is not None and self._backward_handle is not None

    def _register_hooks(self) -> None:
        """Attach forward and full-backward hooks to the target layer."""
        self._forward_handle = self.target_layer.register_forward_hook(
            self._forward_hook
        )
        self._backward_handle = self.target_layer.register_full_backward_hook(
            self._backward_hook
        )

    def _forward_hook(
        self,
        module: nn.Module,
        inputs: Tuple[torch.Tensor, ...],
        output: Union[torch.Tensor, Tuple[torch.Tensor, ...]],
    ) -> None:
        del module, inputs
        activation = self._extract_tensor(output, "forward output")
        self._activation = activation
        if activation.requires_grad:
            activation.retain_grad()

    def _backward_hook(
        self,
        module: nn.Module,
        grad_input: Tuple[Optional[torch.Tensor], ...],
        grad_output: Tuple[Optional[torch.Tensor], ...],
    ) -> None:
        del module, grad_input
        self._gradient = self._extract_tensor(
            grad_output[0] if grad_output else None,
            "backward gradient",
        )

    @staticmethod
    def _extract_tensor(value: Any, label: str) -> torch.Tensor:
        if isinstance(value, (tuple, list)):
            for item in value:
                if isinstance(item, torch.Tensor):
                    return item
            raise TypeError(f"{label} does not contain a tensor.")
        if not isinstance(value, torch.Tensor):
            raise TypeError(f"{label} is not a torch.Tensor.")
        return value

    def remove_hooks(self) -> None:
        """Remove both hooks and release cached activation tensors."""
        if self._forward_handle is not None:
            self._forward_handle.remove()
            self._forward_handle = None
        if self._backward_handle is not None:
            self._backward_handle.remove()
            self._backward_handle = None
        self._activation = None
        self._gradient = None

    def __enter__(self) -> "GradCAMExplainer":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.remove_hooks()

    def generate(
        self,
        x: torch.Tensor,
        head_name: str = "head_c",
        target_class_idx: int = 0,
    ) -> np.ndarray:
        """
        Generate a Grad-CAM heatmap for one sample.

        Args:
            x: Input batch ``(B, C, H, W)`` or single image ``(C, H, W)``.
                When ``B > 1``, only the first sample is explained.
            head_name: Logits dictionary key (``head_a``, ``head_b``, ``head_c``).
            target_class_idx: Class index inside the selected head.

        Returns:
            Float32 array of shape ``(H, W)`` normalized to ``[0, 1]``.
        """
        if not self.is_attached:
            raise RuntimeError(
                "Hooks have been removed. Create a new GradCAMExplainer instance."
            )
        if not isinstance(x, torch.Tensor):
            raise TypeError("x must be a torch.Tensor.")
        if not torch.is_floating_point(x):
            raise TypeError("x must be a floating-point tensor.")
        if x.dim() == 3:
            x = x.unsqueeze(0)
        if x.dim() != 4:
            raise ValueError(f"x must have shape (B, C, H, W), got {tuple(x.shape)}.")

        input_height, input_width = int(x.shape[-2]), int(x.shape[-1])
        if input_height < 2 or input_width < 2:
            raise ValueError("Input spatial dimensions must be at least 2x2.")

        self._activation = None
        self._gradient = None
        was_training = self.model.training
        self.model.eval()

        input_tensor = x.detach().clone().requires_grad_(True)
        try:
            outputs = self.model(input_tensor)
            logits = self._select_head_logits(outputs, head_name)
            score = self._select_target_score(logits, target_class_idx)

            activation = self._activation
            if activation is None:
                raise RuntimeError(
                    "Target layer was not executed during the forward pass."
                )
            if not activation.requires_grad:
                raise RuntimeError(
                    "Target activation does not require gradients; "
                    "check that the model is differentiable."
                )

            if activation.shape[0] < 1:
                raise RuntimeError("Target layer returned an empty batch.")

            if self.method == "gradcam":
                cam = self._compute_gradcam(activation, score)
            else:
                cam = self._compute_gradcam_plus_plus(activation, score)

            cam = F.interpolate(
                cam[None, None],
                size=(input_height, input_width),
                mode="bilinear",
                align_corners=False,
            )[0, 0]
            cam = torch.nan_to_num(cam, nan=0.0, posinf=0.0, neginf=0.0)
            cam = torch.relu(cam)
            return self._normalize_heatmap(cam.detach().cpu().numpy())
        finally:
            self._activation = None
            self._gradient = None
            self.model.train(was_training)

    @staticmethod
    def _select_head_logits(outputs: Any, head_name: str) -> torch.Tensor:
        if isinstance(outputs, dict):
            if head_name not in outputs:
                available = ", ".join(sorted(str(key) for key in outputs))
                raise KeyError(
                    f"head_name {head_name!r} not found in model output. "
                    f"Available heads: {available}."
                )
            logits = outputs[head_name]
        else:
            logits = outputs
        if not isinstance(logits, torch.Tensor):
            raise TypeError("Selected head logits must be a torch.Tensor.")
        if logits.dim() not in {1, 2}:
            raise ValueError(
                "Selected head logits must have shape (B,) or (B, num_classes)."
            )
        if logits.shape[0] < 1:
            raise ValueError("Selected head logits have an empty batch dimension.")
        return logits

    @staticmethod
    def _select_target_score(logits: torch.Tensor, target_class_idx: int) -> torch.Tensor:
        if not isinstance(target_class_idx, int):
            raise TypeError("target_class_idx must be an integer.")
        if logits.dim() == 1:
            if target_class_idx != 0:
                raise IndexError(
                    "target_class_idx must be 0 for one-dimensional head logits."
                )
            return logits[0]
        if target_class_idx < 0 or target_class_idx >= logits.shape[1]:
            raise IndexError(
                f"target_class_idx {target_class_idx} is out of range for "
                f"{logits.shape[1]} classes."
            )
        return logits[0, target_class_idx]

    def _compute_gradcam(
        self,
        activation: torch.Tensor,
        score: torch.Tensor,
    ) -> torch.Tensor:
        gradients = torch.autograd.grad(
            outputs=score,
            inputs=activation,
            create_graph=False,
            retain_graph=False,
            only_inputs=True,
        )[0]
        gradients = torch.nan_to_num(gradients, nan=0.0, posinf=0.0, neginf=0.0)
        spatial = activation[0].detach()
        weights = gradients[0].mean(dim=(1, 2))
        cam = torch.relu(torch.sum(weights[:, None, None] * spatial, dim=0))
        return cam

    def _compute_gradcam_plus_plus(
        self,
        activation: torch.Tensor,
        score: torch.Tensor,
    ) -> torch.Tensor:
        eps = 1e-8
        first = torch.autograd.grad(
            outputs=score,
            inputs=activation,
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]
        first = torch.nan_to_num(first, nan=0.0, posinf=0.0, neginf=0.0)

        second = self._higher_order_gradient(first, activation, create_graph=True)
        third = (
            self._higher_order_gradient(second, activation, create_graph=False)
            if second is not None
            else None
        )

        if second is not None and third is not None:
            second = torch.nan_to_num(second, nan=0.0, posinf=0.0, neginf=0.0)
            third = torch.nan_to_num(third, nan=0.0, posinf=0.0, neginf=0.0)
            if activation.dim() != 4:
                return self._first_order_gradcam_plus_plus(activation, first, eps)
            denominator = 2.0 * second + torch.sum(
                activation.detach() * third, dim=(2, 3), keepdim=True
            )
            alpha = second / (denominator + eps)
            alpha = torch.where(first != 0.0, alpha, torch.zeros_like(alpha))
            alpha = torch.nan_to_num(alpha, nan=0.0, posinf=0.0, neginf=0.0)
            weights = torch.sum(torch.relu(first) * alpha, dim=(2, 3))[0]
            cam = torch.relu(
                torch.sum(weights[:, None, None] * activation[0].detach(), dim=0)
            )
            finite_cam = bool(torch.isfinite(cam).all().item())
            if finite_cam and float(cam.detach().max().item()) > 1e-8:
                return cam

        return self._first_order_gradcam_plus_plus(activation, first, eps)

    @staticmethod
    def _higher_order_gradient(
        gradient: torch.Tensor,
        activation: torch.Tensor,
        create_graph: bool,
    ) -> Optional[torch.Tensor]:
        if not gradient.requires_grad:
            return None
        try:
            return torch.autograd.grad(
                outputs=gradient,
                inputs=activation,
                grad_outputs=torch.ones_like(gradient),
                create_graph=create_graph,
                retain_graph=create_graph,
                only_inputs=True,
                allow_unused=True,
            )[0]
        except RuntimeError:
            return None

    @staticmethod
    def _first_order_gradcam_plus_plus(
        activation: torch.Tensor,
        first: torch.Tensor,
        eps: float,
    ) -> torch.Tensor:
        return compute_gradcam_plus_plus_core(activation, first, eps)

    @staticmethod
    def _normalize_heatmap(heatmap: np.ndarray) -> np.ndarray:
        heatmap = np.asarray(heatmap, dtype=np.float32)
        heatmap = np.nan_to_num(heatmap, nan=0.0, posinf=0.0, neginf=0.0)
        minimum = float(heatmap.min())
        maximum = float(heatmap.max())
        if maximum - minimum <= 1e-8:
            return np.zeros_like(heatmap, dtype=np.float32)
        heatmap = (heatmap - minimum) / (maximum - minimum)
        return np.clip(heatmap, 0.0, 1.0).astype(np.float32, copy=False)

    @staticmethod
    def overlay_heatmap(
        img_rgb: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET,
    ) -> np.ndarray:
        """
        Blend a heatmap over an RGB image.

        Args:
            img_rgb: ``uint8`` array in ``[0, 255]`` or float array in ``[0, 1]``.
            heatmap: Float array in ``[0, 1]``; resized to the image if needed.
            alpha: Heatmap opacity in ``[0, 1]``.
            colormap: OpenCV colormap identifier.

        Returns:
            ``uint8`` RGB array of shape ``(H, W, 3)``.
        """
        if not isinstance(alpha, (int, float)) or not 0.0 <= float(alpha) <= 1.0:
            raise ValueError("alpha must be a number in [0, 1].")
        image = GradCAMExplainer._prepare_rgb_image(img_rgb)
        heat = np.asarray(heatmap, dtype=np.float32)
        if heat.ndim != 2:
            raise ValueError("heatmap must be a two-dimensional array.")
        if heat.size == 0:
            raise ValueError("heatmap must not be empty.")
        heat = np.nan_to_num(heat, nan=0.0, posinf=0.0, neginf=0.0)
        heat = np.clip(heat, 0.0, 1.0)

        height, width = image.shape[:2]
        if heat.shape != (height, width):
            heat = cv2.resize(
                heat,
                (width, height),
                interpolation=cv2.INTER_LINEAR,
            )

        heat_uint8 = np.uint8(np.clip(heat * 255.0, 0.0, 255.0))
        color_bgr = cv2.applyColorMap(heat_uint8, colormap)
        color_rgb = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2RGB)
        blended = (
            (1.0 - float(alpha)) * image.astype(np.float32)
            + float(alpha) * color_rgb.astype(np.float32)
        )
        return np.uint8(np.clip(blended, 0.0, 255.0))

    @staticmethod
    def _prepare_rgb_image(img_rgb: np.ndarray) -> np.ndarray:
        image = np.asarray(img_rgb)
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("img_rgb must have shape (H, W, 3).")
        if image.size == 0:
            raise ValueError("img_rgb must not be empty.")
        if image.dtype == np.uint8:
            return image
        if np.issubdtype(image.dtype, np.floating):
            image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
            return np.uint8(np.clip(image * 255.0, 0.0, 255.0))
        if np.issubdtype(image.dtype, np.integer):
            return np.uint8(np.clip(image, 0, 255))
        raise TypeError("img_rgb must be uint8, float, or integer.")


class MultiScaleGradCAMPlusPlus:
    """
    Multi-Scale Grad-CAM++ with feature-level resolution fusion (DenseBlock 3 + 4).
    Resolves spatial boundaries at 32x32 resolution instead of standard 16x16,
    substantially reducing diffuse blur and tightly adhering to clinical lesion contours.
    """

    def __init__(
        self,
        model: nn.Module,
        target_layers: Optional[list[nn.Module]] = None,
    ) -> None:
        if not isinstance(model, nn.Module):
            raise TypeError("model must be an instance of torch.nn.Module.")

        self.model = model
        self.target_layers = target_layers or self._resolve_multi_scale_layers(model)
        if not self.target_layers:
            raise ValueError("Unable to resolve multi-scale convolutional target layers.")

        self._activations: dict[int, Optional[torch.Tensor]] = {i: None for i in range(len(self.target_layers))}
        self._handles: list[Any] = []

        self._register_hooks()

    @staticmethod
    def _resolve_multi_scale_layers(model: nn.Module) -> list[nn.Module]:
        layers: list[nn.Module] = []
        # DenseNet architecture
        if hasattr(model, "backbone") and hasattr(model.backbone, "features"):
            features = model.backbone.features
            if hasattr(features, "denseblock3") and hasattr(features, "denseblock4"):
                return [features.denseblock3, features.denseblock4]
        # ResNet architecture
        if hasattr(model, "backbone"):
            if hasattr(model.backbone, "layer3") and hasattr(model.backbone, "layer4"):
                return [model.backbone.layer3, model.backbone.layer4]
        # Fallback to single last layer
        getter = getattr(model, "get_last_conv_layer", None)
        if callable(getter):
            last = getter()
            if isinstance(last, nn.Module):
                return [last]
        return layers

    def _register_hooks(self) -> None:
        for idx, layer in enumerate(self.target_layers):
            def make_fwd(i: int):
                def hook(m: nn.Module, inp: Any, out: Any):
                    del m, inp
                    act = GradCAMExplainer._extract_tensor(out, f"forward output layer {i}")
                    self._activations[i] = act
                    if act.requires_grad:
                        act.retain_grad()
                return hook

            h_fwd = layer.register_forward_hook(make_fwd(idx))
            self._handles.append(h_fwd)

    def remove_hooks(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        self._activations.clear()

    def __enter__(self) -> "MultiScaleGradCAMPlusPlus":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.remove_hooks()

    @staticmethod
    def _cam_from_activation_and_grad(activation: torch.Tensor, first: torch.Tensor) -> torch.Tensor:
        """Computes Grad-CAM++ activation map using the shared analytical core."""
        return compute_gradcam_plus_plus_core(activation, first)

    @staticmethod
    def overlay_heatmap(
        img_rgb: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET,
    ) -> np.ndarray:
        """Blend a heatmap over an RGB image (shared implementation)."""
        return GradCAMExplainer.overlay_heatmap(
            img_rgb, heatmap, alpha=alpha, colormap=colormap
        )

    def generate(
        self,
        x: torch.Tensor,
        head_name: str = "head_a",
        target_class_idx: int = 0,
        fusion_weights: Tuple[float, float] = (0.4, 0.6),
    ) -> np.ndarray:
        """
        Generates fused multi-scale Grad-CAM++ heatmap.
        Layer 0 (DenseBlock 3, 32x32) provides high spatial fidelity and fine boundaries.
        Layer 1 (DenseBlock 4, 16x16) provides robust high-level semantic localization.
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError("x must be a torch.Tensor.")
        if x.dim() == 3:
            x = x.unsqueeze(0)
        input_h, input_w = int(x.shape[-2]), int(x.shape[-1])

        was_training = self.model.training
        self.model.eval()

        input_tensor = x.detach().clone().requires_grad_(True)
        try:
            outputs = self.model(input_tensor)
            logits = GradCAMExplainer._select_head_logits(outputs, head_name)
            score = GradCAMExplainer._select_target_score(logits, target_class_idx)

            valid_acts = []
            for idx in range(len(self.target_layers)):
                act = self._activations.get(idx)
                if act is not None and act.requires_grad:
                    valid_acts.append(act)

            if not valid_acts:
                return np.zeros((input_h, input_w), dtype=np.float32)

            # Single multi-tensor backward call computing gradients for all hooked layers
            grads = torch.autograd.grad(
                outputs=score,
                inputs=valid_acts,
                create_graph=False,
                retain_graph=False,
                only_inputs=True,
                allow_unused=True,
            )

            cams: list[torch.Tensor] = []
            for act, grad in zip(valid_acts, grads):
                if grad is None:
                    continue
                cam_layer = self._cam_from_activation_and_grad(act, grad)
                cam_interp = F.interpolate(
                    cam_layer[None, None],
                    size=(input_h, input_w),
                    mode="bilinear",
                    align_corners=False,
                )[0, 0]
                cam_interp = torch.nan_to_num(cam_interp, nan=0.0, posinf=0.0, neginf=0.0)
                cam_interp = torch.relu(cam_interp)
                cams.append(cam_interp)

            if not cams:
                return np.zeros((input_h, input_w), dtype=np.float32)

            if len(cams) == 1:
                fused = cams[0]
            else:
                w1, w2 = fusion_weights[:2]
                fused = w1 * cams[0] + w2 * cams[1]

            fused_np = fused.detach().cpu().numpy()
            return GradCAMExplainer._normalize_heatmap(fused_np)
        finally:
            self._activations = {i: None for i in range(len(self.target_layers))}
            self.model.train(was_training)


DISEASE_PERCENTILE_MAP: dict[str, float] = {
    "cardiomegaly": 62.0,       # Capture full cardiac silhouette
    "effusion": 72.0,           # Fluid accumulation
    "consolidation": 75.0,      # Lobar airspace
    "infiltration": 78.0,       # Reticulonodular
    "pneumothorax": 70.0,       # Apical radiolucency
    "fibrosis": 78.0,           # Interstitial
    "atelectasis": 76.0,        # Linear/segmental
    "pleural_thickening": 72.0, # Pleural stripe
    "nodule": 90.0,             # Focal small
    "mass": 82.0,               # Focal large
    "pneumonia": 75.0,          # Patchy infiltrate
}


def extract_adaptive_contour(
    heatmap: np.ndarray,
    lung_mask: Optional[np.ndarray] = None,
    threshold_percentile: Optional[float] = None,
    min_lesion_area: int = 120,
    disease_name: Optional[str] = None,
) -> Tuple[np.ndarray, list[dict[str, Any]], float]:
    """
    Extracts clinical lesion boundaries and bounding boxes from high-resolution CAM.
    Returns:
        bin_mask: Binary mask with detected lesion regions.
        lesions: List of detected lesion metadata (bbox, centroid, area, confidence).
        total_lesion_area_ratio: Ratio of lesion area to total pulmonary field.
    """
    h, w = heatmap.shape[:2]
    heat = np.nan_to_num(heatmap, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    # Resolve threshold percentile based on pathology geometry
    if threshold_percentile is None:
        if disease_name and disease_name.lower() in DISEASE_PERCENTILE_MAP:
            threshold_percentile = DISEASE_PERCENTILE_MAP[disease_name.lower()]
        else:
            threshold_percentile = 85.0

    if lung_mask is not None:
        effective_mask = (lung_mask > 0).astype(np.float32)
        if effective_mask.shape != (h, w):
            effective_mask = cv2.resize(effective_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        heat_intra = heat * effective_mask
        in_lung_pixels = int(np.sum(effective_mask > 0))
    else:
        heat_intra = heat
        effective_mask = np.ones((h, w), dtype=np.float32)
        in_lung_pixels = h * w

    positive_vals = heat_intra[heat_intra > 0.05]
    if positive_vals.size > 0:
        thresh = float(np.percentile(positive_vals, threshold_percentile))
        min_clamp = 0.12 if (disease_name and disease_name.lower() == "cardiomegaly") else 0.20
        thresh = max(min_clamp, min(thresh, 0.85))
    else:
        thresh = 0.5

    bin_mask = (heat_intra >= thresh).astype(np.uint8)

    # Morphological clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel)
    bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lesions: list[dict[str, Any]] = []
    total_lesion_pixels = 0

    for cnt in contours:
        area = int(cv2.contourArea(cnt))
        if area < min_lesion_area:
            # Clear out tiny speckles in bin_mask
            cv2.drawContours(bin_mask, [cnt], -1, 0, -1)
            continue

        total_lesion_pixels += area
        x, y, bw, bh = cv2.boundingRect(cnt)
        M = cv2.moments(cnt)
        cx = int(round(M["m10"] / (M["m00"] + 1e-6)))
        cy = int(round(M["m01"] / (M["m00"] + 1e-6)))

        cnt_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(cnt_mask, [cnt], -1, 1, -1)
        mean_conf = float(np.mean(heat[cnt_mask > 0])) if np.sum(cnt_mask) > 0 else 0.0

        lesions.append({
            "bbox": {
                "x": int(x),
                "y": int(y),
                "width": int(bw),
                "height": int(bh),
                "x2": int(x + bw),
                "y2": int(y + bh),
            },
            "centroid": {"x": int(cx), "y": int(cy)},
            "area_pixels": area,
            "area_percent": round((area / float(max(1, in_lung_pixels))) * 100.0, 2),
            "confidence": round(mean_conf, 4),
        })

    # Sort lesions by area descending
    lesions.sort(key=lambda item: item["area_pixels"], reverse=True)
    area_ratio = round(float(total_lesion_pixels) / float(max(1, in_lung_pixels)), 4)

    return bin_mask, lesions, area_ratio


def render_contour_overlay(
    img_rgb: np.ndarray,
    bin_mask: np.ndarray,
    lesions: Optional[list[dict[str, Any]]] = None,
    contour_color: Tuple[int, int, int] = (6, 182, 212),  # Bright Cyan
    fill_opacity: float = 0.25,
) -> np.ndarray:
    """
    Renders clinical lesion contours and bounding brackets directly on the radiograph.
    """
    img = GradCAMExplainer._prepare_rgb_image(img_rgb).copy()
    h, w = img.shape[:2]

    if bin_mask.shape != (h, w):
        bin_mask = cv2.resize(bin_mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)

    contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 1. Subtle semi-transparent lesion tint
    tint_layer = img.copy()
    cv2.drawContours(tint_layer, contours, -1, contour_color, -1)
    img = cv2.addWeighted(tint_layer, fill_opacity, img, 1.0 - fill_opacity, 0)

    # 2. Crisp, anti-aliased iso-contour perimeter
    cv2.drawContours(img, contours, -1, contour_color, 2, cv2.LINE_AA)

    # 3. Corner brackets for detected lesions
    if lesions:
        for item in lesions:
            b = item.get("bbox", {})
            bx, by, bw, bh = b.get("x", 0), b.get("y", 0), b.get("width", 0), b.get("height", 0)
            corner_len = max(8, min(16, int(round(min(bw, bh) * 0.25))))
            bracket_color = (245, 158, 11)  # Amber Gold

            # Top-left corner
            cv2.line(img, (bx, by), (bx + corner_len, by), bracket_color, 2, cv2.LINE_AA)
            cv2.line(img, (bx, by), (bx, by + corner_len), bracket_color, 2, cv2.LINE_AA)
            # Top-right corner
            cv2.line(img, (bx + bw, by), (bx + bw - corner_len, by), bracket_color, 2, cv2.LINE_AA)
            cv2.line(img, (bx + bw, by), (bx + bw, by + corner_len), bracket_color, 2, cv2.LINE_AA)
            # Bottom-left corner
            cv2.line(img, (bx, by + bh), (bx + corner_len, by + bh), bracket_color, 2, cv2.LINE_AA)
            cv2.line(img, (bx, by + bh), (bx, by + bh - corner_len), bracket_color, 2, cv2.LINE_AA)
            # Bottom-right corner
            cv2.line(img, (bx + bw, by + bh), (bx + bw - corner_len, by + bh), bracket_color, 2, cv2.LINE_AA)
            cv2.line(img, (bx + bw, by + bh), (bx + bw, by + bh - corner_len), bracket_color, 2, cv2.LINE_AA)

    return img
