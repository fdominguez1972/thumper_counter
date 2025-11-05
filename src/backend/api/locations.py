"""
Locations API router for trail camera locations.

Provides endpoints for managing camera locations (Sanctuary, Hayfield, etc.)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.database import get_db
from backend.models.location import Location
from backend.schemas.location import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationList,
)


# Create API router
router = APIRouter(
    prefix="/api/locations",
    tags=["Locations"],
)


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new location",
    description="Create a new camera location. Location names must be unique."
)
def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db)
) -> LocationResponse:
    """
    Create a new camera location.

    Args:
        location_data: Location details (name, description, coordinates)
        db: Database session

    Returns:
        LocationResponse: Created location with ID

    Raises:
        HTTPException 409: Location with this name already exists
        HTTPException 400: Invalid data
    """
    try:
        # Create location model instance
        location = Location(
            name=location_data.name,
            description=location_data.description,
            active=location_data.active,
        )

        # Set coordinates if provided
        if location_data.coordinates:
            location.set_coordinates(
                latitude=location_data.coordinates.lat,
                longitude=location_data.coordinates.lon
            )

        # Add to database
        db.add(location)
        db.commit()
        db.refresh(location)

        print(f"[OK] Created location: {location.name} (ID: {location.id})")

        return LocationResponse.model_validate(location)

    except IntegrityError as e:
        db.rollback()
        # Check if it's a duplicate name error
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location with name '{location_data.name}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {str(e)}"
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create location"
        )


@router.get(
    "",
    response_model=LocationList,
    summary="List all locations",
    description="Retrieve all camera locations with optional filtering"
)
def list_locations(
    active_only: Optional[bool] = Query(
        None,
        description="Filter by active status (true=active only, false=inactive only, null=all)"
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip (for pagination)"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    ),
    db: Session = Depends(get_db)
) -> LocationList:
    """
    List all camera locations with optional filtering.

    Args:
        active_only: Filter by active status
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        db: Database session

    Returns:
        LocationList: List of locations with total count
    """
    try:
        # Build query
        query = db.query(Location)

        # Apply active filter if specified
        if active_only is not None:
            query = query.filter(Location.active == active_only)

        # Get total count before pagination
        total = query.count()

        # Order by name and apply pagination
        locations = (
            query.order_by(Location.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Convert to response models
        location_responses = [
            LocationResponse.model_validate(loc) for loc in locations
        ]

        return LocationList(
            total=total,
            locations=location_responses
        )

    except Exception as e:
        print(f"[ERROR] Failed to list locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve locations"
        )


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Get location by ID",
    description="Retrieve a specific location by its UUID"
)
def get_location(
    location_id: str,
    db: Session = Depends(get_db)
) -> LocationResponse:
    """
    Get a specific location by ID.

    Args:
        location_id: Location UUID
        db: Database session

    Returns:
        LocationResponse: Location details

    Raises:
        HTTPException 404: Location not found
        HTTPException 400: Invalid UUID format
    """
    try:
        # Validate UUID format
        from uuid import UUID
        try:
            uuid_obj = UUID(location_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {location_id}"
            )

        # Query location
        location = db.query(Location).filter(Location.id == uuid_obj).first()

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_id}"
            )

        return LocationResponse.model_validate(location)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location"
        )


@router.get(
    "/name/{location_name}",
    response_model=LocationResponse,
    summary="Get location by name",
    description="Retrieve a location by its name (e.g., 'Sanctuary', 'Hayfield')"
)
def get_location_by_name(
    location_name: str,
    db: Session = Depends(get_db)
) -> LocationResponse:
    """
    Get a location by its name.

    Args:
        location_name: Location name (e.g., 'Sanctuary')
        db: Database session

    Returns:
        LocationResponse: Location details

    Raises:
        HTTPException 404: Location not found
    """
    try:
        # Query location by name (case-sensitive)
        location = db.query(Location).filter(Location.name == location_name).first()

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_name}"
            )

        return LocationResponse.model_validate(location)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get location by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location"
        )


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    summary="Update location",
    description="Update a location's details (name, description, coordinates, active status)"
)
def update_location(
    location_id: str,
    location_data: LocationUpdate,
    db: Session = Depends(get_db)
) -> LocationResponse:
    """
    Update a location's details.

    Args:
        location_id: Location UUID
        location_data: Updated location details (all fields optional)
        db: Database session

    Returns:
        LocationResponse: Updated location details

    Raises:
        HTTPException 404: Location not found
        HTTPException 400: Invalid UUID format or data
        HTTPException 409: Name already taken by another location
    """
    try:
        # Validate UUID format
        from uuid import UUID
        try:
            uuid_obj = UUID(location_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {location_id}"
            )

        # Query location
        location = db.query(Location).filter(Location.id == uuid_obj).first()

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_id}"
            )

        # Track what changed for logging
        changes = []

        # Update name if provided
        if location_data.name is not None and location_data.name != location.name:
            # Check for duplicate name
            existing = db.query(Location).filter(
                Location.name == location_data.name,
                Location.id != uuid_obj
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Location with name '{location_data.name}' already exists"
                )
            changes.append(f"name: {location.name} -> {location_data.name}")
            location.name = location_data.name

        # Update description if provided
        if location_data.description is not None:
            changes.append("description updated")
            location.description = location_data.description

        # Update coordinates if provided
        if location_data.coordinates is not None:
            location.set_coordinates(
                latitude=location_data.coordinates.lat,
                longitude=location_data.coordinates.lon
            )
            changes.append(f"coordinates: ({location_data.coordinates.lat}, {location_data.coordinates.lon})")

        # Update active status if provided
        if location_data.active is not None and location_data.active != location.active:
            changes.append(f"active: {location.active} -> {location_data.active}")
            location.active = location_data.active

        # Commit changes
        db.commit()
        db.refresh(location)

        if changes:
            print(f"[OK] Updated location {location.name} (ID: {location.id}): {', '.join(changes)}")
        else:
            print(f"[INFO] No changes for location {location.name} (ID: {location.id})")

        return LocationResponse.model_validate(location)

    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to update location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )


# Export router
__all__ = ["router"]
