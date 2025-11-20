"""
Seasonal analysis API router for rut season and wildlife activity queries.
Feature: 008-rut-season-analysis

Provides endpoints for filtering images and detections by predefined seasonal periods.
"""

from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, exists, select, func

from backend.core.database import get_db
from backend.models.image import Image, ProcessingStatus
from backend.models.detection import Detection
from backend.models.location import Location
from backend.models.seasonal import SeasonalFilter
from backend.schemas.seasonal import (
    SeasonalImagesResponse,
    SeasonalDetectionsResponse,
    ImageResponse,
    DetectionResponse,
    PageMetadata,
)


router = APIRouter(
    prefix="/api/seasonal",
    tags=["Seasonal Analysis"],
)


@router.get(
    "/images",
    response_model=SeasonalImagesResponse,
    summary="Filter images by season",
    description="Query trail camera images using predefined seasonal filters (rut season, spring, summer, fall)"
)
def get_seasonal_images(
    season: str = Query(
        ...,
        description="Seasonal filter: RUT_SEASON, SPRING, SUMMER, or FALL"
    ),
    year: int = Query(
        ...,
        ge=2020,
        le=2030,
        description="Target year for seasonal date range (e.g., 2024)"
    ),
    location_id: Optional[UUID] = Query(
        None,
        description="Filter by specific camera location"
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by processing status (pending, processing, completed, failed)"
    ),
    has_detections: Optional[bool] = Query(
        None,
        description="Filter by whether images have deer detections"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=1000,
        description="Number of images per page (max 1000)"
    ),
    db: Session = Depends(get_db)
) -> SeasonalImagesResponse:
    """
    Filter images by predefined seasonal periods.

    This endpoint uses the SeasonalFilter enum to automatically calculate date ranges
    for common wildlife activity periods like rut season (Sept 1 - Jan 31).

    **Example**: Get rut season images for 2024
    ```
    GET /api/seasonal/images?season=RUT_SEASON&year=2024&page=1&page_size=100
    ```

    Args:
        season: Seasonal filter name (RUT_SEASON, SPRING, SUMMER, FALL)
        year: Target year (e.g., 2024)
        location_id: Optional location UUID filter
        status_filter: Optional processing status filter
        has_detections: Optional detection presence filter
        page: Page number (1-indexed)
        page_size: Results per page
        db: Database session

    Returns:
        SeasonalImagesResponse: Paginated list of images with metadata

    Raises:
        HTTPException 400: Invalid season or year
        HTTPException 404: Location not found
    """
    # Validate seasonal filter
    try:
        seasonal_filter = SeasonalFilter[season.upper()]
    except KeyError:
        valid_seasons = [s.name for s in SeasonalFilter]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season: {season}. Valid values: {', '.join(valid_seasons)}"
        )

    # Get date range from seasonal filter
    start_date, end_date = SeasonalFilter.get_date_range(seasonal_filter, year)

    # Convert to datetime with timezone (beginning of start day, end of end day)
    date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Build base query with seasonal date range filter
    query = db.query(Image).filter(
        and_(
            Image.timestamp >= date_from,
            Image.timestamp <= date_to
        )
    )

    # Apply location filter
    if location_id:
        # Verify location exists
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_id}"
            )
        query = query.filter(Image.location_id == location_id)

    # Apply status filter
    if status_filter:
        try:
            status_enum = ProcessingStatus[status_filter.upper()]
            query = query.filter(Image.processing_status == status_enum)
        except KeyError:
            valid_statuses = [s.value for s in ProcessingStatus]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: {', '.join(valid_statuses)}"
            )

    # Apply detection presence filter
    if has_detections is not None:
        if has_detections:
            # Has at least one detection
            detection_exists = (
                select(1)
                .select_from(Detection)
                .where(Detection.image_id == Image.id)
            )
            query = query.filter(exists(detection_exists))
        else:
            # Has no detections
            query = query.outerjoin(Detection).filter(Detection.id.is_(None))

    # Get total count before pagination
    total_count = query.count()

    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_previous = page > 1

    # Calculate offset (convert 1-indexed page to 0-indexed skip)
    skip = (page - 1) * page_size

    # Execute query with pagination and ordering (most recent first)
    images = (
        query.order_by(Image.timestamp.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Count detections per image (for display)
    image_ids = [img.id for img in images]
    detection_counts = {}
    if image_ids:
        counts_query = (
            db.query(Detection.image_id, func.count(Detection.id))
            .filter(Detection.image_id.in_(image_ids))
            .group_by(Detection.image_id)
            .all()
        )
        detection_counts = {img_id: count for img_id, count in counts_query}

    # Build response with ImageResponse schema
    image_responses = []
    for img in images:
        # Get location name if location exists
        location_name = None
        if img.location_id:
            location = db.query(Location).filter(Location.id == img.location_id).first()
            if location:
                location_name = location.name

        image_responses.append(ImageResponse(
            id=img.id,
            filename=img.filename,
            path=img.path,
            timestamp=img.timestamp,
            location_id=img.location_id,
            location_name=location_name,
            processing_status=img.processing_status.value,
            detection_count=detection_counts.get(img.id, 0),
            created_at=img.created_at
        ))

    # Build pagination metadata
    page_metadata = PageMetadata(
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )

    return SeasonalImagesResponse(
        images=image_responses,
        total_count=total_count,
        page_metadata=page_metadata
    )


@router.get(
    "/detections",
    response_model=SeasonalDetectionsResponse,
    summary="Filter detections by season",
    description="Query deer detections using predefined seasonal filters with optional classification filtering"
)
def get_seasonal_detections(
    season: str = Query(
        ...,
        description="Seasonal filter: RUT_SEASON, SPRING, SUMMER, or FALL"
    ),
    year: int = Query(
        ...,
        ge=2020,
        le=2030,
        description="Target year for seasonal date range (e.g., 2024)"
    ),
    classification: Optional[str] = Query(
        None,
        description="Filter by classification: mature, mid, young (bucks), doe (female), fawn, unknown, cattle, pig"
    ),
    location_id: Optional[UUID] = Query(
        None,
        description="Filter by specific camera location"
    ),
    min_confidence: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0-1.0)"
    ),
    deer_id: Optional[UUID] = Query(
        None,
        description="Filter by specific re-identified deer profile"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)"
    ),
    page_size: int = Query(
        100,
        ge=1,
        le=1000,
        description="Number of detections per page (max 1000)"
    ),
    db: Session = Depends(get_db)
) -> SeasonalDetectionsResponse:
    """
    Filter deer detections by predefined seasonal periods.

    Useful for analyzing buck activity during rut season or comparing seasonal patterns.

    **Example**: Get mature buck detections during 2024 rut season
    ```
    GET /api/seasonal/detections?season=RUT_SEASON&year=2024&classification=mature&min_confidence=0.7
    ```

    Args:
        season: Seasonal filter name (RUT_SEASON, SPRING, SUMMER, FALL)
        year: Target year (e.g., 2024)
        classification: Optional classification filter
        location_id: Optional location UUID filter
        min_confidence: Optional minimum confidence threshold
        deer_id: Optional deer profile UUID filter
        page: Page number (1-indexed)
        page_size: Results per page
        db: Database session

    Returns:
        SeasonalDetectionsResponse: Paginated list of detections with metadata

    Raises:
        HTTPException 400: Invalid season or year
        HTTPException 404: Location or deer not found
    """
    # Validate seasonal filter
    try:
        seasonal_filter = SeasonalFilter[season.upper()]
    except KeyError:
        valid_seasons = [s.name for s in SeasonalFilter]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season: {season}. Valid values: {', '.join(valid_seasons)}"
        )

    # Get date range from seasonal filter
    start_date, end_date = SeasonalFilter.get_date_range(seasonal_filter, year)

    # Convert to datetime with timezone
    date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Build query with join to images table (for timestamp filtering)
    query = (
        db.query(Detection)
        .join(Image, Detection.image_id == Image.id)
        .filter(
            and_(
                Image.timestamp >= date_from,
                Image.timestamp <= date_to
            )
        )
    )

    # Apply classification filter
    if classification:
        # Use corrected_classification if available, otherwise use ML classification
        query = query.filter(
            func.coalesce(Detection.corrected_classification, Detection.classification) == classification.lower()
        )

    # Apply location filter
    if location_id:
        # Verify location exists
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_id}"
            )
        query = query.filter(Image.location_id == location_id)

    # Apply confidence filter
    if min_confidence is not None:
        query = query.filter(Detection.confidence >= min_confidence)

    # Apply deer_id filter
    if deer_id:
        # Verify deer exists
        from backend.models.deer import Deer
        deer = db.query(Deer).filter(Deer.id == deer_id).first()
        if not deer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deer profile not found: {deer_id}"
            )
        query = query.filter(Detection.deer_id == deer_id)

    # Get total count before pagination
    total_count = query.count()

    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1

    # Calculate offset
    skip = (page - 1) * page_size

    # Execute query with pagination (most confident first)
    detections = (
        query.order_by(Detection.confidence.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    # Get deer names for detections that have deer_id
    from backend.models.deer import Deer
    deer_ids = [det.deer_id for det in detections if det.deer_id]
    deer_names = {}
    if deer_ids:
        deer_query = db.query(Deer).filter(Deer.id.in_(deer_ids)).all()
        deer_names = {deer.id: deer.name for deer in deer_query}

    # Build response with DetectionResponse schema
    detection_responses = []
    for det in detections:
        # Use corrected_classification if available, otherwise use ML classification
        final_classification = det.corrected_classification if det.corrected_classification else det.classification

        detection_responses.append(DetectionResponse(
            id=det.id,
            image_id=det.image_id,
            bbox=det.bbox,  # JSON field: {x, y, width, height}
            confidence=det.confidence,
            classification=final_classification,
            deer_id=det.deer_id,
            deer_name=deer_names.get(det.deer_id) if det.deer_id else None,
            created_at=det.created_at
        ))

    # Build pagination metadata
    page_metadata = PageMetadata(
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )

    return SeasonalDetectionsResponse(
        detections=detection_responses,
        total_count=total_count,
        page_metadata=page_metadata
    )
