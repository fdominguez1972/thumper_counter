"""
Export Request Validation Helper

Provides validation functions for PDF and ZIP export requests.
Implements VR-001 through VR-004 validation rules.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status


# Validation constants
MAX_DATE_RANGE_DAYS = 365
VALID_GROUP_BY_VALUES = {'day', 'week', 'month'}


def validate_export_request(
    start_date: date,
    end_date: date,
    group_by: str
) -> None:
    """
    Validate export request parameters before queueing worker task.

    Implements validation rules:
    - VR-001: start_date must be before end_date
    - VR-002: Date range cannot exceed 365 days
    - VR-003: group_by must be "day", "week", or "month"
    - VR-004: start_date cannot be in the future

    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        group_by: Aggregation granularity

    Raises:
        HTTPException: 400 status with validation error detail
    """
    # VR-001: Date order validation
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )

    # VR-002: Date range limit validation
    date_range = (end_date - start_date).days
    if date_range > MAX_DATE_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 1 year"
        )

    # VR-003: Group by value validation
    if group_by not in VALID_GROUP_BY_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"group_by must be one of: {', '.join(sorted(VALID_GROUP_BY_VALUES))}"
        )

    # VR-004: Future date validation
    today = date.today()
    if start_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be in the future"
        )

    # VR-005: End date future validation (extension of VR-004)
    if end_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date cannot be in the future"
        )
