"""
Location model for camera sites.

Stores information about trail camera locations and their configuration.
Locations are determined by folder names (e.g., "Sanctuary", "Hayfield").
Multiple cameras can operate at the same location.
Based on specs/system.spec Location data model definition.
"""

import uuid
from typing import Optional, Dict

from sqlalchemy import Column, String, Boolean, Integer, JSON, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Location(Base):
    """
    Trail camera location with configuration and statistics.

    Represents a physical location where trail cameras are deployed.
    Locations are identified by folder names in the image directory structure.
    Multiple cameras can be deployed at the same location over time.

    Relationships:
        - images: All images captured at this location (one-to-many)

    Attributes:
        id: Unique identifier (UUID)
        name: Location name from folder structure (e.g., "Sanctuary", "Hayfield")
        description: Optional notes about the physical location
        coordinates: GPS coordinates as JSON {lat, lon} (manually added via Google Maps)
        active: Whether this location is currently in use
        image_count: Total number of images captured at this location
    """
    __tablename__ = "locations"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for location"
    )

    # Location information
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Location name from folder structure (e.g., 'Sanctuary', 'Hayfield')"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Optional notes about the physical location"
    )

    coordinates = Column(
        JSON,
        nullable=True,
        comment="GPS coordinates as {lat, lon} - manually added via Google Maps"
    )

    # Status and statistics
    active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this location is currently in use"
    )

    image_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of images captured at this location"
    )

    # Relationships
    images = relationship(
        "Image",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_locations_active_name", "active", "name"),
        {"comment": "Trail camera locations with metadata and statistics"}
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Location(id={self.id}, name='{self.name}', "
            f"active={self.active}, images={self.image_count})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Serializable representation of the location
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates,
            "active": self.active,
            "image_count": self.image_count,
        }

    @property
    def latitude(self) -> Optional[float]:
        """
        Extract latitude from coordinates JSON.

        Returns:
            float: Latitude or None if not set
        """
        if self.coordinates and isinstance(self.coordinates, dict):
            return self.coordinates.get("lat")
        return None

    @property
    def longitude(self) -> Optional[float]:
        """
        Extract longitude from coordinates JSON.

        Returns:
            float: Longitude or None if not set
        """
        if self.coordinates and isinstance(self.coordinates, dict):
            return self.coordinates.get("lon")
        return None

    @property
    def has_coordinates(self) -> bool:
        """Check if location has valid GPS coordinates."""
        return (
            self.coordinates is not None
            and isinstance(self.coordinates, dict)
            and "lat" in self.coordinates
            and "lon" in self.coordinates
        )

    def set_coordinates(self, latitude: float, longitude: float) -> None:
        """
        Set GPS coordinates for this location.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90)
            longitude: Longitude in decimal degrees (-180 to 180)

        Raises:
            ValueError: If coordinates are out of valid range
        """
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude: {latitude} (must be -90 to 90)")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude: {longitude} (must be -180 to 180)")

        self.coordinates = {
            "lat": float(latitude),
            "lon": float(longitude)
        }

    def increment_image_count(self) -> None:
        """Increment the image count by 1."""
        self.image_count += 1

    def recalculate_image_count(self, db_session) -> int:
        """
        Recalculate image count from database.

        This queries the actual number of images and updates the cached count.
        Useful for fixing data inconsistencies.

        Args:
            db_session: SQLAlchemy session

        Returns:
            int: Updated image count
        """
        self.image_count = self.images.count()
        return self.image_count

    def activate(self) -> None:
        """Mark location as active."""
        self.active = True

    def deactivate(self) -> None:
        """Mark location as inactive."""
        self.active = False

    def get_recent_images(self, limit: int = 10):
        """
        Get most recent images from this location.

        Args:
            limit: Maximum number of images to return

        Returns:
            Query: SQLAlchemy query for recent images (not executed)
        """
        from backend.models.image import Image
        return (
            self.images
            .order_by(Image.timestamp.desc())
            .limit(limit)
        )

    def get_processed_image_count(self, db_session) -> int:
        """
        Get count of successfully processed images.

        Args:
            db_session: SQLAlchemy session

        Returns:
            int: Number of completed images
        """
        from backend.models.image import Image, ProcessingStatus
        return (
            self.images
            .filter(Image.processing_status == ProcessingStatus.COMPLETED)
            .count()
        )


# Export model
__all__ = ["Location"]
