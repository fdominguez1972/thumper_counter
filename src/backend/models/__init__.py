"""
SQLAlchemy models for Thumper Counter.

This module imports all database models to ensure they are registered
with SQLAlchemy's Base metadata. This is required for:
- Automatic table creation via Base.metadata.create_all()
- Alembic migration generation
- Proper relationship resolution between models

Import order matters: models without foreign keys first, then dependent models.
"""

# Import Base first (required for all models)
from backend.core.database import Base

# Import models without foreign key dependencies
from backend.models.location import Location
from backend.models.deer import Deer, DeerSex

# Import models with foreign key dependencies
from backend.models.image import Image, ProcessingStatus
from backend.models.detection import Detection


# Export all models and enums for easy access
__all__ = [
    # Base
    "Base",

    # Models
    "Location",
    "Image",
    "Deer",
    "Detection",

    # Enums
    "ProcessingStatus",
    "DeerSex",
]
