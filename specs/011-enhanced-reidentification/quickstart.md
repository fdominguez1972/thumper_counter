# Developer Quickstart: Enhanced Re-Identification Pipeline

**Feature**: 010-enhanced-reidentification
**Date**: 2025-11-11
**Phase**: 1 - Design
**Version**: 1.0

## Purpose

This quickstart guide helps developers set up the enhanced re-identification pipeline on their local development environment. Covers installation, configuration, testing, and debugging.

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 22.04+ (Linux) or Windows 10/11 with WSL2
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3060 or better), CUDA 11.8+
- **RAM**: 16GB+ recommended
- **Disk**: 20GB free space (for models and datasets)
- **Docker**: Docker Desktop 24.0+ with GPU support
- **Python**: 3.11+ (for local testing outside containers)

### Knowledge Prerequisites

- Familiarity with Docker Compose
- Basic understanding of ML concepts (feature extraction, embeddings)
- Experience with Celery task queues (helpful but not required)

---

## Installation

### Step 1: Clone Repository and Checkout Feature Branch

```bash
cd /path/to/thumper_counter
git fetch origin
git checkout 010-enhanced-reidentification

# Or create new branch from main
git checkout main
git checkout -b 010-enhanced-reidentification
```

### Step 2: Install Python Dependencies

Update `requirements.txt` to include MMPose and dependencies:

```bash
# Add to requirements.txt
mmpose==1.3.0
mmcv==2.1.0
mmengine==0.10.0
opencv-python==4.8.1.78
scikit-learn==1.3.2
```

Rebuild worker container to install dependencies:

```bash
docker-compose build worker
```

### Step 3: Download Pre-Trained Models

#### 3.1 MMPose AP-10K Animal Pose Model

```bash
# Create pose models directory
mkdir -p src/models/pose

# Download AP-10K MobileNetV2 checkpoint (28MB)
wget https://download.openmmlab.com/mmpose/animal/2d_kpt_sview_rgb_img/topdown_heatmap/ap10k/mobilenetv2_ap10k_256x256-72f1c2bf_20211027.pth \
    -O src/models/pose/ap10k_mobilenetv2.pth

# Verify download
ls -lh src/models/pose/ap10k_mobilenetv2.pth
# Expected: ~28MB
```

#### 3.2 Ensemble Models (Optional - For Phase 4)

```bash
# Create reid ensemble directory
mkdir -p src/models/reid

# Download EfficientNet-B3 pretrained on ImageNet
python3 -c "
import torch
import torchvision.models as models

# Download EfficientNet-B3
efficientnet = models.efficientnet_b3(weights='IMAGENET1K_V1')
torch.save(efficientnet.state_dict(), 'src/models/reid/efficientnet_b3_imagenet.pt')
print('[OK] EfficientNet-B3 downloaded')
"

# Download Vision Transformer ViT-B/16
python3 -c "
import torch
import torchvision.models as models

# Download ViT-B/16
vit = models.vit_b_16(weights='IMAGENET1K_V1')
torch.save(vit.state_dict(), 'src/models/reid/vit_b16_imagenet.pt')
print('[OK] ViT-B/16 downloaded')
"

# Verify ensemble models
ls -lh src/models/reid/
# Expected:
#   efficientnet_b3_imagenet.pt (~45MB)
#   vit_b16_imagenet.pt (~85MB)
```

### Step 4: Run Database Migration

Apply migration 011 to add enhanced re-ID columns:

```bash
# Start database container
docker-compose up -d db

# Wait for PostgreSQL to be ready
sleep 5

# Run migration
docker-compose exec db psql -U deertrack deer_tracking -f /migrations/011_add_enhanced_reid_columns.sql

# Verify migration
docker-compose exec db psql -U deertrack deer_tracking -c "
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'deer'
    AND column_name IN ('antler_fingerprint', 'coat_pattern', 'temporal_profile', 'best_pose_metadata');
"
# Expected: 4 rows (antler_fingerprint: USER-DEFINED, coat_pattern: USER-DEFINED, temporal_profile: jsonb, best_pose_metadata: jsonb)
```

### Step 5: Configure Environment Variables

Add enhanced re-ID configuration to `.env`:

