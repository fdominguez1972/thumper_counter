# Change Log
**Last Updated:** November 8, 2025

## Sprint 1 (Nov 1-4, 2025) - COMPLETE
- Initialized project with spec-kit
- Created 4 database models (Location, Image, Detection, Deer)
- Ingested 35,251 images from trail cameras
- Set up Docker infrastructure (backend, worker, db, redis)
- Created project constitution

## Sprint 2 (Nov 5, 2025) - COMPLETE
- Fixed worker container OpenGL dependencies
- Discovered YOLOv8 multi-class capability
- Updated ML specification
- Created development plan
- Started API implementation (locations, images)

## Sprint 3 (Nov 6, 2025) - COMPLETE
- Enabled GPU acceleration (RTX 4080 Super, CUDA support)
- Fixed CUDA fork error (switched to threads pool)
- Implemented thread-safe model loading
- Created batch processing API (POST /api/processing/batch)
- Added processing status monitoring (GET /api/processing/status)
- Built deer management API (full CRUD operations)
- Fixed all enum issues (lowercase values)
- Made feature_vector nullable for manual profiles
- Achieved 10x speedup: 0.04s vs 0.4s per image

## Sprint 4 (Nov 6-7, 2025) - COMPLETE
- Trained multi-class YOLOv8n model for sex/age classification
- Dataset: Roboflow Whitetail Deer v46 (15,574 images, 5 deer classes)
- Training results: mAP50=0.804, mAP50-95=0.620
- Classes: doe (female), fawn (unknown), mature/mid/young (male)
- Real-world validation: 90.5% doe, 4.8% fawn, 4.8% young
- Integrated into detection pipeline
- Model: src/models/runs/deer_multiclass/weights/best.pt

## Sprint 5 (Nov 6, 2025) - COMPLETE
- Enabled pgvector extension in PostgreSQL
- Added vector(512) column for feature embeddings
- Implemented ResNet50 feature extraction (512-dim embeddings)
- Thread-safe model loading with singleton pattern
- Cosine similarity search with HNSW index
- Sex-based filtering for improved matching
- Automatic deer profile creation
- Migration: 005_migrate_to_pgvector.sql

## Sprint 6 (Nov 6, 2025) - COMPLETE
- Integrated re-ID into detection pipeline (auto-chaining)
- Created batch re-ID processing script (batch_reidentify.py)
- Processed 313 detections, created 14 deer profiles
- Timeline API: GET /api/deer/{id}/timeline (activity patterns)
- Locations API: GET /api/deer/{id}/locations (movement patterns)
- Full automation: Image -> Detection -> Re-ID -> Deer Profile
- Performance: 2.05s total per image (0.05s detection + 2s re-ID)

## Sprint 7 (Nov 7-8, 2025) - COMPLETE
- Timestamp correction system (migration 007)
- Two-stage deduplication (spatial + temporal)
- Batch timestamp correction (15,000+ images updated)
- Deduplication processed 23,000+ images
- Image count synchronization fixes
- Database integrity improvements

## Sprint 8 (Nov 8, 2025) - COMPLETE
- Detection correction system (single and batch)
- Backend: PATCH /api/detections/{id}/correct
- Backend: PATCH /api/detections/batch/correct (up to 1000)
- Frontend: DetectionCorrectionDialog.tsx (199 lines)
- Frontend: BatchCorrectionDialog.tsx (183 lines)
- Frontend: DeerImages.tsx with multi-select (415 lines)
- Multi-species classification: cattle, pig, raccoon
- Species statistics API: GET /api/deer/stats/species
- Feral hog dedicated counter
- Image filtering by classification
- Database migration: 009_add_detection_corrections.sql
- All features tested and verified

## Current Status (Nov 8, 2025)
- **Current Sprint:** 8 (COMPLETE)
- **Active Branch:** main
- Total images: 35,251
- Images processed: ~1,200 (3.4%)
- Total detections: 37,522
- Deer profiles: 14
- Species breakdown:
  - Deer: 37,514 (99.98%)
  - Cattle: 8
  - Feral Hogs: 0
  - Raccoons: 0

## Next Sprint Planning (Sprint 9)

### High Priority
- Continue processing remaining images (34,000+ pending)
- Review and correct misclassifications using new correction UI
- Tag non-deer species (cattle, pigs, raccoons) as found
- Analyze species statistics per location

### Medium Priority
- Add user authentication system
- Implement correction history view
- Add validity filter to images API
- Create export functionality for corrections

### Low Priority
- Add undo correction functionality
- Implement correction patterns analytics
- Create ML model retraining workflow with corrected data
- Add bulk import of corrections (CSV)

## Deviations from Original Specs
- YOLOv8 handles both detection AND classification (improvement)
- 35,251 images instead of 40,617 (different dataset)
- 6 locations instead of 7 (Old_Rusty removed)
- Simple pagination instead of cursor-based
- Added multi-species support (cattle, pig, raccoon)
- Added detection correction system (not in original spec)
- Two-stage deduplication system (enhancement)
