"""
LungRay Multi-Task 3-Head Network Architecture
==============================================
Shared Encoder Backbone with 3 independent clinical classification heads:
- Head A: 14 thoracic pathologies (NIH ChestX-ray14, multi-label)
- Head B: Tuberculosis screening (TB Database, binary)
- Head C: COVID-19 screening (COVIDx CXR-4, binary positive vs negative)

Supports DenseNet-121 (default CheXNet baseline), ResNet-50, and Vision Transformer (ViT).
Standard input resolution: 512x512.

Feature projection (TASK-013):
    GAP -> LayerNorm/BatchNorm -> Dropout(p=0.2) -> task-specific Linear head.
The normalization layer is deliberately parameter-free (``elementwise_affine=False``):
an affine transform placed before a linear head is mathematically absorbable into
that head, while keeping the state dict unchanged preserves compatibility with
pre-existing ``best_model.pth`` checkpoints used by the FastAPI serving layer.
"""
from typing import Dict, Optional, Union
import torch
import torch.nn as nn
from src.models.backbones import build_backbone


_TASK_ID_ALIASES = {
    0: "head_a",
    1: "head_b",
    2: "head_c",
    "head_a": "head_a",
    "head_b": "head_b",
    "head_c": "head_c",
    "a": "head_a",
    "b": "head_b",
    "c": "head_c",
}


def _build_head_norm(kind: str, feature_dim: int) -> nn.Module:
    """Builds the parameter-free intermediate normalization layer."""
    normalized = str(kind).strip().lower()
    if normalized in {"layernorm", "layer_norm", "ln"}:
        return nn.LayerNorm(feature_dim, elementwise_affine=False)
    if normalized in {"batchnorm", "batch_norm", "bn"}:
        return nn.BatchNorm1d(
            feature_dim, affine=False, track_running_stats=False
        )
    if normalized in {"none", "identity"}:
        return nn.Identity()
    raise ValueError(
        "head_norm must be 'layernorm', 'batchnorm', or 'none', got "
        f"{kind!r}."
    )


class MultiTaskChestXrayNet(nn.Module):
    """
    Multi-Task 3-Head Chest X-ray Neural Network for LungRay platform.

    Architecture:
        x (B, 3, 512, 512)
              │
        Shared Backbone (DenseNet-121 / ResNet-50 / ViT)
              │
        Feature Vector z (B, feature_dim) [GAP]
              │
        LayerNorm / BatchNorm (parameter-free) + Dropout(0.2)
         ┌────┼────┐
         │    │    │
       HeadA HeadB HeadC
       (14)  (1)   (1 or 3)
    """

    def __init__(
        self,
        backbone_name: str = "densenet121",
        pretrained: bool = True,
        img_size: int = 512,
        dropout_rate: float = 0.2,
        num_classes_a: int = 14,
        num_classes_b: int = 1,
        num_classes_c: int = 1,
        head_norm: str = "layernorm",
    ):
        super().__init__()
        self.backbone_name = backbone_name.lower()
        self.img_size = img_size
        self.num_classes_a = num_classes_a
        self.num_classes_b = num_classes_b
        self.num_classes_c = num_classes_c

        # Build shared encoder backbone
        self.backbone, self.feature_dim = build_backbone(
            name=backbone_name,
            pretrained=pretrained,
            img_size=img_size,
        )

        self.head_norm_name = str(head_norm).strip().lower()
        self.feature_norm = _build_head_norm(head_norm, self.feature_dim)
        self.dropout = nn.Dropout(p=dropout_rate)

        # 3 Independent Clinical Classification Heads
        self.head_a = nn.Linear(self.feature_dim, num_classes_a)
        self.head_b = nn.Linear(self.feature_dim, num_classes_b)
        self.head_c = nn.Linear(self.feature_dim, num_classes_c)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract pooled feature vector z from shared encoder backbone.
        """
        features = self.backbone(x)
        # Flatten if backbone outputs 4D tensor (B, C, 1, 1)
        if features.dim() > 2:
            features = torch.flatten(features, 1)
        return features

    def projection(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the shared normalized + dropped-out feature representation."""
        z = self.extract_features(x)
        z = self.feature_norm(z)
        return self.dropout(z)

    def forward(
        self,
        x: torch.Tensor,
        task_id: Optional[Union[str, int]] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass returning raw logits dictionary for numerical stability.

        Args:
            x: Input tensor of shape (B, 3, H, W).
            task_id: Optional head selector ('head_a'/'head_b'/'head_c', 'a'/'b'/'c',
                or 0/1/2). When given, only that head is evaluated to save FLOPs;
                when None, all three heads are computed.

        Returns:
            Dictionary with keys 'head_a', 'head_b', 'head_c' containing raw logits.

        Raises:
            ValueError: If ``task_id`` is not a recognized head selector.
        """
        z = self.projection(x)

        if task_id is not None:
            head_key = _TASK_ID_ALIASES.get(task_id)
            if head_key is None:
                raise ValueError(
                    f"Unknown task_id {task_id!r}; expected one of "
                    f"{sorted(_TASK_ID_ALIASES, key=str)!r}."
                )
            return {head_key: getattr(self, head_key)(z)}

        return {
            "head_a": self.head_a(z),
            "head_b": self.head_b(z),
            "head_c": self.head_c(z),
        }

    @torch.no_grad()
    def predict(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Inference forward pass returning activated probabilities:
        - Head A: Sigmoid across 14 multi-label pathologies in [0, 1].
        - Head B: Sigmoid for binary TB screening in [0, 1].
        - Head C: Sigmoid for binary COVID-19 screening (if num_classes_c=1) or Softmax.

        Args:
            x: Input tensor of shape (B, 3, H, W).

        Returns:
            Dictionary of probability tensors.
        """
        was_training = self.training
        self.eval()

        logits = self.forward(x)
        prob_a = torch.sigmoid(logits["head_a"])
        prob_b = torch.sigmoid(logits["head_b"])
        if self.num_classes_c == 1:
            prob_c = torch.sigmoid(logits["head_c"])
        else:
            prob_c = torch.softmax(logits["head_c"], dim=-1)

        if was_training:
            self.train()

        return {
            "head_a": prob_a,
            "head_b": prob_b,
            "head_c": prob_c,
        }

    def get_last_conv_layer(self) -> Optional[nn.Module]:
        """
        Retrieves the last convolutional layer module for Grad-CAM explainability.
        - DenseNet-121: backbone.features.denseblock4 or backbone.features.norm5
        - ResNet-50: backbone.layer4
        """
        if "densenet" in self.backbone_name:
            if hasattr(self.backbone, "features"):
                if hasattr(self.backbone.features, "denseblock4"):
                    return self.backbone.features.denseblock4
                return self.backbone.features[-1]
        elif "resnet" in self.backbone_name:
            if hasattr(self.backbone, "layer4"):
                return self.backbone.layer4
        return None
