"""Pydantic schemas for API requests and responses."""

from backend.schemas.location import (
    LocationCoordinates,
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationList,
)
from backend.schemas.image import (
    ImageUploadResponse,
    ImageResponse,
    ImageList,
    BatchUploadResponse,
)

__all__ = [
    # Location schemas
    "LocationCoordinates",
    "LocationCreate",
    "LocationUpdate",
    "LocationResponse",
    "LocationList",
    # Image schemas
    "ImageUploadResponse",
    "ImageResponse",
    "ImageList",
    "BatchUploadResponse",
]
