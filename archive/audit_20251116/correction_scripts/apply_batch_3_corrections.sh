#!/bin/bash
# Apply Batch 3 Classification Corrections
# Generated from CLASSIFICATION_AUDIT_BATCH_3.md
# Date: November 15, 2025

API_URL="http://localhost:8001"

echo "=========================================="
echo "BATCH 3 CLASSIFICATION CORRECTIONS"
echo "=========================================="
echo "Total corrections: 7"
echo "  - Buck->Doe: 4"
echo "  - Doe->Buck: 2"
echo "  - Doe->Pig: 1 (SPECIES ERROR)"
echo "=========================================="
echo ""

echo "[1/7] Correcting Image 1: Sanctuary2_20251101_152634_001.jpg (buck->doe)"
curl -X PATCH "${API_URL}/api/detections/6877ebe6-3627-4af7-b6fd-b077c3502020/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[2/7] Correcting Image 3: Sanctuary2_20251101_164821_001.jpg (buck->doe)"
curl -X PATCH "${API_URL}/api/detections/a4bedb12-00db-4ce0-8958-554b35edcb38/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[3/7] Correcting Image 4: CAMPHOUSE_00599.jpg (doe->pig - SPECIES ERROR)"
curl -X PATCH "${API_URL}/api/detections/fcf0e213-692a-436e-a815-3d20bd9e7267/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "pig", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[4/7] Correcting Image 8: Sanctuary2_20251106_091044_001.jpg (buck->doe)"
curl -X PATCH "${API_URL}/api/detections/91764ed6-3a84-4bce-b728-75677f12249e/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[5/7] Correcting Image 11: Sanctuary2_20251104_164255_001.jpg (buck->doe)"
curl -X PATCH "${API_URL}/api/detections/b986b44d-ff34-4267-b645-e7d3a1e0e7d5/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[6/7] Correcting Image 14: HAYFIELD_08767.jpg (doe->buck)"
curl -X PATCH "${API_URL}/api/detections/c1a857d1-dcc5-4069-8075-4ec798bf2ce6/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "buck", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "[7/7] Correcting Image 15: Hayfield_20250914_181704_001.jpg (doe->buck)"
curl -X PATCH "${API_URL}/api/detections/096cd749-b40c-4057-ac1b-04925940eed7/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "buck", "reviewed_by": "Claude AI Audit Batch 3"}' \
  && echo " [OK]" || echo " [FAILED]"
echo ""

echo "=========================================="
echo "BATCH 3 CORRECTIONS COMPLETE"
echo "=========================================="
echo "Results summary:"
echo "  - 4 does misclassified as bucks (corrected)"
echo "  - 2 bucks misclassified as does (corrected)"
echo "  - 1 pig misclassified as doe (corrected)"
echo ""
echo "CRITICAL FINDING: Species confusion detected"
echo "RECOMMENDATION: Set minimum confidence threshold to 55%"
echo "=========================================="