```bash
# Enhanced Re-ID Feature Toggles
ENHANCED_REID_ENABLE_ANTLER=true
ENHANCED_REID_ENABLE_POSE=true
ENHANCED_REID_ENABLE_TEMPORAL=true
ENHANCED_REID_ENABLE_COAT=true
ENHANCED_REID_ENABLE_ENSEMBLE=false  # Expensive, opt-in

# Performance Tuning
ENHANCED_REID_SIMILARITY_THRESHOLD=0.85
ENHANCED_REID_BATCH_SIZE=16
ENHANCED_REID_PARALLEL_WORKERS=4

# Model Paths
MMPOSE_MODEL_PATH=/app/src/models/pose/ap10k_mobilenetv2.pth
MMPOSE_CONFIG_PATH=/app/src/models/pose/ap10k_config.py
ENSEMBLE_EFFICIENTNET_PATH=/app/src/models/reid/efficientnet_b3_imagenet.pt
ENSEMBLE_VIT_PATH=/app/src/models/reid/vit_b16_imagenet.pt
```

### Step 6: Start Services

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# Expected output:
# NAME                COMMAND              STATUS    PORTS
# backend             uvicorn ...          Up        0.0.0.0:8001->8000/tcp
# worker              celery worker ...    Up
# db                  postgres ...         Up        5433:5432/tcp
# redis               redis-server ...     Up        6380:6379/tcp
# frontend            npm start ...        Up        0.0.0.0:3000->3000/tcp

# Monitor worker logs
docker-compose logs -f worker
```

---

## Testing

### Test 1: Verify Model Loading

Test that MMPose model loads successfully in worker:

```bash
docker-compose exec worker python3 -c "
import torch
from mmpose.apis import init_model

config_path = '/app/src/models/pose/ap10k_config.py'
checkpoint_path = '/app/src/models/pose/ap10k_mobilenetv2.pth'

print('[INFO] Loading MMPose model...')
model = init_model(config_path, checkpoint_path, device='cuda:0')
print('[OK] MMPose model loaded successfully')
print(f'[INFO] Model on device: {next(model.parameters()).device}')
"
```

**Expected Output**:
```
[INFO] Loading MMPose model...
[OK] MMPose model loaded successfully
[INFO] Model on device: cuda:0
```

### Test 2: Run Antler Feature Extraction

Test antler extraction on a sample buck image:

```bash
# Find a buck detection from database
docker-compose exec backend python3 -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.detection import Detection
from backend.models.image import Image
import os

db_url = f\"postgresql://{os.getenv('POSTGRES_USER', 'deertrack')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'deer_tracking')}\"

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

# Find first buck detection
buck_det = db.query(Detection).filter(Detection.classification == 'buck').first()
if buck_det:
    print(f'[OK] Found buck detection: {buck_det.id}')
    print(f'[INFO] Image: {buck_det.image.path}')
    print(f'[INFO] Bbox: {buck_det.bbox}')
else:
    print('[WARN] No buck detections found. Upload images first.')
"

# Queue antler extraction task (replace DETECTION_ID with output from above)
docker-compose exec worker python3 -c "
from src.worker.tasks.antler_features import extract_antler_features

detection_id = 'DETECTION_ID'  # Replace with actual UUID
result = extract_antler_features.delay(detection_id)

print(f'[INFO] Task queued: {result.id}')
print('[INFO] Waiting for result...')
output = result.get(timeout=30)
print('[OK] Antler extraction complete:')
print(f'  Point count: {output[\"point_count_estimate\"]}')
print(f'  Spread: {output[\"spread_width_px\"]}px')
print(f'  Symmetry: {output[\"symmetry_score\"]}')
print(f'  Time: {output[\"inference_time_ms\"]}ms')
"
```

### Test 3: Run Pose Estimation

Test pose detection on a sample image:

```bash
docker-compose exec worker python3 scripts/test_pose_estimation.py --detection-id DETECTION_ID
```

**Expected Output**:
```
[INFO] Loading detection: DETECTION_ID
[INFO] Loading MMPose model...
[INFO] Running pose estimation...
[OK] Pose detection complete:
  Classification: profile_left
  Angle: 85 degrees
  Confidence: 0.87
  Keypoints detected: 6/6
  Inference time: 52ms
```

### Test 4: End-to-End Enhanced Re-ID

Test full enhanced re-ID pipeline on a detection:

```bash
docker-compose exec worker python3 -c "
from src.worker.tasks.enhanced_reid import enhanced_reidentify_detection

