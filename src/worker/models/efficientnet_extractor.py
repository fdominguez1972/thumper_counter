"""
EfficientNet-B0 feature extraction for ensemble Re-ID.

This module implements EfficientNet-B0 based feature extraction to provide
architectural diversity for ensemble learning. EfficientNet uses compound
scaling (width + depth + resolution) which captures complementary features
compared to ResNet50's residual blocks.

Architecture:
- Base: EfficientNet-B0 pretrained on ImageNet (5.3M params)
- Output: 1280-dimensional features from last convolutional layer
- Reduction: Linear projection 1280 -> 512 dimensions
- Normalization: L2 normalized for cosine similarity

Benefits:
- Architectural diversity vs ResNet50
- Efficient parameters (5.3M vs 25.6M)
- Fast inference (~40ms vs ~80ms for multi-scale ResNet50)
- Complementary feature representation

Feature: 009-reid-enhancement
"""

import os
import threading
from typing import Tuple

import torch
import torch.nn as nn
from torchvision import models, transforms

# GPU device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global model cache (thread-safe singleton)
_efficientnet_model = None
_efficientnet_lock = threading.Lock()


def build_efficientnet_b0() -> nn.Module:
    """
    Build EfficientNet-B0 feature extraction model.

    Loads pretrained EfficientNet-B0, removes the classifier head,
    adds a reduction layer to produce 512-dimensional embeddings,
    and L2 normalizes the output.

    Returns:
        nn.Module: EfficientNet-B0 feature extraction model

    Architecture:
        Input (224x224x3) -> EfficientNet-B0 backbone (no classifier)
            -> Features (1280 dims) -> Linear(1280->512)
            -> L2 Normalize
    """
    # T028-T029: Load pretrained EfficientNet-B0 with ImageNet weights
    base_model = models.efficientnet_b0(
        weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1
    )

    # Build feature extractor
    model = EfficientNetExtractor(base_model)

    return model


class EfficientNetExtractor(nn.Module):
    """
    EfficientNet-B0 feature extraction with dimensionality reduction.

    Extracts 1280-dimensional features from EfficientNet-B0 and reduces
    them to 512 dimensions for consistency with ResNet50 embeddings.

    Attributes:
        features: EfficientNet-B0 feature extraction layers (no classifier)
        avgpool: Adaptive average pooling to (1, 1) spatial size
        reduce: Linear layer (1280 -> 512) for dimensionality reduction
    """

    def __init__(self, base_model: models.EfficientNet):
        super(EfficientNetExtractor, self).__init__()

        # T030: Remove classifier head, keep feature extractor only
        # EfficientNet structure: features -> avgpool -> classifier
        self.features = base_model.features

        # T031: Add adaptive pooling to produce 512-dim output
        # EfficientNet-B0 outputs 1280 channels, we reduce to 512
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.reduce = nn.Linear(1280, 512)  # Reduce from 1280 to 512 dims

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with feature extraction and reduction.

        Args:
            x: Input tensor (batch_size, 3, 224, 224)

        Returns:
            torch.Tensor: 512-dimensional L2-normalized embedding (batch_size, 512)
        """
        # Extract features from EfficientNet-B0 backbone
        x = self.features(x)  # [batch, 1280, H, W]

        # Global average pooling
        x = self.avgpool(x)  # [batch, 1280, 1, 1]
        x = torch.flatten(x, 1)  # [batch, 1280]

        # Reduce dimensionality
        x = self.reduce(x)  # [batch, 512]

        # T032: L2 normalization for cosine similarity
        x = torch.nn.functional.normalize(x, p=2, dim=1)

        return x


def get_efficientnet_model() -> nn.Module:
    """
    Get or create EfficientNet-B0 model singleton.

    Thread-safe lazy initialization with double-checked locking pattern.
    Loads model to GPU and sets to eval mode.

    Returns:
        nn.Module: EfficientNet-B0 feature extraction model
    """
    global _efficientnet_model

    # T033: Double-checked locking for thread-safe singleton
    if _efficientnet_model is None:
        with _efficientnet_lock:
            if _efficientnet_model is None:
                print("[INFO] Loading EfficientNet-B0 model...")

                # T028: Build model
                _efficientnet_model = build_efficientnet_b0()

                # T034: Move to GPU and set eval mode
                _efficientnet_model.to(DEVICE)
                _efficientnet_model.eval()

                print(f"[OK] EfficientNet-B0 loaded on {DEVICE}")

    return _efficientnet_model


def get_transform() -> transforms.Compose:
    """
    Get image preprocessing transform for EfficientNet-B0.

    Uses same ImageNet normalization as ResNet50 for consistency.

    Returns:
        transforms.Compose: PyTorch transform pipeline
    """
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],  # ImageNet stats
            std=[0.229, 0.224, 0.225]
        )
    ])


# Export functions
__all__ = [
    "build_efficientnet_b0",
    "get_efficientnet_model",
    "get_transform",
    "EfficientNetExtractor"
]
