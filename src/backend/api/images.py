"""
Images API router for trail camera image uploads and management.

Provides endpoints for uploading images, listing images with filters, and querying image details.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File,
    Form,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from backend.core.database import get_db
from backend.models.image import Image, ProcessingStatus
from backend.models.location import Location
from backend.schemas.image import (
    ImageUploadResponse,
    ImageResponse,
    ImageList,
    BatchUploadResponse,
)


# Create API router
router = APIRouter(
    prefix="/api/images",
    tags=["Images"],
)


# Configuration
IMAGE_STORAGE_PATH = os.getenv("IMAGE_PATH", "/mnt/images")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per spec
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def extract_exif_data(file_path: Path) -> dict:
    """
    Extract EXIF data from image file.

    Args:
        file_path: Path to image file

    Returns:
        dict: EXIF data as dictionary
    """
    try:
        image = PILImage.open(file_path)
        exif_data = {}

        # Get EXIF data if available
        if hasattr(image, '_getexif') and image._getexif():
            exif = image._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                # Convert bytes to string for JSON serialization
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except:
                        value = str(value)
                exif_data[tag] = value

        return exif_data
    except Exception as e:
        print(f"[WARN] Failed to extract EXIF data: {e}")
        return {}


def extract_timestamp_from_exif(exif_data: dict) -> Optional[datetime]:
    """
    Extract timestamp from EXIF data.

    Tries multiple EXIF timestamp fields in order of preference.

    Args:
        exif_data: EXIF data dictionary

    Returns:
        datetime: Timestamp or None if not found
    """
    # Try different EXIF timestamp fields
    timestamp_fields = [
        'DateTimeOriginal',
        'DateTime',
        'DateTimeDigitized',
    ]

    for field in timestamp_fields:
        if field in exif_data:
            try:
                # EXIF timestamp format: "2025:01:01 12:00:00"
                timestamp_str = exif_data[field]
                return datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")
            except (ValueError, TypeError):
                continue

    return None


def extract_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract timestamp from trail camera filename.

    Supports common formats like: SANCTUARY_YYYYMMDD_HHMMSS.jpg

    Args:
        filename: Image filename

    Returns:
        datetime: Timestamp or None if pattern doesn't match
    """
    try:
        # Remove extension
        name = Path(filename).stem

        # Try to find date pattern (YYYYMMDD)
        parts = name.split('_')
        for i, part in enumerate(parts):
            if len(part) == 8 and part.isdigit():
                # Found date, check for time in next part
                date_str = part
                time_str = '000000'  # Default to midnight

                if i + 1 < len(parts) and len(parts[i + 1]) == 6 and parts[i + 1].isdigit():
                    time_str = parts[i + 1]

                # Parse timestamp
                timestamp_str = f"{date_str}{time_str}"
                return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

        return None
    except Exception as e:
        print(f"[WARN] Failed to extract timestamp from filename: {e}")
        return None


def get_location_by_name_or_id(
    db: Session,
    location_name: Optional[str] = None,
    location_id: Optional[str] = None
) -> Optional[Location]:
    """
    Get location by name or ID.

    Args:
        db: Database session
        location_name: Location name (e.g., "Sanctuary")
        location_id: Location UUID

    Returns:
        Location: Location object or None
    """
    if location_id:
        try:
            from uuid import UUID
            uuid_obj = UUID(location_id)
            return db.query(Location).filter(Location.id == uuid_obj).first()
        except ValueError:
            return None

    if location_name:
        return db.query(Location).filter(Location.name == location_name).first()

    return None


