"""
Detection Task for Deer Detection Pipeline
Version: 1.0.0
Date: 2025-11-05

Implements YOLOv8 deer detection with database integration per spec FR-003, FR-008, FR-009.

Task Flow:
    1. Update image status to "processing"
    2. Load image from filesystem
    3. Run YOLOv8 inference
    4. Create Detection records for each bbox
    5. Update image status to "completed"
    6. [ON ERROR] Update status to "failed" with error_message

Requirements Satisfied:
    - FR-003: Create Detection database records with bbox, confidence, class_id
    - FR-004: Image.processing_status state transitions
    - FR-008: Handle detection failures gracefully
    - FR-009: Store error messages in Image.error_message
    - FR-010: Use Celery task queue
    - NFR-003: Recover from GPU OOM errors
"""

import os
import logging
import time
import threading
from pathlib import Path
from typing import List, Dict
from uuid import UUID

import torch
from PIL import Image as PILImage
from ultralytics import YOLO

from worker.celery_app import app
from backend.core.database import SessionLocal
from backend.models.image import Image, ProcessingStatus
from backend.models.detection import Detection


# Configure logging (T011)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
CONFIDENCE_THRESHOLD = float(os.getenv('DETECTION_CONFIDENCE', 0.5))
IOU_THRESHOLD = float(os.getenv('DETECTION_IOU', 0.45))
MAX_DETECTIONS = int(os.getenv('MAX_DETECTIONS', 20))
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Model paths (Sprint 4: Multi-class model for sex/age classification)
MODEL_DIR = Path(os.getenv('MODEL_DIR', 'src/models'))
YOLO_MODEL_PATH = MODEL_DIR / 'runs' / 'deer_multiclass' / 'weights' / 'best.pt'

# Class mapping from multi-class model (Sprint 4)
# Model has 11 classes, we care about deer classes for sex/age
CLASS_NAMES = {
    0: "UTV",
    1: "cow",
    2: "coyote",
    3: "doe",        # Female deer
    4: "fawn",       # Baby deer (sex unknown)
    5: "mature",     # Mature buck (large antlers)
    6: "mid",        # Mid-age buck (medium antlers)
    7: "person",
    8: "raccoon",
    9: "turkey",
    10: "young"      # Young buck (small/spike antlers)
}

# Deer-specific classes for filtering
DEER_CLASSES = {3, 4, 5, 6, 10}  # doe, fawn, mature, mid, young

# Deduplication settings (Sprint 8)
DEDUP_IOU_THRESHOLD = float(os.getenv('DEDUP_IOU_THRESHOLD', 0.5))  # 50% overlap = duplicate


# Global model cache for worker process (T010)
# WHY: Loading model on every task is expensive. Keep in memory across tasks.
_detection_model = None
_model_lock = threading.Lock()  # Thread-safe model loading (Sprint 3)


def get_detection_model():
    """
    Get or load YOLOv8 detection model (singleton pattern with thread-safety).

    Returns model in GPU memory with optimizations enabled (T010).
    Thread-safe for use with threads pool (Sprint 3).

    Returns:
        YOLO: Detection model ready for inference

    Raises:
        FileNotFoundError: If model file doesn't exist
        RuntimeError: If model fails to load
    """
    global _detection_model

    # Double-checked locking pattern for thread-safe singleton
    if _detection_model is None:
        with _model_lock:
            # Check again inside lock (another thread may have loaded it)
            if _detection_model is None:
                try:
                    logger.info(f"[INFO] Loading YOLOv8 model from {YOLO_MODEL_PATH}")

                    # Validate model file exists (already checked at startup by FR-011)
                    if not YOLO_MODEL_PATH.exists():
                        raise FileNotFoundError(
                            f"Model file not found: {YOLO_MODEL_PATH}. "
                            f"Worker should have failed startup validation."
                        )

                    # Load model
                    _detection_model = YOLO(str(YOLO_MODEL_PATH))

                    # Move to GPU if available (T010)
                    _detection_model.to(DEVICE)

                    logger.info(f"[OK] YOLOv8 model loaded on {DEVICE}")

                except Exception as e:
                    logger.error(f"[FAIL] Failed to load detection model: {e}")
                    raise RuntimeError(f"Model loading failed: {e}")

    return _detection_model


