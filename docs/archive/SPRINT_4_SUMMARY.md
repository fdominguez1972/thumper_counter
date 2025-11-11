# Sprint 4 Summary: Sex/Age Classification

**Status:** COMPLETE
**Date:** November 6-7, 2025
**Branch:** 002-batch-processing

## Overview

Sprint 4 successfully implemented multi-class deer detection with automatic sex/age classification. The system now identifies deer as doe, fawn, mature buck, mid-age buck, or young buck during the detection phase.

## Achievements

### 1. Multi-Class Model Training (COMPLETE)

Trained YOLOv8n model on Roboflow Whitetail Deer v46 dataset:

- **Dataset:** 15,574 images (11 classes total, 5 deer classes)
- **Training Time:** 1.088 hours (79 epochs with early stopping)
- **GPU:** NVIDIA RTX 4080 Super (16GB VRAM)
- **Batch Size:** 32
- **Early Stopping:** Patience 20 (best model at epoch 59)

**Training Results:**
```
Overall:
  mAP50:     0.859
  mAP50-95:  0.643
  Precision: 0.837
  Recall:    0.797

Deer Classes (mAP50):
  doe (female):    0.832
  fawn (unknown):  0.784
  mature (male):   0.824
  mid (male):      0.719
  young (male):    0.755
```

**Test Set Evaluation (347 images):**
```
Overall:
  mAP50:     0.804
  mAP50-95:  0.620
  Precision: 0.896
  Recall:    0.701

Deer Classes (mAP50):
  doe (female):    0.769
  fawn (unknown):  0.796
  mature (male):   0.673
  mid (male):      0.581
  young (male):    0.676
```

### 2. Detection Pipeline Integration (COMPLETE)

Updated detection task to use multi-class model:

**Changes to `src/worker/tasks/detection.py`:**
- Updated model path to use trained multi-class model
- Added class name mapping (11 classes)
- Filters detections to deer-only (classes 3, 4, 5, 6, 10)
- Sets `Detection.classification` field with sex/age
- Skips non-deer detections (UTV, person, raccoon, etc.)

**Class Mapping:**
```python
CLASS_NAMES = {
    0: "UTV",
    1: "cow",
    2: "coyote",
    3: "doe",        # Female deer
    4: "fawn",       # Baby deer (sex unknown)
    5: "mature",     # Mature buck (large antlers)
    6: "mid",        # Mid-age buck (medium antlers)
    7: "person",
    8: "raccoon",
    9: "turkey",
    10: "young"      # Young buck (small/spike antlers)
}
```

### 3. Pipeline Testing (COMPLETE)

Verified multi-class detection working correctly:

**Real-World Test Results (Recent 21 detections):**
```
Classification Distribution:
  doe (female):   19 detections (90.5%)
  fawn (unknown):  1 detection  (4.8%)
  young (male):    1 detection  (4.8%)

Average Confidence:
  doe:   0.72
  fawn:  0.51
  young: 0.51
```

**Sample Detections:**
- `SANCTUARY_05780.jpg`: doe (0.64 conf)
- `270_JASON_00827.jpg`: doe (0.90 conf)
- `HAYFIELD_01636.jpg`: fawn (0.51 conf)
- `270_JASON_00836.jpg`: young buck (0.51 conf)

## Architecture Changes

### Model Storage
```
src/models/runs/deer_multiclass/
├── weights/
│   ├── best.pt          # Best model (epoch 59)
│   └── last.pt          # Last checkpoint (epoch 79)
└── evaluation/
    └── test_results/
        ├── confusion_matrix.png
        ├── PR_curve.png
        └── predictions.json
```

### Training Data
```
/mnt/training_data/Whitetail Deer.v46-buck_classes_v046.yolov8/
├── train/
│   ├── images/      # 13,615 images
│   └── labels/      # 16,696 annotations
├── valid/
│   ├── images/      # 1,612 images
│   └── labels/      # 1,923 annotations
└── test/
    ├── images/      # 347 images
    └── labels/      # 421 annotations
```

### Docker Configuration

**Added to `docker-compose.yml`:**
```yaml
worker:
  volumes:
    - /mnt/i/deer_tracker/models:/mnt/training_data:ro  # Training data mount
  shm_size: '8gb'  # Shared memory for DataLoader
```

## Files Created/Modified

### Created Files
1. `src/models/training_data/deer_multiclass.yaml` - Dataset configuration
2. `scripts/train_deer_multiclass.py` - Training script (container)
3. `train_deer_multiclass.py` - Training script (host)
4. `scripts/evaluate_multiclass_model.py` - Evaluation script
5. `scripts/test_multiclass_pipeline.py` - Pipeline test script
6. `docs/SPRINT_4_SUMMARY.md` - This document

### Modified Files
1. `src/worker/tasks/detection.py` - Multi-class model integration
2. `src/worker/celery_app.py` - Model validation updated
3. `docker-compose.yml` - Training data volume + shared memory
4. `.specify/plan.md` - Sprint 4 progress
5. `CLAUDE.md` - Sprint 4 documentation

