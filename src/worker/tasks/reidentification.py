"""
Re-Identification Task for Deer Tracking
Sprint 5: Individual deer identification using ResNet50 embeddings
Feature 009: Enhanced Re-ID with multi-scale and ensemble learning

This module implements the re-identification stage of the ML pipeline:
1. Extract deer crop from detection bbox
2. Generate feature vectors using multiple models:
   - Original: ResNet50 (512-dim, backward compatible)
   - Multi-scale: ResNet50 layers 2,3,4,avgpool (512-dim)
   - EfficientNet: EfficientNet-B0 (512-dim for ensemble)
3. Ensemble matching: Weighted similarity (0.6 ResNet + 0.4 EfficientNet)
4. Search for matching deer profile using cosine similarity
5. Either link to existing deer or create new profile

Architecture:
- Model: ResNet50 pretrained on ImageNet (original)
- Multi-scale: ResNet50 layer2+layer3+layer4+avgpool (Feature 009)
- Ensemble: EfficientNet-B0 for architectural diversity (Feature 009)
- Embeddings: 512 dimensions (L2 normalized)
- Similarity: Cosine distance via pgvector
- Threshold: 0.40 (data-driven from Feature 010)
- Ensemble weights: 0.6 ResNet + 0.4 EfficientNet (Feature 009)
"""

import os
import logging
import time
import threading
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image as PILImage
import numpy as np

from worker.celery_app import app
from backend.core.database import SessionLocal
from backend.models.image import Image
from backend.models.detection import Detection
from backend.models.deer import Deer, DeerSex

# Feature 009: Import enhanced Re-ID models
try:
    from worker.models.multiscale_resnet import get_multiscale_model, get_transform as get_multiscale_transform
    from worker.models.efficientnet_extractor import get_efficientnet_model, get_transform as get_efficientnet_transform
    ENHANCED_MODELS_AVAILABLE = True
except ImportError as e:
    ENHANCED_MODELS_AVAILABLE = False
    _IMPORT_ERROR = str(e)  # Save error for logging later


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
REID_THRESHOLD = float(os.getenv('REID_THRESHOLD', 0.40))  # Feature 010: Data-driven threshold
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
MIN_CROP_SIZE = 50  # Minimum width/height for valid crop
BURST_WINDOW = 5  # Seconds - group photos within this window as same event

# Feature 009: Enhanced Re-ID configuration
USE_ENHANCED_REID = os.getenv('USE_ENHANCED_REID', 'true').lower() == 'true'
ENSEMBLE_WEIGHT_RESNET = float(os.getenv('ENSEMBLE_WEIGHT_RESNET', 0.6))
ENSEMBLE_WEIGHT_EFFICIENTNET = float(os.getenv('ENSEMBLE_WEIGHT_EFFICIENTNET', 0.4))

# Sprint 9: Enable CUDA optimizations
if torch.cuda.is_available():
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True  # Auto-tune for best performance
    logger.info("[SPRINT9] cuDNN optimizations enabled")

# Feature 009: Log enhanced Re-ID status
if ENHANCED_MODELS_AVAILABLE:
    logger.info("[FEATURE009] Enhanced Re-ID models imported successfully")
else:
    logger.warning(f"[FEATURE009] Enhanced Re-ID models not available: {_IMPORT_ERROR if '_IMPORT_ERROR' in dir() else 'Unknown error'}")

if USE_ENHANCED_REID:
    logger.info(
        f"[FEATURE009] Enhanced Re-ID ENABLED: "
        f"weights={ENSEMBLE_WEIGHT_RESNET:.1f}R + {ENSEMBLE_WEIGHT_EFFICIENTNET:.1f}E, "
        f"threshold={REID_THRESHOLD}"
    )
else:
    logger.info(f"[FEATURE009] Enhanced Re-ID DISABLED: Using original ResNet50 only")


# Global model cache (thread-safe singleton)
_reid_model = None
_reid_transform = None
_model_lock = threading.Lock()


