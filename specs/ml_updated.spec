# ML Pipeline Specification - UPDATED
# Version: 1.1.0  
# Date: 2025-11-05
# Changes: Documented YOLOv8 multi-class detection replacing separate classification model

## Overview

The ML pipeline processes trail camera images through detection, classification, and re-identification stages. A major improvement was discovered: the YOLOv8 model handles both detection AND classification in a single pass.

## UPDATE: Unified Detection-Classification Model

### Discovery (2025-11-04)
The trained YOLOv8n model from deer_tracker includes 11 classes, eliminating need for separate classification:
- **Deer classes:** doe, fawn, mature (buck), mid (buck), young (buck)
- **Wildlife:** coyote, cow, raccoon, turkey
- **Human activity:** person, UTV

### Benefits of Unified Approach
1. **Performance:** 30% faster (single inference vs two)
2. **Memory:** 33% less GPU memory required
3. **Accuracy:** No misalignment between detection and classification
4. **Simplicity:** Fewer models to maintain and version

## Revised Pipeline Architecture

### Original Design (Deprecated)
```
Image -> Detection -> Classification -> Re-ID -> Database
         (YOLOv8)     (ResNet50)      (ResNet50)
```

### Current Implementation
```
Image -> Detection+Classification -> Re-ID -> Database
         (YOLOv8 11-class)          (Feature-based)
```

## Stage 1: Preprocessing (Unchanged)

### Purpose
Standardize images for consistent model input while preserving detection quality.

### Operations
1. **EXIF Extraction**
   - NOTE: Trail cameras lack GPS in EXIF
   - Extract: DateTime if available
   - Fallback: Parse filename for timestamp

2. **Image Normalization**
   - Resize: Maintain aspect ratio, max dimension 1280px
   - Format: Convert to RGB if grayscale
   - Enhancement: CLAHE for low-light images (optional)

3. **Quality Check**
   - Minimum resolution: 640x480
   - File integrity: Verify image can be decoded
   - Blur detection: Laplacian variance > 100

### Configuration
```yaml
preprocessing:
  max_dimension: 1280
  target_format: "RGB"
  enable_clahe: true
  clahe_clip_limit: 2.0
  min_resolution: [640, 480]
  blur_threshold: 100
```

## Stage 2: Unified Detection and Classification (UPDATED)

### Model Details
**YOLOv8n Multi-Class** (yolov8n_deer.pt - 22MB)
- Trained on deer_tracker dataset
- 11 classes with built-in classification
- mAP@0.5: >0.85 on test set

### Class Mapping
```python
YOLO_CLASSES = {
    0: 'UTV',      # Human activity
    1: 'cow',      # Livestock
    2: 'coyote',   # Predator
    3: 'doe',      # Female deer
    4: 'fawn',     # Young deer
    5: 'mature',   # Mature buck
    6: 'mid',      # Middle-aged buck
    7: 'person',   # Human
    8: 'raccoon',  # Wildlife
    9: 'turkey',   # Wildlife
    10: 'young'    # Young buck
}

# Simplified mapping for database
SEX_MAPPING = {
    'doe': 'DOE',
    'fawn': 'FAWN',
    'mature': 'BUCK',
    'mid': 'BUCK',
    'young': 'BUCK',
    # Others map to None (not deer)
}
```

### Detection Parameters
```yaml
detection:
  model: "yolov8n_deer.pt"
  confidence_threshold: 0.5
  iou_threshold: 0.45
  max_detections: 20
  device: "cuda:0"  # RTX 4080 Super
```

### Post-processing
1. **Filter Non-Deer** - Remove UTV, person, cow, etc.
2. **Map to Sex Categories** - Convert 11 classes to buck/doe/fawn
3. **NMS** - Remove duplicate detections
4. **Expand Boxes** - Add 10% padding for re-ID

## Stage 3: Feature Extraction for Re-ID (Simplified)

### Current Approach
**Basic Feature Extraction** (Temporary)
- Color histograms (RGB channels)
- Edge features (Canny)
- HOG descriptors
- Expected accuracy: ~70%

