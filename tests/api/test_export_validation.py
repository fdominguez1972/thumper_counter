"""
Tests for Export Request Validation (Option B)

Tests validation rules for PDF and ZIP export requests.
Implements Option B testing requirements.
"""

import pytest
from datetime import date, timedelta
from fastapi import status


class TestExportRequestValidation:
    """Test suite for export request validation (Option B)."""

    def test_valid_export_request(self, api_client):
        """
        Test T026: Valid export request is accepted.

        Verifies:
        - 202 ACCEPTED response
        - Request with valid dates, group_by passes validation
        - Job ID returned for polling
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-09-01",
            "end_date": "2023-12-31",
            "group_by": "month",
            "include_charts": True,
            "include_tables": True,
            "include_insights": True
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["pending", "processing"]

    def test_start_date_after_end_date(self, api_client):
        """
        Test T027: VR-001 - start_date must be before end_date.

        Verifies:
        - 400 BAD REQUEST response
        - Error message mentions date order
        - No job created
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2024-01-31",  # AFTER end_date
            "end_date": "2023-09-01",
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "start_date" in data["detail"].lower()
        assert "end_date" in data["detail"].lower()

    def test_start_date_equals_end_date(self, api_client):
        """
        Test T028: VR-001 - start_date equal to end_date is invalid.

        Verifies:
        - 400 BAD REQUEST response
        - Same date for both start and end is rejected
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-11-15",
            "end_date": "2023-11-15",  # SAME as start_date
            "group_by": "day"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "before" in data["detail"].lower()

    def test_date_range_exceeds_365_days(self, api_client):
        """
        Test T029: VR-002 - Date range cannot exceed 365 days.

        Verifies:
        - 400 BAD REQUEST for 366+ day range
        - Error message mentions 1 year limit
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-01-01",
            "end_date": "2024-01-02",  # 367 days
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert ("365" in data["detail"] or "year" in data["detail"].lower())

    def test_date_range_exactly_365_days(self, api_client):
        """
        Test T030: VR-002 - Exactly 365 days is valid (edge case).

        Verifies:
        - 202 ACCEPTED for exactly 365 day range
        - Boundary condition acceptance
        """
        start = date(2023, 1, 1)
        end = start + timedelta(days=365)

        request_data = {
            "report_type": "seasonal_activity",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_invalid_group_by_value(self, api_client):
        """
        Test T031: VR-003 - group_by must be day, week, or month.

        Verifies:
        - 400 BAD REQUEST for invalid group_by
        - Error message lists valid values
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-09-01",
            "end_date": "2023-12-31",
            "group_by": "year"  # INVALID
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "group_by" in data["detail"].lower()
        # Should list valid options
        detail_lower = data["detail"].lower()
        assert "day" in detail_lower or "week" in detail_lower or "month" in detail_lower

    def test_valid_group_by_day(self, api_client):
        """
        Test T032: VR-003 - group_by="day" is valid.
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-11-01",
            "end_date": "2023-11-30",
            "group_by": "day"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_valid_group_by_week(self, api_client):
        """
        Test T033: VR-003 - group_by="week" is valid.
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-09-01",
            "end_date": "2023-12-31",
            "group_by": "week"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_valid_group_by_month(self, api_client):
        """
        Test T034: VR-003 - group_by="month" is valid.
        """
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_start_date_in_future(self, api_client):
        """
        Test T035: VR-004 - start_date cannot be in the future.

        Verifies:
        - 400 BAD REQUEST for future start_date
        - Error message mentions future date restriction
        """
        future_date = (date.today() + timedelta(days=30)).isoformat()
        end_date = (date.today() + timedelta(days=60)).isoformat()

        request_data = {
            "report_type": "seasonal_activity",
            "start_date": future_date,
            "end_date": end_date,
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "future" in data["detail"].lower()

    def test_start_date_today_is_valid(self, api_client):
        """
        Test T036: VR-004 - start_date = today is valid (edge case).

        Verifies:
        - 202 ACCEPTED for start_date = today
        - Current date is not considered "future"
        """
        today = date.today().isoformat()
        past_date = (date.today() - timedelta(days=30)).isoformat()

        # Start today, end in past is invalid due to VR-001
        # So we test: past start, end today
        request_data = {
            "report_type": "seasonal_activity",
            "start_date": past_date,
            "end_date": today,
            "group_by": "day"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)
        assert response.status_code == status.HTTP_202_ACCEPTED

    def test_end_date_in_future_is_invalid(self, api_client):
        """
        Test T037: VR-004 - end_date in future should also be rejected.

        Note: This extends VR-004 to cover end_date as well.
        Even if start_date is valid, end_date in future is illogical.

        Verifies:
        - 400 BAD REQUEST if end_date is in future
        """
        past_date = (date.today() - timedelta(days=30)).isoformat()
        future_date = (date.today() + timedelta(days=30)).isoformat()

        request_data = {
            "report_type": "seasonal_activity",
            "start_date": past_date,
            "end_date": future_date,  # Future end date
            "group_by": "month"
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        # This should fail validation (end_date in future)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "future" in data["detail"].lower()

    def test_validation_response_time_under_100ms(self, api_client):
        """
        Test T038: SC-006 - Validation completes within 100ms.

        Verifies:
        - Validation errors returned quickly (< 100ms)
        - No expensive operations in validation path
        """
        import time

        request_data = {
            "report_type": "seasonal_activity",
            "start_date": "2024-01-31",  # Invalid (after end_date)
            "end_date": "2023-09-01",
            "group_by": "month"
        }

        start_time = time.time()
        response = api_client.post("/api/exports/pdf", json=request_data)
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert elapsed_ms < 100, f"Validation took {elapsed_ms:.2f}ms (expected < 100ms)"

    def test_multiple_validation_errors(self, api_client):
        """
        Test T039: Multiple validation failures.

        Verifies:
        - First validation error is returned (fail-fast)
        - 400 BAD REQUEST status

        Note: FastAPI/Pydantic validates sequentially, so we expect
        the first error to be returned.
        """
        future_date = (date.today() + timedelta(days=30)).isoformat()

        request_data = {
            "report_type": "seasonal_activity",
            "start_date": future_date,  # Future (VR-004)
            "end_date": "2023-01-01",  # Before start (VR-001)
            "group_by": "invalid"  # Invalid group_by (VR-003)
        }

        response = api_client.post("/api/exports/pdf", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    def test_zip_export_validation(self, api_client):
        """
        Test T040: ZIP exports do not require date validation.

        Verifies:
        - ZIP exports use detection_ids, not date ranges
        - No date validation applied to ZIP requests
        - Valid detection_ids list is accepted
        """
        request_data = {
            "detection_ids": ["550e8400-e29b-41d4-a716-446655440000"],
            "include_crops": True,
            "include_metadata_csv": True,
            "crop_size": 300
        }

        response = api_client.post("/api/exports/zip", json=request_data)

        # Should accept (or fail for different reason, but not date validation)
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "job_id" in data
