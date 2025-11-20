"""
Static File Serving for Images
Serves original images and thumbnails
"""

import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Depends
from fastapi.responses import FileResponse
from PIL import Image as PILImage
from sqlalchemy.orm import Session
import io

from backend.core.database import get_db
from backend.models.image import Image

router = APIRouter(prefix="/api/static", tags=["Static Files"])

# Image directories
IMAGE_PATH = Path(os.getenv('IMAGE_PATH', '/mnt/images'))
UPLOAD_PATH = Path(os.getenv('UPLOAD_PATH', '/mnt/uploads'))
THUMBNAIL_PATH = Path(os.getenv('THUMBNAIL_PATH', '/mnt/thumbnails'))
EXPORT_PATH = Path('/mnt/exports')

# Create directories if they don't exist
THUMBNAIL_PATH.mkdir(parents=True, exist_ok=True)
EXPORT_PATH.mkdir(parents=True, exist_ok=True)


def generate_thumbnail(image_path: Path, thumbnail_path: Path, size: tuple = (300, 300)) -> Path:
    """
    Generate a thumbnail for an image if it doesn't exist.

    Args:
        image_path: Path to original image
        thumbnail_path: Path to save thumbnail
        size: Thumbnail dimensions (width, height)

    Returns:
        Path to thumbnail
    """
    if thumbnail_path.exists():
        return thumbnail_path

    try:
        # Create thumbnail directory if needed
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

        # Open and resize image
        with PILImage.open(image_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Use thumbnail() to preserve aspect ratio
            img.thumbnail(size, PILImage.Resampling.LANCZOS)

            # Save thumbnail as JPEG
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

        return thumbnail_path
    except Exception as e:
        print(f"[ERROR] Failed to generate thumbnail for {image_path}: {e}")
        raise


@router.get(
    "/images/{image_id}",
    response_class=FileResponse,
    summary="Serve original image",
    description="Returns the original full-resolution image file"
)
async def serve_image(
    image_id: str = FastAPIPath(..., description="Image UUID"),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    Serve an original image file by looking up the path in the database.
    """
    try:
        uuid_obj = UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID format")

    # Look up image in database
    image = db.query(Image).filter(Image.id == uuid_obj).first()
    if not image:
        raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")

    # Check if file exists
    image_path = Path(image.path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Image file not found at path: {image.path}")

    return FileResponse(
        image_path,
        media_type='image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=86400',  # Cache for 24 hours
        }
    )


@router.get(
    "/thumbnails/{image_id}",
    response_class=FileResponse,
    summary="Serve image thumbnail",
    description="Returns a thumbnail version of the image (300x300)"
)
async def serve_thumbnail(
    image_id: str = FastAPIPath(..., description="Image UUID"),
    db: Session = Depends(get_db),
    size: Optional[int] = 300
) -> FileResponse:
    """
    Serve an image thumbnail, generating it if necessary.

    Thumbnails are cached in THUMBNAIL_PATH for fast serving.
    """
    # Limit thumbnail size
    if size > 600:
        size = 600

    try:
        uuid_obj = UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID format")

    # Look up image in database
    image = db.query(Image).filter(Image.id == uuid_obj).first()
    if not image:
        raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")

    # Check if original file exists
    original_path = Path(image.path)
    if not original_path.exists():
        raise HTTPException(status_code=404, detail=f"Image file not found at path: {image.path}")

    # Generate thumbnail path
    thumbnail_filename = f"{image_id}_{size}.jpg"
    thumbnail_path = THUMBNAIL_PATH / thumbnail_filename

    try:
        # Generate thumbnail if it doesn't exist
        generate_thumbnail(original_path, thumbnail_path, size=(size, size))

        return FileResponse(
            thumbnail_path,
            media_type='image/jpeg',
            headers={
                'Cache-Control': 'public, max-age=86400',  # Cache for 24 hours
            }
        )
    except Exception as e:
        print(f"[ERROR] Failed to serve thumbnail: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")


@router.get(
    "/exports/{filename}",
    response_class=FileResponse,
    summary="Download export file",
    description="Download generated PDF report or ZIP archive"
)
async def serve_export_file(
    filename: str = FastAPIPath(..., description="Export filename (PDF or ZIP)")
) -> FileResponse:
    """
    Serve an export file (PDF report or ZIP archive).

    Export files are auto-generated by async tasks and stored temporarily.
    PDF files expire after 24 hours, ZIP files after 7 days.
    """
    # Sanitize filename to prevent directory traversal
    filename = Path(filename).name

    # Check if file exists
    file_path = EXPORT_PATH / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Export file not found: {filename}")

    # Determine media type based on extension
    if filename.endswith('.pdf'):
        media_type = 'application/pdf'
        content_disposition = f'attachment; filename="{filename}"'
    elif filename.endswith('.zip'):
        media_type = 'application/zip'
        content_disposition = f'attachment; filename="{filename}"'
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            'Content-Disposition': content_disposition,
            'Cache-Control': 'no-cache',  # Don't cache export files
        }
    )
