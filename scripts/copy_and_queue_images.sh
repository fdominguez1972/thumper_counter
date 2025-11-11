#!/bin/bash
# Copy new trail camera images and queue them for processing
# This script runs on the HOST, not in a container

set -e

SOURCE_BASE="/mnt/i/Hopkins_Ranch_Trail_Cam_Dumps"
TARGET_BASE="/mnt/i/Hopkins_Ranch_Trail_Cam_Pics"

echo "[INFO] Starting image copy and queue process..."
echo "[INFO] Source: $SOURCE_BASE"
echo "[INFO] Target: $TARGET_BASE"
echo ""

# Process each location
for LOCATION in "270_Jason" "Hayfield" "Sanctuary"; do
    SOURCE_DIR="$SOURCE_BASE/$LOCATION"
    TARGET_DIR="$TARGET_BASE/$LOCATION"

    if [ ! -d "$SOURCE_DIR" ]; then
        echo "[WARN] Source directory not found: $SOURCE_DIR"
        continue
    fi

    echo "=== Processing: $LOCATION ==="

    # Create target directory if needed
    mkdir -p "$TARGET_DIR"

    # Count images in source
    IMAGE_COUNT=$(find "$SOURCE_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" \) | wc -l)
    echo "[INFO] Found $IMAGE_COUNT images in $SOURCE_DIR"

    # Copy images (preserving timestamps)
    echo "[INFO] Copying images to $TARGET_DIR..."
    rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/" \
        --include="*.jpg" --include="*.JPG" --include="*.jpeg" --include="*.JPEG" \
        --exclude="*"

    echo "[OK] Copied images for $LOCATION"
    echo ""
done

echo "============================================================"
echo "COPY COMPLETE"
echo "============================================================"
echo ""
echo "Next step: Use the API to import these images into the database"
echo "The bulk upload feature (Feature 009) will handle this via web interface"
echo ""
echo "For now, you can queue existing images using:"
echo "  curl -X POST http://localhost:8001/api/processing/batch?limit=25000"
