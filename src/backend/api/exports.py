"""
Export API for PDF reports and ZIP archives.
Feature: 008-rut-season-analysis

Provides endpoints for generating downloadable exports (PDF reports, ZIP archives).
Uses Celery for async processing with job tracking.
"""

import os
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from celery import Celery

from backend.core.database import get_db
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


# In-memory job tracking (in production, use Redis or database)
export_jobs = {}


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

    # Create job record
    now = datetime.utcnow()
    export_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "job_type": "pdf",
        "created_at": now,
        "expires_at": now + timedelta(hours=24),
        "request": request.dict(),
    }

    # Queue Celery task for PDF generation
    try:
        task = celery_app.send_task(
            "worker.tasks.exports.generate_pdf_report_task",
            args=[job_id, request.dict()],
            queue="exports"
        )

        export_jobs[job_id]["celery_task_id"] = task.id
        export_jobs[job_id]["status"] = "processing"

        print(f"[OK] Queued PDF export job {job_id} (Celery task: {task.id})")

    except Exception as e:
        print(f"[ERROR] Failed to queue PDF export: {e}")
        export_jobs[job_id]["status"] = "failed"
        export_jobs[job_id]["error_message"] = str(e)

    # Estimate completion time (5-10 seconds)
    estimated_completion = now + timedelta(seconds=10)

    return PDFReportResponse(
        job_id=job_id,
        status=export_jobs[job_id]["status"],
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
    Check PDF export job status.

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
    # Check if job exists
    if job_id not in export_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job not found: {job_id}"
        )

    job = export_jobs[job_id]

    # Check if expired
    if datetime.utcnow() > job["expires_at"]:
        job["status"] = "expired"

    # Build response
    response = PDFStatusResponse(
        job_id=job_id,
        status=job["status"],
        download_url=job.get("download_url"),
        file_size_bytes=job.get("file_size_bytes"),
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        expires_at=job["expires_at"]
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

    # Create job record
    now = datetime.utcnow()
    export_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "job_type": "zip",
        "created_at": now,
        "expires_at": now + timedelta(days=7),  # ZIP archives expire after 7 days
        "total_detections": detection_count,
        "processed_count": 0,
        "request": request.dict(),
    }

    # Queue Celery task for ZIP creation
    try:
        task = celery_app.send_task(
            "worker.tasks.exports.create_zip_archive_task",
            args=[job_id, request.dict()],
            queue="exports"
        )

        export_jobs[job_id]["celery_task_id"] = task.id
        export_jobs[job_id]["status"] = "processing"

        print(f"[OK] Queued ZIP export job {job_id} (Celery task: {task.id})")

    except Exception as e:
        print(f"[ERROR] Failed to queue ZIP export: {e}")
        export_jobs[job_id]["status"] = "failed"
        export_jobs[job_id]["error_message"] = str(e)

    # Estimate completion time (varies by detection count)
    # Rough estimate: 0.1 second per detection
    estimated_seconds = max(10, detection_count * 0.1)
    estimated_completion = now + timedelta(seconds=estimated_seconds)

    return ZIPExportResponse(
        job_id=job_id,
        status=export_jobs[job_id]["status"],
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
    Check ZIP export job status with progress tracking.

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
    # Check if job exists
    if job_id not in export_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job not found: {job_id}"
        )

    job = export_jobs[job_id]

    # Check if expired
    if datetime.utcnow() > job["expires_at"]:
        job["status"] = "expired"

    # Calculate progress percentage
    total = job.get("total_detections", 1)
    processed = job.get("processed_count", 0)
    progress_percent = round((processed / total) * 100, 1) if total > 0 else 0.0

    # Build response
    response = ZIPStatusResponse(
        job_id=job_id,
        status=job["status"],
        total_detections=total,
        processed_count=processed,
        progress_percent=progress_percent,
        download_url=job.get("download_url"),
        file_size_bytes=job.get("file_size_bytes"),
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        estimated_completion=job.get("estimated_completion"),
        expires_at=job["expires_at"]
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
    Delete export job and associated files.

    Cancels pending/processing jobs or deletes completed export files.

    Args:
        job_id: Job ID to delete
        db: Database session

    Raises:
        HTTPException 404: Job not found
    """
    # Check if job exists
    if job_id not in export_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job not found: {job_id}"
        )

    job = export_jobs[job_id]

    # Cancel Celery task if still processing
    if job["status"] in ["pending", "processing"]:
        celery_task_id = job.get("celery_task_id")
        if celery_task_id:
            celery_app.control.revoke(celery_task_id, terminate=True)
            print(f"[INFO] Cancelled Celery task {celery_task_id}")

    # Delete file if exists
    file_path = job.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Deleted export file: {file_path}")
        except Exception as e:
            print(f"[WARN] Failed to delete file {file_path}: {e}")

    # Remove job from tracking
    del export_jobs[job_id]
    print(f"[OK] Deleted export job {job_id}")

    return None  # 204 No Content