def deduplicate_within_image(db, image_id: UUID) -> int:
    """
    Mark duplicate detections within a single image.

    When YOLOv8 detects the same deer multiple times with overlapping bboxes,
    keep only the highest confidence detection and mark others as duplicates.

    Args:
        db: Database session
        image_id: UUID of image to deduplicate

    Returns:
        int: Number of detections marked as duplicates

    Algorithm:
        1. Get all detections for image, sorted by confidence descending
        2. For each detection, check IoU with higher-confidence detections
        3. If IoU > threshold, mark as duplicate
        4. Skip re-ID processing for duplicates
    """
    # Get all detections for this image, sorted by confidence descending
    detections = (
        db.query(Detection)
        .filter(Detection.image_id == image_id)
        .order_by(Detection.confidence.desc())
        .all()
    )

    if len(detections) <= 1:
        return 0  # No duplicates possible with 0 or 1 detection

    duplicate_count = 0

    # Keep track of non-duplicate (keeper) detections
    keepers = []

    for detection in detections:
        # Check if this detection overlaps significantly with any keeper
        is_duplicate = False

        for keeper in keepers:
            iou = detection.iou(keeper)

            if iou > DEDUP_IOU_THRESHOLD:
                # Significant overlap with higher-confidence detection
                detection.is_duplicate = True
                is_duplicate = True
                duplicate_count += 1
                logger.debug(
                    f"[DEDUP] Marking detection {detection.id} as duplicate "
                    f"(IoU={iou:.3f} with {keeper.id})"
                )
                break

        if not is_duplicate:
            # This is a unique detection, add to keepers
            keepers.append(detection)

    if duplicate_count > 0:
        logger.info(
            f"[DEDUP] Marked {duplicate_count} of {len(detections)} detections "
            f"as duplicates (kept {len(keepers)} unique)"
        )

    return duplicate_count


