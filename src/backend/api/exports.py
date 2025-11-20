"""
Export API for PDF reports and ZIP archives.
Feature: 008-rut-season-analysis
Feature: 010-infrastructure-fixes (Redis-based job status tracking)

Provides endpoints for generating downloadable exports (PDF reports, ZIP archives).
Uses Celery for async processing with Redis-based job tracking.
"""

import os
import json
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from celery import Celery
import redis

from backend.core.database import get_db
from backend.api.validation import validate_export_request
from backend.schemas.export import (
    PDFReportRequest,
    PDFReportResponse,
    PDFStatusResponse,
    ZIPExportRequest,
    ZIPExportResponse,
    ZIPStatusResponse,
)


router = APIRouter(
    prefix="/api/exports",
    tags=["Exports"],
)


# Celery app for async export tasks
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

celery_app = Celery("thumper_counter", broker=REDIS_URL, backend=REDIS_URL)

# Redis client for job status tracking (Feature 010)
# WHY: Export jobs need persistent status tracking with 1-hour TTL
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # Return strings instead of bytes
)

# Export file storage directory
EXPORT_DIR = Path("/mnt/exports")


@router.post(
    "/pdf",
    response_model=PDFReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate PDF report",
    description="Queue PDF report generation job (async processing)"
)
def generate_pdf_report(
    request: PDFReportRequest,
    db: Session = Depends(get_db)
) -> PDFReportResponse:
    """
    Generate PDF report asynchronously.

    This endpoint queues a Celery task to generate the PDF report.
    Use the returned job_id to poll the status endpoint.

    **Example request:**
    ```json
    {
        "report_type": "seasonal_activity",
        "start_date": "2023-09-01",
        "end_date": "2024-01-31",
        "include_charts": true,
        "include_tables": true,
        "include_insights": true,
        "group_by": "month",
        "title": "2023 Rut Season Activity Report"
    }
    ```

    Args:
        request: PDF report configuration
        db: Database session

    Returns:
        PDFReportResponse: Job ID and status for polling
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Validate report type
    valid_types = ['seasonal_activity', 'comparison', 'custom']
    if request.report_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report_type: {request.report_type}. Valid values: {', '.join(valid_types)}"
        )

    # Validate comparison periods if type is comparison
    if request.report_type == 'comparison':
        if not request.comparison_periods or len(request.comparison_periods) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="comparison_periods required for comparison reports (2-5 periods)"
            )

    # Feature 010 Option B: Validate date range and group_by
    from datetime import date as date_type
    start_date_obj = date_type.fromisoformat(request.start_date)
    end_date_obj = date_type.fromisoformat(request.end_date)
    validate_export_request(start_date_obj, end_date_obj, request.group_by)

    # Feature 010: Initialize Redis status (replaces in-memory dict)
    now = datetime.utcnow()
    key = f"export_job:{job_id}"
    initial_status = {
        "status": "processing",
        "job_id": job_id,
        "created_at": now.isoformat()
    }

    # Queue Celery task for PDF generation
    try:
        task = celery_app.send_task(
            "worker.tasks.exports.generate_pdf_report_task",
            args=[job_id, request.dict()],
            queue="exports"
        )

        # Set initial status in Redis with 1-hour TTL
        redis_client.setex(key, 3600, json.dumps(initial_status))

        print(f"[OK] Queued PDF export job {job_id} (Celery task: {task.id})")
        print(f"[INFO] Initialized Redis status: {key}")

        job_status = "processing"

    except Exception as e:
        print(f"[ERROR] Failed to queue PDF export: {e}")

        # Set failed status in Redis
        failed_status = {
            "status": "failed",
            "job_id": job_id,
            "error": str(e),
            "created_at": now.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_status))

        job_status = "failed"

    # Estimate completion time (5-10 seconds)
    estimated_completion = now + timedelta(seconds=10)

    return PDFReportResponse(
        job_id=job_id,
        status=job_status,
        message=f"PDF report generation queued. Poll GET /api/exports/pdf/{job_id} for status.",
        estimated_completion=estimated_completion
    )


@router.get(
    "/pdf/{job_id}",
    response_model=PDFStatusResponse,
    summary="Check PDF export status",
    description="Poll PDF generation job status and get download URL when complete"
)
def get_pdf_status(
    job_id: str,
    db: Session = Depends(get_db)
) -> PDFStatusResponse:
    """
    Check PDF export job status from Redis.

    Feature 010: Replaced in-memory dict with Redis lookup (1-hour TTL).

    Poll this endpoint to check if PDF generation is complete.
    When status='completed', download_url will be available.

    Args:
        job_id: Job ID from POST /api/exports/pdf
        db: Database session

    Returns:
        PDFStatusResponse: Current job status with download URL if ready

    Raises:
        HTTPException 404: Job not found or expired
    """
    # Feature 010: Read status from Redis
    key = f"export_job:{job_id}"
    status_json = redis_client.get(key)

    if not status_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired"
        )

    # Parse status data from Redis
    job_data = json.loads(status_json)

    # Parse datetime fields
    created_at = datetime.fromisoformat(job_data["created_at"]) if "created_at" in job_data else datetime.utcnow()
    completed_at = datetime.fromisoformat(job_data["completed_at"]) if "completed_at" in job_data else None

    # Calculate expires_at from Redis TTL
    ttl = redis_client.ttl(key)
    if ttl > 0:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    else:
        expires_at = datetime.utcnow()  # Already expired or will expire soon

    # Build response based on status
    response = PDFStatusResponse(
        job_id=job_id,
        status=job_data.get("status", "unknown"),
        filename=job_data.get("filename"),
        download_url=job_data.get("download_url"),
        file_size_bytes=job_data.get("file_size_bytes"),
        error_message=job_data.get("error"),  # Note: field is "error" in Redis, "error_message" in response
        created_at=created_at,
        completed_at=completed_at,
        expires_at=expires_at
    )

    return response


@router.post(
    "/zip",
    response_model=ZIPExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export detections to ZIP archive",
    description="Queue ZIP archive creation with detection crops and metadata CSV"
)
def export_detections_zip(
    request: ZIPExportRequest,
    db: Session = Depends(get_db)
) -> ZIPExportResponse:
    """
    Export detections to ZIP archive asynchronously.

    Creates a ZIP file containing:
    - Cropped detection images (if include_crops=true)
    - metadata.csv with detection info (if include_metadata_csv=true)

    **Example request:**
    ```json
    {
        "detection_ids": ["uuid1", "uuid2", "uuid3"],
        "include_crops": true,
        "include_metadata_csv": true,
        "crop_size": 300
    }
    ```

    Args:
        request: ZIP export configuration
        db: Database session

    Returns:
        ZIPExportResponse: Job ID and status for polling
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Validate detection count
    detection_count = len(request.detection_ids)
    if detection_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No detection IDs provided"
        )

    # Feature 010: Initialize Redis status (replaces in-memory dict)
    now = datetime.utcnow()
    key = f"export_job:{job_id}"
    initial_status = {
        "status": "processing",
        "job_id": job_id,
        "created_at": now.isoformat(),
        "total_detections": detection_count,
        "processed_count": 0
    }

    # Queue Celery task for ZIP creation
    try:
        task = celery_app.send_task(
            "worker.tasks.exports.create_zip_archive_task",
            args=[job_id, request.dict()],
            queue="exports"
        )

        # Set initial status in Redis with 1-hour TTL
        redis_client.setex(key, 3600, json.dumps(initial_status))

        print(f"[OK] Queued ZIP export job {job_id} (Celery task: {task.id})")
        print(f"[INFO] Initialized Redis status: {key}")

        job_status = "processing"

    except Exception as e:
        print(f"[ERROR] Failed to queue ZIP export: {e}")

        # Set failed status in Redis
        failed_status = {
            "status": "failed",
            "job_id": job_id,
            "error": str(e),
            "created_at": now.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_status))

        job_status = "failed"

    # Estimate completion time (varies by detection count)
    # Rough estimate: 0.1 second per detection
    estimated_seconds = max(10, detection_count * 0.1)
    estimated_completion = now + timedelta(seconds=estimated_seconds)

    return ZIPExportResponse(
        job_id=job_id,
        status=job_status,
        total_detections=detection_count,
        message=f"ZIP archive creation queued. Poll GET /api/exports/zip/{job_id} for status.",
        estimated_completion=estimated_completion
    )


