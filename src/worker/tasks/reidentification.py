"""
Re-Identification Task for Deer Tracking
Sprint 5: Individual deer identification using ResNet50 embeddings

This module implements the re-identification stage of the ML pipeline:
1. Extract deer crop from detection bbox
2. Generate 512-dim feature vector using ResNet50
3. Search for matching deer profile using cosine similarity
4. Either link to existing deer or create new profile

Architecture:
- Model: ResNet50 pretrained on ImageNet
- Embeddings: 512 dimensions (final pooling layer)
- Similarity: Cosine distance via pgvector
- Threshold: 0.85 (conservative to avoid false matches)
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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
REID_THRESHOLD = float(os.getenv('REID_THRESHOLD', 0.85))
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
MIN_CROP_SIZE = 50  # Minimum width/height for valid crop
BURST_WINDOW = 5  # Seconds - group photos within this window as same event


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


def find_matching_deer(db, feature_vector: np.ndarray, sex: str) -> Optional[Tuple[Deer, float]]:
    """
    Find matching deer profile using vector similarity search.

    Uses pgvector cosine distance to find nearest neighbor.
    Only searches within same sex category for better accuracy.

    Args:
        db: Database session
        feature_vector: 512-dim embedding to match
        sex: Detected sex (doe, fawn, mature, mid, young)

    Returns:
        Tuple[Deer, float]: Matching deer and similarity score, or None
    """
    try:
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import func, cast

        # Map classification to deer sex
        sex_mapping = {
            'doe': DeerSex.DOE,
            'fawn': DeerSex.FAWN,
            'mature': DeerSex.BUCK,
            'mid': DeerSex.BUCK,
            'young': DeerSex.BUCK,
            'unknown': DeerSex.UNKNOWN
        }

        deer_sex = sex_mapping.get(sex, DeerSex.UNKNOWN)

        # Query for nearest neighbor using cosine distance
        # Only search deer with feature vectors and matching sex
        # Convert numpy array to list for pgvector
        feature_list = feature_vector.tolist() if hasattr(feature_vector, 'tolist') else list(feature_vector)

        result = (
            db.query(
                Deer,
                (1 - Deer.feature_vector.cosine_distance(feature_list)).label('similarity')
            )
            .filter(Deer.feature_vector.isnot(None))
            .filter(Deer.sex == deer_sex)
            .order_by(Deer.feature_vector.cosine_distance(feature_list))
            .limit(1)
            .first()
        )

        if result:
            deer, similarity = result
            logger.info(f"[INFO] Found potential match: {deer.id} (similarity: {similarity:.3f})")

            # Check if similarity exceeds threshold
            if similarity >= REID_THRESHOLD:
                return deer, similarity
            else:
                logger.info(f"[INFO] Similarity {similarity:.3f} below threshold {REID_THRESHOLD}")
                return None
        else:
            logger.info(f"[INFO] No existing deer profiles found for sex={deer_sex.value}")
            return None

    except Exception as e:
        logger.error(f"[FAIL] Similarity search failed: {e}")
        return None


def get_burst_detections(db, detection: Detection) -> List[Detection]:
    """
    Find all detections in the same photo burst/event.

    A burst is defined as photos taken within BURST_WINDOW seconds
    at the same camera location. This handles cases where cameras
    take multiple photos within the same second or a few seconds apart.

    Args:
        db: Database session
        detection: Detection to find burst companions for

    Returns:
        List[Detection]: All non-duplicate detections in the same burst,
                         including the input detection
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
    burst_detections = []
    for img in burst_images:
        for det in img.detections:
            # Only include non-duplicate detections
            if not det.is_duplicate:
                burst_detections.append(det)

    logger.debug(
        f"[BURST] Found {len(burst_detections)} detections in burst "
        f"({len(burst_images)} images within {BURST_WINDOW}s)"
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

        # Extract feature vector
        feature_vector = extract_feature_vector(crop)
        if feature_vector is None:
            logger.error(f"[FAIL] Failed to extract features for detection {detection_id}")
            return {"status": "failed", "error": "Feature extraction failed"}

        # Search for matching deer
        match_result = find_matching_deer(db, feature_vector, detection.classification)

        # Generate burst_group_id for all detections in this burst
        burst_group_id = uuid.uuid4()

        if match_result:
            # Match found - link to existing deer
            deer, similarity = match_result

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
                f"burst_size={len(burst_detections)}, duration={duration:.2f}s"
            )

            return {
                "status": "matched",
                "detection_id": detection_id,
                "deer_id": str(deer.id),
                "burst_group_id": str(burst_group_id),
                "burst_size": len(burst_detections),
                "similarity": float(similarity),
                "duration": duration
            }
        else:
            # No match - create new deer profile
            new_deer = Deer(
                sex=DeerSex.DOE if detection.classification == 'doe'
                    else DeerSex.FAWN if detection.classification == 'fawn'
                    else DeerSex.BUCK,
                first_seen=image.timestamp,
                last_seen=image.timestamp,
                feature_vector=feature_vector.tolist(),
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
                f"deer={new_deer.id}, burst_size={len(burst_detections)}, "
                f"duration={duration:.2f}s"
            )

            return {
                "status": "new_profile",
                "detection_id": detection_id,
                "deer_id": str(new_deer.id),
                "burst_group_id": str(burst_group_id),
                "burst_size": len(burst_detections),
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


# Export task
__all__ = ["reidentify_deer_task", "extract_feature_vector", "find_matching_deer"]
