#!/bin/bash
# Apply Classification Audit Corrections
# Generated: 2025-11-16
#
# This script applies the corrections identified in the classification audit
# for the 10 lowest confidence detections reviewed.

set -e

API_URL="http://localhost:8001"

echo "=========================================="
echo "Classification Audit Corrections"
echo "=========================================="
echo ""

# Correction 1: Cattle misidentified as doe
echo "[1/3] Correcting cattle misidentification..."
curl -s -X PATCH "${API_URL}/api/detections/cdd57436-24e3-4ed6-a61e-428db996d7ac/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "cattle"}' | python3 -m json.tool
echo "✓ Corrected CAMPHOUSE_02025.jpg: doe → cattle"
echo ""

# Correction 2: Buck misidentified as doe (actually does)
echo "[2/3] Correcting buck/doe misidentification..."
curl -s -X PATCH "${API_URL}/api/detections/b429d667-47b2-4903-bfa1-4673b34bd97d/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe"}' | python3 -m json.tool
echo "✓ Corrected CAMPHOUSE_01253.jpg: buck → doe"
echo ""

# Correction 3: False positive - mark as invalid
echo "[3/3] Marking false positive as invalid..."
curl -s -X PATCH "${API_URL}/api/detections/53c3cf10-2d7b-4791-a80a-00cf8594642e/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false}' | python3 -m json.tool
echo "✓ Marked SANCTUARY_01496.jpg detection as invalid (no deer present)"
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Corrections applied: 3"
echo "  - Cattle misidentification: 1"
echo "  - Buck/doe confusion: 1"
echo "  - False positive: 1"
echo ""
echo "Audit complete! See CLASSIFICATION_AUDIT_RESULTS.md for details."
echo ""
echo "Next steps:"
echo "1. Review remaining 40+ low-confidence images"
echo "2. Monitor model performance"
echo "3. Consider retraining with corrected data"
echo "=========================================="
