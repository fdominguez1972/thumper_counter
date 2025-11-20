#!/usr/bin/env python3
"""
Test Enhanced Re-ID (Feature 009)

Tests multi-scale ResNet50 and EfficientNet-B0 feature extraction
with ensemble matching on a sample detection.

Usage:
    docker-compose exec backend python3 /app/scripts/test_enhanced_reid.py
"""

import sys
sys.path.insert(0, '/app')

from pathlib import Path
from PIL import Image as PILImage
import numpy as np

from backend.core.database import SessionLocal
from backend.models.detection import Detection
from backend.models.image import Image
from worker.tasks.reidentification import (
    extract_feature_vector,
    extract_multiscale_features,
    extract_efficientnet_features,
    extract_all_features,
    extract_deer_crop
)

def test_enhanced_reid():
    """Test enhanced Re-ID feature extraction."""
    print("[TEST] Starting Enhanced Re-ID test (Feature 009)")
    print("=" * 80)

    db = SessionLocal()

    try:
        # Find a detection with deer classification
        detection = (
            db.query(Detection)
            .filter(Detection.classification == 'doe')
            .filter(Detection.bbox.isnot(None))
            .first()
        )

        if not detection:
            print("[FAIL] No doe detections found for testing")
            return False

        print(f"\n[TEST] Testing with detection: {detection.id}")
        print(f"  Classification: {detection.classification}")
        print(f"  Confidence: {detection.confidence:.3f}")
        print(f"  BBox: {detection.bbox}")

        # Load image
        image = db.query(Image).filter(Image.id == detection.image_id).first()
        if not image:
            print("[FAIL] Image not found")
            return False

        print(f"  Image: {image.filename}")
        print(f"  Path: {image.path}")

        # Extract crop
        image_path = Path(image.path)
        if not image_path.exists():
            print(f"[FAIL] Image file not found: {image.path}")
            return False

        crop = extract_deer_crop(image_path, detection.bbox)
        if crop is None:
            print("[FAIL] Failed to extract crop")
            return False

        print(f"\n[OK] Crop extracted: {crop.size}")

        # Test 1: Original ResNet50
        print("\n" + "=" * 80)
        print("[TEST 1] Original ResNet50 Feature Extraction")
        print("-" * 80)

        resnet_features = extract_feature_vector(crop)
        if resnet_features is None:
            print("[FAIL] ResNet50 feature extraction failed")
            return False

        print(f"[OK] ResNet50 features extracted")
        print(f"  Shape: {resnet_features.shape}")
        print(f"  L2 norm: {np.linalg.norm(resnet_features):.6f}")
        print(f"  Min: {resnet_features.min():.6f}, Max: {resnet_features.max():.6f}")
        print(f"  Mean: {resnet_features.mean():.6f}, Std: {resnet_features.std():.6f}")

        # Test 2: Multi-scale ResNet50
        print("\n" + "=" * 80)
        print("[TEST 2] Multi-Scale ResNet50 Feature Extraction (Feature 009)")
        print("-" * 80)

        multiscale_features = extract_multiscale_features(crop)
        if multiscale_features is None:
            print("[FAIL] Multi-scale feature extraction failed")
            return False

        print(f"[OK] Multi-scale features extracted")
        print(f"  Shape: {multiscale_features.shape}")
        print(f"  L2 norm: {np.linalg.norm(multiscale_features):.6f}")
        print(f"  Min: {multiscale_features.min():.6f}, Max: {multiscale_features.max():.6f}")
        print(f"  Mean: {multiscale_features.mean():.6f}, Std: {multiscale_features.std():.6f}")

        # Test 3: EfficientNet-B0
        print("\n" + "=" * 80)
        print("[TEST 3] EfficientNet-B0 Feature Extraction (Feature 009)")
        print("-" * 80)

        efficientnet_features = extract_efficientnet_features(crop)
        if efficientnet_features is None:
            print("[FAIL] EfficientNet feature extraction failed")
            return False

        print(f"[OK] EfficientNet features extracted")
        print(f"  Shape: {efficientnet_features.shape}")
        print(f"  L2 norm: {np.linalg.norm(efficientnet_features):.6f}")
        print(f"  Min: {efficientnet_features.min():.6f}, Max: {efficientnet_features.max():.6f}")
        print(f"  Mean: {efficientnet_features.mean():.6f}, Std: {efficientnet_features.std():.6f}")

        # Test 4: Extract all features
        print("\n" + "=" * 80)
        print("[TEST 4] Extract All Features (Feature 009)")
        print("-" * 80)

        all_features = extract_all_features(crop)

        print(f"[OK] All features extracted:")
        print(f"  ResNet50: {'YES' if all_features['resnet50'] is not None else 'NO'}")
        print(f"  Multi-scale: {'YES' if all_features['multiscale'] is not None else 'NO'}")
        print(f"  EfficientNet: {'YES' if all_features['efficientnet'] is not None else 'NO'}")

        # Test 5: Feature comparison
        print("\n" + "=" * 80)
        print("[TEST 5] Feature Comparison")
        print("-" * 80)

        # Compare similarity between features
        resnet_norm = resnet_features / np.linalg.norm(resnet_features)
        multiscale_norm = multiscale_features / np.linalg.norm(multiscale_features)
        efficientnet_norm = efficientnet_features / np.linalg.norm(efficientnet_features)

        sim_resnet_multiscale = np.dot(resnet_norm, multiscale_norm)
        sim_resnet_efficientnet = np.dot(resnet_norm, efficientnet_norm)
        sim_multiscale_efficientnet = np.dot(multiscale_norm, efficientnet_norm)

        print(f"Cosine similarity between feature types:")
        print(f"  ResNet50 <-> Multi-scale:   {sim_resnet_multiscale:.4f}")
        print(f"  ResNet50 <-> EfficientNet:  {sim_resnet_efficientnet:.4f}")
        print(f"  Multi-scale <-> EfficientNet: {sim_multiscale_efficientnet:.4f}")

        print("\n" + "=" * 80)
        print("[SUCCESS] All Enhanced Re-ID tests passed!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == '__main__':
    success = test_enhanced_reid()
    sys.exit(0 if success else 1)
