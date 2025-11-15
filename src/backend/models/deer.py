"""
Deer model for individual tracking.

Stores deer profiles with feature vectors for ML-based re-identification.
Based on specs/system.spec Deer data model definition.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from backend.core.database import Base


class DeerSex(enum.Enum):
    """
    Sex classification for deer.

    Classifications are determined by the ML classification model
    based on visual characteristics (antlers, body size, etc.)
    """
    BUCK = "buck"          # Male deer (typically has antlers)
    DOE = "doe"            # Female deer
    FAWN = "fawn"          # Young deer (sex not yet determinable)
    UNKNOWN = "unknown"    # Sex could not be determined


# Aliases for API compatibility (Sprint 3)
Sex = DeerSex  # API uses Sex, model uses DeerSex


class DeerStatus(enum.Enum):
    """
    Status of deer (alive/deceased/unknown).

    Used for population tracking and management.
    """
    ALIVE = "alive"
    DECEASED = "deceased"
    UNKNOWN = "unknown"


class Deer(Base):
    """
    Individual deer profile with re-identification tracking.

    Each record represents a unique deer that has been identified by the
    ML pipeline. The feature_vector enables matching new detections to
    existing deer through similarity comparison (cosine similarity).

    The re-identification process:
    1. Detection finds deer in image
    2. Classification determines sex
    3. ResNet50 extracts feature vector (embedding)
    4. Compare embedding to all known deer
    5. If match found (similarity > threshold), update existing deer
    6. If no match, create new deer profile

    Relationships:
        - detections: All detections matched to this deer (one-to-many)

    Attributes:
        id: Unique identifier (UUID)
        name: Optional human-assigned name (e.g., "Big Buck", "Spike")
        sex: Classification (buck/doe/fawn/unknown)
        first_seen: Timestamp of first detection
        last_seen: Timestamp of most recent detection
        feature_vector: ML embedding for re-identification (ResNet50 output)
        confidence: Average confidence score for this deer identity
        sighting_count: Total number of detections matched to this deer
    """
    __tablename__ = "deer"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for deer"
    )

    # Optional identification
    name = Column(
        String(100),
        nullable=True,
        comment="Optional human-assigned name (e.g., 'Big Buck', 'Spike')"
    )

    # Classification
    sex = Column(
        Enum(DeerSex, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DeerSex.UNKNOWN,
        index=True,
        comment="Sex classification from ML model"
    )

    # Additional management fields (Sprint 3)
    status = Column(
        Enum(DeerStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DeerStatus.ALIVE,
        index=True,
        comment="Current status (alive, deceased, unknown)"
    )

    species = Column(
        String(100),
        nullable=False,
        default="white_tailed_deer",
        comment="Species identifier (white_tailed_deer, mule_deer, etc.)"
    )

    notes = Column(
        String(1000),
        nullable=True,
        comment="Additional notes and observations"
    )

    # Timestamps (Sprint 3)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this deer record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
        comment="When this deer record was last updated"
    )

    # Temporal tracking
    first_seen = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Timestamp of first detection"
    )

    last_seen = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Timestamp of most recent detection"
    )

    # Re-identification features (Sprint 5: Using pgvector for efficient similarity search)
    feature_vector = Column(
        Vector(512),  # ResNet50 outputs 512-dim embeddings
        nullable=True,  # Optional for manually created profiles
        comment="ML embedding for re-identification (ResNet50 output, 512 dimensions)"
    )

    # Feature 009: Enhanced Re-ID with multi-scale and ensemble embeddings
    feature_vector_multiscale = Column(
        Vector(512),  # Multi-scale ResNet50 (layer2 + layer3 + layer4 + avgpool)
        nullable=True,
        comment="Multi-scale ResNet50 embedding combining texture, shapes, parts, and semantics. 512 dimensions, L2 normalized. Feature 009-reid-enhancement."
    )

    feature_vector_efficientnet = Column(
        Vector(512),  # EfficientNet-B0 for ensemble learning
        nullable=True,
        comment="EfficientNet-B0 embedding for ensemble learning. Captures complementary features using compound scaling architecture. 512 dimensions, L2 normalized. Feature 009-reid-enhancement."
    )

    embedding_version = Column(
        String(20),
        nullable=False,
        default='v1_resnet50',
        comment="Version identifier for embedding extraction. Values: v1_resnet50 (original), v2_multiscale (multi-scale only), v3_ensemble (multi-scale + EfficientNet). Feature 009-reid-enhancement."
    )

    confidence = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Average confidence score for this deer identity (0.0 to 1.0)"
    )

    # Statistics
    sighting_count = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Total number of detections matched to this deer"
    )

    # Best photo reference (Sprint 7: UI image display)
    best_photo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the best quality photo of this deer"
    )

    # Relationships
    detections = relationship(
        "Detection",
        back_populates="deer",
        lazy="dynamic"
    )

    best_photo = relationship(
        "Image",
        foreign_keys=[best_photo_id],
        lazy="joined"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_deer_last_seen_sex", "last_seen", "sex"),
        Index("ix_deer_sighting_count", "sighting_count"),
        # HNSW index for fast vector similarity search (Sprint 5)
        # Uses cosine distance for re-identification matching
        Index("ix_deer_feature_vector_hnsw", "feature_vector", postgresql_using="hnsw", postgresql_ops={"feature_vector": "vector_cosine_ops"}),
        # Feature 009: HNSW indexes for enhanced Re-ID embeddings
        Index("ix_deer_feature_vector_multiscale_hnsw", "feature_vector_multiscale", postgresql_using="hnsw", postgresql_ops={"feature_vector_multiscale": "vector_cosine_ops"}),
        Index("ix_deer_feature_vector_efficientnet_hnsw", "feature_vector_efficientnet", postgresql_using="hnsw", postgresql_ops={"feature_vector_efficientnet": "vector_cosine_ops"}),
        Index("ix_deer_embedding_version", "embedding_version"),
        {"comment": "Individual deer profiles with re-identification tracking"}
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        name_str = f"'{self.name}'" if self.name else "unnamed"
        return (
            f"<Deer(id={self.id}, name={name_str}, sex={self.sex.value}, "
            f"sightings={self.sighting_count})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model to dictionary for API responses.

        Note: feature_vector is excluded by default as it's large (2048 floats).
        Use include_features=True if needed.

        Returns:
            dict: Serializable representation of the deer
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "sex": self.sex.value,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "confidence": self.confidence,
            "sighting_count": self.sighting_count,
        }

    def to_dict_with_features(self) -> dict:
        """
        Convert model to dictionary including feature vector.

        Returns:
            dict: Complete representation including feature vector
        """
        data = self.to_dict()
        data["feature_vector"] = self.feature_vector
        return data

    @property
    def is_named(self) -> bool:
        """Check if deer has been given a name."""
        return self.name is not None and len(self.name.strip()) > 0

    @property
    def days_since_last_seen(self) -> int:
        """
        Calculate days since last sighting.

        Returns:
            int: Number of days since last_seen timestamp
        """
        if not self.last_seen:
            return 0
        delta = datetime.utcnow() - self.last_seen.replace(tzinfo=None)
        return delta.days

    @property
    def feature_dimension(self) -> int:
        """
        Get dimensionality of feature vector.

        Returns:
            int: Number of dimensions in feature_vector
        """
        return len(self.feature_vector) if self.feature_vector else 0

    def update_sighting(self, timestamp: datetime, confidence: float) -> None:
        """
        Update deer record with new sighting.

        This should be called when a detection is matched to this deer.
        Updates last_seen timestamp, increments sighting count, and
        recalculates average confidence.

        Args:
            timestamp: When the deer was detected
            confidence: Confidence score for this detection (0.0 to 1.0)
        """
        # Update temporal tracking
        if not self.first_seen or timestamp < self.first_seen:
            self.first_seen = timestamp
        if not self.last_seen or timestamp > self.last_seen:
            self.last_seen = timestamp

        # Update statistics with running average
        total_confidence = self.confidence * self.sighting_count
        self.sighting_count += 1
        self.confidence = (total_confidence + confidence) / self.sighting_count

    def set_name(self, name: str) -> None:
        """
        Assign a human-readable name to this deer.

        Args:
            name: Name to assign (e.g., "Big Buck", "Spike")
        """
        self.name = name.strip() if name else None

    def update_sex(self, new_sex: DeerSex) -> None:
        """
        Update sex classification.

        This may be called if a fawn grows up and sex becomes determinable,
        or if classification model improves identification.

        Args:
            new_sex: Updated sex classification
        """
        self.sex = new_sex

    def cosine_similarity(self, other_vector: List[float]) -> float:
        """
        Calculate cosine similarity between this deer's feature vector and another.

        Used for re-identification: comparing a new detection's embedding
        against known deer to find matches.

        Args:
            other_vector: Feature vector to compare against

        Returns:
            float: Similarity score (0.0 to 1.0, higher = more similar)
        """
        if not self.feature_vector or not other_vector:
            return 0.0

        if len(self.feature_vector) != len(other_vector):
            raise ValueError(
                f"Vector dimension mismatch: {len(self.feature_vector)} vs {len(other_vector)}"
            )

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(self.feature_vector, other_vector))

        # Calculate magnitudes
        magnitude_a = sum(a * a for a in self.feature_vector) ** 0.5
        magnitude_b = sum(b * b for b in other_vector) ** 0.5

        # Avoid division by zero
        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0

        # Cosine similarity
        similarity = dot_product / (magnitude_a * magnitude_b)

        # Clamp to [0, 1] range (should already be in [-1, 1], map to [0, 1])
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0))

    def get_recent_detections(self, limit: int = 10):
        """
        Get most recent detections for this deer.

        Args:
            limit: Maximum number of detections to return

        Returns:
            Query: SQLAlchemy query for recent detections (not executed)
        """
        from backend.models.detection import Detection
        return (
            self.detections
            .join(Detection.image)
            .order_by(Detection.image.timestamp.desc())
            .limit(limit)
        )

    def get_detection_locations(self, db_session) -> List[dict]:
        """
        Get unique locations where this deer has been detected.

        Args:
            db_session: SQLAlchemy session

        Returns:
            List[dict]: Location information with sighting counts
        """
        from sqlalchemy import func
        from backend.models.detection import Detection
        from backend.models.image import Image
        from backend.models.location import Location

        results = (
            db_session.query(
                Location.name,
                Location.id,
                func.count(Detection.id).label("count")
            )
            .join(Image, Detection.image_id == Image.id)
            .join(Location, Image.location_id == Location.id)
            .filter(Detection.deer_id == self.id)
            .group_by(Location.id, Location.name)
            .order_by(func.count(Detection.id).desc())
            .all()
        )

        return [
            {
                "location_name": r.name,
                "location_id": str(r.id),
                "sighting_count": r.count
            }
            for r in results
        ]


# Export model and enums
__all__ = ["Deer", "DeerSex", "Sex", "DeerStatus"]
