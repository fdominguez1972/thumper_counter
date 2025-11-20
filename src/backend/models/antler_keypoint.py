"""
AntlerKeypoint model for storing antler keypoint detections.

Links detections to antler structure keypoints from YOLOv8-pose model.
"""

import uuid
from datetime import datetime
from typing import List, Dict

from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.core.database import Base


# Keypoint name mapping (index -> name)
KEYPOINT_NAMES = {
    0: "left_main_beam",
    1: "left_brow_tine",
    2: "left_g2",
    3: "left_g3",
    4: "left_g4",
    5: "left_tip",
    6: "left_bez_tine",
    7: "left_royal_tine",
    8: "right_main_beam",
    9: "right_brow_tine",
    10: "right_g2",
    11: "right_g3",
    12: "right_g4",
    13: "right_tip",
    14: "right_bez_tine",
    15: "right_royal_tine",
}


class AntlerKeypoint(Base):
    """
    Antler keypoint detection from YOLOv8-pose model.

    Each keypoint represents a specific anatomical point on a buck's antlers,
    used for enhanced Re-ID matching and antler scoring.

    Relationships:
        - detection: The deer detection this keypoint belongs to (many-to-one)

    Attributes:
        id: Unique identifier (UUID)
        detection_id: Foreign key to Detection table
        keypoint_index: Index of keypoint (0-15)
        keypoint_name: Human-readable name (e.g., "left_g2")
        x: X-coordinate in pixels
        y: Y-coordinate in pixels
        visibility: 0=not visible, 1=occluded, 2=visible
        confidence: Detection confidence (0.0 to 1.0)
        created_at: When this keypoint was detected
    """
    __tablename__ = "antler_keypoints"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for keypoint"
    )

    # Foreign key
    detection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Detection this keypoint belongs to"
    )

    # Keypoint data
    keypoint_index = Column(
        Integer,
        nullable=False,
        comment="Keypoint index (0-15)"
    )

    keypoint_name = Column(
        String(50),
        nullable=False,
        comment="Keypoint name (e.g., left_g2)"
    )

    x = Column(
        Float,
        nullable=False,
        comment="X-coordinate in pixels"
    )

    y = Column(
        Float,
        nullable=False,
        comment="Y-coordinate in pixels"
    )

    visibility = Column(
        Integer,
        nullable=False,
        default=2,
        comment="0=not visible, 1=occluded, 2=visible"
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Detection confidence (0.0 to 1.0)"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this keypoint was detected"
    )

    # Relationships
    detection = relationship(
        "Detection",
        backref="antler_keypoints",
        lazy="joined"
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "keypoint_index >= 0 AND keypoint_index <= 15",
            name="valid_keypoint_index"
        ),
        CheckConstraint(
            "visibility >= 0 AND visibility <= 2",
            name="valid_visibility"
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="valid_confidence"
        ),
        Index("ix_antler_keypoints_detection_id", "detection_id"),
        Index("ix_antler_keypoints_name", "keypoint_name"),
        {
            "comment": "Antler keypoint detections from YOLOv8-pose for enhanced buck Re-ID"
        }
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<AntlerKeypoint(id={self.id}, detection={self.detection_id}, "
            f"{self.keypoint_name}, x={self.x:.1f}, y={self.y:.1f})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Serializable representation of the keypoint
        """
        return {
            "id": str(self.id),
            "detection_id": str(self.detection_id),
            "keypoint_index": self.keypoint_index,
            "keypoint_name": self.keypoint_name,
            "x": self.x,
            "y": self.y,
            "visibility": self.visibility,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_yolo_result(
        cls,
        detection_id: uuid.UUID,
        keypoints: List[List[float]]
    ) -> List["AntlerKeypoint"]:
        """
        Create keypoint instances from YOLOv8-pose result.

        Args:
            detection_id: UUID of the parent detection
            keypoints: List of [x, y, visibility] from YOLO model

        Returns:
            List[AntlerKeypoint]: Keypoint instances ready to insert
        """
        instances = []
        for idx, kpt in enumerate(keypoints):
            if len(kpt) >= 2:  # Must have at least x, y
                x, y = kpt[0], kpt[1]
                visibility = int(kpt[2]) if len(kpt) >= 3 else 2

                # Skip keypoints with zero coordinates (not detected)
                if x == 0 and y == 0:
                    continue

                instance = cls(
                    detection_id=detection_id,
                    keypoint_index=idx,
                    keypoint_name=KEYPOINT_NAMES.get(idx, f"unknown_{idx}"),
                    x=float(x),
                    y=float(y),
                    visibility=visibility,
                    confidence=1.0  # YOLO pose doesn't provide per-keypoint confidence
                )
                instances.append(instance)

        return instances

    @staticmethod
    def get_keypoint_name(index: int) -> str:
        """
        Get keypoint name from index.

        Args:
            index: Keypoint index (0-15)

        Returns:
            str: Keypoint name
        """
        return KEYPOINT_NAMES.get(index, f"unknown_{index}")

    @property
    def is_visible(self) -> bool:
        """Check if keypoint is visible (not occluded)."""
        return self.visibility == 2

    @property
    def is_left_antler(self) -> bool:
        """Check if keypoint is on left antler."""
        return self.keypoint_name.startswith("left_")

    @property
    def is_right_antler(self) -> bool:
        """Check if keypoint is on right antler."""
        return self.keypoint_name.startswith("right_")

    @property
    def is_tine(self) -> bool:
        """Check if keypoint is a tine (not main beam or tip)."""
        return "tine" in self.keypoint_name or self.keypoint_name.endswith(("g2", "g3", "g4"))


class AntlerProcessingLog(Base):
    """
    Tracks antler detection processing status for all detections.

    Stores whether a detection has been processed for antler detection,
    including cases where no antlers were found. This prevents reprocessing
    and provides processing history.

    Relationships:
        - detection: The deer detection this log entry belongs to (one-to-one)

    Attributes:
        detection_id: Primary key and foreign key to Detection table
        processed_at: When antler detection was performed
        antlers_detected: Whether antlers were found (True) or not (False)
        keypoints_count: Number of keypoints saved (0-16)
        model_version: Version/name of the antler detection model used
        processing_notes: Optional notes about processing (errors, warnings)
    """
    __tablename__ = "antler_processing_log"

    # Primary key (also foreign key)
    detection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("detections.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Detection this log entry belongs to"
    )

    # Processing metadata
    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When antler detection was performed"
    )

    antlers_detected = Column(
        Boolean,
        nullable=False,
        comment="Whether antlers were detected (True=yes, False=no)"
    )

    keypoints_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of keypoints saved (typically 16 for success, 0 for none)"
    )

    model_version = Column(
        String(100),
        nullable=False,
        comment="Version/name of the antler detection model used"
    )

    processing_notes = Column(
        String,
        nullable=True,
        comment="Optional notes about processing (errors, warnings, quality issues)"
    )

    # Relationships
    detection = relationship(
        "Detection",
        backref="antler_processing_log",
        lazy="joined",
        uselist=False
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "keypoints_count >= 0",
            name="valid_keypoints_count"
        ),
        Index("idx_antler_processing_detected", "antlers_detected"),
        Index("idx_antler_processing_timestamp", "processed_at"),
        Index("idx_antler_processing_model", "model_version"),
        {
            "comment": "Tracks antler detection processing status including 'no antlers found' cases"
        }
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<AntlerProcessingLog(detection={self.detection_id}, "
            f"antlers_detected={bool(self.antlers_detected)}, "
            f"keypoints={self.keypoints_count}, "
            f"processed={self.processed_at})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Returns:
            dict: Serializable representation of the log entry
        """
        return {
            "detection_id": str(self.detection_id),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "antlers_detected": bool(self.antlers_detected),
            "keypoints_count": self.keypoints_count,
            "model_version": self.model_version,
            "processing_notes": self.processing_notes,
        }


# Export model and constants
__all__ = ["AntlerKeypoint", "AntlerProcessingLog", "KEYPOINT_NAMES"]
