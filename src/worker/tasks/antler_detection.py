"""
Antler keypoint detection task for bucks.

Uses YOLOv8-pose model to detect 16 anatomical keypoints on buck antlers
for enhanced Re-ID matching and scoring.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from uuid import UUID

from PIL import Image
import torch
from ultralytics import YOLO

from worker.celery_app import celery_app
from backend.core.database import get_db
from backend.models import Detection, AntlerKeypoint

logger = logging.getLogger(__name__)

# Model configuration
ANTLER_MODEL_PATH = os.getenv(
    "ANTLER_MODEL_PATH",
    "/app/models/runs/antler_detection_20251116/weights/best.pt"
)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Global model instance (loaded on-demand per thread)
_antler_model = None


def get_antler_model() -> YOLO:
    """
    Get or load the antler detection model.

    Returns:
        YOLO: Loaded antler keypoint detection model
    """
    global _antler_model

    if _antler_model is None:
        logger.info(f"Loading antler model from {ANTLER_MODEL_PATH}")
        _antler_model = YOLO(ANTLER_MODEL_PATH)
        _antler_model.to(DEVICE)
        logger.info(f"[OK] Antler model loaded on {DEVICE}")

    return _antler_model


@celery_app.task(
    name="worker.tasks.antler_detection.detect_antler_keypoints",
    bind=True,
    max_retries=2,
    default_retry_delay=30
)
def detect_antler_keypoints(self, detection_id: str) -> Dict:
    """
    Detect antler keypoints for a buck detection.

    Args:
        detection_id: UUID of the detection to process

    Returns:
        Dict: Results with keypoint count and status
    """
    db = next(get_db())

    try:
        # Get detection
        detection = db.query(Detection).filter(Detection.id == UUID(detection_id)).first()

        if not detection:
            logger.error(f"Detection {detection_id} not found")
            return {"status": "error", "message": "Detection not found"}

        # Only process bucks
        classification = detection.corrected_classification or detection.classification
        if classification.lower() != "buck":
            logger.debug(f"Skipping non-buck detection {detection_id} ({classification})")
            return {
                "status": "skipped",
                "message": f"Not a buck ({classification})",
                "keypoints_detected": 0
            }

        # Get image path
        image_path = Path(detection.image.path)
        if not image_path.exists():
            logger.error(f"Image file not found: {image_path}")
            return {"status": "error", "message": "Image file not found"}

        # Load image
        img = Image.open(image_path)

        # Crop to detection bbox
        x, y, w, h = detection.bbox_coords
        crop = img.crop((x, y, x + w, y + h))

        # Run antler detection
        model = get_antler_model()
        results = model(crop, verbose=False)

        # Extract keypoints
        keypoints_saved = 0

        if results and len(results) > 0:
            result = results[0]

            # Check if keypoints were detected
            if hasattr(result, 'keypoints') and result.keypoints is not None:
                # Get keypoint data (shape: [num_detections, num_keypoints, 3])
                kpts = result.keypoints.data.cpu().numpy()

                if len(kpts) > 0:
                    # Use first detection (highest confidence)
                    keypoint_coords = kpts[0]  # Shape: [16, 3] (x, y, visibility)

                    # Delete existing keypoints for this detection (if reprocessing)
                    db.query(AntlerKeypoint).filter(
                        AntlerKeypoint.detection_id == UUID(detection_id)
                    ).delete()

                    # Create keypoint instances
                    keypoint_instances = AntlerKeypoint.from_yolo_result(
                        detection_id=UUID(detection_id),
                        keypoints=keypoint_coords.tolist()
                    )

                    # Save to database
                    for kpt in keypoint_instances:
                        db.add(kpt)
                        keypoints_saved += 1

                    db.commit()

                    logger.info(
                        f"[OK] Detected {keypoints_saved} antler keypoints for detection {detection_id}"
                    )
                else:
                    logger.warning(f"No antler detections in crop for {detection_id}")

        return {
            "status": "success",
            "detection_id": detection_id,
            "keypoints_detected": keypoints_saved,
        }

    except Exception as e:
        logger.error(f"Error detecting antler keypoints for {detection_id}: {e}")
        db.rollback()

        # Retry on transient errors
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name="worker.tasks.antler_detection.batch_detect_antler_keypoints",
    bind=True
)
def batch_detect_antler_keypoints(
    self,
    detection_ids: Optional[List[str]] = None,
    limit: int = 100
) -> Dict:
    """
    Batch process antler keypoint detection for multiple bucks.

    Args:
        detection_ids: Optional list of detection UUIDs to process
        limit: Maximum number of detections to process (default 100)

    Returns:
        Dict: Results summary
    """
    db = next(get_db())

    try:
        # Get buck detections to process
        query = db.query(Detection).filter(
            Detection.classification.in_(["buck"])
        )

        # Filter by IDs if provided
        if detection_ids:
            uuids = [UUID(did) for did in detection_ids]
            query = query.filter(Detection.id.in_(uuids))

        # Limit results
        detections = query.limit(limit).all()

        logger.info(f"Processing antler keypoints for {len(detections)} buck detections")

        # Queue individual tasks
        task_ids = []
        for detection in detections:
            task = detect_antler_keypoints.apply_async(
                args=[str(detection.id)],
                queue='ml_processing'
            )
            task_ids.append(task.id)

        return {
            "status": "queued",
            "detections_queued": len(task_ids),
            "task_ids": task_ids
        }

    except Exception as e:
        logger.error(f"Error in batch antler detection: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        db.close()


__all__ = [
    "detect_antler_keypoints",
    "batch_detect_antler_keypoints",
    "get_antler_model"
]
