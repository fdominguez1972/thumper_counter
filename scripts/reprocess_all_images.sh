#!/bin/bash
# Reprocess entire dataset with new YOLOv8 model
# Created: 2025-11-11
# Purpose: Apply newly trained model to all images for improved classification
# Author: Claude Code

set -e

echo "======================================================================"
echo "FULL DATASET REPROCESSING WITH NEW MODEL"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Mark all completed images as 'pending' to force reprocessing"
echo "  2. Clear old detections (optional - recommended for clean slate)"
echo "  3. Queue all images in batches for processing"
echo "  4. Monitor processing progress"
echo ""
echo "New Model Details:"
echo "  - Model: corrected_final_buck_doe"
echo "  - Accuracy: mAP50=0.851 (85.1%)"
echo "  - Classes: buck, doe, fawn, cattle, pig, raccoon"
echo "  - Training Data: 779 manually corrected images"
echo ""
echo "======================================================================"
echo ""

# Database connection details
PGHOST="${POSTGRES_HOST:-db}"
PGPORT="${POSTGRES_PORT:-5432}"
PGUSER="${POSTGRES_USER:-deertrack}"
PGPASSWORD="${POSTGRES_PASSWORD:-secure_password_here}"
PGDATABASE="${POSTGRES_DB:-deer_tracking}"

export PGPASSWORD

# Ask for confirmation
read -p "This will reprocess ALL 35,251 images. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "[INFO] Aborted by user"
    exit 0
fi

# Ask about clearing old detections
echo ""
echo "Options for existing detections:"
echo "  1. Keep old detections (new detections will be added)"
echo "  2. Clear ALL old detections (recommended for clean comparison)"
echo "  3. Clear only non-reviewed detections (preserve manual corrections)"
echo ""
read -p "Choose option [1-3]: " -n 1 -r CLEAR_OPTION
echo
echo ""

# Step 1: Clear old detections (if requested)
if [ "$CLEAR_OPTION" = "2" ]; then
    echo "[INFO] Clearing ALL old detections..."
    docker-compose exec -T db psql -U $PGUSER $PGDATABASE <<EOF
    -- Backup counts before deletion
    SELECT
        'Before deletion' as status,
        COUNT(*) as total_detections,
        COUNT(CASE WHEN is_reviewed = true THEN 1 END) as reviewed_count
    FROM detections;

    -- Delete all detections
    DELETE FROM detections;

    -- Reset deer profiles
    UPDATE deer SET sighting_count = 0;

    -- Show results
    SELECT '[OK] Deleted all detections' as result;
EOF
    echo "[OK] All detections cleared"
    echo ""

elif [ "$CLEAR_OPTION" = "3" ]; then
    echo "[INFO] Clearing non-reviewed detections only..."
    docker-compose exec -T db psql -U $PGUSER $PGDATABASE <<EOF
    -- Backup counts before deletion
    SELECT
        'Before deletion' as status,
        COUNT(*) as total_detections,
        COUNT(CASE WHEN is_reviewed = true THEN 1 END) as reviewed_count,
        COUNT(CASE WHEN is_reviewed = false OR is_reviewed IS NULL THEN 1 END) as to_delete
    FROM detections;

    -- Delete non-reviewed detections
    DELETE FROM detections
    WHERE is_reviewed = false OR is_reviewed IS NULL;

    -- Update deer sighting counts
    UPDATE deer d
    SET sighting_count = (
        SELECT COUNT(*)
        FROM detections det
        WHERE det.deer_id = d.id AND det.is_valid = true
    );

    -- Show results
    SELECT
        'After deletion' as status,
        COUNT(*) as total_detections,
        COUNT(CASE WHEN is_reviewed = true THEN 1 END) as reviewed_count
    FROM detections;
EOF
    echo "[OK] Non-reviewed detections cleared"
    echo ""
else
    echo "[INFO] Keeping all existing detections"
    echo ""
fi

# Step 2: Reset image processing status
echo "[INFO] Resetting image processing status..."
docker-compose exec -T db psql -U $PGUSER $PGDATABASE <<EOF
-- Show current status counts
SELECT
    'Before reset' as status,
    processing_status,
    COUNT(*) as count
FROM images
GROUP BY processing_status
ORDER BY processing_status;

-- Reset all completed/failed images to pending
UPDATE images
SET processing_status = 'pending',
    processed_at = NULL,
    error_message = NULL
WHERE processing_status IN ('completed', 'failed');

-- Show new status counts
SELECT
    'After reset' as status,
    processing_status,
    COUNT(*) as count
FROM images
GROUP BY processing_status
ORDER BY processing_status;
EOF
echo "[OK] Image statuses reset to pending"
echo ""

# Step 3: Queue images for processing
echo "[INFO] Queuing images for processing..."
echo "[INFO] This will queue in batches of 10,000 images"
echo ""

BATCH_SIZE=10000
TOTAL_BATCHES=4  # 35,251 images / 10,000 = ~4 batches

for i in $(seq 1 $TOTAL_BATCHES); do
    echo "[INFO] Queuing batch $i/$TOTAL_BATCHES..."

    RESPONSE=$(curl -s -X POST "http://localhost:8001/api/processing/batch?limit=$BATCH_SIZE")
    QUEUED=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('queued_count', 0))")

    echo "  [OK] Queued: $QUEUED images"

    # If no more images to queue, stop
    if [ "$QUEUED" -eq "0" ]; then
        echo "[INFO] No more images to queue"
        break
    fi

    # Brief pause between batches
    sleep 2
done

echo ""
echo "[OK] All images queued for processing"
echo ""

# Step 4: Show processing status
echo "======================================================================"
echo "PROCESSING STATUS"
echo "======================================================================"
echo ""

curl -s "http://localhost:8001/api/processing/status" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Images: {data['total_images']:,d}\")
print(f\"Completed: {data['completed_images']:,d} ({data['completion_rate']:.1f}%)\")
print(f\"Pending: {data['pending_images']:,d}\")
print(f\"Processing: {data['processing_images']:,d}\")
print(f\"Failed: {data['failed_images']:,d}\")
print(f\"\")
print(f\"Queue Status:\")
print(f\"  Total Tasks: {data['queue_status']['total_tasks']:,d}\")
print(f\"  Active Tasks: {data['queue_status']['active_tasks']:,d}\")
print(f\"\")
if data['completion_rate'] > 0:
    remaining = data['total_images'] - data['completed_images']
    # Estimate based on 840 images/min from previous session
    throughput = 840  # images per minute
    eta_minutes = remaining / throughput
    eta_hours = eta_minutes / 60
    print(f\"Estimated Time: {eta_hours:.1f} hours ({eta_minutes:.0f} minutes)\")
    print(f\"  (Based on 840 images/min throughput)\")
"

echo ""
echo "======================================================================"
echo "MONITORING"
echo "======================================================================"
echo ""
echo "Monitor processing progress:"
echo "  1. API Status: curl http://localhost:8001/api/processing/status"
echo "  2. Worker Logs: docker-compose logs -f worker | grep 'Detection complete'"
echo "  3. Flower UI: http://localhost:5555"
echo "  4. GPU Usage: docker stats worker"
echo ""
echo "Expected Throughput:"
echo "  - 840 images/minute (14 images/second)"
echo "  - Full dataset (35,251 images): ~42 minutes"
echo ""
echo "[OK] Reprocessing started successfully!"
echo ""
