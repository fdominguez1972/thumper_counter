# Scripts Archive

This directory contains historical scripts that have been superseded or are no longer actively used.

## Archive Date
November 11, 2025

## What's Archived

### Sprint 3 - GPU Optimization (Historical)
- benchmark_detection.py - Detection performance benchmarking

### Sprint 5 - Re-ID System (Historical)
- test_reidentification.py - Re-ID pipeline testing

### Sprint 6 - Pipeline Integration (Superseded)
- batch_reidentify.py - Manual batch re-ID processing (now automated in pipeline)

### Sprint 7 - OCR Investigation (Not Implemented)
- test_ocr_extraction.py - OCR extraction testing (feature postponed)

### Sprint 8 - Database Optimization (One-Off Scripts)
- apply_postgres_optimizations.sh - PostgreSQL tuning (applied once)
- reid_corrected_detections.py - Re-ID corrected detections batch

### Sprint 9 - Performance Analysis (Historical)
- benchmark_reid.py - Re-ID GPU performance testing
- verify_and_queue_rut_season.py - Rut season image queueing

### Training Scripts (Superseded)
- train_multiclass_model.py - Old training script (replaced by train_deer_multiclass.py)

### Monitoring (Replaced by API)
- monitor_processing.sh - Manual processing monitor (use /api/processing/status instead)

## Active Scripts

Current scripts are in the parent scripts/ directory:

- **bulk_import_images.py** - Bulk image import from trail cameras
- **export_training_data.py** - Export corrected detections for model training
- **import_trail_cam_images.py** - Import trail camera images with EXIF data
- **test_new_model.py** - Test newly trained models
- **train_deer_multiclass.py** - Train YOLOv8 multi-class deer models

## Retrieval

If you need to reference archived scripts:

```bash
# List all archived scripts
ls scripts/archive/

# View specific archived script
cat scripts/archive/batch_reidentify.py

# Search across archived scripts
grep -r "keyword" scripts/archive/
```

## Archival Policy

Scripts are archived when:
1. Sprint is complete and script was for one-time testing/benchmarking
2. Script is superseded by a newer version or automated pipeline
3. Feature was investigated but not implemented
4. One-off migration or optimization script already applied

Archived scripts are retained for historical reference and understanding past approaches.
