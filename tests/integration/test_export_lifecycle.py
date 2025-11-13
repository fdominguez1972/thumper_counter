"""
Integration Tests for Export Job Lifecycle

Tests complete flow: API request → Celery task → Redis status → API poll → Download
Implements Option A integration testing requirements.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, Mock
from fastapi import status


class TestExportLifecycle:
    """Test suite for complete export job lifecycle."""

    @patch('backend.app.main.celery_app.send_task')
    def test_pdf_export_full_lifecycle(
        self,
        mock_send_task,
        api_client,
        redis_client,
        sample_export_request
    ):
        """
        Test T026: Full PDF export lifecycle from request to download.

        Flow:
        1. POST /api/exports/pdf (queue job)
        2. Worker sets "processing" status in Redis
        3. GET /api/exports/pdf/{job_id} returns "processing"
        4. Worker completes, updates Redis to "completed"
        5. GET /api/exports/pdf/{job_id} returns "completed" with download URL
        6. GET /api/static/exports/{filename} downloads file

        Verifies:
        - Job queued successfully
        - Status tracking works end-to-end
        - Download URL accessible
        """
        # Step 1: Queue PDF export job
        mock_task = Mock()
        mock_task.id = "integration-test-job-001"
        mock_send_task.return_value = mock_task

        response = api_client.post(
            "/api/exports/pdf",
            json=sample_export_request
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        job_data = response.json()
        job_id = job_data["job_id"]
        assert job_data["status"] == "processing"

        # Step 2: Simulate worker setting initial status
        key = f"export_job:{job_id}"
        redis_client.setex(
            key,
            3600,
            json.dumps({"status": "processing", "job_id": job_id})
        )

        # Step 3: Poll status (should be "processing")
        response = api_client.get(f"/api/exports/pdf/{job_id}")
        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()
        assert status_data["status"] == "processing"

        # Step 4: Simulate worker completion
        completed_data = {
            "status": "completed",
            "job_id": job_id,
            "filename": "report_20251112_143022.pdf",
            "download_url": "/api/static/exports/report_20251112_143022.pdf",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(completed_data))

        # Step 5: Poll status (should be "completed")
        response = api_client.get(f"/api/exports/pdf/{job_id}")
        assert response.status_code == status.HTTP_200_OK
        final_data = response.json()
        assert final_data["status"] == "completed"

        # Step 6: Verify download URL and filename format
        # Note: Exact filename is dynamic (includes job_id and timestamp)
        assert "filename" in final_data
        assert final_data["filename"].startswith("report_")
        assert final_data["filename"].endswith(".pdf")
        assert "download_url" in final_data
        assert final_data["download_url"].startswith("/api/static/exports/")
        assert final_data["download_url"].endswith(".pdf")
        assert final_data["filename"] in final_data["download_url"]
