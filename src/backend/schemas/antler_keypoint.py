"""
Pydantic schemas for antler keypoint API responses.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class AntlerKeypointBase(BaseModel):
    """Base schema for antler keypoint data."""
    keypoint_index: int = Field(..., ge=0, le=15, description="Keypoint index (0-15)")
    keypoint_name: str = Field(..., description="Keypoint name (e.g., left_g2)")
    x: float = Field(..., description="X-coordinate in pixels")
    y: float = Field(..., description="Y-coordinate in pixels")
    visibility: int = Field(..., ge=0, le=2, description="0=hidden, 1=occluded, 2=visible")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class AntlerKeypointResponse(AntlerKeypointBase):
    """Schema for antler keypoint API response."""
    id: UUID
    detection_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AntlerKeypointsResponse(BaseModel):
    """Schema for multiple keypoints response."""
    detection_id: UUID
    keypoints: List[AntlerKeypointResponse]
    total_keypoints: int
    visible_keypoints: int
    left_antler_keypoints: int
    right_antler_keypoints: int


class BatchAntlerDetectionRequest(BaseModel):
    """Request schema for batch antler detection."""
    detection_ids: Optional[List[UUID]] = Field(None, description="Optional list of detection IDs to process")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of detections to process")


class BatchAntlerDetectionResponse(BaseModel):
    """Response schema for batch antler detection."""
    status: str
    detections_queued: int
    task_ids: List[str]


class AntlerDetectionTaskResponse(BaseModel):
    """Response schema for single antler detection task."""
    status: str
    detection_id: UUID
    keypoints_detected: int
    message: Optional[str] = None


__all__ = [
    "AntlerKeypointBase",
    "AntlerKeypointResponse",
    "AntlerKeypointsResponse",
    "BatchAntlerDetectionRequest",
    "BatchAntlerDetectionResponse",
    "AntlerDetectionTaskResponse",
]
