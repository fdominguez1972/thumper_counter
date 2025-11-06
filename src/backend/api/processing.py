"""
Processing API Endpoints
Version: 1.0.0
Date: 2025-11-06 (Sprint 3)

Batch processing and status monitoring endpoints for ML pipeline.

Endpoints:
    POST /api/processing/batch - Queue batch of images for processing
    GET /api/processing/status - Get processing statistics

WHY batch processing: Efficiently process large image datasets (35k+ images)
with GPU acceleration. Batch endpoint queries pending images and queues them
to Celery for asynchronous detection.

WHY status endpoint: Real-time monitoring of processing progress for UI and
debugging. Returns counts by processing status.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.models.image import Image, ProcessingStatus


router = APIRouter(
    prefix="/api/processing",
    tags=["processing"],
)


@router.post("/batch")
async def queue_batch_processing(
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    status: ProcessingStatus = Query(
        ProcessingStatus.PENDING,
        description="Filter by processing status (default: pending)"
    ),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum images to queue"),
    db: Session = Depends(get_db),
):
    """
    Queue a batch of images for processing.

    This endpoint queries images by status (typically 'pending') and optionally
    filters by location, then queues them to Celery for detection processing.

    Parameters:
        location_id: Optional UUID to filter images by location
        status: Processing status to filter (default: pending)
        limit: Maximum number of images to queue (1-10000)

    Returns:
        {
            "queued_count": int,
            "task_ids": List[str],
            "location_id": Optional[str],
            "status_filter": str
        }

    Requirements:
        - FR-020: Batch processing endpoint for large datasets
        - FR-021: Location filtering for targeted processing

    Performance:
        - With GPU: ~1200 images/minute (0.05s per image)
        - With CPU: ~150 images/minute (0.4s per image)

    Example:
        POST /api/processing/batch?limit=1000&location_id=<uuid>
        Returns task IDs for monitoring via Flower UI
    """
    # Build query for images to process
    query = db.query(Image).filter(Image.processing_status == status)

    # Apply location filter if provided
    if location_id:
        query = query.filter(Image.location_id == location_id)

    # Get images to process (ordered by timestamp for FIFO processing)
    images = query.order_by(Image.timestamp).limit(limit).all()

    if not images:
        return {
            "queued_count": 0,
            "task_ids": [],
            "location_id": str(location_id) if location_id else None,
            "status_filter": status.value,
            "message": "No images found matching criteria"
        }

    # Queue images for detection processing
    # WHY send_task: Backend cannot import worker modules directly
    task_ids = []
    from backend.app.main import celery_app

    for image in images:
        # Queue detection task for each image
        task = celery_app.send_task(
            'worker.tasks.detection.detect_deer_task',
            args=[str(image.id)],
            queue='ml_processing'
        )
        task_ids.append(task.id)

    return {
        "queued_count": len(task_ids),
        "task_ids": task_ids,
        "location_id": str(location_id) if location_id else None,
        "status_filter": status.value,
        "message": f"Successfully queued {len(task_ids)} images for processing"
    }


@router.get("/status")
async def get_processing_status(
    location_id: Optional[UUID] = Query(None, description="Filter by location ID"),
    db: Session = Depends(get_db),
):
    """
    Get processing statistics and status counts.

    Returns counts of images grouped by processing status, optionally filtered
    by location. Useful for monitoring progress and debugging.

    Parameters:
        location_id: Optional UUID to filter statistics by location

    Returns:
        {
            "total": int,
            "pending": int,
            "processing": int,
            "completed": int,
            "failed": int,
            "location_id": Optional[str],
            "completion_rate": float  # percentage of completed images
        }

    Requirements:
        - FR-022: Real-time processing status monitoring
        - FR-023: Per-location statistics

    Example:
        GET /api/processing/status
        Returns counts for all images across all locations

        GET /api/processing/status?location_id=<uuid>
        Returns counts for specific location only
    """
    # Build base query
    query = db.query(
        Image.processing_status,
        func.count(Image.id).label('count')
    )

    # Apply location filter if provided
    if location_id:
        query = query.filter(Image.location_id == location_id)

    # Group by status and get counts
    status_counts = query.group_by(Image.processing_status).all()

    # Convert to dictionary
    stats = {
        "total": 0,
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "location_id": str(location_id) if location_id else None,
    }

    for status, count in status_counts:
        stats[status.value] = count
        stats["total"] += count

    # Calculate completion rate
    if stats["total"] > 0:
        stats["completion_rate"] = round(
            (stats["completed"] / stats["total"]) * 100, 2
        )
    else:
        stats["completion_rate"] = 0.0

    return stats