@router.post(
    "",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload images",
    description="Upload one or more trail camera images with optional location assignment"
)
async def upload_images(
    files: List[UploadFile] = File(..., description="Image files to upload (max 50MB each)"),
    location_name: Optional[str] = Form(None, description="Location name (e.g., 'Sanctuary')"),
    location_id: Optional[str] = Form(None, description="Location UUID"),
    process_immediately: bool = Form(False, description="Queue for immediate processing"),
    db: Session = Depends(get_db)
) -> BatchUploadResponse:
    """
    Upload one or more trail camera images.

    Supports batch upload with automatic location detection from folder structure.
    Images are saved to disk, EXIF data is extracted, and records are created in database.

    Args:
        files: List of image files to upload
        location_name: Optional location name for all images
        location_id: Optional location UUID for all images
        process_immediately: Whether to queue images for immediate processing
        db: Database session

    Returns:
        BatchUploadResponse: Upload results with image IDs and queue positions

    Raises:
        HTTPException 400: Invalid file format or size
        HTTPException 404: Location not found
        HTTPException 413: File too large
    """
    uploaded_images = []
    errors = []
    location = None

    # Validate and get location if specified
    if location_name or location_id:
        location = get_location_by_name_or_id(db, location_name, location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location not found: {location_name or location_id}"
            )

    # Process each uploaded file
    for file in files:
        try:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                errors.append({
                    "filename": file.filename,
                    "error": f"Invalid file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
                })
                continue

            # Read file content
            content = await file.read()

            # Validate file size
            if len(content) > MAX_FILE_SIZE:
                errors.append({
                    "filename": file.filename,
                    "error": f"File too large: {len(content) / 1024 / 1024:.1f}MB (max 50MB)"
                })
                continue

            # Generate unique ID for image
            image_id = uuid.uuid4()

            # Determine storage path
            # If location is specified, use location name as subfolder
            if location:
                storage_dir = Path(IMAGE_STORAGE_PATH) / location.name
            else:
                storage_dir = Path(IMAGE_STORAGE_PATH) / "uploads"

            # Create directory if it doesn't exist
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with UUID to avoid collisions
            original_filename = file.filename
            file_path = storage_dir / f"{image_id}_{original_filename}"

            # Write file to disk
            with open(file_path, "wb") as f:
                f.write(content)

            print(f"[OK] Saved image: {file_path}")

            # Extract EXIF data
            exif_data = extract_exif_data(file_path)

            # Extract timestamp from EXIF or filename
            timestamp = extract_timestamp_from_exif(exif_data)
            if not timestamp:
                timestamp = extract_timestamp_from_filename(original_filename)
            if not timestamp:
                # Fall back to current time
                timestamp = datetime.utcnow()
                print(f"[WARN] No timestamp in EXIF or filename, using current time for {original_filename}")

            # Create image record in database
            image = Image(
                id=image_id,
                filename=original_filename,
                path=str(file_path),
                timestamp=timestamp,
                location_id=location.id if location else None,
                exif_data=exif_data,
                processing_status=ProcessingStatus.QUEUED if process_immediately else ProcessingStatus.PENDING
            )

            db.add(image)

            # Update location image count
            if location:
                location.increment_image_count()

            # Calculate queue position (simplified - count queued images)
            queue_position = None
            if process_immediately:
                queue_position = db.query(Image).filter(
                    Image.processing_status == ProcessingStatus.QUEUED
                ).count()

            # Prepare response
            uploaded_images.append(ImageUploadResponse(
                id=image.id,
                filename=image.filename,
                processing_status=image.processing_status.value,
                queue_position=queue_position,
                timestamp=image.timestamp,
                location_id=image.location_id
            ))

            print(f"[OK] Created image record: {image.id} ({original_filename})")

        except Exception as e:
            print(f"[ERROR] Failed to process {file.filename}: {e}")
            errors.append({
                "filename": file.filename,
                "error": f"Processing failed: {str(e)}"
            })
            continue

    # Commit all changes
    try:
        db.commit()
        print(f"[OK] Uploaded {len(uploaded_images)} images")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to commit uploads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save images to database"
        )

    return BatchUploadResponse(
        total_uploaded=len(uploaded_images),
        total_failed=len(errors),
        images=uploaded_images,
        errors=errors
    )