detection_id = 'DETECTION_ID'  # Replace with actual UUID
config = {
    'enable_antler': True,
    'enable_pose': True,
    'enable_temporal': True,
    'enable_coat': True,
    'enable_ensemble': False
}

print('[INFO] Queuing enhanced re-ID task...')
result = enhanced_reidentify_detection.delay(detection_id, config)
output = result.get(timeout=60)

print('[OK] Enhanced re-ID complete:')
print(f'  Matched deer: {output[\"matched_deer_id\"]}')
print(f'  Confidence: {output[\"match_confidence\"]}')
print(f'  Created new profile: {output[\"created_new_profile\"]}')
print(f'  Total time: {output[\"timings\"][\"total_ms\"]}ms')
print(f'  Features extracted:')
for feature, success in output['feature_extraction'].items():
    print(f'    {feature}: {success}')
"
```

### Test 5: Batch Processing

Test batch processing with 16 detections:

```bash
docker-compose exec worker python3 scripts/test_batch_reid.py --count 16
```

**Expected Output**:
```
[INFO] Selecting 16 random detections...
[INFO] Queuing batch enhanced re-ID...
[OK] Batch processing complete:
  Total: 16
  Successful: 16
  Failed: 0
  Batch time: 8.2s (512ms per detection)
  Throughput: 1.95 detections/second
```

---

## Development Workflow

### Adding New Feature Extractors

1. **Create module**: `src/worker/tasks/new_feature.py`
2. **Define task**:
   ```python
   @celery_app.task(name='extract_new_feature')
   def extract_new_feature(detection_id: str) -> Dict[str, Any]:
       # Implementation
       pass
   ```
3. **Register task**: Import in `src/worker/celery_app.py`
4. **Add unit tests**: `tests/worker/test_new_feature.py`
5. **Integrate**: Call from `enhanced_reidentify_detection` task
6. **Update schema**: Add fields to `enhancement_metadata` JSONB

### Debugging Re-ID Matches

View enhancement metadata for a detection:

```bash
docker-compose exec backend python3 -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.detection import Detection
import os
import json

db_url = f\"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}\"

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

detection_id = 'DETECTION_ID'
det = db.query(Detection).filter(Detection.id == detection_id).first()

if det and det.enhancement_metadata:
    print(json.dumps(det.enhancement_metadata, indent=2))
else:
    print('[WARN] No enhancement metadata found')
"
```

### Performance Profiling

Profile feature extraction timing:

```bash
docker-compose exec worker python3 scripts/profile_enhanced_reid.py --detections 100
```

**Expected Output**:
```
[INFO] Profiling 100 detections...

Average Timings (ms):
  Body extraction (ResNet50): 89
  Antler extraction:          185
  Pose estimation:            52
  Coat patterns:              95
  Temporal scoring:           3
  Database matching:          45
  Total (sequential):         469
  Total (parallel):           224  # Body, antler, pose, coat run in parallel

Throughput:
  Sequential: 2.1 det/s
  Parallel:   4.5 det/s

GPU Utilization: 78%
Memory Usage: 5.2GB / 16GB
```

---

## Configuration Tuning

### Adjusting Similarity Thresholds

Test different thresholds to find optimal matching:

```bash
# Test with lenient threshold (more matches, higher false positives)
docker-compose exec worker python3 scripts/tune_threshold.py --threshold 0.75 --test-detections 100

# Test with strict threshold (fewer matches, higher accuracy)
docker-compose exec worker python3 scripts/tune_threshold.py --threshold 0.90 --test-detections 100

# Recommended: 0.85 for balanced accuracy
```

### Adjusting Feature Weights

Experiment with different feature fusion weights:

```python
# src/worker/tasks/enhanced_reid.py

# Current weights
DEFAULT_WEIGHTS = {
    'body': 0.6,     # ResNet50 body features
    'antler': 0.25,  # Antler geometric features
    'coat': 0.15,    # Coat color patterns
    'temporal': 0.10  # Temporal boost (additive)
}

# Example: Increase antler weight for mature bucks
if classification == 'mature':
    weights = {'body': 0.5, 'antler': 0.35, 'coat': 0.15, 'temporal': 0.10}
```

### Selective Enhancement (Performance Optimization)

Enable selective enhancement to reduce processing time:

```python
# src/worker/tasks/enhanced_reid.py

def should_extract_antler(detection):
    """Only extract antlers for buck classifications."""
    return detection.classification in ['buck', 'mature', 'mid', 'young']