def get_reid_model() -> Tuple[nn.Module, transforms.Compose]:
    """
    Get or load ResNet50 re-identification model (singleton pattern).

    Returns pre-trained ResNet50 with final FC layer removed for embeddings.
    Thread-safe for use with Celery threads pool.

    Returns:
        Tuple[nn.Module, transforms.Compose]: Model and image transform

    Raises:
        RuntimeError: If model fails to load
    """
    global _reid_model, _reid_transform

    # Double-checked locking for thread-safe singleton
    if _reid_model is None or _reid_transform is None:
        with _model_lock:
            if _reid_model is None or _reid_transform is None:
                try:
                    logger.info(f"[INFO] Loading ResNet50 re-ID model on {DEVICE}")

                    # Load pretrained ResNet50
                    resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

                    # Remove final FC layer to get embeddings
                    # ResNet50 outputs 2048-dim features before FC
                    # We'll use adaptive pooling to get 512-dim
                    modules = list(resnet.children())[:-1]  # Remove FC layer
                    _reid_model = nn.Sequential(*modules)

                    # Add adaptive pooling to reduce from 2048 to 512
                    _reid_model = nn.Sequential(
                        _reid_model,
                        nn.AdaptiveAvgPool2d((1, 1)),
                        nn.Flatten(),
                        nn.Linear(2048, 512),  # Reduce dimensionality
                        nn.ReLU(),
                        nn.BatchNorm1d(512)
                    )

                    # Move to device and set to eval mode
                    _reid_model = _reid_model.to(DEVICE)
                    _reid_model.eval()

                    # Create image transform
                    # Standard ImageNet preprocessing
                    _reid_transform = transforms.Compose([
                        transforms.Resize((224, 224)),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225]
                        )
                    ])

                    logger.info(f"[OK] ResNet50 re-ID model loaded on {DEVICE}")

                except Exception as e:
                    logger.error(f"[FAIL] Failed to load re-ID model: {e}")
                    raise RuntimeError(f"Re-ID model loading failed: {e}")

    return _reid_model, _reid_transform


def extract_deer_crop(image_path: Path, bbox: Dict) -> Optional[PILImage.Image]:
    """
    Extract deer crop from image using bounding box.

    Args:
        image_path: Path to source image
        bbox: Bounding box dict with x, y, width, height

    Returns:
        PIL.Image: Cropped deer image, or None if invalid
    """
    try:
        # Load image
        img = PILImage.open(image_path)

        # Get bbox coordinates
        x = bbox['x']
        y = bbox['y']
        width = bbox['width']
        height = bbox['height']

        # Validate crop size
        if width < MIN_CROP_SIZE or height < MIN_CROP_SIZE:
            logger.warning(f"[WARN] Crop too small: {width}x{height} (min: {MIN_CROP_SIZE})")
            return None

        # Crop image (x1, y1, x2, y2)
        crop = img.crop((x, y, x + width, y + height))

        return crop

    except Exception as e:
        logger.error(f"[FAIL] Failed to extract crop: {e}")
        return None


def extract_feature_vector(crop: PILImage.Image) -> Optional[np.ndarray]:
    """
    Extract 512-dim feature vector from deer crop using ResNet50.

    Args:
        crop: PIL Image of deer

    Returns:
        np.ndarray: 512-dim feature vector, or None if extraction fails
    """
    try:
        # Get model and transform
        model, transform = get_reid_model()

        # Preprocess image
        img_tensor = transform(crop).unsqueeze(0).to(DEVICE)

        # Extract features (no gradient computation)
        with torch.no_grad():
            features = model(img_tensor)

        # Convert to numpy and normalize
        features = features.cpu().numpy()[0]

        # L2 normalization for cosine similarity
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm

        return features

    except Exception as e:
        logger.error(f"[FAIL] Failed to extract features: {e}")
        return None


