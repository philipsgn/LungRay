"""
LungRay Multi-Task 3-Head Network Architecture
==============================================
Shared Encoder Backbone with 3 independent clinical classification heads:
- Head A: 14 thoracic pathologies (NIH ChestX-ray14, multi-label)
- Head B: Tuberculosis screening (TB Database, binary)
- Head C: COVID-19 screening (COVID-19 Radiography, 4-class)

Supports DenseNet-121 (default CheXNet baseline), ResNet-50, and Vision Transformer (ViT).
Standard input resolution: 512x512.
"""
from typing import Dict, Optional, Tuple, Any
import torch
import torch.nn as nn
from src.models.backbones import build_backbone


class MultiTaskChestXrayNet(nn.Module):
    """
    Multi-Task 3-Head Chest X-ray Neural Network for LungRay platform.

    Architecture:
        x (B, 3, 512, 512)
              │
        Shared Backbone (DenseNet-121 / ResNet-50 / ViT)
              │
        Feature Vector z (B, feature_dim) [GAP + Dropout(0.2)]
         ┌────┼────┐
         │    │    │
       HeadA HeadB HeadC
       (14)  (1)   (3)
    """

    def __init__(
        self,
        backbone_name: str = "densenet121",
        pretrained: bool = True,
        img_size: int = 512,
        dropout_rate: float = 0.2,
        num_classes_a: int = 14,
        num_classes_b: int = 1,
        num_classes_c: int = 3,
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

    def forward(
        self,
        x: torch.Tensor,
        task_id: Optional[str] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass returning raw logits dictionary for numerical stability.

        Args:
            x: Input tensor of shape (B, 3, H, W).
            task_id: Optional filter ('head_a', 'head_b', 'head_c'). If None, computes all 3.

        Returns:
            Dictionary with keys 'head_a', 'head_b', 'head_c' containing raw logits.
        """
        z = self.extract_features(x)
        z = self.dropout(z)

        if task_id == "head_a":
            return {"head_a": self.head_a(z)}
        elif task_id == "head_b":
            return {"head_b": self.head_b(z)}
        elif task_id == "head_c":
            return {"head_c": self.head_c(z)}

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
        - Head C: Softmax across 3 COVID-Net classes (COVID-19, Normal, Pneumonia) (sum to 1.0).

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
