"""
Image model for trail camera photos.

Stores metadata and processing status for uploaded images.
Based on specs/system.spec Image data model definition.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class ProcessingStatus(enum.Enum):
    """
    Processing status for images as they move through the ML pipeline.

    Flow: pending -> queued -> processing -> completed
    Alternative: pending -> queued -> processing -> failed
    """
    PENDING = "pending"          # Image uploaded, not yet queued
    QUEUED = "queued"            # Submitted to Celery queue
    PROCESSING = "processing"    # Currently being processed by worker
    COMPLETED = "completed"      # Successfully processed
    FAILED = "failed"            # Processing failed


class Image(Base):
    """
    Trail camera image with metadata and processing status.

    Represents a single image file from a trail camera. Stores both the
    original file location and EXIF metadata extracted during ingestion.
    Processing status tracks the image through the ML pipeline.

    Relationships:
        - location: The camera location where this image was captured
        - detections: All deer detections found in this image (one-to-many)

    Attributes:
        id: Unique identifier (UUID)
        filename: Original filename from trail camera
        path: Full filesystem path to stored image
        timestamp: When the photo was taken (from EXIF or filename)
        location_id: Foreign key to Location table
        exif_data: Raw EXIF metadata as JSON
        processing_status: Current state in ML pipeline
        created_at: When this record was created in the database
    """
    __tablename__ = "images"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for image record"
    )

    # File information
    filename = Column(
        String(255),
        nullable=False,
        comment="Original filename from trail camera"
    )

    path = Column(
        String(512),
        nullable=False,
        unique=True,
        comment="Full filesystem path to stored image"
    )

    # Temporal information
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the photo was taken (from EXIF or filename)"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this record was created"
    )

    # Location relationship
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Camera location where image was captured"
    )

    # Metadata
    exif_data = Column(
        JSON,
        nullable=True,
        comment="Raw EXIF metadata from image (camera model, settings, etc.)"
    )

    # Processing status
    processing_status = Column(
        Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True,
        comment="Current state in ML pipeline"
    )

    # Relationships
    location = relationship(
        "Location",
        back_populates="images",
        lazy="joined"
    )

    detections = relationship(
        "Detection",
        back_populates="image",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_images_timestamp_status", "timestamp", "processing_status"),
        Index("ix_images_location_timestamp", "location_id", "timestamp"),
        {"comment": "Trail camera images with metadata and processing status"}
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Image(id={self.id}, filename='{self.filename}', "
            f"status={self.processing_status.value}, timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Serializable representation of the image
        """
        return {
            "id": str(self.id),
            "filename": self.filename,
            "path": self.path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "exif_data": self.exif_data,
            "processing_status": self.processing_status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_processed(self) -> bool:
        """Check if image has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def can_reprocess(self) -> bool:
        """Check if image can be queued for reprocessing."""
        return self.processing_status in [
            ProcessingStatus.FAILED,
            ProcessingStatus.COMPLETED
        ]

    def mark_queued(self) -> None:
        """Mark image as queued for processing."""
        self.processing_status = ProcessingStatus.QUEUED

    def mark_processing(self) -> None:
        """Mark image as currently being processed."""
        self.processing_status = ProcessingStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark image as successfully processed."""
        self.processing_status = ProcessingStatus.COMPLETED

    def mark_failed(self) -> None:
        """Mark image as failed processing."""
        self.processing_status = ProcessingStatus.FAILED


# Export model and enum
__all__ = ["Image", "ProcessingStatus"]