def extract_feature_vectors_batch(crops: List[PILImage.Image]) -> Optional[np.ndarray]:
    """
    Extract feature vectors for multiple crops in single batch (Sprint 9 optimization).

    Processes multiple deer crops in a single forward pass for better GPU utilization.
    Up to 12x faster than individual processing.

    Args:
        crops: List of PIL images

    Returns:
        np.ndarray: (N, 512) array of L2-normalized feature vectors, or None if fails
    """
    try:
        if len(crops) == 0:
            return None

        # Get model and transform
        model, transform = get_reid_model()

        # Stack all crops into single batch
        batch_tensor = torch.stack([transform(crop) for crop in crops]).to(DEVICE)

        # Extract features for all crops in one forward pass
        with torch.no_grad():
            features = model(batch_tensor)

        # Convert to numpy
        features_np = features.cpu().numpy()

        # L2 normalization for each vector
        norms = np.linalg.norm(features_np, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # Avoid division by zero
        features_normalized = features_np / norms

        return features_normalized

    except Exception as e:
        logger.error(f"[FAIL] Batch feature extraction failed: {e}")
        return None


def extract_multiscale_features(crop: PILImage.Image) -> Optional[np.ndarray]:
    """
    Extract 512-dim multi-scale feature vector from deer crop (Feature 009).

    Combines features from ResNet50 layers 2, 3, 4, and avgpool to capture
    texture, shapes, parts, and semantic features at multiple scales.

    Args:
        crop: PIL Image of deer

    Returns:
        np.ndarray: 512-dim L2-normalized feature vector, or None if extraction fails
    """
    if not ENHANCED_MODELS_AVAILABLE:
        logger.warning("[FEATURE009] Multi-scale model not available, skipping")
        return None

    try:
        # Get model and transform
        model = get_multiscale_model()
        transform = get_multiscale_transform()

        # Preprocess image
        img_tensor = transform(crop).unsqueeze(0).to(DEVICE)

        # Extract features (no gradient computation)
        with torch.no_grad():
            features = model(img_tensor)

        # Convert to numpy (already L2 normalized by model)
        features = features.cpu().numpy()[0]

        return features

    except Exception as e:
        logger.error(f"[FAIL] Multi-scale feature extraction failed: {e}")
        return None


def extract_efficientnet_features(crop: PILImage.Image) -> Optional[np.ndarray]:
    """
    Extract 512-dim EfficientNet-B0 feature vector from deer crop (Feature 009).

    Provides architectural diversity for ensemble learning using compound
    scaling (width + depth + resolution).

    Args:
        crop: PIL Image of deer

    Returns:
        np.ndarray: 512-dim L2-normalized feature vector, or None if extraction fails
    """
    if not ENHANCED_MODELS_AVAILABLE:
        logger.warning("[FEATURE009] EfficientNet model not available, skipping")
        return None

    try:
        # Get model and transform
        model = get_efficientnet_model()
        transform = get_efficientnet_transform()

        # Preprocess image
        img_tensor = transform(crop).unsqueeze(0).to(DEVICE)

        # Extract features (no gradient computation)
        with torch.no_grad():
            features = model(img_tensor)

        # Convert to numpy (already L2 normalized by model)
        features = features.cpu().numpy()[0]

        return features

    except Exception as e:
        logger.error(f"[FAIL] EfficientNet feature extraction failed: {e}")
        return None


def extract_all_features(crop: PILImage.Image) -> Dict[str, Optional[np.ndarray]]:
    """
    Extract all feature vectors for a deer crop (Feature 009).

    Extracts:
    - Original ResNet50 (512-dim, for backward compatibility)
    - Multi-scale ResNet50 (512-dim, layers 2+3+4+avgpool)
    - EfficientNet-B0 (512-dim, for ensemble)

    Args:
        crop: PIL Image of deer

    Returns:
        dict: Feature vectors with keys 'resnet50', 'multiscale', 'efficientnet'
              Values are np.ndarray or None if extraction failed
    """
    features = {
        'resnet50': None,
        'multiscale': None,
        'efficientnet': None
    }

    # Always extract original ResNet50 (backward compatibility)
    features['resnet50'] = extract_feature_vector(crop)

    # Extract enhanced features if enabled
    if USE_ENHANCED_REID and ENHANCED_MODELS_AVAILABLE:
        features['multiscale'] = extract_multiscale_features(crop)
        features['efficientnet'] = extract_efficientnet_features(crop)

    return features


def find_matching_deer_ensemble(
    db,
    features: Dict[str, Optional[np.ndarray]],
    sex: str,
    detection_id: Optional[UUID] = None
) -> Optional[Tuple[Deer, float, Dict[str, float]]]:
    """
    Find matching deer using ensemble similarity (Feature 009).

    Combines multiple feature vectors with weighted similarity:
    - Multi-scale ResNet50: captures texture + shapes + parts + semantics
    - EfficientNet-B0: provides architectural diversity
    - Weighted sum: 0.6 * multiscale + 0.4 * efficientnet (configurable)

    Falls back to original ResNet50 if enhanced features unavailable.

    Args:
        db: Database session
        features: Dict with keys 'resnet50', 'multiscale', 'efficientnet'
        sex: Detected sex (doe, buck, fawn, etc.)
        detection_id: UUID of detection (for similarity logging)

    Returns:
        Tuple[Deer, float, Dict]: Matching deer, ensemble similarity, component scores
        or None if no match found
    """
    try:
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import func, cast, text

        # Map classification to deer sex
        sex_mapping = {
            'doe': DeerSex.DOE,
            'buck': DeerSex.BUCK,
            'fawn': DeerSex.FAWN,
            'mature': DeerSex.BUCK,
            'mid': DeerSex.BUCK,
            'young': DeerSex.BUCK,
            'unknown': DeerSex.UNKNOWN
        }
        deer_sex = sex_mapping.get(sex, DeerSex.UNKNOWN)

        # Determine which features to use for matching
        use_ensemble = (
            USE_ENHANCED_REID and
            ENHANCED_MODELS_AVAILABLE and
            features.get('multiscale') is not None and
            features.get('efficientnet') is not None
        )

        if use_ensemble:
            # Feature 009: Ensemble matching with multi-scale + EfficientNet
            multiscale_list = features['multiscale'].tolist()
            efficientnet_list = features['efficientnet'].tolist()

            # Query all deer with enhanced feature vectors
            results = (
                db.query(
                    Deer,
                    (1 - Deer.feature_vector_multiscale.cosine_distance(multiscale_list)).label('sim_multiscale'),
                    (1 - Deer.feature_vector_efficientnet.cosine_distance(efficientnet_list)).label('sim_efficientnet')
                )
                .filter(Deer.feature_vector_multiscale.isnot(None))
                .filter(Deer.feature_vector_efficientnet.isnot(None))
                .filter(Deer.sex == deer_sex)
                .all()
            )

            if not results:
                logger.info(f"[FEATURE009] No deer with enhanced embeddings found, sex={deer_sex.value}")
                return None

            # Calculate ensemble similarity for each deer
            best_deer = None
            best_ensemble_score = 0.0
            best_component_scores = {}

            for deer, sim_multiscale, sim_efficientnet in results:
                # Weighted ensemble: 0.6 * multiscale + 0.4 * efficientnet
                ensemble_score = (
                    ENSEMBLE_WEIGHT_RESNET * sim_multiscale +
                    ENSEMBLE_WEIGHT_EFFICIENTNET * sim_efficientnet
                )

                if ensemble_score > best_ensemble_score:
                    best_ensemble_score = ensemble_score
                    best_deer = deer
                    best_component_scores = {
                        'multiscale': float(sim_multiscale),
                        'efficientnet': float(sim_efficientnet),
                        'ensemble': float(ensemble_score)
                    }

                # Optional: Log all scores for analysis
                if detection_id:
                    try:
                        db.execute(
                            text("""
                                INSERT INTO reid_similarity_scores
                                (detection_id, deer_id, similarity_score, sex_match, matched,
                                 threshold_used, detection_classification, deer_sex,
                                 similarity_multiscale, similarity_efficientnet, similarity_ensemble)
                                VALUES (:detection_id, :deer_id, :similarity_score, :sex_match,
                                        :matched, :threshold_used, :detection_classification, :deer_sex,
                                        :sim_multiscale, :sim_efficientnet, :sim_ensemble)
                                ON CONFLICT (detection_id, deer_id) DO NOTHING
                            """),
                            {
                                'detection_id': detection_id,
                                'deer_id': deer.id,
                                'similarity_score': float(ensemble_score),  # Use ensemble as primary score
                                'sex_match': True,
                                'matched': ensemble_score >= REID_THRESHOLD,
                                'threshold_used': float(REID_THRESHOLD),
                                'detection_classification': sex,
                                'deer_sex': deer.sex.value,
                                'sim_multiscale': float(sim_multiscale),
                                'sim_efficientnet': float(sim_efficientnet),
                                'sim_ensemble': float(ensemble_score)
                            }
                        )
                    except Exception as log_error:
                        logger.debug(f"[FEATURE009] Similarity logging failed: {log_error}")

            # Commit similarity logs
            if detection_id:
                try:
                    db.commit()
                except Exception:
                    db.rollback()

            # Check threshold
            if best_ensemble_score >= REID_THRESHOLD:
                logger.info(
                    f"[FEATURE009] Ensemble match found: deer={best_deer.id}, "
                    f"ensemble={best_ensemble_score:.3f} "
                    f"(M={best_component_scores['multiscale']:.3f}, "
                    f"E={best_component_scores['efficientnet']:.3f})"
                )
                return best_deer, best_ensemble_score, best_component_scores
            else:
                logger.info(
                    f"[FEATURE009] Best ensemble {best_ensemble_score:.3f} below threshold {REID_THRESHOLD}"
                )
                return None

        else:
            # Fallback: Original ResNet50 matching
            if features.get('resnet50') is None:
                logger.error("[FEATURE009] No feature vectors available for matching")
                return None

            resnet_list = features['resnet50'].tolist()

            results = (
                db.query(
                    Deer,
                    (1 - Deer.feature_vector.cosine_distance(resnet_list)).label('similarity')
                )
                .filter(Deer.feature_vector.isnot(None))
                .filter(Deer.sex == deer_sex)
                .order_by(Deer.feature_vector.cosine_distance(resnet_list))
                .all()
            )

            if not results:
                logger.info(f"[FEATURE009] No deer profiles found for sex={deer_sex.value}")
                return None

            best_deer, best_similarity = results[0]

            # Log similarity scores
            if detection_id:
                for deer, similarity_score in results:
                    try:
                        db.execute(
                            text("""
                                INSERT INTO reid_similarity_scores
                                (detection_id, deer_id, similarity_score, sex_match, matched,
                                 threshold_used, detection_classification, deer_sex)
                                VALUES (:detection_id, :deer_id, :similarity_score, :sex_match,
                                        :matched, :threshold_used, :detection_classification, :deer_sex)
                                ON CONFLICT (detection_id, deer_id) DO NOTHING
                            """),
                            {
                                'detection_id': detection_id,
                                'deer_id': deer.id,
                                'similarity_score': float(similarity_score),
                                'sex_match': True,
                                'matched': similarity_score >= REID_THRESHOLD,
                                'threshold_used': float(REID_THRESHOLD),
                                'detection_classification': sex,
                                'deer_sex': deer.sex.value
                            }
                        )
                    except Exception:
                        pass

                try:
                    db.commit()
                except Exception:
                    db.rollback()

            if best_similarity >= REID_THRESHOLD:
                logger.info(
                    f"[FEATURE009] ResNet50 match found: deer={best_deer.id}, "
                    f"similarity={best_similarity:.3f}"
                )
                component_scores = {'resnet50': float(best_similarity)}
                return best_deer, best_similarity, component_scores
            else:
                logger.info(
                    f"[FEATURE009] Best similarity {best_similarity:.3f} below threshold {REID_THRESHOLD}"
                )
                return None

    except Exception as e:
        logger.error(f"[FEATURE009] Ensemble matching failed: {e}")
        logger.exception(e)
        return None


def find_matching_deer(db, feature_vector: np.ndarray, sex: str, detection_id: Optional[UUID] = None) -> Optional[Tuple[Deer, float]]:
    """
    Find matching deer profile using vector similarity search.

    Uses pgvector cosine distance to find nearest neighbor.
    Only searches within same sex category for better accuracy.

    **Option D Enhancement (Nov 2025):** Now logs ALL similarity scores to
    reid_similarity_scores table for performance monitoring and threshold analysis.

    Args:
        db: Database session
        feature_vector: 512-dim embedding to match
        sex: Detected sex (doe, fawn, mature, mid, young)
        detection_id: UUID of detection (for similarity logging - Option D)

    Returns:
        Tuple[Deer, float]: Matching deer and similarity score, or None
    """
    try:
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import func, cast, text

        # Map classification to deer sex
        sex_mapping = {
            'doe': DeerSex.DOE,
            'buck': DeerSex.BUCK,
            'fawn': DeerSex.FAWN,
            'mature': DeerSex.BUCK,
            'mid': DeerSex.BUCK,
            'young': DeerSex.BUCK,
            'unknown': DeerSex.UNKNOWN
        }

        deer_sex = sex_mapping.get(sex, DeerSex.UNKNOWN)

        # Query for ALL deer with feature vectors and matching sex
        # Option D: We need all similarity scores, not just the best match
        # Convert numpy array to list for pgvector
        feature_list = feature_vector.tolist() if hasattr(feature_vector, 'tolist') else list(feature_vector)

        all_results = (
            db.query(
                Deer,
                (1 - Deer.feature_vector.cosine_distance(feature_list)).label('similarity')
            )
            .filter(Deer.feature_vector.isnot(None))
            .filter(Deer.sex == deer_sex)
            .order_by(Deer.feature_vector.cosine_distance(feature_list))
            .all()
        )

        # Option D: Log ALL similarity scores for performance monitoring
        if detection_id and all_results:
            try:
                for deer, similarity_score in all_results:
                    # Determine if this score resulted in a match
                    matched = similarity_score >= REID_THRESHOLD
                    sex_match = (deer.sex == deer_sex)

                    # Insert similarity score record
                    db.execute(
                        text("""
                            INSERT INTO reid_similarity_scores
                            (detection_id, deer_id, similarity_score, sex_match, matched,
                             threshold_used, detection_classification, deer_sex)
                            VALUES (:detection_id, :deer_id, :similarity_score, :sex_match,
                                    :matched, :threshold_used, :detection_classification, :deer_sex)
                            ON CONFLICT (detection_id, deer_id) DO NOTHING
                        """),
                        {
                            'detection_id': detection_id,
                            'deer_id': deer.id,
                            'similarity_score': float(similarity_score),
                            'sex_match': sex_match,
                            'matched': matched,
                            'threshold_used': float(REID_THRESHOLD),
                            'detection_classification': sex,
                            'deer_sex': deer.sex.value
                        }
                    )
                # Commit similarity logs immediately (separate from deer assignment)
                db.commit()
            except Exception as log_error:
                logger.warning(f"[WARN] Failed to log similarity scores: {log_error}")
                # Don't fail the whole task if logging fails
                db.rollback()

        # Now find the best match (original logic)
        if all_results:
            best_deer, best_similarity = all_results[0]  # First result is best match
            logger.info(f"[INFO] Found potential match: {best_deer.id} (similarity: {best_similarity:.3f})")

            # Check if similarity exceeds threshold
            if best_similarity >= REID_THRESHOLD:
                return best_deer, best_similarity
            else:
                logger.info(f"[INFO] Similarity {best_similarity:.3f} below threshold {REID_THRESHOLD}")
                return None
        else:
            logger.info(f"[INFO] No existing deer profiles found for sex={deer_sex.value}")
            return None

    except Exception as e:
        logger.error(f"[FAIL] Similarity search failed: {e}")
        return None


def get_burst_detections(db, detection: Detection) -> List[Detection]:
    """
    Find all detections in the same photo burst/event with matching classification.

    A burst is defined as photos taken within BURST_WINDOW seconds
    at the same camera location. This handles cases where cameras
    take multiple photos within the same second or a few seconds apart.

    IMPORTANT: Only returns detections with the SAME classification (sex)
    as the input detection to prevent cross-sex deer profile contamination.

    Args:
        db: Database session
        detection: Detection to find burst companions for

    Returns:
        List[Detection]: All non-duplicate detections in the same burst
                         with matching classification, including the input detection
    """
    # Get the image for this detection
    image = db.query(Image).filter(Image.id == detection.image_id).first()
    if not image or not image.timestamp or not image.location_id:
        # Can't group without timestamp and location
        return [detection]

    # Calculate time window
    time_start = image.timestamp - timedelta(seconds=BURST_WINDOW)
    time_end = image.timestamp + timedelta(seconds=BURST_WINDOW)

    # Find all images within burst window at same location
    burst_images = (
        db.query(Image)
        .filter(Image.location_id == image.location_id)
        .filter(Image.timestamp >= time_start)
        .filter(Image.timestamp <= time_end)
        .all()
    )

    # Collect all non-duplicate detections from burst images
    # FILTER BY CLASSIFICATION to prevent cross-sex grouping
    burst_detections = []
    for img in burst_images:
        for det in img.detections:
            # Only include non-duplicate detections with matching classification
            if not det.is_duplicate and det.classification == detection.classification:
                burst_detections.append(det)

    logger.debug(
        f"[BURST] Found {len(burst_detections)} detections in burst "
        f"({len(burst_images)} images within {BURST_WINDOW}s, classification={detection.classification})"
    )

    return burst_detections


def check_burst_for_existing_deer(db, burst_detections: List[Detection]) -> Optional[UUID]:
    """
    Check if any detection in burst already has an assigned deer_id.

    If multiple deer_ids exist, returns the one with highest confidence.

    Args:
        db: Database session
        burst_detections: List of detections in the burst

    Returns:
        UUID: Existing deer_id if found, None otherwise
    """
    # Find detections with deer_id assigned
    assigned = [det for det in burst_detections if det.deer_id is not None]

    if not assigned:
        return None

    # If multiple deer_ids, use the one with highest confidence
    # (This handles edge case where re-ID ran on some but not all)
    best_detection = max(assigned, key=lambda d: d.confidence)

    logger.info(
        f"[BURST] Found existing deer_id in burst: {best_detection.deer_id} "
        f"(from {len(assigned)} of {len(burst_detections)} detections)"
    )

    return best_detection.deer_id


@app.task(bind=True, name='worker.tasks.reidentification.reidentify_deer_task')
def reidentify_deer_task(self, detection_id: str) -> Dict:
    """
    Re-identify individual deer from detection with burst grouping.

    This task implements the final stage of the ML pipeline:
    1. Check if detection is in a photo burst (5-second window)
    2. If burst exists and any detection has deer_id, reuse it
    3. Otherwise: Extract crop, generate features, search for match
    4. Link all burst detections to same deer (assign burst_group_id)
    5. Either link to existing deer or create new profile

    Burst grouping prevents creating separate deer profiles for the
    same animal photographed multiple times within seconds.

    Args:
        self: Celery task instance (bound)
        detection_id: UUID string of detection to process

    Returns:
        dict: Processing results with deer_id and match status
    """
    db = SessionLocal()

    try:
        # Convert detection_id to UUID
        try:
            detection_uuid = UUID(detection_id)
        except ValueError as e:
            logger.error(f"[FAIL] Invalid UUID format: {detection_id}")
            return {"status": "error", "error": f"Invalid UUID: {e}"}

        # Load detection record
        detection = db.query(Detection).filter(Detection.id == detection_uuid).first()

        if not detection:
            logger.error(f"[FAIL] Detection not found: {detection_id}")
            return {"status": "error", "error": "Detection not found"}

        logger.info(f"[INFO] Starting re-ID for detection {detection_id}")
        task_start_time = time.time()

        # Sprint 8: Find all detections in same photo burst
        burst_detections = get_burst_detections(db, detection)

        # Check if any detection in burst already has deer_id assigned
        existing_deer_id = check_burst_for_existing_deer(db, burst_detections)

        if existing_deer_id:
            # Reuse existing deer_id from burst companion
            # Generate burst_group_id and link all detections
            burst_group_id = uuid.uuid4()

            for det in burst_detections:
                if det.deer_id is None:
                    det.deer_id = existing_deer_id
                det.burst_group_id = burst_group_id

            db.commit()

            duration = time.time() - task_start_time
            logger.info(
                f"[OK] Re-ID complete (BURST_LINK): detection={detection_id}, "
                f"deer={existing_deer_id}, burst_size={len(burst_detections)}, "
                f"duration={duration:.2f}s"
            )

            return {
                "status": "burst_linked",
                "detection_id": detection_id,
                "deer_id": str(existing_deer_id),
                "burst_group_id": str(burst_group_id),
                "burst_size": len(burst_detections),
                "duration": duration
            }

        # Load image
        image = db.query(Image).filter(Image.id == detection.image_id).first()
        if not image:
            logger.error(f"[FAIL] Image not found for detection {detection_id}")
            return {"status": "error", "error": "Image not found"}

        image_path = Path(image.path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image.path}")

        # Extract deer crop
        crop = extract_deer_crop(image_path, detection.bbox)
        if crop is None:
            logger.warning(f"[WARN] Failed to extract crop for detection {detection_id}")
            return {"status": "skipped", "reason": "Invalid crop"}

        # Feature 009: Extract all feature vectors (ResNet50 + multi-scale + EfficientNet)
        features = extract_all_features(crop)
        if features['resnet50'] is None:
            logger.error(f"[FAIL] Failed to extract features for detection {detection_id}")
            return {"status": "failed", "error": "Feature extraction failed"}

        # Feature 009: Search for matching deer using ensemble matching
        match_result = find_matching_deer_ensemble(db, features, detection.classification, detection_id=detection_uuid)

        # Generate burst_group_id for all detections in this burst
        burst_group_id = uuid.uuid4()

        if match_result:
            # Match found - link to existing deer
            deer, similarity, component_scores = match_result

            # Link all burst detections to matched deer
            for det in burst_detections:
                det.deer_id = deer.id
                det.burst_group_id = burst_group_id

            # Update deer sighting
            deer.update_sighting(image.timestamp, detection.confidence)

            db.commit()

            duration = time.time() - task_start_time
            logger.info(
                f"[OK] Re-ID complete (MATCH): detection={detection_id}, "
                f"deer={deer.id}, similarity={similarity:.3f}, "
                f"scores={component_scores}, "
                f"burst_size={len(burst_detections)}, duration={duration:.2f}s"
            )

            return {
                "status": "matched",
                "detection_id": detection_id,
                "deer_id": str(deer.id),
                "burst_group_id": str(burst_group_id),
                "burst_size": len(burst_detections),
                "similarity": float(similarity),
                "component_scores": component_scores,
                "duration": duration
            }
        else:
            # No match - create new deer profile with all feature vectors
            sex_value = (
                DeerSex.DOE if detection.classification == 'doe'
                else DeerSex.FAWN if detection.classification == 'fawn'
                else DeerSex.BUCK
            )

            # Feature 009: Store all feature vectors with version tracking
            embedding_version = 'v1_resnet50'  # Default
            if USE_ENHANCED_REID and features.get('multiscale') is not None and features.get('efficientnet') is not None:
                embedding_version = 'v3_ensemble'  # Multi-scale + EfficientNet
            elif features.get('multiscale') is not None:
                embedding_version = 'v2_multiscale'  # Multi-scale only

            new_deer = Deer(
                sex=sex_value,
                first_seen=image.timestamp,
                last_seen=image.timestamp,
                feature_vector=features['resnet50'].tolist() if features['resnet50'] is not None else None,
                feature_vector_multiscale=features['multiscale'].tolist() if features.get('multiscale') is not None else None,
                feature_vector_efficientnet=features['efficientnet'].tolist() if features.get('efficientnet') is not None else None,
                embedding_version=embedding_version,
                confidence=detection.confidence,
                sighting_count=1
            )

            db.add(new_deer)
            db.flush()  # Get ID before linking

            # Link all burst detections to new deer
            for det in burst_detections:
                det.deer_id = new_deer.id
                det.burst_group_id = burst_group_id

            db.commit()

            duration = time.time() - task_start_time
            logger.info(
                f"[OK] Re-ID complete (NEW): detection={detection_id}, "
                f"deer={new_deer.id}, version={embedding_version}, "
                f"burst_size={len(burst_detections)}, duration={duration:.2f}s"
            )

            return {
                "status": "new_profile",
                "detection_id": detection_id,
                "deer_id": str(new_deer.id),
                "burst_group_id": str(burst_group_id),
                "burst_size": len(burst_detections),
                "embedding_version": embedding_version,
                "duration": duration
            }

    except FileNotFoundError as e:
        error_msg = f"Image file not found: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for detection {detection_id}")
        return {"status": "failed", "detection_id": detection_id, "error": error_msg}

    except Exception as e:
        error_msg = f"Re-ID failed: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for detection {detection_id}")
        logger.exception(e)
        return {"status": "failed", "detection_id": detection_id, "error": error_msg}

    finally:
        db.close()


# Export task and Feature 009 enhanced functions
__all__ = [
    "reidentify_deer_task",
    "extract_feature_vector",
    "extract_multiscale_features",
    "extract_efficientnet_features",
    "extract_all_features",
    "find_matching_deer",
    "find_matching_deer_ensemble"
]
