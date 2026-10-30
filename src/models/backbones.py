"""
LungRay Backbone Builders & ViT Positional Embedding Utilities
==============================================================
Provides factory functions to initialize CNN encoders (DenseNet-121, ResNet-50)
and Vision Transformer (ViT) with dynamic 2D positional embedding interpolation
for 512x512 chest X-ray resolution.
"""
import os
import glob
import socket
from typing import Tuple, Optional
import torch
import torch.nn as nn
import timm


def _find_local_weights(model_name: str) -> Optional[str]:
    """
    Search for locally cached or Kaggle-mounted pretrained checkpoint files
    to enable offline model initialization when Kaggle Internet is OFF.
    """
    search_patterns = [
        f"/kaggle/input/**/{model_name}*.pth",
        f"/kaggle/input/**/{model_name}*.pt",
        os.path.expanduser(f"~/.cache/torch/hub/checkpoints/{model_name}*.pth"),
        os.path.expanduser(f"~/.cache/huggingface/hub/**/{model_name}*.bin"),
        f"checkpoints/{model_name}*.pth",
        f"../checkpoints/{model_name}*.pth",
        f"dataset/{model_name}*.pth",
    ]
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches and os.path.exists(matches[0]):
            return matches[0]
    return None


def interpolate_vit_pos_embed_for_512(
    model: nn.Module,
    new_img_size: int = 512,
    patch_size: int = 16
) -> nn.Module:
    """
    Interpolates absolute positional embeddings of a Vision Transformer (ViT)
    from native pretrained size (e.g. 224x224 or 384x384) to LungRay's standard 512x512.

    Uses timm's `resample_abs_pos_embed` to perform 2D bicubic interpolation on the grid
    while preserving class token embeddings.

    Rationale:
    - Pretrained ViT-B/16 expects 224x224 (14x14 = 196 patches) or 384x384 (24x24 = 576 patches).
    - LungRay 512x512 requires (512 / 16) = 32x32 = 1024 spatial patches (+ 1 cls_token).
    """
    if hasattr(model, 'pos_embed') and model.pos_embed is not None:
        num_patches_side = new_img_size // patch_size
        new_grid_size = (num_patches_side, num_patches_side)
        
        # Check timm version compatibility for resample_abs_pos_embed
        try:
            from timm.layers import resample_abs_pos_embed
        except ImportError:
            from timm.models.vision_transformer import resample_abs_pos_embed

        old_pos_embed = model.pos_embed
        has_cls_token = getattr(model, 'cls_token', None) is not None
        num_prefix_tokens = 1 if has_cls_token else 0

        resampled_pos_embed = resample_abs_pos_embed(
            posemb=old_pos_embed,
            new_size=new_grid_size,
            num_prefix_tokens=num_prefix_tokens,
            interpolation='bicubic',
            antialias=True
        )
        model.pos_embed = nn.Parameter(resampled_pos_embed)
        
        if hasattr(model.patch_embed, 'img_size'):
            model.patch_embed.img_size = (new_img_size, new_img_size)
            model.patch_embed.grid_size = new_grid_size
            model.patch_embed.num_patches = new_grid_size[0] * new_grid_size[1]
            
    return model


def build_backbone(
    name: str = "densenet121",
    pretrained: bool = True,
    img_size: int = 512
) -> Tuple[nn.Module, int]:
    """
    Builds the shared encoder backbone for LungRay Multi-Task 3-Head Net.

    Args:
        name: Backbone architecture name ('densenet121', 'resnet50', 'vit_base_patch16_224', 'vit_base_patch16_384').
        pretrained: Whether to load ImageNet pretrained weights.
        img_size: Input spatial resolution (default: 512).

    Returns:
        tuple: (backbone_encoder, in_features_dim)
    """
    name = name.lower()
    local_weights = _find_local_weights(name) if pretrained else None

    print(f"[*] Initializing backbone '{name}' (pretrained={pretrained})...")
    if local_weights:
        print(f"[*] Found local offline weights for '{name}': {local_weights}")

    def _create_with_fallback(arch_name: str, pretrained_flag: bool):
        try:
            # If local checkpoint found and pretrained requested, create uninitialized first
            if local_weights and pretrained_flag:
                m = timm.create_model(arch_name, pretrained=False, num_classes=0)
                state_dict = torch.load(local_weights, map_location="cpu")
                # Handle possible state_dict key wrappers (e.g. 'state_dict', 'model')
                if "state_dict" in state_dict:
                    state_dict = state_dict["state_dict"]
                elif "model" in state_dict:
                    state_dict = state_dict["model"]
                m.load_state_dict(state_dict, strict=False)
                print(f"[OK] Successfully loaded local pretrained weights into {arch_name}!")
                return m
            
            # Normal creation via timm (downloads if pretrained_flag is True)
            old_timeout = socket.getdefaulttimeout()
            try:
                if pretrained_flag:
                    socket.setdefaulttimeout(20.0)
                return timm.create_model(arch_name, pretrained=pretrained_flag, num_classes=0)
            finally:
                socket.setdefaulttimeout(old_timeout)
        except Exception as err:
            if pretrained_flag:
                print(f"[!] Warning: Failed to load pretrained weights for '{arch_name}' via timm.")
                print(f"    Detail: {type(err).__name__}: {err}")
                print("[!] Kaggle Tip: Ensure 'Internet: ON' is enabled in the right panel (Notebook Settings),")
                print("    or add a Kaggle dataset containing pretrained .pth checkpoints.")
                print("[*] Falling back to uninitialized weights (pretrained=False) to prevent deadlock...")
                return timm.create_model(arch_name, pretrained=False, num_classes=0)
            raise err

    if name == "densenet121":
        model = _create_with_fallback("densenet121", pretrained)
        in_features = model.num_features  # 1024
        return model, in_features

    elif name == "resnet50":
        model = _create_with_fallback("resnet50", pretrained)
        in_features = model.num_features  # 2048
        return model, in_features

    elif "vit" in name:
        model = _create_with_fallback(name, pretrained)
        if img_size != 224:
            model = interpolate_vit_pos_embed_for_512(model, new_img_size=img_size, patch_size=16)
        in_features = model.num_features  # 768 for vit_base
        return model, in_features

    else:
        raise ValueError(f"Unsupported backbone: {name}. Choose from densenet121, resnet50, vit_base_patch16_224.")