def should_use_pose_normalization(detection, baseline_confidence):
    """Only normalize pose when baseline confidence is low."""
    return baseline_confidence < 0.75
```

---

## Troubleshooting

### Issue 1: MMPose Model Not Loading

**Symptom**: `FileNotFoundError: /app/src/models/pose/ap10k_mobilenetv2.pth not found`

**Solution**:
```bash
# Verify model file exists in container
docker-compose exec worker ls -lh /app/src/models/pose/

# If missing, download again and rebuild
wget https://download.openmmlab.com/mmpose/animal/2d_kpt_sview_rgb_img/topdown_heatmap/ap10k/mobilenetv2_ap10k_256x256-72f1c2bf_20211027.pth \
    -O src/models/pose/ap10k_mobilenetv2.pth

docker-compose build worker
docker-compose restart worker
```

### Issue 2: CUDA Out of Memory

**Symptom**: `RuntimeError: CUDA out of memory`

**Solution**:
```bash
# Reduce batch size in .env
ENHANCED_REID_BATCH_SIZE=8  # Down from 16

# Or disable ensemble mode
ENHANCED_REID_ENABLE_ENSEMBLE=false

# Restart worker
docker-compose restart worker
```

### Issue 3: Pose Estimation Fails on Some Images

**Symptom**: `PoseEstimationError: Failed to detect keypoints`

**Solution**:
```python
# Implement graceful fallback in pose_estimation.py

try:
    keypoints = model.predict(image)
    if keypoints['confidence'] < 0.6:
        raise PoseEstimationError("Low confidence")
except Exception as e:
    logger.warning(f"Pose estimation failed: {e}. Using baseline features.")
    return {
        'extraction_success': False,
        'normalized_features': None,  # Will trigger fallback
        'error': str(e)
    }
```

### Issue 4: Temporal Conflicts False Positives

**Symptom**: Detections marked with temporal_conflict when same deer at different cameras

**Solution**:
```bash
# Check location distances in database
docker-compose exec db psql -U deertrack deer_tracking -c "
    SELECT l1.name, l2.name,
           ST_Distance(l1.coordinates, l2.coordinates) AS distance_meters
    FROM locations l1, locations l2
    WHERE l1.id != l2.id;
"

# Adjust temporal conflict distance threshold (currently 1km)
# In src/worker/tasks/temporal_scoring.py
TEMPORAL_CONFLICT_DISTANCE_KM = 2.0  # Increase to 2km
```

---

## Next Steps

After completing quickstart:

1. **Phase 2 Implementation**: Begin coding antler extraction module
2. **Phase 2 Testing**: Benchmark on rut season dataset (6,115 images)
3. **Phase 3 Implementation**: Add pose normalization
4. **Phase 4 Implementation**: Implement ensemble mode (optional)
5. **Phase 5 Deployment**: Production deployment and monitoring

---

## Additional Resources

### Documentation

- MMPose Documentation: https://mmpose.readthedocs.io/
- PyTorch torchvision Models: https://pytorch.org/vision/stable/models.html
- pgvector HNSW Index: https://github.com/pgvector/pgvector

### Scripts

- `scripts/test_antler_extraction.py` - Test antler feature extraction
- `scripts/test_pose_estimation.py` - Test pose detection
- `scripts/benchmark_enhanced_reid.py` - Performance benchmarking
- `scripts/tune_threshold.py` - Similarity threshold tuning
- `scripts/profile_enhanced_reid.py` - Profiling tool

### Useful Commands

```bash
# Check worker task queue
docker-compose exec redis redis-cli LLEN celery

# Monitor Celery tasks (Flower UI)
open http://localhost:5555

# View enhancement statistics
curl http://localhost:8001/api/stats/enhancements | jq

# Re-process specific deer with enhancements
curl -X POST http://localhost:8001/api/deer/DEER_ID/reprocess_enhancements \
    -H "Content-Type: application/json" \
    -d '{"config": {"enable_ensemble": true}}'
```

---

## Phase 1 Exit Criteria

- [X] Installation steps documented
- [X] Model download instructions provided
- [X] Database migration guide included
- [X] Testing procedures defined
- [X] Development workflow outlined
- [X] Troubleshooting guide provided

**Status**: COMPLETE - Developer quickstart guide ready

---

**Need Help?** Open an issue on GitHub or check the troubleshooting section above.
