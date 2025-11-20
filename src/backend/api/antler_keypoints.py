"""
API endpoints for antler keypoint detection and retrieval.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models import Detection, AntlerKeypoint
from backend.schemas.antler_keypoint import (
    AntlerKeypointResponse,
    AntlerKeypointsResponse,
    BatchAntlerDetectionRequest,
    BatchAntlerDetectionResponse,
    AntlerDetectionTaskResponse,
)
# Import Celery app to send tasks
# WHY: Backend cannot import worker modules directly (missing dependencies like cv2)
from backend.core.celery import celery_app


router = APIRouter()


@router.get("/detections/{detection_id}/antler_keypoints", response_model=AntlerKeypointsResponse)
async def get_detection_antler_keypoints(
    detection_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all antler keypoints for a specific detection.

    Args:
        detection_id: UUID of the detection

    Returns:
        AntlerKeypointsResponse: Keypoints data with statistics
    """
    # Verify detection exists
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    # Get keypoints
    keypoints = db.query(AntlerKeypoint).filter(
        AntlerKeypoint.detection_id == detection_id
    ).order_by(AntlerKeypoint.keypoint_index).all()

    # Calculate statistics
    visible_count = sum(1 for kpt in keypoints if kpt.visibility == 2)
    left_count = sum(1 for kpt in keypoints if kpt.is_left_antler)
    right_count = sum(1 for kpt in keypoints if kpt.is_right_antler)

    return AntlerKeypointsResponse(
        detection_id=detection_id,
        keypoints=[AntlerKeypointResponse.from_orm(kpt) for kpt in keypoints],
        total_keypoints=len(keypoints),
        visible_keypoints=visible_count,
        left_antler_keypoints=left_count,
        right_antler_keypoints=right_count,
    )


@router.get("/antler_keypoints", response_model=List[AntlerKeypointResponse])
async def get_antler_keypoints(
    detection_id: Optional[UUID] = Query(None, description="Filter by detection ID"),
    keypoint_name: Optional[str] = Query(None, description="Filter by keypoint name"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    visible_only: bool = Query(False, description="Only return visible keypoints"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get antler keypoints with optional filtering.

    Args:
        detection_id: Optional filter by detection
        keypoint_name: Optional filter by keypoint name
        min_confidence: Optional minimum confidence threshold
        visible_only: Only return visible keypoints (visibility=2)
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List[AntlerKeypointResponse]: List of keypoints
    """
    query = db.query(AntlerKeypoint)

    # Apply filters
    if detection_id:
        query = query.filter(AntlerKeypoint.detection_id == detection_id)

    if keypoint_name:
        query = query.filter(AntlerKeypoint.keypoint_name == keypoint_name)

    if min_confidence is not None:
        query = query.filter(AntlerKeypoint.confidence >= min_confidence)

    if visible_only:
        query = query.filter(AntlerKeypoint.visibility == 2)

    # Apply pagination
    query = query.order_by(AntlerKeypoint.created_at.desc())
    keypoints = query.offset(offset).limit(limit).all()

    return [AntlerKeypointResponse.from_orm(kpt) for kpt in keypoints]


@router.post("/detections/{detection_id}/detect_antlers", response_model=dict)
async def trigger_antler_detection(
    detection_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Trigger antler keypoint detection for a specific detection.

    Args:
        detection_id: UUID of the detection to process

    Returns:
        dict: Task information
    """
    # Verify detection exists
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    # Check if it's a buck
    classification = detection.corrected_classification or detection.classification
    if classification.lower() != "buck":
        raise HTTPException(
            status_code=400,
            detail=f"Antler detection only works on bucks (this is a {classification})"
        )

    # Queue task using send_task (avoids direct import of worker)
    task = celery_app.send_task(
        'worker.tasks.antler_detection.detect_antler_keypoints',
        args=[str(detection_id)],
        queue='ml_processing'
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "detection_id": str(detection_id),
        "message": "Antler detection task queued"
    }


@router.post("/antler_keypoints/batch_detect", response_model=BatchAntlerDetectionResponse)
async def batch_detect_antlers(
    request: BatchAntlerDetectionRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger batch antler keypoint detection for multiple bucks.

    Args:
        request: Batch detection request with optional detection IDs and limit

    Returns:
        BatchAntlerDetectionResponse: Batch task information
    """
    # Convert UUIDs to strings if provided
    detection_ids = [str(did) for did in request.detection_ids] if request.detection_ids else None

    # Queue batch task using send_task (async - returns immediately)
    task = celery_app.send_task(
        'worker.tasks.antler_detection.batch_detect_antler_keypoints',
        kwargs={
            'detection_ids': detection_ids,
            'limit': request.limit
        },
        queue='ml_processing'
    )

    # Return immediately without waiting for task completion
    # The batch task will queue individual detection tasks in the background
    return BatchAntlerDetectionResponse(
        status="queued",
        detections_queued=request.limit,
        task_ids=[task.id]
    )


@router.get("/antler_keypoints/stats", response_model=dict)
async def get_antler_keypoints_stats(
    db: Session = Depends(get_db)
):
    """
    Get statistics about antler keypoint detections.

    Returns:
        dict: Statistics including total detections, keypoints, etc.
    """
    # Count total keypoints
    total_keypoints = db.query(AntlerKeypoint).count()

    # Count unique detections with antler data
    detections_with_antlers = db.query(AntlerKeypoint.detection_id).distinct().count()

    # Count visible keypoints
    visible_keypoints = db.query(AntlerKeypoint).filter(
        AntlerKeypoint.visibility == 2
    ).count()

    # Count by side
    left_keypoints = db.query(AntlerKeypoint).filter(
        AntlerKeypoint.keypoint_name.like('left_%')
    ).count()

    right_keypoints = db.query(AntlerKeypoint).filter(
        AntlerKeypoint.keypoint_name.like('right_%')
    ).count()

    # Average keypoints per detection
    avg_per_detection = total_keypoints / detections_with_antlers if detections_with_antlers > 0 else 0

    return {
        "total_keypoints": total_keypoints,
        "detections_with_antlers": detections_with_antlers,
        "visible_keypoints": visible_keypoints,
        "left_keypoints": left_keypoints,
        "right_keypoints": right_keypoints,
        "average_keypoints_per_detection": round(avg_per_detection, 2),
    }


@router.delete("/detections/{detection_id}/antler_keypoints", response_model=dict)
async def delete_detection_antler_keypoints(
    detection_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete all antler keypoints for a specific detection.

    Useful for reprocessing or correction.

    Args:
        detection_id: UUID of the detection

    Returns:
        dict: Deletion confirmation
    """
    # Delete keypoints
    deleted_count = db.query(AntlerKeypoint).filter(
        AntlerKeypoint.detection_id == detection_id
    ).delete()

    db.commit()

    return {
        "status": "success",
        "detection_id": str(detection_id),
        "deleted_keypoints": deleted_count
    }


__all__ = ["router"]
