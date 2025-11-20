#!/bin/bash
# Deploy new trained model
# Created: 2025-11-11
# Author: Claude Code

set -e

echo "======================================================================="
echo "Deploying New YOLOv8 Model"
echo "======================================================================="
echo ""

# Model paths
OLD_MODEL="src/models/yolov8n_deer.pt"
NEW_MODEL="src/models/runs/corrected_final_buck_doe/weights/best.pt"
BACKUP_MODEL="src/models/yolov8n_deer_OLD_$(date +%Y%m%d_%H%M%S).pt"

# Verify new model exists
if [ ! -f "$NEW_MODEL" ]; then
    echo "[FAIL] New model not found: $NEW_MODEL"
    exit 1
fi

echo "[INFO] New model found: $NEW_MODEL"
NEW_SIZE=$(ls -lh "$NEW_MODEL" | awk '{print $5}')
echo "  Size: $NEW_SIZE"
echo ""

# Backup old model
if [ -f "$OLD_MODEL" ]; then
    echo "[INFO] Backing up current model..."
    cp "$OLD_MODEL" "$BACKUP_MODEL"
    OLD_SIZE=$(ls -lh "$OLD_MODEL" | awk '{print $5}')
    echo "  [OK] Backup created: $BACKUP_MODEL ($OLD_SIZE)"
else
    echo "[WARN] No existing model to backup"
fi
echo ""

# Deploy new model
echo "[INFO] Deploying new model..."
cp "$NEW_MODEL" "$OLD_MODEL"
echo "  [OK] New model deployed: $OLD_MODEL"
echo ""

# Verify deployment
DEPLOYED_SIZE=$(ls -lh "$OLD_MODEL" | awk '{print $5}')
echo "[INFO] Deployment verification:"
echo "  File: $OLD_MODEL"
echo "  Size: $DEPLOYED_SIZE"
echo ""

echo "======================================================================="
echo "[OK] Model deployment complete!"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "  1. Restart worker: docker-compose restart worker"
echo "  2. Monitor logs: docker-compose logs -f worker"
echo "  3. Test with sample images"
echo ""
