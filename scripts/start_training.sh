#!/bin/bash
# Start YOLOv8 model retraining inside worker container
# Date: November 16, 2025

set -e

echo "========================================================================"
echo "YOLOV8 MODEL RETRAINING - FIXING BUCK OVER-CLASSIFICATION BIAS"
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
docker cp scripts/train_balanced_model.py thumper_worker:/app/train_balanced_model.py

echo "[OK] Script copied"
echo ""

# Start training in background
echo "[INFO] Starting training in background..."
echo "[INFO] This will take 4-6 hours"
echo "[INFO] Monitor progress with: docker-compose logs -f worker"
echo ""

# Run training
docker-compose exec -d worker python3 /app/train_balanced_model.py

echo ""
echo "========================================================================"
echo "[OK] TRAINING STARTED"
echo "========================================================================"
echo ""
echo "Monitor with:"
echo "  docker-compose logs -f worker | grep -E 'epoch|mAP|precision|recall'"
echo ""
echo "Check progress:"
echo "  ls -lh src/models/runs/deer_balanced_20251116/weights/"
echo ""
echo "Stop training:"
echo "  docker-compose restart worker"
echo ""
echo "========================================================================"
