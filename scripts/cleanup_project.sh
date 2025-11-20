#!/bin/bash
# Project Cleanup Script
# Archives temporary audit files and failed training runs
# Date: 2025-11-16

set -e

echo "========================================================================"
echo "PROJECT CLEANUP - Thumper Counter"
echo "========================================================================"
echo ""

# Create archive directory
ARCHIVE_DIR="archive/audit_20251116"
mkdir -p "$ARCHIVE_DIR"

echo "[1/6] Archiving audit batch files (84 files)..."
mkdir -p "$ARCHIVE_DIR/batch_reports"
mv CLASSIFICATION_AUDIT_BATCH_*.md "$ARCHIVE_DIR/batch_reports/" 2>/dev/null || true
echo "  [OK] Moved to: $ARCHIVE_DIR/batch_reports/"

echo ""
echo "[2/6] Archiving audit correction scripts (10 files)..."
mkdir -p "$ARCHIVE_DIR/correction_scripts"
mv apply_batch_*_corrections.sh "$ARCHIVE_DIR/correction_scripts/" 2>/dev/null || true
echo "  [OK] Moved to: $ARCHIVE_DIR/correction_scripts/"

echo ""
echo "[3/6] Archiving audit result JSONs (82 files)..."
mkdir -p "$ARCHIVE_DIR/batch_results"
mv audit_batch_*_results.json "$ARCHIVE_DIR/batch_results/" 2>/dev/null || true
echo "  [OK] Moved to: $ARCHIVE_DIR/batch_results/"

echo ""
echo "[4/6] Archiving batch metadata (84 files)..."
mkdir -p "$ARCHIVE_DIR/batch_metadata"
mv batch_*_metadata.txt "$ARCHIVE_DIR/batch_metadata/" 2>/dev/null || true
echo "  [OK] Moved to: $ARCHIVE_DIR/batch_metadata/"

echo ""
echo "[5/6] Consolidating audit summary documents..."
mkdir -p "$ARCHIVE_DIR/summaries"
mv AUDIT_*.md COMPLETE_*.md FINAL_*.md VISION_*.md REPROCESSING_*.md CONSOLIDATED_*.txt "$ARCHIVE_DIR/summaries/" 2>/dev/null || true
# Keep the main resume document
mv "$ARCHIVE_DIR/summaries/RESUME_NEXT_SESSION.md" . 2>/dev/null || true
echo "  [OK] Moved to: $ARCHIVE_DIR/summaries/"

echo ""
echo "[6/6] Archiving failed training run (269MB)..."
mkdir -p archive/failed_training_runs
mv src/models/runs/deer_balanced_20251116 archive/failed_training_runs/ 2>/dev/null || true
echo "  [OK] Moved to: archive/failed_training_runs/deer_balanced_20251116"

echo ""
echo "========================================================================"
echo "OPTIONAL CLEANUP (Manual Confirmation Required)"
echo "========================================================================"
echo ""
echo "The following can also be cleaned up but require manual confirmation:"
echo ""
echo "[A] Old training datasets (now superseded by merged dataset):"
echo "    - src/models/training_data/audit_corrected_20251116/ (28 images)"
echo "    - src/models/training_data/corrected_final_20251111/ (779 images)"
echo "    These are safe to archive since merged_corrected_20251116 contains all data."
echo ""
echo "[B] Old training runs (if not needed):"
echo "    - src/models/runs/deer_multiclass/"
echo "    - src/models/runs/corrected_simplified_buck/"
echo ""
echo "[C] Temporary scripts (if validated):"
echo "    - scripts/debug_new_model.py"
echo "    - scripts/test_models_on_audit_data.py"
echo "    - scripts/validate_retrained_model.py"
echo ""
echo "To archive these, run:"
echo "  bash scripts/cleanup_project.sh --archive-old-datasets"
echo "  bash scripts/cleanup_project.sh --archive-old-runs"
echo "  bash scripts/cleanup_project.sh --archive-temp-scripts"
echo ""
echo "========================================================================"
echo "CLEANUP SUMMARY"
echo "========================================================================"
echo ""

# Calculate space saved
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | awk '{print $1}')
echo "Files archived: ~260 files"
echo "Archive location: $ARCHIVE_DIR"
echo "Archive size: $ARCHIVE_SIZE"
echo ""

# List what's left in root directory
echo "Remaining files in project root:"
ls -1 *.md *.txt *.sh 2>/dev/null | wc -l || echo "0"
echo ""

echo "[OK] Cleanup complete!"
echo ""
echo "To restore archived files if needed:"
echo "  cp -r $ARCHIVE_DIR/* ."
echo ""
echo "To permanently delete archive (after validation):"
echo "  rm -rf archive/audit_20251116"
echo ""
echo "========================================================================"
