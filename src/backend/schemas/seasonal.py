"""
Pydantic schemas for seasonal queries.
Feature: 008-rut-season-analysis
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID


class PageMetadata(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Items per page", ge=1, le=1000)
    total_pages: int = Field(..., description="Total number of pages", ge=0)
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class ImageResponse(BaseModel):
    """Image object in seasonal query responses."""

    id: UUID
    filename: str
    path: str
    timestamp: datetime
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    processing_status: str
    detection_count: int = Field(default=0, description="Number of detections in this image")
    created_at: datetime

    class Config:
        from_attributes = True


class SeasonalImagesResponse(BaseModel):
    """Response schema for seasonal image queries."""

    images: List[ImageResponse] = Field(..., description="Array of image objects")
    total_count: int = Field(..., description="Total images matching filters (all pages)", ge=0)
    page_metadata: PageMetadata


class DetectionResponse(BaseModel):
    """Detection object in seasonal query responses."""

    id: UUID
    image_id: UUID
    bbox: Dict[str, int] = Field(..., description="Bounding box as {x, y, width, height} in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    classification: str = Field(..., description="Sex/age/species classification")
    deer_id: Optional[UUID] = Field(None, description="Re-identified deer profile ID")
    deer_name: Optional[str] = Field(None, description="User-assigned deer name")
    created_at: datetime

    class Config:
        from_attributes = True


class SeasonalDetectionsResponse(BaseModel):
    """Response schema for seasonal detection queries."""

    detections: List[DetectionResponse] = Field(..., description="Array of detection objects")
    total_count: int = Field(..., description="Total detections matching filters", ge=0)
    page_metadata: PageMetadata
