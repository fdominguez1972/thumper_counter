"""
Pydantic schemas for Detection API requests and responses.

These schemas handle validation and serialization for detection endpoints.
"""

from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    """Schema for bounding box coordinates."""
    x: int = Field(..., description="Left edge x-coordinate in pixels", ge=0)
    y: int = Field(..., description="Top edge y-coordinate in pixels", ge=0)
    width: int = Field(..., description="Box width in pixels", ge=0)
    height: int = Field(..., description="Box height in pixels", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "x": 100,
                "y": 150,
                "width": 200,
                "height": 250
            }
        }


class DetectionResponse(BaseModel):
    """Schema for detection API responses."""
    id: UUID
    image_id: UUID
    deer_id: Optional[UUID] = Field(
        None,
        description="Deer ID if matched via re-identification (null if not yet matched)"
    )
    bbox: Dict[str, int] = Field(
        ...,
        description="Bounding box as {x, y, width, height} in pixels"
    )
    confidence: float = Field(
        ...,
        description="YOLOv8 detection confidence (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    classification: str = Field(
        ...,
        description="Sex classification: buck, doe, fawn, or unknown"
    )
    created_at: datetime

    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v):
        """Validate bounding box has required keys."""
        required_keys = {'x', 'y', 'width', 'height'}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"bbox must contain keys: {required_keys}")
        for key in required_keys:
            if not isinstance(v[key], (int, float)):
                raise ValueError(f"bbox.{key} must be numeric")
            if v[key] < 0:
                raise ValueError(f"bbox.{key} must be non-negative")
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "image_id": "550e8400-e29b-41d4-a716-446655440001",
                "deer_id": "550e8400-e29b-41d4-a716-446655440002",
                "bbox": {
                    "x": 100,
                    "y": 150,
                    "width": 200,
                    "height": 250
                },
                "confidence": 0.95,
                "classification": "buck",
                "created_at": "2025-01-01T12:00:00Z"
            }
        }


class DetectionWithImageInfo(DetectionResponse):
    """Schema for detection with related image information."""
    image_filename: str = Field(..., description="Filename of the image")
    image_timestamp: datetime = Field(..., description="When the photo was taken")
    location_id: Optional[UUID] = Field(None, description="Camera location ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "image_id": "550e8400-e29b-41d4-a716-446655440001",
                "deer_id": "550e8400-e29b-41d4-a716-446655440002",
                "bbox": {
                    "x": 100,
                    "y": 150,
                    "width": 200,
                    "height": 250
                },
                "confidence": 0.95,
                "classification": "buck",
                "created_at": "2025-01-01T12:00:00Z",
                "image_filename": "SANCTUARY_00123.jpg",
                "image_timestamp": "2025-01-01T12:00:00Z",
                "location_id": "550e8400-e29b-41d4-a716-446655440003"
            }
        }


class DetectionList(BaseModel):
    """Schema for paginated detection list response."""
    total: int = Field(..., description="Total number of detections matching filters")
    detections: list[DetectionResponse] = Field(..., description="List of detections")
    page_size: int = Field(..., description="Number of detections per page")
    skip: int = Field(..., description="Number of detections skipped")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 523,
                "detections": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "image_id": "550e8400-e29b-41d4-a716-446655440001",
                        "deer_id": "550e8400-e29b-41d4-a716-446655440002",
                        "bbox": {
                            "x": 100,
                            "y": 150,
                            "width": 200,
                            "height": 250
                        },
                        "confidence": 0.95,
                        "classification": "buck",
                        "created_at": "2025-01-01T12:00:00Z"
                    }
                ],
                "page_size": 20,
                "skip": 0
            }
        }


class DetectionStats(BaseModel):
    """Schema for detection statistics."""
    total_detections: int = Field(..., description="Total number of detections")
    by_classification: Dict[str, int] = Field(
        ...,
        description="Count by classification (buck/doe/fawn/unknown)"
    )
    avg_confidence: float = Field(
        ...,
        description="Average detection confidence",
        ge=0.0,
        le=1.0
    )
    high_confidence_count: int = Field(
        ...,
        description="Number of detections with confidence >= 0.7"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_detections": 52341,
                "by_classification": {
                    "buck": 8234,
                    "doe": 21456,
                    "fawn": 12341,
                    "unknown": 10310
                },
                "avg_confidence": 0.87,
                "high_confidence_count": 47123
            }
        }


# Export all schemas
__all__ = [
    "BoundingBox",
    "DetectionResponse",
    "DetectionWithImageInfo",
    "DetectionList",
    "DetectionStats",
]
