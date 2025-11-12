"""
Detection management API endpoints.

Provides endpoints for:
- Reviewing and correcting detection data
- Marking detections as valid/invalid
- Updating classification information
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.detection import Detection
from backend.models.deer import Deer
from backend.models.image import Image

router = APIRouter(prefix="/api/detections", tags=["detections"])


def cleanup_deer_reference(detection: Detection, db: Session) -> None:
    """
    Clean up deer re-identification references when a detection is marked invalid.

    When a detection is invalidated:
    - Clear the deer_id from the detection
    - Update the deer's sighting_count
    - Update the deer's first_seen and last_seen timestamps
    - If deer has no more valid detections, leave profile for manual review

    Args:
        detection: Detection being invalidated
        db: Database session
    """
    if not detection.deer_id:
        return  # No deer reference to clean up

    print(f"[INFO] Cleaning up deer reference for detection {detection.id}")

    # Get the deer profile
    deer = db.query(Deer).filter(Deer.id == detection.deer_id).first()
    if not deer:
        print(f"[WARN] Deer {detection.deer_id} not found, clearing detection reference")
        detection.deer_id = None
        return

    # Clear the deer_id from this detection
    old_deer_id = detection.deer_id
    detection.deer_id = None

    # Count remaining valid detections for this deer
    valid_detections = db.query(Detection).filter(
        Detection.deer_id == old_deer_id,
        Detection.is_valid == True
    ).all()

    # Update deer sighting count
    deer.sighting_count = len(valid_detections)

    if valid_detections:
        # Update first_seen and last_seen based on remaining valid detections
        timestamps = []
        for det in valid_detections:
            image = db.query(Image).filter(Image.id == det.image_id).first()
            if image:
                timestamps.append(image.timestamp)

        if timestamps:
            deer.first_seen = min(timestamps)
            deer.last_seen = max(timestamps)
    else:
        # No more valid detections - leave first_seen/last_seen as is for reference
        # Don't delete the deer profile - may need manual review
        print(f"[WARN] Deer {old_deer_id} has no more valid detections")

    print(f"[INFO] Updated deer {old_deer_id}: sighting_count={deer.sighting_count}")


class DetectionCorrectionRequest(BaseModel):
    """Request model for correcting a detection."""

    is_valid: Optional[bool] = Field(
        None,
        description="Whether this detection is usable (False for rear-ends, wrong species, poor quality)"
    )
    corrected_classification: Optional[str] = Field(
        None,
        description="Corrected sex/age classification (buck/doe/fawn/unknown)"
    )
    correction_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notes explaining the correction or issue"
    )
    reviewed_by: str = Field(
        ...,
        max_length=100,
        description="Username or identifier of reviewer"
    )


class DetectionCorrectionResponse(BaseModel):
    """Response model for detection correction."""

    success: bool
    detection_id: str
    message: str
    detection: dict


class BatchCorrectionRequest(BaseModel):
    """Request model for batch correcting multiple detections."""

    detection_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of detection IDs to correct (max 1000)"
    )
    is_valid: Optional[bool] = Field(
        None,
        description="Whether detections are usable"
    )
    corrected_classification: Optional[str] = Field(
        None,
        description="Corrected sex/age classification for all selected"
    )
    correction_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notes applied to all selected detections"
    )
    reviewed_by: str = Field(
        ...,
        max_length=100,
        description="Username or identifier of reviewer"
    )


class BatchCorrectionResponse(BaseModel):
    """Response model for batch correction."""

    success: bool
    total_requested: int
    total_corrected: int
    failed_ids: List[str]
    message: str


@router.patch("/batch/correct", response_model=BatchCorrectionResponse)
def batch_correct_detections(
    correction: BatchCorrectionRequest,
    db: Session = Depends(get_db),
) -> BatchCorrectionResponse:
    """
    Apply corrections to multiple detections at once.

    Useful for bulk operations like:
    - Marking all images from a burst as invalid
    - Correcting classification for multiple similar detections
    - Batch reviewing sets of detections

    Parameters:
        correction: Batch correction data

    Returns:
        Summary of batch operation results

    Raises:
        400: Invalid correction data
    """
    # Fetch all detections in one query (much faster for large batches)
    review_time = datetime.utcnow()

    try:
        # Bulk fetch all detections
        detections = db.query(Detection).filter(
            Detection.id.in_(correction.detection_ids)
        ).all()

        # Track which IDs were found
        found_ids = {d.id for d in detections}
        failed_ids = [str(d_id) for d_id in correction.detection_ids if d_id not in found_ids]
        corrected_count = 0

        # Apply corrections to all fetched detections
        for detection in detections:
            try:
                # Apply corrections
                detection.is_reviewed = True
                detection.reviewed_at = review_time
                detection.reviewed_by = correction.reviewed_by

                if correction.is_valid is not None:
                    detection.is_valid = correction.is_valid

                    # Clean up deer references if marking as invalid
                    if correction.is_valid is False:
                        cleanup_deer_reference(detection, db)

                if correction.corrected_classification:
                    detection.corrected_classification = correction.corrected_classification.lower()

                if correction.correction_notes:
                    detection.correction_notes = correction.correction_notes

                corrected_count += 1

            except Exception as e:
                failed_ids.append(str(detection.id))
                print(f"[WARN] Failed to correct detection {detection.id}: {e}")
                continue

        # Commit all changes
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save batch corrections: {str(e)}"
        )

    # Build response message
    changes = []
    if correction.is_valid is False:
        changes.append("marked as invalid")
    elif correction.is_valid is True:
        changes.append("marked as valid")
    if correction.corrected_classification:
        changes.append(f"classification corrected to {correction.corrected_classification}")
    if correction.correction_notes:
        changes.append("notes added")

    action_msg = f" and {', '.join(changes)}" if changes else ""
    message = f"Reviewed {corrected_count} detections{action_msg}"

    if failed_ids:
        message += f". {len(failed_ids)} detections could not be found."

    return BatchCorrectionResponse(
        success=True,
        total_requested=len(correction.detection_ids),
        total_corrected=corrected_count,
        failed_ids=failed_ids,
        message=message
    )


@router.patch("/{detection_id}/correct", response_model=DetectionCorrectionResponse)
def correct_detection(
    detection_id: UUID,
    correction: DetectionCorrectionRequest,
    db: Session = Depends(get_db),
) -> DetectionCorrectionResponse:
    """
    Review and correct a detection.

    Allows users to:
    - Mark detection as invalid (unusable image, wrong species, etc.)
    - Correct the ML-predicted classification
    - Add notes explaining the issue or correction

    Parameters:
        detection_id: UUID of the detection to correct
        correction: Correction data

    Returns:
        Updated detection information

    Raises:
        404: Detection not found
        400: Invalid correction data
    """
    # Find detection
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with ID {detection_id} not found"
        )

    # Apply corrections
    detection.is_reviewed = True
    detection.reviewed_at = datetime.utcnow()
    detection.reviewed_by = correction.reviewed_by

    if correction.is_valid is not None:
        detection.is_valid = correction.is_valid

        # Clean up deer references if marking as invalid
        if correction.is_valid is False:
            cleanup_deer_reference(detection, db)

    if correction.corrected_classification:
        detection.corrected_classification = correction.corrected_classification.lower()

    if correction.correction_notes:
        detection.correction_notes = correction.correction_notes

    # Commit changes
    try:
        db.commit()
        db.refresh(detection)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save correction: {str(e)}"
        )

    # Build response message
    changes = []
    if correction.is_valid is False:
        changes.append("marked as invalid")
    if correction.corrected_classification:
        changes.append(f"classification corrected to {correction.corrected_classification}")
    if correction.correction_notes:
        changes.append("notes added")

    message = f"Detection reviewed and {', '.join(changes)}" if changes else "Detection reviewed"

    return DetectionCorrectionResponse(
        success=True,
        detection_id=str(detection.id),
        message=message,
        detection=detection.to_dict()
    )


@router.get("/stats/reviewed", response_model=dict)
def get_review_stats(db: Session = Depends(get_db)) -> dict:
    """
    Get statistics about reviewed detections for progress tracking.

    Returns:
        Dictionary with review counts and progress metrics
    """
    # Count total reviewed detections
    reviewed_count = db.query(Detection).filter(Detection.is_reviewed == True).count()

    # Count by validity
    valid_count = db.query(Detection).filter(
        Detection.is_reviewed == True,
        Detection.is_valid == True
    ).count()

    invalid_count = db.query(Detection).filter(
        Detection.is_reviewed == True,
        Detection.is_valid == False
    ).count()

    # Calculate progress toward retraining goal (500 reviews)
    progress_percent = min((reviewed_count / 500) * 100, 100)

    return {
        "reviewed_count": reviewed_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "progress_percent": progress_percent,
        "retraining_ready": reviewed_count >= 500,
    }


@router.get("/{detection_id}", response_model=dict)
def get_detection(
    detection_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific detection.

    Parameters:
        detection_id: UUID of the detection

    Returns:
        Detection information with related image and deer data

    Raises:
        404: Detection not found
    """
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with ID {detection_id} not found"
        )

    return detection.to_dict_with_relations()
