"""
Pydantic schemas for Location API requests and responses.

These schemas handle validation and serialization for location endpoints.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class LocationCoordinates(BaseModel):
    """GPS coordinates for a location."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    lon: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")

    class Config:
        json_schema_extra = {
            "example": {
                "lat": 30.5678,
                "lon": -98.1234
            }
        }


class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Location name from folder structure (e.g., 'Sanctuary', 'Hayfield')"
    )
    description: Optional[str] = Field(
        None,
        description="Optional notes about the physical location"
    )
    coordinates: Optional[LocationCoordinates] = Field(
        None,
        description="GPS coordinates (manually added via Google Maps)"
    )
    active: bool = Field(
        True,
        description="Whether this location is currently in use"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean location name."""
        # Strip whitespace
        v = v.strip()
        if not v:
            raise ValueError("Location name cannot be empty or whitespace")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sanctuary",
                "description": "East pasture near water tank, heavy deer traffic",
                "coordinates": {
                    "lat": 30.5678,
                    "lon": -98.1234
                },
                "active": True
            }
        }


class LocationUpdate(BaseModel):
    """Schema for updating an existing location."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated location name"
    )
    description: Optional[str] = Field(
        None,
        description="Updated description"
    )
    coordinates: Optional[LocationCoordinates] = Field(
        None,
        description="Updated GPS coordinates"
    )
    active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate and clean location name."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Location name cannot be empty or whitespace")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Updated description with more details",
                "coordinates": {
                    "lat": 30.5678,
                    "lon": -98.1234
                }
            }
        }


class LocationResponse(BaseModel):
    """Schema for location API responses."""
    id: UUID
    name: str
    description: Optional[str]
    coordinates: Optional[LocationCoordinates]
    active: bool
    image_count: int

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sanctuary",
                "description": "East pasture near water tank",
                "coordinates": {
                    "lat": 30.5678,
                    "lon": -98.1234
                },
                "active": True,
                "image_count": 1523
            }
        }


class LocationList(BaseModel):
    """Schema for paginated location list response."""
    total: int = Field(..., description="Total number of locations")
    locations: list[LocationResponse] = Field(..., description="List of locations")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 6,
                "locations": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Sanctuary",
                        "description": "East pasture near water tank",
                        "coordinates": {"lat": 30.5678, "lon": -98.1234},
                        "active": True,
                        "image_count": 1523
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "Hayfield",
                        "description": "Open field with good visibility",
                        "coordinates": {"lat": 30.5679, "lon": -98.1235},
                        "active": True,
                        "image_count": 892
                    }
                ]
            }
        }


# Export all schemas
__all__ = [
    "LocationCoordinates",
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "LocationList",
]
