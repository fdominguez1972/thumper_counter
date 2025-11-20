#!/bin/bash
# Start YOLOv8-Pose Antler Detection Training
# Phase 2B: Antler Keypoint Detection
# Date: November 16, 2025

set -e

echo "========================================================================"
echo "YOLOV8-POSE ANTLER DETECTION TRAINING"
echo "Phase 2B: 16 Keypoint Antler Detection"
echo "========================================================================"
echo ""

# Check worker is running
if ! docker-compose ps worker | grep -q "Up"; then
    echo "[INFO] Starting worker container..."
    docker-compose up -d worker
    echo "[INFO] Waiting for worker to be ready (30s)..."
    sleep 30
fi

echo "[OK] Worker container is running"
echo ""

# Copy training script to worker
echo "[INFO] Copying training script to worker container..."
docker cp scripts/train_antler_detection.py thumper_worker:/app/train_antler_detection.py

echo "[OK] Script copied"
echo ""

# Check dataset exists
echo "[INFO] Verifying dataset..."
if [ ! -d "src/models/training_data/antler_yolo_20251116" ]; then
    echo "[FAIL] Dataset not found: src/models/training_data/antler_yolo_20251116"
    echo "[INFO] Run: python3 scripts/convert_labelstudio_to_yolo.py"
    exit 1
fi

echo "[OK] Dataset found (73 images with antler annotations)"
echo ""

# Start training
echo "[INFO] Starting antler detection training..."
echo "[INFO] This will take 2-3 hours"
echo "[INFO] Monitor with: docker-compose logs -f worker | grep -E 'epoch|OKS|mAP'"
echo ""

# Run training in background
MSYS_NO_PATHCONV=1 docker-compose exec -d worker bash -c "cd /app && python3 /app/train_antler_detection.py > /app/training_antler.log 2>&1"

sleep 10

# Verify training started
if MSYS_NO_PATHCONV=1 docker-compose exec worker test -f /app/training_antler.log; then
    echo ""
    echo "========================================================================"
    echo "[OK] ANTLER DETECTION TRAINING STARTED"
    echo "========================================================================"
    echo ""
    echo "Monitor with:"
    echo "  docker-compose logs -f worker | grep -E 'epoch|OKS'"
    echo ""
    echo "Check progress:"
    echo "  MSYS_NO_PATHCONV=1 docker-compose exec worker tail -50 /app/training_antler.log"
    echo ""
    echo "Check saved models:"
    echo "  ls -lh src/models/runs/antler_detection_20251116/weights/"
    echo ""
    echo "Stop training:"
    echo "  docker-compose restart worker"
    echo ""
    echo "========================================================================"
else
    echo "[FAIL] Training log not created - check worker logs"
    docker-compose logs worker --tail=20
    exit 1
fi