## Performance Metrics

### Training Performance
- **Training Time:** 1.088 hours (vs estimated 3-5 hours)
- **GPU Memory:** ~4GB VRAM (batch 32)
- **Early Stopping:** Saved ~2-3 hours by stopping at epoch 79

### Detection Performance (With New Model)
- **Speed:** 0.04-0.05s per image (GPU)
- **Throughput:** 1.2 images/second (including DB writes)
- **Accuracy:** 80.4% mAP50 on test set

### Classification Quality
- **Female Detection (doe):** 76.9% mAP50
- **Male Detection (mature/mid/young):** 64.3% avg mAP50
- **Age Classification:** 79.6% mAP50 (fawn detection)

## Key Decisions

### 1. Why YOLOv8n (Nano)?
- Fast inference (0.04s per image)
- Good accuracy for deer detection
- Fits in 16GB VRAM with batch 32
- Supports GPU acceleration

### 2. Why Batch 32 (not 64)?
- Better generalization (more weight updates per epoch)
- Lower risk of overfitting
- Comfortable GPU memory usage (~4GB)
- Faster per-epoch training

### 3. Why Filter to Deer-Only Detections?
- Reduces database storage (no UTV, person, etc.)
- Cleaner data for re-identification
- Faster re-ID processing (fewer candidates)
- Focus on core use case (deer tracking)

### 4. Why Early Stopping (Patience 20)?
- Prevents overfitting
- Saves training time (stopped at 79/200 epochs)
- Automatic best model selection
- No manual monitoring required

## Roboflow Dataset Details

**Source:** https://universe.roboflow.com/buckvsdoe/whitetail-deer/dataset/46
**License:** CC BY 4.0
**Workspace:** buckvsdoe
**Project:** whitetail-deer
**Version:** 46

**Class Distribution (Training Set):**
```
Deer Classes:
  doe:    2,900 annotations (17.4%)
  fawn:     737 annotations ( 4.4%)
  mature: 2,113 annotations (12.7%)
  mid:    2,978 annotations (17.8%)
  young:  2,413 annotations (14.5%)

Total Deer: 11,141 annotations (66.8% of dataset)

Other Classes:
  UTV, cow, coyote, person, raccoon, turkey
  Total: 5,555 annotations (33.2%)
```

## Next Steps (Sprint 5)

1. **Re-Identification Engine**
   - Implement ResNet50 feature extraction
   - Build vector similarity search
   - Match detections to existing deer profiles
   - Automatic deer profile creation

2. **Database Schema Updates**
   - Add `Deer.feature_vector` column
   - Add `Deer.sex` field (derived from classifications)
   - Add `Deer.age_class` field (fawn/young/mid/mature)

3. **Sex/Age Aggregation**
   - Aggregate multiple detections to determine deer sex
   - Track age progression over time
   - Handle classification uncertainties

4. **Performance Optimization**
   - Batch re-ID processing
   - Vector index optimization (pgvector)
   - Parallel detection + re-ID

## Lessons Learned

1. **Shared Memory for DataLoader**
   - Docker default (64MB) too small for large datasets
   - Required 8GB for 15k+ images with multiple workers
   - Error: "DataLoader worker killed by signal: Bus error"

2. **Model Path Confusion**
   - Symlinks don't work across Docker volumes
   - Use explicit volume mounts for external data
   - Validate paths in container startup

3. **Early Stopping Works Well**
   - Saved 60% of training time (79/200 epochs)
   - No accuracy loss (best model at epoch 59)
   - Automatic hyperparameter tuning

4. **Classification Quality**
   - Does easier to detect than bucks (76.9% vs 64.3%)
   - Likely due to antler complexity
   - May need separate buck age classifier later

## Commands Reference

### Training
```bash
# Train multi-class model (in worker container)
docker-compose exec worker python3 /app/scripts/train_deer_multiclass.py

# Evaluate on test set
docker-compose exec worker python3 /app/scripts/evaluate_multiclass_model.py
```

### Testing
```bash
# Test pipeline with sample images
python3 scripts/test_multiclass_pipeline.py

# Check recent detections
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT classification, COUNT(*) FROM detections \
   WHERE created_at > NOW() - INTERVAL '1 hour' \
   GROUP BY classification;"
```

### Monitoring
```bash
# Watch worker logs for classifications
docker-compose logs -f worker | grep "deer Detection"

# Check classification distribution
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT classification, COUNT(*), AVG(confidence) \
   FROM detections GROUP BY classification;"
```

## Conclusion

Sprint 4 successfully implemented end-to-end sex/age classification:

**COMPLETE:**
- Multi-class YOLOv8 model trained (80.4% mAP50)
- Detection pipeline integrated with filtering
- Sex/age classifications stored in database
- Real-world testing verified

**NEXT:**
- Re-identification for individual deer tracking
- Automatic deer profile creation
- Sex/age aggregation logic

The system now provides automatic deer classification in a single detection pass, eliminating the need for a separate classification stage. This simplifies the ML pipeline and improves performance.
