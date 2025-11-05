# ML Pipeline Specification
# Version: 1.0.0  
# Date: 2025-11-04

## Overview

The ML pipeline processes trail camera images through three stages: detection, classification, and re-identification. Each stage is designed for specific accuracy and performance trade-offs.

## Pipeline Architecture

### Processing Flow
```
Raw Image -> Preprocessing -> Detection -> Classification -> Re-identification -> Database
    |             |              |             |                |                 |
    v             v              v             v                v                 v
  EXIF       Normalization   Bounding Box   Sex/Age      Individual ID      Updates
  Extract     & Resize         & Score     Prediction    Matching Score    Profiles
```

## Stage 1: Preprocessing

### Purpose
Standardize images for consistent model input while preserving detection quality.

### Operations
1. **EXIF Extraction**
   - WHY: Timestamps and location data for tracking patterns
   - Extract: DateTime, GPS (if available), Camera Model
   - Store: Original metadata before any modifications

2. **Image Normalization**
   - WHY: Models trained on specific input distributions
   - Resize: Maintain aspect ratio, max dimension 1280px
   - Format: Convert to RGB if grayscale
   - Enhancement: CLAHE for low-light images (optional)

3. **Quality Check**
   - WHY: Skip processing corrupted/invalid images
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

## Stage 2: Object Detection (YOLOv8)

### Model Selection
**YOLOv8n** (nano variant)
- WHY: Best speed/accuracy trade-off for our hardware
- FPS: 50+ on RTX 4070
- mAP: Sufficient for large mammals
- Size: 6MB (fast loading)

### Training Strategy
**Transfer Learning** from COCO dataset
- WHY: COCO includes general animal detection
- Fine-tuning: 5000 deer-specific images
- Augmentation: Rotation, brightness, weather effects
- Validation split: 80/20

### Detection Parameters
```yaml
detection:
  model: "yolov8n.pt"
  confidence_threshold: 0.5  # WHY: Balance false positives vs missed detections
  iou_threshold: 0.45        # WHY: Handle overlapping deer in groups
  max_detections: 20         # WHY: Herds rarely exceed this
  classes: ["deer"]          # WHY: Single class simplifies training
```

### Post-processing
1. **Non-Maximum Suppression (NMS)**
   - WHY: Remove duplicate detections of same deer
   - Algorithm: Soft-NMS for better group handling
   
2. **Bounding Box Refinement**
   - WHY: Improve classification accuracy
   - Expand boxes by 10% for context
   - Ensure boxes within image bounds

## Stage 3: Sex/Age Classification

### Model Architecture
**Custom CNN** (ResNet50 backbone)
- WHY: ResNet50 proven for fine-grained classification
- Input size: 224x224 (cropped detections)
- Classes: Buck, Doe, Fawn, Unknown
- Output: Softmax probabilities

### Training Data
```yaml
classification_dataset:
  buck: 5000     # Adult male with antlers
  doe: 5000      # Adult female
  fawn: 2000     # Young deer
  unknown: 1000  # Ambiguous/obscured
```

### Classification Rules
1. **Confidence Thresholding**
   - WHY: Avoid incorrect high-confidence labels
   - Threshold: 0.7 for buck/doe, 0.8 for fawn
   - Below threshold -> "unknown"

2. **Temporal Consistency**  
   - WHY: Same deer shouldn't change sex between frames
   - Check last 5 sightings
   - Use majority vote for conflicts

### Feature Extraction
Extract features for re-identification:
- Layer: ResNet50 layer4 (2048-dim)
- Normalization: L2 normalize vectors
- Storage: Float32 array in database

## Stage 4: Individual Re-identification

### Approach
**Metric Learning** with triplet loss
- WHY: Learn deer-specific similarity metrics
- Architecture: ResNet50 + projection head
- Embedding dimension: 512
- Distance metric: Cosine similarity

### Matching Algorithm
```python
def match_deer(new_embedding, database_embeddings):
    """
    WHY: Incremental matching scales better than clustering
    """
    similarities = cosine_similarity(new_embedding, database_embeddings)
    best_match_idx = np.argmax(similarities)
    best_score = similarities[best_match_idx]
    
    if best_score > REID_THRESHOLD:
        return database_embeddings[best_match_idx].deer_id
    else:
        return create_new_deer_profile()
```

### Threshold Selection
```yaml
reid_thresholds:
  same_day: 0.90      # WHY: Higher confidence for same-day matches
  same_week: 0.85     # WHY: Account for slight appearance changes  
  same_month: 0.80    # WHY: Seasonal coat changes
  default: 0.85       # WHY: Balance between splitting and merging
```

### Feature Update Strategy
**Exponential Moving Average**
- WHY: Adapt to gradual appearance changes
- Formula: `new_features = 0.7 * old_features + 0.3 * current_features`
- Update frequency: Every confirmed sighting
- History limit: Keep last 10 feature vectors

## Stage 5: Group Detection (Advanced)

### Purpose
Identify and track deer traveling together