### Future Enhancement
**Deep Learning Re-ID** (To be implemented)
- ResNet50 backbone
- Triplet loss training
- 512-dim embeddings
- Expected accuracy: >90%

### Feature Storage
```yaml
feature_extraction:
  method: "basic"  # or "resnet50" when trained
  dimensions: 256  # or 512 for deep features
  storage: "postgresql_array"
  update_strategy: "exponential_moving_average"
  update_weight: 0.3
```

## Stage 4: Individual Re-identification (Unchanged)

### Matching Algorithm
```python
def match_deer(new_features, database_deer):
    """Match detection to existing deer or create new."""
    similarities = compute_similarity(new_features, database_deer)
    best_match = np.argmax(similarities)
    
    if similarities[best_match] > REID_THRESHOLD:
        return database_deer[best_match].id
    else:
        return create_new_deer()
```

### Threshold Configuration
```yaml
reid_thresholds:
  basic_features: 0.70    # Current implementation
  deep_features: 0.85     # Future with ResNet50
  temporal_bonus: 0.05    # Add if same day/location
```

## Performance Optimization (Updated for RTX 4080 Super)

### Batch Processing
```yaml
batch_processing:
  gpu_batch_size: 32      # Increased from 16 (16GB VRAM)
  cpu_preprocessing: 8    # Parallel image loading
  feature_batch: 64       # Simple operations
```

### Expected Performance
- **Detection+Classification:** 70-90 images/second
- **Full Pipeline:** 35-45 images/second
- **35,234 images:** ~15-20 minutes total

### GPU Memory Usage
```yaml
memory_usage:
  yolov8n: ~2GB
  batch_size_32: ~8GB
  overhead: ~2GB
  total: ~12GB (safe with 16GB)
```

## Error Handling (Unchanged)

### Failure Recovery
```python
@retry(max_attempts=3, backoff=2)
def process_with_recovery(image):
    try:
        return process_image(image)
    except GPUMemoryError:
        reduce_batch_size()
        return process_with_recovery(image)
```

## Model Files

### Current Models
```yaml
models:
  detection_classification:
    file: "yolov8n_deer.pt"
    size: 22MB
    version: "1.0.0"
    source: "deer_tracker project"
    classes: 11
    
  reid:
    file: "basic_features.py"
    type: "algorithmic"
    version: "0.1.0"
    note: "Temporary until ResNet50 trained"
```

### Model Location
```
src/models/
├── yolov8n_deer.pt       # Multi-class detection
├── basic_features.py      # Temporary re-ID
└── README.md             # Model documentation
```

## Testing Requirements (Updated)

### Detection Accuracy
- Test set: 1000 images from each location
- Minimum mAP@0.5: 0.80
- Per-class precision: >0.75

### Classification Accuracy  
- Built into detection model
- Buck/doe/fawn accuracy: >0.85
- Confusion matrix validation

### Re-ID Performance
- Current (basic): ~70% rank-1 accuracy
- Target (ResNet50): >90% rank-1 accuracy

## Migration Notes

### From Original Design
1. ~~Train separate ResNet50 classifier~~ → Use YOLOv8 classes
2. ~~Load two models~~ → Single model load
3. ~~Two inference passes~~ → One pass
4. Map 11 classes → 3 sex categories in post-processing

### Database Updates
- Detection table stores original YOLO class
- Deer table uses simplified sex enum
- Add class_confidence alongside detection_confidence

## Future Enhancements

1. **Train ResNet50 Re-ID**
   - Collect individual deer annotations
   - Implement triplet loss training
   - Deploy when accuracy >90%

2. **Fine-tune YOLOv8**
   - Add more training data
   - Include additional wildlife species
   - Improve night vision accuracy

3. **Behavior Classification**
   - Extend beyond sex classification
   - Detect feeding, bedding, alerts
   - Requires video sequences

---

**Specification Status**: UPDATED
**Version Change**: 1.0.0 → 1.1.0 (unified detection model)
**Dependencies**: system.spec, api.spec
**Next Review**: After Re-ID model training