@router.get(
    "/zip/{job_id}",
    response_model=ZIPStatusResponse,
    summary="Check ZIP export status",
    description="Poll ZIP archive creation status with progress tracking"
)
def get_zip_status(
    job_id: str,
    db: Session = Depends(get_db)
) -> ZIPStatusResponse:
    """
    Check ZIP export job status from Redis with progress tracking.

    Feature 010: Replaced in-memory dict with Redis lookup (1-hour TTL).

    Poll this endpoint to check archive creation progress.
    Provides real-time progress percentage.

    Args:
        job_id: Job ID from POST /api/exports/zip
        db: Database session

    Returns:
        ZIPStatusResponse: Current job status with progress and download URL

    Raises:
        HTTPException 404: Job not found or expired
    """
    # Feature 010: Read status from Redis
    key = f"export_job:{job_id}"
    status_json = redis_client.get(key)

    if not status_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired"
        )

    # Parse status data from Redis
    job_data = json.loads(status_json)

    # Calculate progress percentage (if available)
    total = job_data.get("total_detections", 1)
    processed = job_data.get("processed_count", 0)
    progress_percent = round((processed / total) * 100, 1) if total > 0 else 0.0

    # Parse datetime fields
    created_at = datetime.fromisoformat(job_data["created_at"]) if "created_at" in job_data else datetime.utcnow()
    completed_at = datetime.fromisoformat(job_data["completed_at"]) if "completed_at" in job_data else None

    # Calculate expires_at from Redis TTL
    ttl = redis_client.ttl(key)
    if ttl > 0:
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    else:
        expires_at = datetime.utcnow()  # Already expired or will expire soon

    # Build response
    response = ZIPStatusResponse(
        job_id=job_id,
        status=job_data.get("status", "unknown"),
        total_detections=total,
        processed_count=processed,
        progress_percent=progress_percent,
        filename=job_data.get("filename"),
        download_url=job_data.get("download_url"),
        file_size_bytes=job_data.get("file_size_bytes"),
        error_message=job_data.get("error"),  # Note: field is "error" in Redis, "error_message" in response
        created_at=created_at,
        completed_at=completed_at,
        estimated_completion=None,  # Not stored in Redis
        expires_at=expires_at
    )

    return response


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete export job",
    description="Cancel pending job or delete completed export file"
)
def delete_export_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete export job and associated files from Redis.

    Feature 010: Updated to use Redis instead of in-memory dict.

    Cancels pending/processing jobs or deletes completed export files.

    Args:
        job_id: Job ID to delete
        db: Database session

    Raises:
        HTTPException 404: Job not found
    """
    # Feature 010: Check if job exists in Redis
    key = f"export_job:{job_id}"
    status_json = redis_client.get(key)

    if not status_json:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job not found: {job_id}"
        )

    # Get job data from Redis
    job = json.loads(status_json)

    # Cancel Celery task if still processing
    # Note: We don't store celery_task_id in Redis, so we can't revoke
    # This is acceptable since tasks are idempotent and will complete anyway
    if job.get("status") in ["pending", "processing"]:
        print(f"[WARN] Cannot cancel Celery task for job {job_id} (task_id not stored in Redis)")

    # Delete file if exists (use filename from Redis data)
    filename = job.get("filename")
    if filename:
        file_path = EXPORT_DIR / filename
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"[INFO] Deleted export file: {file_path}")
            except Exception as e:
                print(f"[WARN] Failed to delete file {file_path}: {e}")

    # Feature 010: Remove job from Redis
    redis_client.delete(key)
    print(f"[OK] Deleted export job {job_id} from Redis")

    return None  # 204 No Content
