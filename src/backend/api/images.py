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
from backend.models.detection import Detection
from backend.schemas.image import (
    ImageUploadResponse,
    ImageResponse,
    ImageList,
    BatchUploadResponse,
)
from celery import Celery

# Create minimal Celery app for task queueing (no worker dependencies)
# WHY: Backend needs to queue tasks but cannot import worker modules (ultralytics/cv2)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

celery_app = Celery('thumper_counter', broker=REDIS_URL, backend=REDIS_URL)


# Create API router
router = APIRouter(
    prefix="/api/images",
    tags=["Images"],
)


# Configuration
IMAGE_STORAGE_PATH = os.getenv("IMAGE_PATH", "/mnt/images")  # Read-only source images
UPLOAD_STORAGE_PATH = os.getenv("UPLOAD_PATH", "/mnt/uploads")  # Writable upload storage
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
                storage_dir = Path(UPLOAD_STORAGE_PATH) / location.name
            else:
                storage_dir = Path(UPLOAD_STORAGE_PATH) / "uploads"

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
            # All images start as PENDING per spec (FR-004)
            image = Image(
                id=image_id,
                filename=original_filename,
                path=str(file_path),
                timestamp=timestamp,
                location_id=location.id if location else None,
                exif_data=exif_data,
                processing_status=ProcessingStatus.PENDING
            )

            db.add(image)

            # Update location image count
            if location:
                location.increment_image_count()

            # Prepare response
            uploaded_images.append(ImageUploadResponse(
                id=image.id,
                filename=image.filename,
                processing_status=image.processing_status.value,
                queue_position=None,  # Removed: queue position not tracked in new design
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

    # Queue images for immediate processing if requested (T007 - FR-002)
    if process_immediately and uploaded_images:
        print(f"[INFO] Queueing {len(uploaded_images)} images for immediate processing")

        # Queue tasks by name using send_task() to avoid importing worker dependencies
        # WHY: Backend cannot import worker modules (ultralytics/cv2 require GPU libraries)
        for img_response in uploaded_images:
            try:
                # Queue Celery task for detection by name (no import needed)
                task = celery_app.send_task(
                    'worker.tasks.detection.detect_deer_task',
                    args=[str(img_response.id)],
                    queue='ml_processing'  # Route to ML processing queue
                )
                print(f"[OK] Queued detection task {task.id} for image {img_response.id}")
            except Exception as e:
                print(f"[ERROR] Failed to queue task for image {img_response.id}: {e}")
                # Don't fail the upload if queueing fails - image is still saved
                # User can trigger processing later via batch endpoint

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
        description="Filter by processing status (pending, processing, completed, failed)"
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
    classification: Optional[str] = Query(
        None,
        description="Filter by detection classification (buck/doe/fawn/unknown/cattle/pig). Uses corrected_classification if available, otherwise ML classification."
    ),
    show_duplicates: Optional[bool] = Query(
        None,
        description="Filter duplicate images (same location and timestamp within 1 second). True=only duplicates, False=exclude duplicates, None=all"
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
        classification: Filter by detection classification
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
                # Has at least one detection - use EXISTS to avoid DISTINCT with JSON
                from sqlalchemy import exists, select
                detection_exists = (
                    select(1)
                    .select_from(Detection)
                    .where(Detection.image_id == Image.id)
                )
                query = query.filter(exists(detection_exists))
            else:
                # Has no detections (left outer join with filter)
                query = query.outerjoin(Detection).filter(Detection.id.is_(None))

        # Apply classification filter
        if classification:
            from backend.models.detection import Detection
            from sqlalchemy import or_, func, exists, select

            # Use EXISTS subquery to avoid DISTINCT issues with JSON columns
            # This filters images that have at least one detection with matching classification
            classification_subquery = (
                select(1)
                .select_from(Detection)
                .where(Detection.image_id == Image.id)
                .where(func.coalesce(Detection.corrected_classification, Detection.classification) == classification.lower())
            )
            query = query.filter(exists(classification_subquery))

        # Apply duplicate filter
        if show_duplicates is not None:
            from sqlalchemy import func, exists, select, and_

            # Create alias for self-join
            ImageAlias = Image.__table__.alias('img_dup')

            # Find images with same location_id and timestamp within 1 second
            duplicate_subquery = (
                select(1)
                .select_from(ImageAlias)
                .where(and_(
                    Image.location_id == ImageAlias.c.location_id,
                    func.date_trunc('second', Image.timestamp) == func.date_trunc('second', ImageAlias.c.timestamp),
                    Image.id != ImageAlias.c.id
                ))
            )

            if show_duplicates:
                # Show only images that have duplicates
                query = query.filter(exists(duplicate_subquery))
            else:
                # Exclude images that have duplicates
                query = query.filter(~exists(duplicate_subquery))

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
        from backend.schemas.image import DetectionSummary
        image_responses = []
        for img in images:
            # Get detections for each image
            detections_list = []
            if img.is_processed:
                detection_count = img.detections.count()
                # Get detections and convert to summaries
                for det in img.detections:
                    detections_list.append(DetectionSummary(
                        id=det.id,
                        classification=det.classification,
                        corrected_classification=det.corrected_classification,
                        confidence=det.confidence,
                        is_valid=det.is_valid,
                        is_reviewed=det.is_reviewed
                    ))
            else:
                detection_count = None

            img_response = ImageResponse(
                id=img.id,
                filename=img.filename,
                path=img.path,
                timestamp=img.timestamp,
                location_id=img.location_id,
                exif_data=img.exif_data,
                processing_status=img.processing_status.value,
                created_at=img.created_at,
                detection_count=detection_count,
                detections=detections_list
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


@router.get("/classifications")
def get_classifications(db: Session = Depends(get_db)) -> dict:
    """
    Get all unique classification values for filtering.

    Returns both ML classifications and corrected classifications
    to populate the filter dropdown with all available options,
    including custom tags like 'human', 'vehicle', etc.

    Returns:
        Dictionary with list of unique classification values
    """
    try:
        # Get unique ML classifications
        ml_classifications = db.query(Detection.classification).distinct().all()
        ml_set = {c[0] for c in ml_classifications if c[0]}

        # Get unique corrected classifications
        corrected_classifications = db.query(Detection.corrected_classification).distinct().all()
        corrected_set = {c[0] for c in corrected_classifications if c[0]}

        # Combine and sort
        all_classifications = sorted(ml_set | corrected_set)

        return {
            "classifications": all_classifications,
            "count": len(all_classifications)
        }

    except Exception as e:
        print(f"[ERROR] Failed to get classifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classifications"
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
