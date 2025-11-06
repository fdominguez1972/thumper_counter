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
    min_sightings: Optional[int] = Query(None, description="Minimum sighting count"),
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

    return {
        "deer": deer_list,
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

    return deer


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
