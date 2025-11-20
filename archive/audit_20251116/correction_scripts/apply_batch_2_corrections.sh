#!/bin/bash
# Apply Classification Audit Corrections - Batch 2
# Generated: November 16, 2025
#
# This script applies the corrections identified in Batch 2 audit
# 5 buck->doe corrections + 2 false positives

set -e

API_URL="http://localhost:8001"

echo "=========================================="
echo "Classification Audit Corrections - Batch 2"
echo "=========================================="
echo ""

# Buck -> Doe Corrections (5 total)
echo "[1/7] Correcting Hayfield_20250910_184443_001.jpg: buck -> doe"
curl -s -X PATCH "${API_URL}/api/detections/cc143c1d-04c9-4eb6-a8d1-072c72d58bd9/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "[2/7] Correcting Hayfield_20251020_073510_001.jpg: buck -> doe"
curl -s -X PATCH "${API_URL}/api/detections/39facc44-dfa6-4887-bc28-91f49de0b8cf/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "[3/7] Correcting Sanctuary2_20251104_164008_001.jpg: buck -> doe"
curl -s -X PATCH "${API_URL}/api/detections/a2a87d11-ffb2-4cb1-be73-fc32a79e340c/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "[4/7] Correcting Hayfield_20251029_073217_001.jpg: buck -> doe"
curl -s -X PATCH "${API_URL}/api/detections/6689745a-192d-4692-821b-e216f7f453cc/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "[5/7] Correcting Sanctuary2_20251103_095644_001.jpg: buck -> doe"
curl -s -X PATCH "${API_URL}/api/detections/329449c7-c621-44c7-af2b-6d4713e1e1bb/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

# False Positives (2 total)
echo "[6/7] Marking Jason1_20250915_030941_001.jpg as invalid (no deer)"
curl -s -X PATCH "${API_URL}/api/detections/ad878ecc-b5b3-4edf-9e5b-bf8160353eb8/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "[7/7] Marking TINMAN_00116.jpg as invalid (no deer)"
curl -s -X PATCH "${API_URL}/api/detections/446b6e8d-9fef-4169-a1ae-2dad082e4b86/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}' | python3 -m json.tool
echo ""

echo "=========================================="
echo "Summary - Batch 2"
echo "=========================================="
echo "Corrections applied: 7"
echo "  - Buck->Doe corrections: 5"
echo "  - False positives marked invalid: 2"
echo ""
echo "Batch 2 complete!"
echo ""
echo "Combined Results (Batch 1 + 2):"
echo "  - Total reviewed: 30 images"
echo "  - Batch 1 corrections: 3"
echo "  - Batch 2 corrections: 7"
echo "  - Total corrections: 10 (33% error rate)"
echo ""
echo "Next: Review Batch 3 (images 31-50, confidence 50.22-52%)"
echo "=========================================="
