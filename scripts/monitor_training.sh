#!/bin/bash
# Monitor YOLOv8 training progress
# Date: November 16, 2025

echo "========================================================================"
echo "YOLOV8 TRAINING MONITOR"
echo "========================================================================"
echo ""

# Check if training is running
if ! docker ps | grep -q thumper_worker; then
    echo "[FAIL] Worker container not running"
    exit 1
fi

# Check training log
if ! MSYS_NO_PATHCONV=1 docker-compose exec worker test -f /app/training.log 2>/dev/null; then
    echo "[WARN] Training log not found - training may not be started"
    exit 1
fi

echo "[OK] Training is running"
echo ""

# Show recent progress
echo "========================================================================"
echo "RECENT PROGRESS (Last 30 lines)"
echo "========================================================================"
MSYS_NO_PATHCONV=1 docker-compose exec worker tail -30 /app/training.log | grep -E "Epoch|box_loss|cls_loss|mAP|precision|recall" || \
    MSYS_NO_PATHCONV=1 docker-compose exec worker tail -30 /app/training.log

echo ""
echo "========================================================================"
echo "TRAINING STATISTICS"
echo "========================================================================"

# Extract current epoch
CURRENT_EPOCH=$(MSYS_NO_PATHCONV=1 docker-compose exec worker tail -100 /app/training.log | grep "Epoch" | tail -1 | awk '{print $1}' | sed 's/\[K//')
echo "Current Epoch: $CURRENT_EPOCH"

# Check model weights
echo ""
echo "Saved Checkpoints:"
MSYS_NO_PATHCONV=1 docker-compose exec worker ls -lh /app/models/runs/deer_balanced_20251116/weights/ 2>/dev/null || echo "  No checkpoints yet"

echo ""
echo "========================================================================"
echo "MONITORING COMMANDS"
echo "========================================================================"
echo ""
echo "Watch live progress:"
echo "  docker-compose logs -f worker | grep -E 'Epoch|mAP'"
echo ""
echo "View full training log:"
echo "  MSYS_NO_PATHCONV=1 docker-compose exec worker cat /app/training.log"
echo ""
echo "Check GPU usage:"
echo "  docker-compose exec worker nvidia-smi"
echo ""
echo "Stop training:"
echo "  docker-compose restart worker"
echo ""
echo "Resume training (if stopped early):"
echo "  # Training will auto-resume from last checkpoint"
echo ""
echo "========================================================================"