@app.task(bind=True, name='worker.tasks.detection.detect_deer_task')
def detect_deer_task(self, image_id: str) -> Dict:
    """
    Detect deer in a single image using YOLOv8 (T008).

    This task implements the first stage of the ML pipeline per spec.
    Handles all error cases gracefully per FR-008.

    Args:
        self: Celery task instance (bound)
        image_id: UUID string of image to process

    Returns:
        dict: Processing results with detection count and status

    Task Flow:
        1. Load image record from database
        2. Update status to "processing"
        3. Load image file from filesystem
        4. Run YOLOv8 inference with GPU optimization
        5. Create Detection records for each bbox
        6. Update status to "completed"
        7. Return results

    Error Handling (T009):
        - PIL.UnidentifiedImageError: Corrupted image -> mark failed
        - torch.cuda.OutOfMemoryError: GPU OOM -> mark failed, log for monitoring
        - FileNotFoundError: Image file missing -> mark failed
        - Exception: Any other error -> mark failed with error message
    """
    # Get database session
    db = SessionLocal()

    try:
        # Convert image_id to UUID
        try:
            image_uuid = UUID(image_id)
        except ValueError as e:
            logger.error(f"[FAIL] Invalid UUID format: {image_id}")
            return {"status": "error", "error": f"Invalid UUID: {e}"}

        # Load image record from database (T008)
        image = db.query(Image).filter(Image.id == image_uuid).first()

        if not image:
            logger.error(f"[FAIL] Image not found in database: {image_id}")
            return {"status": "error", "error": "Image not found"}

        # Log task start (T011 - FR-005: log with image_id)
        logger.info(f"[INFO] Starting detection for image {image_id} ({image.filename})")
        task_start_time = time.time()

        # Update status to PROCESSING (T008 - FR-004 state transition)
        image.mark_processing()
        db.commit()
        logger.info(f"[INFO] Image {image_id} status -> processing")

        # Load image from filesystem (T008)
        image_path = Path(image.path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image.path}")

        try:
            pil_image = PILImage.open(image_path)
        except PILImage.UnidentifiedImageError as e:
            # Corrupted image file (T009 - Edge case handling)
            raise PILImage.UnidentifiedImageError(f"Corrupted image file: {e}")

        logger.info(f"[INFO] Loaded image {image.filename} ({pil_image.size[0]}x{pil_image.size[1]})")

        # Get detection model (T010 - GPU optimization)
        model = get_detection_model()

        # Run YOLOv8 inference (T010 - with GPU optimization)
        # Use torch.no_grad() to reduce memory usage
        with torch.no_grad():
            try:
                results = model.predict(
                    source=str(image_path),
                    conf=CONFIDENCE_THRESHOLD,
                    iou=IOU_THRESHOLD,
                    max_det=MAX_DETECTIONS,
                    device=DEVICE,
                    verbose=False  # Reduce log noise
                )
            except torch.cuda.OutOfMemoryError as e:
                # GPU OOM error (T009 - NFR-003)
                # Log for monitoring, mark image as failed
                logger.error(f"[FAIL] GPU OOM during inference for {image_id}: {e}")
                raise torch.cuda.OutOfMemoryError(f"GPU out of memory: {e}")

        # Process detection results (T008 - FR-003)
        detections_created = []
        detection_count = 0

        if results and len(results) > 0:
            result = results[0]  # Single image result

            # Get bounding boxes, confidences, and class IDs
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                logger.info(f"[INFO] Found {len(boxes)} total detections in {image.filename}")

                # Create Detection record for each bbox (T008 - FR-003)
                for i, box in enumerate(boxes):
                    # Get bbox coordinates (x1, y1, x2, y2 format from YOLO)
                    xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    x1, y1, x2, y2 = xyxy

                    # Convert to (x, y, width, height) format for database
                    bbox_dict = {
                        "x": int(x1),
                        "y": int(y1),
                        "width": int(x2 - x1),
                        "height": int(y2 - y1)
                    }

                    # Get confidence and class_id
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])

                    # Get class name from model (Sprint 4: Multi-class classification)
                    class_name = CLASS_NAMES.get(class_id, "unknown")

                    # Only create Detection records for deer (Sprint 4)
                    # Skip non-deer detections (UTV, person, etc.)
                    if class_id not in DEER_CLASSES:
                        logger.debug(f"[INFO] Skipping non-deer detection: {class_name}")
                        continue

                    # Create Detection record with classification
                    detection = Detection(
                        image_id=image.id,
                        bbox=bbox_dict,
                        confidence=confidence,
                        classification=class_name,  # Sprint 4: Set sex/age classification
                        deer_id=None  # Will be set by re-ID stage
                    )

                    db.add(detection)
                    detection_count += 1

                # Flush to assign IDs to detections
                db.flush()

                # Deduplicate within-image detections (Sprint 8: Deduplication)
                # Mark overlapping detections as duplicates, keep highest confidence
                if detection_count > 1:
                    logger.info(f"[INFO] Checking for duplicate detections (found {detection_count})")
                    deduplicate_within_image(db, image.id)
                    db.flush()  # Flush duplicate flags

                # Collect non-duplicate detection IDs for re-ID processing
                # Skip duplicates to avoid creating redundant deer profiles
                for detection in db.query(Detection).filter(Detection.image_id == image.id).all():
                    if not detection.is_duplicate and str(detection.id) not in detections_created:
                        detections_created.append(str(detection.id))

                logger.info(f"[OK] Created {detection_count} deer Detection records for {image_id}")
            else:
                logger.info(f"[INFO] No deer detections found in {image.filename}")

        # Update image status to COMPLETED (T008 - FR-004 state transition)
        image.mark_completed()
        db.commit()

        # Sprint 6: Queue re-identification tasks for each detection
        # Chain re-ID after successful detection to build deer profiles
        reid_task_ids = []
        if detection_count > 0:
            from worker.tasks.reidentification import reidentify_deer_task

            for detection_id in detections_created:
                # Queue re-ID task asynchronously
                result = reidentify_deer_task.delay(detection_id)
                reid_task_ids.append(result.id)

            logger.info(f"[OK] Queued {len(reid_task_ids)} re-ID tasks for image {image_id}")

        # Calculate task duration (T011)
        task_end_time = time.time()
        duration = task_end_time - task_start_time

        # Log completion (T011 - FR-005: log detection count and duration)
        avg_confidence = sum(
            det.confidence for det in db.query(Detection).filter(Detection.image_id == image.id).all()
        ) / detection_count if detection_count > 0 else 0.0

        logger.info(
            f"[OK] Detection complete for {image_id}: "
            f"{detection_count} detections, "
            f"avg confidence {avg_confidence:.2f}, "
            f"duration {duration:.2f}s"
        )

        return {
            "status": "completed",
            "image_id": image_id,
            "detection_count": detection_count,
            "detections": detections_created,
            "reid_tasks": reid_task_ids,  # Sprint 6: Re-ID task IDs for monitoring
            "avg_confidence": avg_confidence,
            "duration": duration
        }

    except PILImage.UnidentifiedImageError as e:
        # Corrupted image (T009)
        error_msg = f"Corrupted image file: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for image {image_id}")

        if image:
            image.mark_failed(error_msg)
            db.commit()

        return {"status": "failed", "image_id": image_id, "error": error_msg}

    except torch.cuda.OutOfMemoryError as e:
        # GPU OOM (T009 - NFR-003)
        error_msg = f"GPU out of memory: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for image {image_id}")

        if image:
            image.mark_failed(error_msg)
            db.commit()

        # Clear GPU cache to help recover
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("[INFO] Cleared GPU cache after OOM")

        return {"status": "failed", "image_id": image_id, "error": error_msg}

    except FileNotFoundError as e:
        # Image file missing (T009)
        error_msg = f"Image file not found: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for image {image_id}")

        if image:
            image.mark_failed(error_msg)
            db.commit()

        return {"status": "failed", "image_id": image_id, "error": error_msg}

    except Exception as e:
        # Any other error (T009 - FR-008: handle failures gracefully)
        error_msg = f"Detection failed: {str(e)}"
        logger.error(f"[FAIL] {error_msg} for image {image_id}")
        logger.exception(e)  # Log full traceback

        if image:
            image.mark_failed(error_msg)
            db.commit()

        return {"status": "failed", "image_id": image_id, "error": error_msg}

    finally:
        # Always close database session
        db.close()


# Export task
__all__ = ["detect_deer_task"]
