#!/bin/bash
# Docker Compose wrapper to ensure correct REID_THRESHOLD
# Feature 009: Enhanced Re-ID uses threshold 0.60 (recommended from validation)

export REID_THRESHOLD=0.60
export USE_ENHANCED_REID=true
export ENSEMBLE_WEIGHT_RESNET=0.6
export ENSEMBLE_WEIGHT_EFFICIENTNET=0.4

echo "[INFO] Starting containers with REID_THRESHOLD=${REID_THRESHOLD}"
docker-compose up -d "$@"

echo "[OK] Containers started"
echo "[INFO] Verify worker threshold:"
sleep 3
docker-compose logs worker | grep "FEATURE009" | tail -2