@router.get(
    "",
    response_model=ImageList,
    summary="List images",
    description="Retrieve images with optional filtering by location, status, and date range"
)
def list_images(
    location_id: Optional[str] = Query(
        None,
        description="Filter by location UUID"
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by processing status (pending, queued, processing, completed, failed)"
    ),
    date_from: Optional[datetime] = Query(
        None,
        description="Filter images taken on or after this date (ISO 8601 format)"
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="Filter images taken on or before this date (ISO 8601 format)"
    ),
    has_detections: Optional[bool] = Query(
        None,
        description="Filter by whether images have detections (true/false)"
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of images per page (max 100)"
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of images to skip (for pagination)"
    ),
    db: Session = Depends(get_db)
) -> ImageList:
    """
    List images with optional filtering.

    Args:
        location_id: Filter by location UUID
        status_filter: Filter by processing status
        date_from: Filter by minimum timestamp
        date_to: Filter by maximum timestamp
        has_detections: Filter by detection presence
        page_size: Number of results per page
        skip: Number of results to skip
        db: Database session

    Returns:
        ImageList: Paginated list of images with total count

    Raises:
        HTTPException 400: Invalid filter parameters
    """
    try:
        # Build base query
        query = db.query(Image)

        # Apply location filter
        if location_id:
            try:
                from uuid import UUID
                uuid_obj = UUID(location_id)
                query = query.filter(Image.location_id == uuid_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid UUID format: {location_id}"
                )

        # Apply status filter
        if status_filter:
            try:
                status_enum = ProcessingStatus[status_filter.upper()]
                query = query.filter(Image.processing_status == status_enum)
            except KeyError:
                valid_statuses = [s.value for s in ProcessingStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. Valid values: {', '.join(valid_statuses)}"
                )

        # Apply date range filters
        if date_from:
            query = query.filter(Image.timestamp >= date_from)

        if date_to:
            query = query.filter(Image.timestamp <= date_to)

        # Apply detection filter (requires join with detections table)
        if has_detections is not None:
            from backend.models.detection import Detection
            if has_detections:
                # Has at least one detection
                query = query.join(Detection).distinct()
            else:
                # Has no detections (left outer join with filter)
                query = query.outerjoin(Detection).filter(Detection.id.is_(None))

        # Get total count before pagination
        total = query.count()

        # Order by timestamp descending (most recent first) and apply pagination
        images = (
            query.order_by(Image.timestamp.desc())
            .offset(skip)
            .limit(page_size)
            .all()
        )

        # Convert to response models and add detection count
        image_responses = []
        for img in images:
            # Count detections for each image
            detection_count = img.detections.count() if img.is_processed else None

            img_response = ImageResponse(
                id=img.id,
                filename=img.filename,
                path=img.path,
                timestamp=img.timestamp,
                location_id=img.location_id,
                exif_data=img.exif_data,
                processing_status=img.processing_status.value,
                created_at=img.created_at,
                detection_count=detection_count
            )
            image_responses.append(img_response)

        return ImageList(
            total=total,
            images=image_responses,
            page_size=page_size,
            skip=skip
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to list images: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve images"
        )


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    summary="Get image by ID",
    description="Retrieve a specific image by its UUID"
)
def get_image(
    image_id: str,
    db: Session = Depends(get_db)
) -> ImageResponse:
    """
    Get a specific image by ID.

    Args:
        image_id: Image UUID
        db: Database session

    Returns:
        ImageResponse: Image details

    Raises:
        HTTPException 404: Image not found
        HTTPException 400: Invalid UUID format
    """
    try:
        # Validate UUID format
        from uuid import UUID
        try:
            uuid_obj = UUID(image_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format: {image_id}"
            )

        # Query image
        image = db.query(Image).filter(Image.id == uuid_obj).first()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {image_id}"
            )

        # Count detections
        detection_count = image.detections.count() if image.is_processed else None

        return ImageResponse(
            id=image.id,
            filename=image.filename,
            path=image.path,
            timestamp=image.timestamp,
            location_id=image.location_id,
            exif_data=image.exif_data,
            processing_status=image.processing_status.value,
            created_at=image.created_at,
            detection_count=detection_count
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image"
        )


# Export router
__all__ = ["router"]
