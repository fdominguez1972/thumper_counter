"""
Multi-scale ResNet50 feature extraction for enhanced Re-ID.

This module implements multi-scale feature extraction from ResNet50 by combining
features from multiple layers (layer2, layer3, layer4, avgpool) to capture both
low-level details (texture, patterns) and high-level semantic information.

Architecture:
- layer2 (512 channels): Body texture and patterns (coat color, markings)
- layer3 (1024 channels): Body shape and proportions (size, build)
- layer4 (2048 channels): High-level features (antler configuration, stance)
- avgpool (2048 channels): Semantic-level identification features

Each layer's features are:
1. Adaptively pooled to normalize spatial dimensions
2. Flattened to 1D vector
3. Reduced via linear projection to 128 dimensions
4. Concatenated (4 x 128 = 512 dimensions)
5. L2 normalized for cosine similarity

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
_multiscale_model = None
_multiscale_lock = threading.Lock()


def build_multiscale_resnet50() -> nn.Module:
    """
    Build multi-scale ResNet50 feature extraction model.

    The model extracts features from 4 layers and combines them into a
    512-dimensional embedding. Thread-safe with double-checked locking.

    Returns:
        nn.Module: Multi-scale feature extraction model

    Architecture:
        Input (224x224x3) -> ResNet50 backbone
            -> layer2 (512 ch) -> AdaptiveAvgPool(4,4) -> Linear(8192->128)
            -> layer3 (1024 ch) -> AdaptiveAvgPool(2,2) -> Linear(4096->128)
            -> layer4 (2048 ch) -> AdaptiveAvgPool(1,1) -> Linear(2048->128)
            -> avgpool (2048 ch) -> Linear(2048->128)
            -> Concatenate(512) -> L2 Normalize
    """
    # Load pretrained ResNet50
    base_model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

    # Extract layers up to avgpool (before classifier)
    # ResNet50 structure: conv1 -> bn1 -> relu -> maxpool -> layer1 -> layer2 -> layer3 -> layer4 -> avgpool -> fc
    layer2 = base_model.layer2
    layer3 = base_model.layer3
    layer4 = base_model.layer4
    avgpool = base_model.avgpool

    # Build multi-scale extraction model
    model = MultiScaleResNet50(
        layer1=base_model.conv1,
        bn1=base_model.bn1,
        relu=base_model.relu,
        maxpool=base_model.maxpool,
        layer1_block=base_model.layer1,
        layer2=layer2,
        layer3=layer3,
        layer4=layer4,
        avgpool=avgpool
    )

    return model


class MultiScaleResNet50(nn.Module):
    """
    Multi-scale feature extraction from ResNet50.

    Extracts features from layer2, layer3, layer4, and avgpool, then combines
    them into a 512-dimensional embedding.

    Attributes:
        conv1, bn1, relu, maxpool: Initial ResNet50 layers
        layer1, layer2, layer3, layer4: ResNet50 residual blocks
        avgpool: Global average pooling

        pool_layer2: AdaptiveAvgPool2d((4, 4)) for layer2 features
        pool_layer3: AdaptiveAvgPool2d((2, 2)) for layer3 features
        pool_layer4: AdaptiveAvgPool2d((1, 1)) for layer4 features

        reduce_layer2: Linear(8192 -> 128) for layer2 reduction
        reduce_layer3: Linear(4096 -> 128) for layer3 reduction
        reduce_layer4: Linear(2048 -> 128) for layer4 reduction
        reduce_avgpool: Linear(2048 -> 128) for avgpool reduction
    """

    def __init__(self, layer1, bn1, relu, maxpool, layer1_block, layer2, layer3, layer4, avgpool):
        super(MultiScaleResNet50, self).__init__()

        # Base layers
        self.conv1 = layer1
        self.bn1 = bn1
        self.relu = relu
        self.maxpool = maxpool
        self.layer1 = layer1_block
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer4 = layer4
        self.avgpool = avgpool

        # T021: Adaptive pooling layers for spatial normalization
        self.pool_layer2 = nn.AdaptiveAvgPool2d((4, 4))  # 512 x 4 x 4 = 8192
        self.pool_layer3 = nn.AdaptiveAvgPool2d((2, 2))  # 1024 x 2 x 2 = 4096
        self.pool_layer4 = nn.AdaptiveAvgPool2d((1, 1))  # 2048 x 1 x 1 = 2048

        # T022: Linear reduction layers (reduce to 128 dims each)
        self.reduce_layer2 = nn.Linear(512 * 4 * 4, 128)  # 8192 -> 128
        self.reduce_layer3 = nn.Linear(1024 * 2 * 2, 128)  # 4096 -> 128
        self.reduce_layer4 = nn.Linear(2048 * 1 * 1, 128)  # 2048 -> 128
        self.reduce_avgpool = nn.Linear(2048, 128)  # 2048 -> 128

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with multi-scale feature extraction.

        Args:
            x: Input tensor (batch_size, 3, 224, 224)

        Returns:
            torch.Tensor: 512-dimensional L2-normalized embedding (batch_size, 512)
        """
        # Initial layers
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)

        # T020: Extract features from layer2, layer3, layer4
        feat_layer2 = self.layer2(x)  # [batch, 512, H1, W1]
        feat_layer3 = self.layer3(feat_layer2)  # [batch, 1024, H2, W2]
        feat_layer4 = self.layer4(feat_layer3)  # [batch, 2048, H3, W3]

        # T020: Extract avgpool features
        feat_avgpool = self.avgpool(feat_layer4)  # [batch, 2048, 1, 1]
        feat_avgpool = torch.flatten(feat_avgpool, 1)  # [batch, 2048]

        # T021: Apply adaptive pooling to normalize spatial dimensions
        pooled_layer2 = self.pool_layer2(feat_layer2)  # [batch, 512, 4, 4]
        pooled_layer3 = self.pool_layer3(feat_layer3)  # [batch, 1024, 2, 2]
        pooled_layer4 = self.pool_layer4(feat_layer4)  # [batch, 2048, 1, 1]

        # Flatten pooled features
        flat_layer2 = torch.flatten(pooled_layer2, 1)  # [batch, 8192]
        flat_layer3 = torch.flatten(pooled_layer3, 1)  # [batch, 4096]
        flat_layer4 = torch.flatten(pooled_layer4, 1)  # [batch, 2048]

        # T022: Apply linear reduction layers
        reduced_layer2 = self.reduce_layer2(flat_layer2)  # [batch, 128]
        reduced_layer3 = self.reduce_layer3(flat_layer3)  # [batch, 128]
        reduced_layer4 = self.reduce_layer4(flat_layer4)  # [batch, 128]
        reduced_avgpool = self.reduce_avgpool(feat_avgpool)  # [batch, 128]

        # T023: Concatenate features (4 x 128 = 512)
        combined = torch.cat([
            reduced_layer2,
            reduced_layer3,
            reduced_layer4,
            reduced_avgpool
        ], dim=1)  # [batch, 512]

        # T024: L2 normalization for cosine similarity
        normalized = torch.nn.functional.normalize(combined, p=2, dim=1)

        return normalized


def get_multiscale_model() -> nn.Module:
    """
    Get or create multi-scale ResNet50 model singleton.

    Thread-safe lazy initialization with double-checked locking pattern.
    Loads model to GPU and sets to eval mode.

    Returns:
        nn.Module: Multi-scale feature extraction model
    """
    global _multiscale_model

    # T025: Double-checked locking for thread-safe singleton
    if _multiscale_model is None:
        with _multiscale_lock:
            if _multiscale_model is None:
                print("[INFO] Loading multi-scale ResNet50 model...")

                # T019: Build model
                _multiscale_model = build_multiscale_resnet50()

                # T026: Move to GPU and set eval mode
                _multiscale_model.to(DEVICE)
                _multiscale_model.eval()

                print(f"[OK] Multi-scale ResNet50 loaded on {DEVICE}")

    return _multiscale_model


def get_transform() -> transforms.Compose:
    """
    Get image preprocessing transform for ResNet50.

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
    "build_multiscale_resnet50",
    "get_multiscale_model",
    "get_transform",
    "MultiScaleResNet50"
]
