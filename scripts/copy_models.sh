#!/bin/bash
#
# Copy Models from Original deer_tracker Project
# Version: 1.0.0
# Date: 2025-11-04
#
# WHY: Reuse trained YOLOv8 detection model from original project
# instead of retraining. Classification and Re-ID models need to be trained.
#
# Usage:
#   chmod +x scripts/copy_models.sh
#   ./scripts/copy_models.sh
#

set -e

# Colors for output (ASCII only)
INFO="[INFO]"
OK="[OK]"
FAIL="[FAIL]"
WARN="[WARN]"

echo "========================================"
echo "Model Copy Script"
echo "========================================"
echo ""

# Define paths
SOURCE_PROJECT="/mnt/i/deer_tracker"
TARGET_PROJECT="/mnt/i/projects/thumper_counter"
TARGET_MODELS_DIR="${TARGET_PROJECT}/src/models"

# Create target directory
echo "${INFO} Creating models directory..."
mkdir -p "${TARGET_MODELS_DIR}"

# ========================================
# 1. YOLOv8 Detection Model
# ========================================
echo ""
echo "${INFO} Copying YOLOv8 detection model..."

# Use the best trained model from the training runs
SOURCE_YOLO="${SOURCE_PROJECT}/scripts/Testing/WhiteTail_ModelTesting/runs/train/whitetail-deer/weights/best.pt"
TARGET_YOLO="${TARGET_MODELS_DIR}/yolov8n_deer.pt"

if [ -f "${SOURCE_YOLO}" ]; then
    cp "${SOURCE_YOLO}" "${TARGET_YOLO}"
    SIZE=$(du -h "${TARGET_YOLO}" | cut -f1)
    echo "${OK} Copied YOLOv8 detection model (${SIZE})"
    echo "    Source: ${SOURCE_YOLO}"
    echo "    Target: ${TARGET_YOLO}"
else
    echo "${FAIL} YOLOv8 model not found at: ${SOURCE_YOLO}"
    echo "${INFO} Trying alternative location..."

    # Try the backend model
    SOURCE_YOLO_ALT="${SOURCE_PROJECT}/backend/app/ml/deer_detector.pt"
    if [ -f "${SOURCE_YOLO_ALT}" ]; then
        cp "${SOURCE_YOLO_ALT}" "${TARGET_YOLO}"
        SIZE=$(du -h "${TARGET_YOLO}" | cut -f1)
        echo "${OK} Copied YOLOv8 detection model from backend (${SIZE})"
        echo "    Source: ${SOURCE_YOLO_ALT}"
        echo "    Target: ${TARGET_YOLO}"
    else
        echo "${FAIL} No YOLOv8 model found. You will need to download or train one."
        exit 1
    fi
fi

# ========================================
# 2. Sex Classification Model
# ========================================
echo ""
echo "${INFO} Checking for sex classification model..."

SOURCE_CLASSIFIER="${SOURCE_PROJECT}/models/sex_classifier.pt"
TARGET_CLASSIFIER="${TARGET_MODELS_DIR}/resnet50_sex_classification.pt"

if [ -f "${SOURCE_CLASSIFIER}" ]; then
    cp "${SOURCE_CLASSIFIER}" "${TARGET_CLASSIFIER}"
    SIZE=$(du -h "${TARGET_CLASSIFIER}" | cut -f1)
    echo "${OK} Copied sex classification model (${SIZE})"
else
    echo "${WARN} Sex classification model NOT found"
    echo "${INFO} The original project uses heuristics (no trained model)"
    echo "${INFO} You will need to train this model for buck/doe/fawn classification"
    echo ""
    echo "    Training Requirements (from specs/ml.spec):"
    echo "    - Model: ResNet50 backbone with custom head"
    echo "    - Classes: buck, doe, fawn, unknown"
    echo "    - Dataset: 5000 buck, 5000 doe, 2000 fawn, 1000 unknown"
    echo "    - Input size: 224x224"
    echo ""
fi

# ========================================
# 3. Re-Identification Model
# ========================================
echo ""
echo "${INFO} Checking for re-identification model..."

SOURCE_REID="${SOURCE_PROJECT}/models/reid_model.pt"
TARGET_REID="${TARGET_MODELS_DIR}/resnet50_reid.pt"

if [ -f "${SOURCE_REID}" ]; then
    cp "${SOURCE_REID}" "${TARGET_REID}"
    SIZE=$(du -h "${TARGET_REID}" | cut -f1)
    echo "${OK} Copied re-identification model (${SIZE})"
else
    echo "${WARN} Re-identification model NOT found"
    echo "${INFO} The original project uses basic feature extraction (no trained model)"
    echo "${INFO} You will need to train this model for individual deer tracking"
    echo ""
    echo "    Training Requirements (from specs/ml.spec):"
    echo "    - Model: ResNet50 + projection head"
    echo "    - Training: Triplet loss for metric learning"
    echo "    - Embedding dim: 512 or 2048"
    echo "    - Dataset: 1000+ individuals with 10+ images each"
    echo ""
fi

# ========================================
# Summary
# ========================================
echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "Models Status:"
echo ""

if [ -f "${TARGET_YOLO}" ]; then
    echo "  ${OK} YOLOv8 Detection: READY"
    echo "      ${TARGET_YOLO}"
else
    echo "  ${FAIL} YOLOv8 Detection: MISSING"
fi

if [ -f "${TARGET_CLASSIFIER}" ]; then
    echo "  ${OK} Sex Classification: READY"
    echo "      ${TARGET_CLASSIFIER}"
else
    echo "  ${WARN} Sex Classification: NEEDS TRAINING"
fi

if [ -f "${TARGET_REID}" ]; then
    echo "  ${OK} Re-Identification: READY"
    echo "      ${TARGET_REID}"
else
    echo "  ${WARN} Re-Identification: NEEDS TRAINING"
fi

echo ""
echo "========================================"
echo "Next Steps"
echo "========================================"
echo ""
echo "1. Review copied models in: ${TARGET_MODELS_DIR}"
echo "2. Update .env file with model paths"
echo "3. For missing models, see:"
echo "   - docs/MODEL_TRAINING.md (to be created)"
echo "   - specs/ml.spec (training specifications)"
echo ""
echo "${OK} Model copy script completed"
