"""
Detection model for deer detections in images.

Links images to deer via bounding box detections from YOLOv8.
Based on specs/system.spec Detection data model definition.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Tuple

from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Detection(Base):
    """
    Deer detection with bounding box and classification.

    Represents a single deer detected in an image by the YOLOv8 model.
    Each detection may or may not be matched to a known deer (via re-identification).

    The ML pipeline flow:
    1. YOLOv8 detects deer in image -> creates Detection with bbox
    2. Classification model determines sex -> updates classification field
    3. ResNet50 extracts feature vector from crop
    4. Re-ID matches to existing Deer OR creates new Deer
    5. Detection.deer_id is set to matched/new Deer

    Relationships:
        - image: The image this detection was found in (many-to-one)
        - deer: The deer this detection was matched to (many-to-one, nullable)

    Attributes:
        id: Unique identifier (UUID)
        image_id: Foreign key to Image table
        deer_id: Foreign key to Deer table (nullable if not yet matched)
        bbox: Bounding box coordinates as JSON {x, y, width, height}
        confidence: Detection confidence from YOLOv8 (0.0 to 1.0)
        classification: Sex classification (buck/doe/fawn/unknown)
        created_at: When this detection was created
    """
    __tablename__ = "detections"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for detection"
    )

    # Foreign keys
    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Image where this deer was detected"
    )

    deer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("deer.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Deer this detection was matched to (null if not yet matched)"
    )

    # Detection data
    bbox = Column(
        JSON,
        nullable=False,
        comment="Bounding box as {x, y, width, height} in pixels"
    )

    confidence = Column(
        Float,
        nullable=False,
        comment="YOLOv8 detection confidence (0.0 to 1.0)"
    )

    classification = Column(
        String(20),
        nullable=False,
        default="unknown",
        comment="Sex classification (buck/doe/fawn/unknown)"
    )

    # Deduplication fields
    is_duplicate = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if this detection overlaps significantly with another in same image"
    )

    burst_group_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Groups detections from same photo burst/event (same timestamp + location)"
    )

    # User correction/review fields
    is_reviewed = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if a user has reviewed and verified this detection"
    )

    is_valid = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="False if detection is unusable (rear-end, wrong species, poor quality, etc.)"
    )

    corrected_classification = Column(
        String(20),
        nullable=True,
        comment="User-corrected classification if ML was wrong (buck/doe/fawn/unknown)"
    )

    correction_notes = Column(
        String,
        nullable=True,
        comment="User notes explaining correction or why detection is invalid"
    )

    reviewed_by = Column(
        String(100),
        nullable=True,
        comment="Username or identifier of who reviewed this detection"
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when detection was reviewed"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this detection was created"
    )

    # Relationships
    image = relationship(
        "Image",
        back_populates="detections",
        lazy="joined"
    )

    deer = relationship(
        "Deer",
        back_populates="detections",
        lazy="joined"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_detections_image_deer", "image_id", "deer_id"),
        Index("ix_detections_confidence", "confidence"),
        Index("ix_detections_classification", "classification"),
        {"comment": "Deer detections with bounding boxes and classifications"}
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        deer_str = f"deer={self.deer_id}" if self.deer_id else "unmatched"
        return (
            f"<Detection(id={self.id}, image={self.image_id}, {deer_str}, "
            f"confidence={self.confidence:.2f})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Serializable representation of the detection
        """
        return {
            "id": str(self.id),
            "image_id": str(self.image_id),
            "deer_id": str(self.deer_id) if self.deer_id else None,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "classification": self.classification,
            "is_reviewed": self.is_reviewed,
            "is_valid": self.is_valid,
            "corrected_classification": self.corrected_classification,
            "correction_notes": self.correction_notes,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict_with_relations(self) -> dict:
        """
        Convert model to dictionary including related data.

        Returns:
            dict: Detection with image and deer information
        """
        data = self.to_dict()

        if self.image:
            data["image"] = {
                "filename": self.image.filename,
                "timestamp": self.image.timestamp.isoformat() if self.image.timestamp else None,
                "location_id": str(self.image.location_id) if self.image.location_id else None,
            }

        if self.deer:
            data["deer"] = {
                "name": self.deer.name,
                "sex": self.deer.sex.value,
                "sighting_count": self.deer.sighting_count,
            }

        return data

    @property
    def is_matched(self) -> bool:
        """Check if detection has been matched to a deer."""
        return self.deer_id is not None

    @property
    def bbox_coords(self) -> Tuple[int, int, int, int]:
        """
        Get bounding box as tuple.

        Returns:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        if not self.bbox:
            return (0, 0, 0, 0)
        return (
            self.bbox.get("x", 0),
            self.bbox.get("y", 0),
            self.bbox.get("width", 0),
            self.bbox.get("height", 0)
        )

    @property
    def bbox_area(self) -> int:
        """
        Calculate bounding box area in pixels.

        Returns:
            int: Area (width * height)
        """
        x, y, w, h = self.bbox_coords
        return w * h

    @property
    def bbox_center(self) -> Tuple[float, float]:
        """
        Calculate center point of bounding box.

        Returns:
            Tuple[float, float]: (center_x, center_y)
        """
        x, y, w, h = self.bbox_coords
        return (x + w / 2, y + h / 2)

    def set_bbox(self, x: int, y: int, width: int, height: int) -> None:
        """
        Set bounding box coordinates.

        Args:
            x: Left edge x-coordinate (pixels)
            y: Top edge y-coordinate (pixels)
            width: Box width (pixels)
            height: Box height (pixels)

        Raises:
            ValueError: If any dimension is negative
        """
        if x < 0 or y < 0 or width < 0 or height < 0:
            raise ValueError(
                f"Bounding box dimensions must be non-negative: "
                f"x={x}, y={y}, width={width}, height={height}"
            )

        self.bbox = {
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height)
        }

    def set_bbox_from_yolo(self, x_center: float, y_center: float,
                           width: float, height: float,
                           img_width: int, img_height: int) -> None:
        """
        Set bounding box from YOLO normalized format.

        YOLO format: (x_center, y_center, width, height) all normalized 0-1

        Args:
            x_center: Center x-coordinate (normalized 0-1)
            y_center: Center y-coordinate (normalized 0-1)
            width: Box width (normalized 0-1)
            height: Box height (normalized 0-1)
            img_width: Image width in pixels
            img_height: Image height in pixels
        """
        # Convert from normalized to pixel coordinates
        pixel_width = width * img_width
        pixel_height = height * img_height
        pixel_x = (x_center * img_width) - (pixel_width / 2)
        pixel_y = (y_center * img_height) - (pixel_height / 2)

        self.set_bbox(
            int(pixel_x),
            int(pixel_y),
            int(pixel_width),
            int(pixel_height)
        )

    def get_crop_coordinates(self) -> Tuple[int, int, int, int]:
        """
        Get coordinates for cropping the detected region from image.

        Returns:
            Tuple[int, int, int, int]: (left, top, right, bottom)
        """
        x, y, w, h = self.bbox_coords
        return (x, y, x + w, y + h)

    def match_to_deer(self, deer_id: uuid.UUID) -> None:
        """
        Match this detection to a deer.

        Args:
            deer_id: UUID of the deer to match to
        """
        self.deer_id = deer_id

    def unmatch(self) -> None:
        """Remove deer association (for re-processing)."""
        self.deer_id = None

    def iou(self, other: "Detection") -> float:
        """
        Calculate Intersection over Union (IoU) with another detection.

        Used for detecting duplicate detections or tracking across frames.

        Args:
            other: Another Detection to compare with

        Returns:
            float: IoU score (0.0 to 1.0)
        """
        x1, y1, w1, h1 = self.bbox_coords
        x2, y2, w2, h2 = other.bbox_coords

        # Calculate intersection rectangle
        inter_x1 = max(x1, x2)
        inter_y1 = max(y1, y2)
        inter_x2 = min(x1 + w1, x2 + w2)
        inter_y2 = min(y1 + h1, y2 + h2)

        # Calculate intersection area
        inter_width = max(0, inter_x2 - inter_x1)
        inter_height = max(0, inter_y2 - inter_y1)
        inter_area = inter_width * inter_height

        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area

        # Avoid division by zero
        if union_area == 0:
            return 0.0

        return inter_area / union_area

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """
        Check if detection meets confidence threshold.

        Args:
            threshold: Minimum confidence (default from .env: CONFIDENCE_THRESHOLD=0.7)

        Returns:
            bool: True if confidence >= threshold
        """
        return self.confidence >= threshold

    def to_yolo_format(self, img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        Convert bounding box to YOLO normalized format.

        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels

        Returns:
            Tuple[float, float, float, float]: (x_center, y_center, width, height) normalized
        """
        x, y, w, h = self.bbox_coords

        x_center = (x + w / 2) / img_width
        y_center = (y + h / 2) / img_height
        norm_width = w / img_width
        norm_height = h / img_height

        return (x_center, y_center, norm_width, norm_height)


# Export model
__all__ = ["Detection"]