### Algorithm
1. **Spatial Clustering**
   - WHY: Deer in same frame likely together
   - Method: DBSCAN on bounding box centers
   - Distance threshold: 200 pixels

2. **Temporal Association**
   - WHY: Groups persist across multiple frames
   - Track group IDs across time
   - Minimum duration: 3 consecutive sightings

### Group Metrics
```yaml
group_analysis:
  min_group_size: 2
  max_group_size: 15
  temporal_window: 300  # seconds
  spatial_threshold: 200  # pixels
```

## Performance Optimization

### Batching Strategy
```yaml
batch_processing:
  detection_batch: 16    # WHY: Optimal for GPU memory
  classification_batch: 32  # WHY: Smaller input size
  reid_batch: 64        # WHY: Simple forward pass
```

### Caching
1. **Model Caching**
   - WHY: Avoid repeated model loading
   - Keep models in GPU memory
   - Lazy loading on first request

2. **Feature Caching**
   - WHY: Re-ID needs historical features
   - Cache recent 1000 deer features
   - Redis with 1-hour TTL

### GPU Utilization
```yaml
gpu_config:
  device: "cuda:0"
  mixed_precision: true  # WHY: 2x speedup with minimal accuracy loss
  cudnn_benchmark: true  # WHY: Optimize for consistent input sizes
  num_workers: 4        # WHY: Parallel data loading
```

## Error Handling

### Failure Modes
1. **GPU Out of Memory**
   - Action: Reduce batch size dynamically
   - Fallback: Process single images

2. **Model Load Failure**
   - Action: Retry with exponential backoff
   - Fallback: Mark for manual review

3. **Corrupt Image**
   - Action: Log and skip
   - Store: Original for debugging

### Recovery Strategy
```python
@retry(max_attempts=3, backoff=2)
def process_with_recovery(image):
    try:
        return pipeline.process(image)
    except GPUMemoryError:
        reduce_batch_size()
        return process_with_recovery(image)
    except ModelError:
        reload_models()
        return process_with_recovery(image)
```

## Model Versioning

### Version Control
```yaml
models:
  detection:
    version: "1.0.0"
    path: "models/yolov8n_deer_v1.pt"
    sha256: "abc123..."
  
  classification:
    version: "1.0.0"  
    path: "models/resnet50_sex_v1.pt"
    sha256: "def456..."
  
  reid:
    version: "1.0.0"
    path: "models/reid_deer_v1.pt"
    sha256: "ghi789..."
```

### Update Strategy
1. **A/B Testing**
   - Run old and new models in parallel
   - Compare accuracy on validation set
   - Gradual rollout: 10% -> 50% -> 100%

2. **Backward Compatibility**
   - Keep last 2 versions available
   - Feature vectors include version number
   - Migration script for database updates

## Monitoring & Metrics

### Performance Metrics
```yaml
metrics:
  - images_processed_per_minute
  - average_detection_confidence  
  - classification_accuracy
  - reid_match_rate
  - false_positive_rate
  - gpu_utilization_percent
```

### Quality Metrics
```yaml
quality_checks:
  - detection_recall: > 0.85
  - classification_f1: > 0.80
  - reid_precision: > 0.75
  - processing_time_p95: < 2s
```

### Alerting Thresholds
```yaml
alerts:
  - metric: detection_confidence_avg
    condition: < 0.5
    severity: warning
    
  - metric: gpu_memory_usage
    condition: > 90%
    severity: critical
    
  - metric: processing_failures
    condition: > 5%
    severity: critical
```

## Testing Requirements

### Unit Tests
- Preprocessing functions
- NMS algorithm
- Feature extraction
- Similarity calculations

### Integration Tests  
- Full pipeline flow
- Model loading/unloading
- Batch processing
- Error recovery

### Performance Tests
- Throughput benchmarks
- Memory usage profiles
- GPU utilization
- Latency percentiles

### Accuracy Tests
- Detection mAP on test set
- Classification confusion matrix
- Re-ID rank-1 accuracy
- Group detection IoU

## Data Requirements

### Training Data
```yaml
minimum_training_data:
  detection: 5000 images with bboxes
  classification: 10000 cropped deer
  reid: 1000 individuals with 10+ images each
```

### Validation Data
```yaml
validation_split:
  detection: 20%
  classification: 20%
  reid: 10%  # WHY: Expensive to annotate individuals
```

### Test Data
```yaml
test_requirements:
  source: Different camera/season
  size: 1000 images minimum
  diversity: All 7 locations
```

## Future Enhancements

1. **Behavior Classification**
   - Feeding, walking, alert, bedding
   - Requires video sequences

2. **Age Estimation**
   - Fawn, yearling, adult, senior
   - Based on body proportions

3. **Health Assessment**
   - Injury detection
   - Body condition scoring
   - Disease indicators

4. **Multi-species**
   - Expand to turkey, hogs, predators
   - Shared backbone, multiple heads

5. **Edge Deployment**
   - TensorRT optimization
   - ONNX conversion
   - Jetson deployment

---

**Specification Status**: DRAFT
**Dependencies**: system.spec
**Next Review**: After detection model training
