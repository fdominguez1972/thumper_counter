"""
Tests for Export Status API Endpoints

Tests API endpoints for polling export job status from Redis.
Implements Option A API testing requirements.
"""

import json
import pytest
from datetime import datetime
from fastapi import status


class TestExportStatusAPI:
    """Test suite for export status API endpoints."""

    def test_get_pdf_status_processing(self, api_client, redis_client):
        """
        Test T020: GET /api/exports/pdf/{job_id} returns "processing" status.

        Verifies:
        - 200 OK response
        - status field is "processing"
        - job_id field present
        """
        job_id = "test-pdf-001"
        key = f"export_job:{job_id}"

        # Setup: Create processing status in Redis
        redis_client.setex(
            key,
            3600,
            json.dumps({"status": "processing", "job_id": job_id})
        )

        # Make API request
        response = api_client.get(f"/api/exports/pdf/{job_id}")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "processing"
        assert data["job_id"] == job_id

    def test_get_pdf_status_completed(self, api_client, redis_client):
        """
        Test T021: GET /api/exports/pdf/{job_id} returns "completed" with download URL.

        Verifies:
        - 200 OK response
        - status field is "completed"
        - filename field present
        - download_url field present
        - completed_at timestamp present
        """
        job_id = "test-pdf-002"
        key = f"export_job:{job_id}"

        # Setup: Create completed status in Redis
        completed_data = {
            "status": "completed",
            "job_id": job_id,
            "filename": "report_20251112_143022.pdf",
            "download_url": "/api/static/exports/report_20251112_143022.pdf",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(completed_data))

        # Make API request
        response = api_client.get(f"/api/exports/pdf/{job_id}")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["filename"] == "report_20251112_143022.pdf"
        assert data["download_url"].startswith("/api/static/exports/")
        assert "completed_at" in data

    def test_get_pdf_status_failed(self, api_client, redis_client):
        """
        Test T022: GET /api/exports/pdf/{job_id} returns "failed" with error.

        Verifies:
        - 200 OK response
        - status field is "failed"
        - error field present with message
        """
        job_id = "test-pdf-003"
        key = f"export_job:{job_id}"

        # Setup: Create failed status in Redis
        failed_data = {
            "status": "failed",
            "job_id": job_id,
            "error": "No detections found in specified date range",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_data))

        # Make API request
        response = api_client.get(f"/api/exports/pdf/{job_id}")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "No detections found in specified date range"

    def test_get_pdf_status_not_found(self, api_client, redis_client):
        """
        Test T023: GET /api/exports/pdf/{job_id} returns 404 for non-existent job.

        Verifies:
        - 404 NOT FOUND response
        - Error message present (either 'detail' field or FastAPI custom 404 format)
        """
        job_id = "non-existent-job"

        # Make API request (no Redis data)
        response = api_client.get(f"/api/exports/pdf/{job_id}")

        # Verify response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()

        # Accept either format: {"detail": "..."} or {"error": "...", "message": "..."}
        error_message = data.get("detail", "") or data.get("message", "") or data.get("error", "")
        assert len(error_message) > 0, "Response should contain an error message"
        # Don't check content since the custom 404 handler has different message format

    def test_get_zip_status_completed(self, api_client, redis_client):
        """
        Test T024: GET /api/exports/zip/{job_id} returns completed ZIP status.

        Verifies:
        - 200 OK response
        - filename is .zip file
        - download_url points to ZIP
        """
        job_id = "test-zip-001"
        key = f"export_job:{job_id}"

        # Setup: Create completed ZIP status
        completed_data = {
            "status": "completed",
            "job_id": job_id,
            "filename": "detections_20251112_143530.zip",
            "download_url": "/api/static/exports/detections_20251112_143530.zip",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(completed_data))

        # Make API request
        response = api_client.get(f"/api/exports/zip/{job_id}")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["filename"].endswith(".zip")
        assert ".zip" in data["download_url"]

    def test_status_endpoint_performance(self, api_client, redis_client):
        """
        Test T025: Verify status polling completes in < 100ms.

        Verifies:
        - API response time is fast (Redis lookup is O(1))
        """
        import time

        job_id = "test-perf-001"
        key = f"export_job:{job_id}"

        # Setup: Create status in Redis
        redis_client.setex(
            key,
            3600,
            json.dumps({"status": "processing", "job_id": job_id})
        )

        # Measure response time
        start_time = time.time()
        response = api_client.get(f"/api/exports/pdf/{job_id}")
        elapsed_ms = (time.time() - start_time) * 1000

        # Verify performance
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_ms < 100, f"Status polling took {elapsed_ms:.2f}ms (expected < 100ms)"
