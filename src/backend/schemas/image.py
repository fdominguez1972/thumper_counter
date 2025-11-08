"""
Pydantic schemas for Image API requests and responses.

These schemas handle validation and serialization for image endpoints.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class DetectionSummary(BaseModel):
    """Summary of a detection for image lists."""
    id: UUID
    classification: str
    corrected_classification: Optional[str] = None
    confidence: float
    is_valid: bool
    is_reviewed: bool

    class Config:
        from_attributes = True


class ImageUploadResponse(BaseModel):
    """Schema for image upload response."""
    id: UUID
    filename: str
    processing_status: str
    queue_position: Optional[int] = Field(
        None,
        description="Position in processing queue (null if not queued)"
    )
    timestamp: datetime
    location_id: Optional[UUID]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "SANCTUARY_00123.jpg",
                "processing_status": "pending",
                "queue_position": None,
                "timestamp": "2025-01-01T12:00:00Z",
                "location_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class ImageResponse(BaseModel):
    """Schema for image API responses."""
    id: UUID
    filename: str
    path: str
    timestamp: datetime
    location_id: Optional[UUID]
    exif_data: Optional[dict]
    processing_status: str
    error_message: Optional[str] = Field(
        None,
        description="Error message if processing failed (only present when status=failed)"
    )
    created_at: datetime
    detection_count: Optional[int] = Field(
        None,
        description="Number of deer detections in this image"
    )
    detections: List[DetectionSummary] = Field(
        default_factory=list,
        description="List of detections in this image"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "SANCTUARY_00123.jpg",
                "path": "/mnt/images/Sanctuary/SANCTUARY_00123.jpg",
                "timestamp": "2025-01-01T12:00:00Z",
                "location_id": "550e8400-e29b-41d4-a716-446655440001",
                "exif_data": {
                    "camera_make": "Reconyx",
                    "camera_model": "HC500"
                },
                "processing_status": "completed",
                "error_message": None,
                "created_at": "2025-01-01T12:01:00Z",
                "detection_count": 3
            }
        }


class ImageList(BaseModel):
    """Schema for paginated image list response."""
    total: int = Field(..., description="Total number of images matching filters")
    images: list[ImageResponse] = Field(..., description="List of images")
    page_size: int = Field(..., description="Number of images per page")
    skip: int = Field(..., description="Number of images skipped")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1523,
                "images": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "SANCTUARY_00123.jpg",
                        "path": "/mnt/images/Sanctuary/SANCTUARY_00123.jpg",
                        "timestamp": "2025-01-01T12:00:00Z",
                        "location_id": "550e8400-e29b-41d4-a716-446655440001",
                        "exif_data": {},
                        "processing_status": "completed",
                        "error_message": None,
                        "created_at": "2025-01-01T12:01:00Z",
                        "detection_count": 3
                    }
                ],
                "page_size": 20,
                "skip": 0
            }
        }


class BatchUploadResponse(BaseModel):
    """Schema for batch upload response."""
    total_uploaded: int = Field(..., description="Number of images successfully uploaded")
    total_failed: int = Field(..., description="Number of images that failed to upload")
    images: list[ImageUploadResponse] = Field(..., description="List of uploaded images")
    errors: list[dict] = Field(default_factory=list, description="List of upload errors")

    class Config:
        json_schema_extra = {
            "example": {
                "total_uploaded": 5,
                "total_failed": 0,
                "images": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "SANCTUARY_00123.jpg",
                        "processing_status": "pending",
                        "queue_position": None,
                        "timestamp": "2025-01-01T12:00:00Z",
                        "location_id": "550e8400-e29b-41d4-a716-446655440001"
                    }
                ],
                "errors": []
            }
        }


# Export all schemas
__all__ = [
    "DetectionSummary",
    "ImageUploadResponse",
    "ImageResponse",
    "ImageList",
    "BatchUploadResponse",
]
