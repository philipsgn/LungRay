"""
LungRay Fail-Safe Layer: Out-of-Distribution & Uncertainty Scoring Engine
========================================================================
Implements mathematical scoring functions for post-hoc inference safety:
1. Sigmoid-adapted Helmholtz free energy score for multi-label classification.
2. Mean binary Shannon entropy for multi-label predictive uncertainty.
3. Max-sigmoid confidence distance baseline.
"""
from typing import Union
import torch
import torch.nn.functional as F


def compute_sigmoid_energy(
    logits: Union[torch.Tensor, list],
    temperature: float = 1.0,
) -> torch.Tensor:
    """
    Computes the Sigmoid-adapted Helmholtz Free Energy score.

    For a multi-label model where each class c has an independent binary logit z_c:
        S_E(x) = T * sum_{c=1}^C ln(1 + exp(z_c / T)) = T * sum_{c=1}^C softplus(z_c / T)

    High energy indicates the inputs align with the learned feature distributions (ID).
    Low energy indicates uncharacteristic or abnormal activations (OOD).

    Args:
        logits: Logit tensor of shape (B, C) or (C,).
        temperature: Temperature scaling factor (default: 1.0).

    Returns:
        Tensor of shape (B,) or scalar (0-d tensor) containing energy scores.
    """
    if not isinstance(logits, torch.Tensor):
        logits = torch.tensor(logits, dtype=torch.float32)

    scaled_logits = logits / temperature
    # softplus(x) = ln(1 + exp(x)), numerically stable in PyTorch
    softplus_val = F.softplus(scaled_logits)

    if softplus_val.dim() > 1:
        # Sum across class dimension C (B, C) -> (B,)
        return temperature * torch.sum(softplus_val, dim=-1)
    return temperature * torch.sum(softplus_val)


def compute_shannon_entropy(
    probs: Union[torch.Tensor, list],
    epsilon: float = 1e-7,
) -> torch.Tensor:
    """
    Computes the Mean Binary Shannon Entropy across C independent probabilities.

    For each pathology c with probability p_c:
        H_c(p_c) = - [ p_c * ln(p_c) + (1 - p_c) * ln(1 - p_c) ]
        H(x) = (1 / C) * sum_{c=1}^C H_c(p_c)

    Range: [0.0, ln(2) ~= 0.6931].
    Low entropy: Model has clear confidence (probabilities near 0 or 1).
    High entropy: Model is highly uncertain / conflicted (probabilities hover near 0.5).

    Args:
        probs: Probability tensor of shape (B, C) or (C,), values in [0, 1].
        epsilon: Small numerical clamp to prevent ln(0).

    Returns:
        Tensor of shape (B,) or scalar (0-d tensor) containing normalized entropy scores.
    """
    if not isinstance(probs, torch.Tensor):
        probs = torch.tensor(probs, dtype=torch.float32)

    clamped_p = torch.clamp(probs, min=epsilon, max=1.0 - epsilon)
    # Binary Shannon entropy for each class
    binary_entropy = -(
        clamped_p * torch.log(clamped_p) + (1.0 - clamped_p) * torch.log(1.0 - clamped_p)
    )

    if binary_entropy.dim() > 1:
        # Mean across class dimension C (B, C) -> (B,)
        return torch.mean(binary_entropy, dim=-1)
    return torch.mean(binary_entropy)


def compute_max_sigmoid_confidence(
    probs: Union[torch.Tensor, list],
) -> torch.Tensor:
    """
    Baseline confidence score: Maximum distance from the ambiguous 0.5 boundary.

    Score = max_{c} |2 * p_c - 1| in range [0, 1].
    """
    if not isinstance(probs, torch.Tensor):
        probs = torch.tensor(probs, dtype=torch.float32)

    dist = torch.abs(2.0 * probs - 1.0)
    if dist.dim() > 1:
        return torch.max(dist, dim=-1).values
    return torch.max(dist)
