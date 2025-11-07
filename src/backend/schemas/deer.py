"""
Pydantic Schemas for Deer Management
Version: 1.0.0
Date: 2025-11-06

Validation schemas for deer profile creation, updates, and responses.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from backend.models.deer import DeerSex as Sex, DeerStatus


class DeerBase(BaseModel):
    """Base deer schema with common fields."""

    sex: Sex = Field(..., description="Biological sex (male, female, unknown)")
    species: str = Field(
        default="white_tailed_deer",
        max_length=100,
        description="Species (white_tailed_deer, mule_deer, etc.)",
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes and observations"
    )


class DeerCreate(DeerBase):
    """Schema for creating a new deer profile."""

    name: str = Field(..., min_length=1, max_length=100, description="Deer identifier/name")


class DeerUpdate(BaseModel):
    """Schema for updating deer profile. All fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sex: Optional[Sex] = None
    species: Optional[str] = Field(None, max_length=100)
    status: Optional[DeerStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class DeerResponse(DeerBase):
    """Schema for deer profile response."""

    id: UUID
    name: Optional[str] = Field(None, max_length=100, description="Deer identifier/name (optional)")
    status: DeerStatus
    confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score (0.0-1.0)")
    first_seen: datetime
    last_seen: datetime
    sighting_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    best_photo_id: Optional[UUID] = Field(None, description="Image ID of best photo")
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail image")
    photo_url: Optional[str] = Field(None, description="URL to full-resolution photo")

    class Config:
        from_attributes = True


class DeerListResponse(BaseModel):
    """Schema for paginated deer list response."""

    deer: List[DeerResponse]
    total: int = Field(..., description="Total number of deer matching filters")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=200, description="Items per page")
    pages: int = Field(..., ge=0, description="Total number of pages")
