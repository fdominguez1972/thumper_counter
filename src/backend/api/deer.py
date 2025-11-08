"""
Deer Management API Endpoints
Version: 1.0.0
Date: 2025-11-06 (Sprint 3)

CRUD operations for deer profiles and sightings management.

Endpoints:
    POST /api/deer - Create new deer profile
    GET /api/deer - List all deer with filtering
    GET /api/deer/{id} - Get specific deer profile with sightings
    PUT /api/deer/{id} - Update deer profile
    DELETE /api/deer/{id} - Delete deer profile

WHY deer profiles: Track individual deer across multiple sightings for
population monitoring, behavior analysis, and re-identification validation.

Each deer profile contains:
- Basic info: name, sex, species, status (alive/deceased)
- Physical features: size, distinguishing marks
- Sighting history: first_seen, last_seen, sighting_count
- Linked detections for re-ID training
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.core.database import get_db
from backend.models.deer import Deer, DeerStatus, DeerSex as Sex
from backend.models.detection import Detection
from backend.models.image import Image
from backend.schemas.deer import (
    DeerCreate,
    DeerUpdate,
    DeerResponse,
    DeerListResponse,
)


router = APIRouter(
    prefix="/api/deer",
    tags=["deer"],
)


@router.post("", response_model=DeerResponse, status_code=status.HTTP_201_CREATED)
async def create_deer(
    deer_data: DeerCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new deer profile.

    Parameters:
        deer_data: Deer information (name, sex, species, etc.)

    Returns:
        DeerResponse: Created deer profile with ID

    Example:
        POST /api/deer
        {
            "name": "Buck-01",
            "sex": "male",
            "species": "white_tailed_deer",
            "notes": "Large 8-point buck, distinctive scar on left shoulder"
        }

    Requirements:
        - FR-024: Create deer profile with basic info
        - FR-025: Record sex and species
    """
    # Create deer instance
    deer = Deer(
        name=deer_data.name,
        sex=deer_data.sex,
        species=deer_data.species,
        status=DeerStatus.ALIVE,  # Default to alive
        notes=deer_data.notes,
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        sighting_count=0,
    )

    db.add(deer)
    db.commit()
    db.refresh(deer)

    return deer


