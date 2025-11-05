# ML Models Directory

This directory stores trained models for the Thumper Counter ML pipeline.

## Available Models

### 1. YOLOv8 Detection Model [READY]

**File:** `yolov8n_deer.pt` (22 MB)
**Status:** Copied from original deer_tracker project
**Purpose:** Detect deer in trail camera images

**Model Details:**
- Architecture: YOLOv8n (nano variant)
- Training: Custom-trained on whitetail deer dataset
- Source: Roboflow dataset v46 (buck_classes_v046)
- Performance: 50+ FPS on RTX 4070 (higher on RTX 4080 Super)
- Confidence threshold: 0.5 (configurable)
- IOU threshold: 0.45
- Max detections: 20 per image

**Configuration in `.env`:**
```env
MODEL_DIR=/app/src/models
# Model will load from: ${MODEL_DIR}/yolov8n_deer.pt
```

**Testing:**
```python
from ultralytics import YOLO
model = YOLO('src/models/yolov8n_deer.pt')
results = model.predict('path/to/image.jpg', conf=0.5)
```

---

### 2. Sex Classification Model [NEEDS TRAINING]

**File:** `resnet50_sex_classification.pt` (NOT YET CREATED)
**Status:** Needs to be trained
**Purpose:** Classify deer as buck/doe/fawn/unknown

**Model Specification (from specs/ml.spec):**
- Architecture: ResNet50 backbone + custom classification head
- Input size: 224x224 (cropped deer from detections)
- Output classes: buck, doe, fawn, unknown
- Output: Softmax probabilities + 2048-dim feature vector

**Training Requirements:**
```yaml
dataset:
  buck: 5000 images      # Adult male with antlers
  doe: 5000 images       # Adult female
  fawn: 2000 images      # Young deer
  unknown: 1000 images   # Ambiguous/obscured

training:
  batch_size: 32
  epochs: 50
  optimizer: Adam
  learning_rate: 0.001
  augmentation: true
  validation_split: 0.2

thresholds:
  buck: 0.7
  doe: 0.7
  fawn: 0.8
  unknown: 0.0  # No threshold needed
```

**Workaround Until Trained:**
The original deer_tracker project used heuristics based on bounding box size:
- Large bbox (>0.3 area) -> likely buck (low confidence 0.3)
- Small bbox (<0.1 area) -> likely fawn (low confidence 0.2)
- Medium -> unknown (confidence 0.1)

For production use, a trained model is required for accurate classification.

**Training Resources:**
- Original code: `/mnt/i/deer_tracker/backend/app/ml/sex_classifier.py`
- Dataset: Images from 7 camera locations (40,617 total images)
- Annotation: Will need manual labeling of buck/doe/fawn

---

### 3. Re-Identification Model [NEEDS TRAINING]

**File:** `resnet50_reid.pt` (NOT YET CREATED)
**Status:** Needs to be trained
**Purpose:** Match individual deer across images for tracking

**Model Specification (from specs/ml.spec):**
- Architecture: ResNet50 + projection head
- Embedding dimension: 512 (projected) or 2048 (layer4)
- Training method: Triplet loss for metric learning
- Distance metric: Cosine similarity
- Threshold: 0.85 (default), 0.90 (same day), 0.80 (same month)

**Training Requirements:**
```yaml
dataset:
  individuals: 1000+          # Unique deer
  images_per_individual: 10+  # Multiple sightings
  triplets: Generated on-the-fly during training

training:
  batch_size: 64
  triplet_margin: 0.2
  embedding_dim: 512
  epochs: 100
  hard_negative_mining: true
```

**Feature Update Strategy:**
- Exponential Moving Average: `new = 0.7 * old + 0.3 * current`
- WHY: Adapts to gradual appearance changes (seasonal coats, antler growth)
- History: Keep last 10 feature vectors per individual

**Workaround Until Trained:**
The original deer_tracker project used basic feature extraction:
- Color histograms (48 features)
- Gray histograms (64 features)
- Edge density grid (100 features)
- HOG features (256 features)
- Spatial features (44 features)
- Total: 512-dimensional vector

This provides ~70% accuracy but is not robust to:
- Lighting changes
- Seasonal coat changes
- Different camera angles
- Partial occlusions

For production use, a trained deep learning model is required.

**Training Resources:**
- Original code: `/mnt/i/deer_tracker/backend/app/ml/reid_engine.py`
- Dataset: Need to build from detections with verified identities
- Pre-training: Consider transfer learning from person re-ID models

---

## Model Training Workflow

### Step 1: Data Preparation

1. **Extract detections** from 40,617 images using YOLOv8 model
2. **Create crops** for each detection (224x224 for classification)
3. **Manual annotation** for classification:
   - Use UI to label buck/doe/fawn/unknown
   - Export to training dataset format
4. **Identity assignment** for re-ID:
   - Track deer manually across multiple sightings
   - Build triplet dataset with anchor/positive/negative

### Step 2: Model Training

See planned documentation:
- `docs/MODEL_TRAINING.md` (to be created)
- `scripts/train_classifier.py` (to be created)
- `scripts/train_reid.py` (to be created)

### Step 3: Model Evaluation

Test on held-out validation set:
- Detection mAP on test images
- Classification confusion matrix
- Re-ID rank-1 accuracy

### Step 4: Deployment

1. Save trained models to `src/models/`
2. Update `src/worker/tasks/process_images.py` model paths
3. Restart Celery worker
4. Monitor performance metrics via Flower

---

## GPU Requirements

**Hardware:** RTX 4080 Super (16GB VRAM)

**Memory Budget:**
- YOLOv8n: ~2GB
- Classification (batch=32): ~3GB
- Re-ID (batch=64): ~4GB
- Total: ~9GB (leaves 7GB headroom)

**Batch Sizes (configured for RTX 4080 Super):**
```env
DETECTION_BATCH_SIZE=16
CLASSIFICATION_BATCH_SIZE=32
REID_BATCH_SIZE=64
MIXED_PRECISION=true  # Enable for 2x speedup
```

---

## Model Versioning

Track model versions in this README:

| Model | Version | Date | mAP/Accuracy | Notes |
|-------|---------|------|--------------|-------|
| YOLOv8 Detection | 1.0.0 | 2025-11-03 | TBD | Copied from deer_tracker |
| Sex Classification | - | - | - | Not yet trained |
| Re-Identification | - | - | - | Not yet trained |

---

## References

- **YOLOv8:** https://github.com/ultralytics/ultralytics
- **Original Project:** `/mnt/i/deer_tracker/`
- **Roboflow Dataset:** Whitetail Deer v46 (buck_classes_v046)
- **Spec:** `specs/ml.spec` for detailed requirements
