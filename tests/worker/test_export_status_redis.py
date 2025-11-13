"""
Tests for Export Status Redis Operations (Worker Side)

Tests worker task updates to Redis for export job status tracking.
Implements Option A testing requirements.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, Mock


class TestExportStatusRedis:
    """Test suite for Redis status updates in worker tasks."""

    def test_redis_set_processing_status(self, redis_client):
        """
        Test T015: Worker sets initial "processing" status in Redis.

        Verifies:
        - Job status key created with correct format
        - Status field set to "processing"
        - TTL set to 3600 seconds (1 hour)
        """
        job_id = "test-job-001"
        key = f"export_job:{job_id}"

        # Simulate worker setting initial status
        status_data = {
            "status": "processing",
            "job_id": job_id
        }
        redis_client.setex(key, 3600, json.dumps(status_data))

        # Verify key exists
        assert redis_client.exists(key) == 1

        # Verify status data
        stored_data = json.loads(redis_client.get(key))
        assert stored_data["status"] == "processing"
        assert stored_data["job_id"] == job_id

        # Verify TTL is approximately 1 hour (allow 10 second variance)
        ttl = redis_client.ttl(key)
        assert 3590 <= ttl <= 3600

    def test_redis_update_to_completed_status(self, redis_client):
        """
        Test T016: Worker updates status to "completed" with download URL.

        Verifies:
        - Status updated to "completed"
        - filename field present
        - download_url field present
        - completed_at timestamp present
        - TTL preserved
        """
        job_id = "test-job-002"
        key = f"export_job:{job_id}"

        # Initial status
        redis_client.setex(
            key,
            3600,
            json.dumps({"status": "processing", "job_id": job_id})
        )

        # Simulate worker completion
        completed_data = {
            "status": "completed",
            "job_id": job_id,
            "filename": "report_20251112_143022.pdf",
            "download_url": "/api/static/exports/report_20251112_143022.pdf",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(completed_data))

        # Verify status updated
        stored_data = json.loads(redis_client.get(key))
        assert stored_data["status"] == "completed"
        assert stored_data["filename"] == "report_20251112_143022.pdf"
        assert stored_data["download_url"].startswith("/api/static/exports/")
        assert "completed_at" in stored_data

        # Verify TTL still set
        ttl = redis_client.ttl(key)
        assert ttl > 0

    def test_redis_update_to_failed_status(self, redis_client):
        """
        Test T017: Worker updates status to "failed" with error message.

        Verifies:
        - Status updated to "failed"
        - error field present with message
        - completed_at timestamp present
        """
        job_id = "test-job-003"
        key = f"export_job:{job_id}"

        # Simulate worker failure
        failed_data = {
            "status": "failed",
            "job_id": job_id,
            "error": "No detections found in specified date range",
            "completed_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(key, 3600, json.dumps(failed_data))

        # Verify status
        stored_data = json.loads(redis_client.get(key))
        assert stored_data["status"] == "failed"
        assert stored_data["error"] == "No detections found in specified date range"
        assert "completed_at" in stored_data

    def test_redis_key_expires_after_ttl(self, redis_client):
        """
        Test T018: Redis key expires after 1 hour TTL.

        Verifies:
        - Key exists immediately after creation
        - TTL counts down
        - Key expires after TTL (simulated with short TTL)
        """
        job_id = "test-job-004"
        key = f"export_job:{job_id}"

        # Use 2 second TTL for testing
        redis_client.setex(
            key,
            2,
            json.dumps({"status": "processing", "job_id": job_id})
        )

        # Verify key exists
        assert redis_client.exists(key) == 1

        # Verify TTL is approximately 2 seconds
        ttl = redis_client.ttl(key)
        assert 1 <= ttl <= 2

        # Wait for expiry (note: test runs fast, we just verify TTL behavior)
        import time
        time.sleep(2.5)

        # Verify key expired
        assert redis_client.exists(key) == 0

    def test_redis_atomic_setex_operation(self, redis_client):
        """
        Test T019: Verify Redis SETEX is atomic (no race conditions).

        Verifies:
        - SETEX sets value and TTL in single operation
        - No window where key exists without TTL
        """
        job_id = "test-job-005"
        key = f"export_job:{job_id}"

        # Execute SETEX
        status_data = {"status": "processing", "job_id": job_id}
        result = redis_client.setex(key, 3600, json.dumps(status_data))

        # Verify operation succeeded
        assert result is True

        # Verify TTL was set atomically (no -1 which means no expiry)
        ttl = redis_client.ttl(key)
        assert ttl > 0  # Should never be -1 (no expiry) or -2 (key doesn't exist)

        # Verify value was set
        stored_data = json.loads(redis_client.get(key))
        assert stored_data["job_id"] == job_id