@router.get("", response_model=DeerListResponse)
async def list_deer(
    sex: Optional[Sex] = Query(None, description="Filter by sex"),
    status: Optional[DeerStatus] = Query(None, description="Filter by status"),
    species: Optional[str] = Query(None, description="Filter by species"),
    min_sightings: Optional[int] = Query(1, description="Minimum sighting count (default: 1 to hide invalidated profiles)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all deer profiles with optional filtering.

    Parameters:
        sex: Filter by sex (male, female, unknown)
        status: Filter by status (alive, deceased, unknown)
        species: Filter by species
        min_sightings: Minimum number of sightings
        page: Page number (1-indexed)
        page_size: Number of results per page (1-200)

    Returns:
        {
            "deer": List[DeerResponse],
            "total": int,
            "page": int,
            "page_size": int,
            "pages": int
        }

    Example:
        GET /api/deer?sex=male&min_sightings=5&page=1&page_size=20
        Returns male deer with 5+ sightings, sorted by last seen

    Requirements:
        - FR-026: List deer with filtering
        - FR-027: Pagination support
    """
    # Build query
    query = db.query(Deer)

    # Apply filters
    if sex is not None:
        query = query.filter(Deer.sex == sex)
    if status is not None:
        query = query.filter(Deer.status == status)
    if species is not None:
        query = query.filter(Deer.species == species)
    if min_sightings is not None:
        query = query.filter(Deer.sighting_count >= min_sightings)

    # Get total count
    total = query.count()

    # Apply pagination and sorting (most recently seen first)
    deer_list = (
        query.order_by(desc(Deer.last_seen))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    # Add photo URLs to each deer
    deer_with_photos = []
    for deer in deer_list:
        deer_dict = {
            "id": deer.id,
            "name": deer.name,
            "sex": deer.sex,
            "species": deer.species,
            "notes": deer.notes,
            "status": deer.status,
            "confidence": deer.confidence,
            "first_seen": deer.first_seen,
            "last_seen": deer.last_seen,
            "sighting_count": deer.sighting_count,
            "created_at": deer.created_at,
            "updated_at": deer.updated_at,
            "best_photo_id": deer.best_photo_id,
            "thumbnail_url": f"/api/static/thumbnails/{deer.best_photo_id}" if deer.best_photo_id else None,
            "photo_url": f"/api/static/images/{deer.best_photo_id}" if deer.best_photo_id else None,
        }
        deer_with_photos.append(deer_dict)

    return {
        "deer": deer_with_photos,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{deer_id}", response_model=DeerResponse)
async def get_deer(
    deer_id: UUID,
    include_detections: bool = Query(
        False, description="Include detection history"
    ),
    db: Session = Depends(get_db),
):
    """
    Get a specific deer profile by ID.

    Parameters:
        deer_id: UUID of the deer
        include_detections: Include full detection/sighting history

    Returns:
        DeerResponse: Deer profile with optional detection history

    Raises:
        404: Deer not found

    Example:
        GET /api/deer/{uuid}?include_detections=true
        Returns deer with all sightings and detection metadata

    Requirements:
        - FR-028: Get deer profile by ID
        - FR-029: Include sighting history
    """
    deer = db.query(Deer).filter(Deer.id == deer_id).first()

    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Optionally include detection history
    if include_detections:
        # Get all detections for this deer with image info
        detections = (
            db.query(Detection, Image)
            .join(Image, Detection.image_id == Image.id)
            .filter(Detection.deer_id == deer_id)
            .order_by(desc(Image.timestamp))
            .all()
        )

        # Attach to response (handled by Pydantic model)
        deer.detection_history = [d[0] for d in detections]

    # Construct response with photo URLs
    deer_dict = {
        "id": deer.id,
        "name": deer.name,
        "sex": deer.sex,
        "species": deer.species,
        "notes": deer.notes,
        "status": deer.status,
        "confidence": deer.confidence,
        "first_seen": deer.first_seen,
        "last_seen": deer.last_seen,
        "sighting_count": deer.sighting_count,
        "created_at": deer.created_at,
        "updated_at": deer.updated_at,
        "best_photo_id": deer.best_photo_id,
        "thumbnail_url": f"/api/static/thumbnails/{deer.best_photo_id}" if deer.best_photo_id else None,
        "photo_url": f"/api/static/images/{deer.best_photo_id}" if deer.best_photo_id else None,
    }

    return deer_dict


@router.put("/{deer_id}", response_model=DeerResponse)
async def update_deer(
    deer_id: UUID,
    deer_update: DeerUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a deer profile.

    Parameters:
        deer_id: UUID of the deer
        deer_update: Fields to update

    Returns:
        DeerResponse: Updated deer profile

    Raises:
        404: Deer not found

    Example:
        PUT /api/deer/{uuid}
        {
            "name": "Big Buck",
            "status": "deceased",
            "notes": "Not seen since 2025-10-15"
        }

    Requirements:
        - FR-030: Update deer profile
        - FR-031: Update status (alive/deceased)
    """
    deer = db.query(Deer).filter(Deer.id == deer_id).first()

    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Update fields (only provided fields)
    update_data = deer_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deer, field, value)

    db.commit()
    db.refresh(deer)

    return deer


@router.delete("/{deer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deer(
    deer_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a deer profile.

    WARNING: This will unlink all associated detections but not delete them.
    Detections will have deer_id set to NULL.

    Parameters:
        deer_id: UUID of the deer

    Raises:
        404: Deer not found

    Returns:
        204 No Content on success

    Requirements:
        - FR-032: Delete deer profile
        - FR-033: Preserve detection records
    """
    deer = db.query(Deer).filter(Deer.id == deer_id).first()

    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Unlink detections (set deer_id to NULL)
    db.query(Detection).filter(Detection.deer_id == deer_id).update(
        {"deer_id": None}
    )

    # Delete deer profile
    db.delete(deer)
    db.commit()

    return None


@router.get("/{deer_id}/timeline", response_model=dict, status_code=status.HTTP_200_OK)
def get_deer_timeline(
    deer_id: UUID,
    db: Session = Depends(get_db),
    group_by: str = Query("day", regex="^(hour|day|week|month)$"),
) -> dict:
    """
    Get sighting timeline for a deer (Sprint 6).

    Returns sightings grouped by time period with counts and confidence averages.
    Useful for understanding deer activity patterns over time.

    Parameters:
        deer_id: UUID of the deer
        group_by: Time grouping (hour, day, week, month) - default: day

    Raises:
        404: Deer not found
        400: Invalid group_by parameter

    Returns:
        dict: Timeline data with sightings grouped by time period

    Example Response:
        {
            "deer_id": "uuid...",
            "group_by": "day",
            "total_sightings": 15,
            "date_range": {"first": "2024-01-01", "last": "2024-01-15"},
            "timeline": [
                {"period": "2024-01-01", "count": 3, "avg_confidence": 0.85},
                {"period": "2024-01-02", "count": 5, "avg_confidence": 0.82},
                ...
            ]
        }
    """
    # Verify deer exists
    deer = db.query(Deer).filter(Deer.id == deer_id).first()
    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Determine date truncation based on group_by
    if group_by == "hour":
        date_trunc = func.date_trunc('hour', Image.timestamp)
    elif group_by == "day":
        date_trunc = func.date_trunc('day', Image.timestamp)
    elif group_by == "week":
        date_trunc = func.date_trunc('week', Image.timestamp)
    elif group_by == "month":
        date_trunc = func.date_trunc('month', Image.timestamp)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by parameter: {group_by}. Must be hour, day, week, or month.",
        )

    # Query sightings grouped by time period
    timeline_data = (
        db.query(
            date_trunc.label('period'),
            func.count(Detection.id).label('count'),
            func.avg(Detection.confidence).label('avg_confidence')
        )
        .join(Image, Detection.image_id == Image.id)
        .filter(Detection.deer_id == deer_id)
        .group_by('period')
        .order_by('period')
        .all()
    )

    # Format response
    timeline = [
        {
            "period": row.period.isoformat() if row.period else None,
            "count": row.count,
            "avg_confidence": round(float(row.avg_confidence), 3) if row.avg_confidence else 0.0
        }
        for row in timeline_data
    ]

    return {
        "deer_id": str(deer_id),
        "group_by": group_by,
        "total_sightings": deer.sighting_count,
        "date_range": {
            "first": deer.first_seen.isoformat() if deer.first_seen else None,
            "last": deer.last_seen.isoformat() if deer.last_seen else None,
        },
        "timeline": timeline
    }


@router.get("/{deer_id}/locations", response_model=dict, status_code=status.HTTP_200_OK)
def get_deer_locations(
    deer_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get location patterns for a deer (Sprint 6).

    Returns locations where this deer has been spotted with sighting counts
    and date ranges. Useful for understanding deer movement patterns and
    territory.

    Parameters:
        deer_id: UUID of the deer

    Raises:
        404: Deer not found

    Returns:
        dict: Location data with sighting counts

    Example Response:
        {
            "deer_id": "uuid...",
            "total_sightings": 15,
            "unique_locations": 3,
            "locations": [
                {
                    "location_id": "uuid...",
                    "location_name": "Sanctuary",
                    "sighting_count": 10,
                    "first_seen": "2024-01-01T00:00:00",
                    "last_seen": "2024-01-15T00:00:00",
                    "avg_confidence": 0.85
                },
                ...
            ]
        }
    """
    from backend.models.location import Location

    # Verify deer exists
    deer = db.query(Deer).filter(Deer.id == deer_id).first()
    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Query locations with sighting stats
    location_data = (
        db.query(
            Location.id.label('location_id'),
            Location.name.label('location_name'),
            func.count(Detection.id).label('sighting_count'),
            func.min(Image.timestamp).label('first_seen'),
            func.max(Image.timestamp).label('last_seen'),
            func.avg(Detection.confidence).label('avg_confidence')
        )
        .join(Image, Detection.image_id == Image.id)
        .join(Location, Image.location_id == Location.id)
        .filter(Detection.deer_id == deer_id)
        .group_by(Location.id, Location.name)
        .order_by(desc(func.count(Detection.id)))
        .all()
    )

    # Format response
    locations = [
        {
            "location_id": str(row.location_id),
            "location_name": row.location_name,
            "sighting_count": row.sighting_count,
            "first_seen": row.first_seen.isoformat() if row.first_seen else None,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "avg_confidence": round(float(row.avg_confidence), 3) if row.avg_confidence else 0.0
        }
        for row in location_data
    ]

    return {
        "deer_id": str(deer_id),
        "total_sightings": deer.sighting_count,
        "unique_locations": len(locations),
        "locations": locations
    }


@router.get("/{deer_id}/images", response_model=dict, status_code=status.HTTP_200_OK)
def get_deer_images(
    deer_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get all images containing this deer.

    Returns images with their metadata sorted by timestamp (most recent first).
    Useful for browsing all sightings of a specific deer.

    Parameters:
        deer_id: UUID of the deer

    Raises:
        404: Deer not found

    Returns:
        dict: Images data with timestamps and locations

    Example Response:
        {
            "deer_id": "uuid...",
            "deer_name": "Wendy",
            "total_images": 174,
            "images": [
                {
                    "id": "uuid...",
                    "filename": "CAM1_20220626_123456.jpg",
                    "timestamp": "2022-06-26T12:34:56",
                    "location_name": "Sanctuary",
                    "confidence": 0.85
                },
                ...
            ]
        }
    """
    from backend.models.location import Location

    # Verify deer exists
    deer = db.query(Deer).filter(Deer.id == deer_id).first()
    if not deer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deer with ID {deer_id} not found",
        )

    # Query all images for this deer via detections with detection details
    images_data = (
        db.query(
            Image.id,
            Image.filename,
            Image.timestamp,
            Location.name.label('location_name'),
            Detection.id.label('detection_id'),
            Detection.confidence,
            Detection.classification,
            Detection.is_reviewed,
            Detection.is_valid,
            Detection.corrected_classification,
            Detection.correction_notes
        )
        .join(Detection, Image.id == Detection.image_id)
        .join(Location, Image.location_id == Location.id)
        .filter(Detection.deer_id == deer_id)
        .order_by(desc(Image.timestamp))
        .all()
    )

    # Format response with detection details
    images = [
        {
            "id": str(row.id),
            "filename": row.filename,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "location_name": row.location_name,
            "detection_id": str(row.detection_id),
            "confidence": round(float(row.confidence), 3) if row.confidence else 0.0,
            "classification": row.classification,
            "is_reviewed": row.is_reviewed,
            "is_valid": row.is_valid,
            "corrected_classification": row.corrected_classification,
            "correction_notes": row.correction_notes,
        }
        for row in images_data
    ]

    return {
        "deer_id": str(deer_id),
        "deer_name": deer.name,
        "total_images": len(images),
        "images": images
    }


@router.get(
    "/stats/species",
    summary="Get species population statistics",
    description="Get counts of detections by species including deer and non-deer animals"
)
def get_species_stats(
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get population breakdown by species.

    Returns counts for:
    - Deer (buck/doe/fawn/unknown combined)
    - Feral Hogs (pigs)
    - Cattle
    - Raccoons
    - Other/Unknown

    Uses corrected_classification if available, otherwise ML classification.

    Args:
        location_id: Optional location UUID to filter results
        db: Database session

    Returns:
        dict: Species counts with breakdown

    Example Response:
        {
            "total_detections": 12450,
            "deer": {
                "total": 12000,
                "buck": 3500,
                "doe": 7200,
                "fawn": 800,
                "unknown": 500
            },
            "non_deer": {
                "total": 450,
                "feral_hogs": 200,
                "cattle": 150,
                "raccoons": 100
            }
        }
    """
    from backend.models.detection import Detection
    from backend.models.image import Image
    from sqlalchemy import func, case

    # Base query
    query = db.query(Detection)

    # Join with images if filtering by location
    if location_id:
        query = query.join(Image).filter(Image.location_id == location_id)

    # Get classification (prefer corrected over ML)
    classification_col = func.coalesce(
        Detection.corrected_classification,
        Detection.classification
    )

    # Count by classification
    counts = {}
    for classification, count in (
        query
        .with_entities(classification_col, func.count(Detection.id))
        .group_by(classification_col)
        .all()
    ):
        if classification:
            counts[classification.lower()] = count

    # Build response
    deer_classes = {"buck", "doe", "fawn", "unknown"}
    deer_breakdown = {}
    deer_total = 0

    for deer_class in deer_classes:
        count = counts.get(deer_class, 0)
        deer_breakdown[deer_class] = count
        deer_total += count

    non_deer_breakdown = {
        "feral_hogs": counts.get("pig", 0),
        "cattle": counts.get("cattle", 0),
        "raccoons": counts.get("raccoon", 0),
    }
    non_deer_total = sum(non_deer_breakdown.values())

    total_detections = deer_total + non_deer_total

    return {
        "total_detections": total_detections,
        "deer": {
            "total": deer_total,
            **deer_breakdown
        },
        "non_deer": {
            "total": non_deer_total,
            **non_deer_breakdown
        },
        "location_filter": str(location_id) if location_id else None
    }
