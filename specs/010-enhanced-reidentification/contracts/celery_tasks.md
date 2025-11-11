# API Contract: Celery Tasks - Enhanced Re-Identification

**Feature**: 010-enhanced-reidentification
**Date**: 2025-11-11
**Phase**: 1 - Design
**Version**: 1.0

## Purpose

This contract defines the Celery task signatures for enhanced re-identification pipeline. Tasks are asynchronous and queued via Redis, processed by GPU-accelerated worker containers.

---

## Task: enhanced_reidentify_detection

**Purpose**: Extract enhanced biometric features (antler, pose, coat, temporal) and match detection to existing deer or create new profile.

**Queue**: `reid` (same as baseline reidentify_detection)

**Module**: `src/worker/tasks/enhanced_reid.py`

### Signature

```python
@celery_app.task(
    name='enhanced_reidentify_detection',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def enhanced_reidentify_detection(
    self,
    detection_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Enhanced re-identification with antler, pose, coat, and temporal features.

    Args:
        detection_id: UUID of detection to process
        config: Optional configuration overrides
            {
                "enable_antler": bool (default: True),
                "enable_pose": bool (default: True),
                "enable_temporal": bool (default: True),
                "enable_coat": bool (default: True),
                "enable_ensemble": bool (default: False),
                "similarity_threshold": float (default: 0.85),
                "fast_mode": bool (default: False)  # ResNet50-only bypass
            }

    Returns:
        {
            "detection_id": str,
            "matched_deer_id": str | None,
            "match_confidence": float,
            "created_new_profile": bool,
            "feature_extraction": {
                "body_features": bool,
                "antler_features": bool,
                "pose_features": bool,
                "coat_features": bool,
                "temporal_score": bool
            },
            "timings": {
                "total_ms": float,
                "body_extraction_ms": float,
                "antler_extraction_ms": float,
                "pose_estimation_ms": float,
                "coat_extraction_ms": float,
                "temporal_scoring_ms": float,
                "matching_ms": float
            },
            "enhancement_metadata": {
                # Stored in detections.enhancement_metadata JSONB column
            }
        }

    Raises:
        DetectionNotFoundError: detection_id does not exist
        ImageFileNotFoundError: Detection's image file missing from filesystem
        ModelLoadError: Failed to load ML models (ResNet50, MMPose, etc.)
        FeatureExtractionError: All feature extractors failed (retryable)
    """
```

### Behavior

1. **Load Detection**: Query database for detection by ID, eager-load image and location
2. **Fast Mode Check**: If config.fast_mode=True, skip to baseline reidentify_detection
3. **Load Image**: Read image file from filesystem (detection.image.path)
4. **Crop Detection**: Extract bounding box region (detection.bbox)
5. **Parallel Feature Extraction**:
   - Body features (ResNet50): Always executed
   - Antler features: If classification in ['buck', 'mature', 'mid', 'young'] AND config.enable_antler=True
   - Pose estimation: If config.enable_pose=True
   - Coat patterns: If config.enable_coat=True
6. **Temporal Scoring**: If config.enable_temporal=True, calculate activity pattern alignment
7. **Weighted Fusion**: Combine features with weights (body: 0.6, antler: 0.25, coat: 0.15, temporal: boost 0.05-0.10)
8. **Database Matching**: Search deer table for similar profiles (pgvector HNSW index)
9. **Match Decision**:
   - If similarity > config.similarity_threshold: Update existing deer profile
   - Else: Create new deer profile
10. **Store Metadata**: Save enhancement_metadata JSONB to detections.enhancement_metadata
11. **Update Temporal Profile**: Increment location frequency, time-of-day histogram for matched deer
12. **Return Result**: Task result with matched_deer_id and timings

### Error Handling

- **Retry Strategy**: Exponential backoff, max 3 retries
- **Graceful Degradation**: If antler/pose/coat extraction fails, continue with available features
- **Fallback**: If all enhancements fail, fallback to baseline ResNet50-only matching
- **Dead Letter Queue**: After 3 retries, log error and mark detection.processing_status = 'failed'

### Configuration Defaults

```python
DEFAULT_CONFIG = {
    "enable_antler": True,
    "enable_pose": True,
    "enable_temporal": True,
    "enable_coat": True,
    "enable_ensemble": False,  # Expensive, opt-in only
    "similarity_threshold": 0.85,
    "fast_mode": False,
    "antler_weight": 0.25,
    "body_weight": 0.6,
    "coat_weight": 0.15,
    "temporal_boost": 0.10  # Maximum boost from temporal alignment
}
```

---

## Task: batch_enhanced_reidentify

**Purpose**: Process multiple detections in batch for improved GPU utilization (ensemble mode).

**Queue**: `reid`

**Module**: `src/worker/tasks/enhanced_reid.py`

### Signature

```python
@celery_app.task(
    name='batch_enhanced_reidentify',
    bind=True,
    max_retries=2
)
def batch_enhanced_reidentify(
    self,
    detection_ids: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Batch process multiple detections with ensemble mode for maximum accuracy.

    Args:
        detection_ids: List of detection UUIDs (max 16 for memory constraints)
        config: Optional configuration (same as enhanced_reidentify_detection)

    Returns:
        {
            "total_detections": int,
            "successful": int,
            "failed": int,
            "results": [
                {
                    "detection_id": str,
                    "matched_deer_id": str | None,
                    "match_confidence": float,
                    "created_new_profile": bool
                },
                ...
            ],
            "batch_timings": {
                "total_ms": float,
                "feature_extraction_ms": float,  # Parallel batch inference
                "matching_ms": float
            }
        }

    Raises:
        BatchSizeExceededError: detection_ids length > 16
        PartialBatchFailureError: Some detections failed (includes partial results)
    """
```

### Behavior

1. **Validate Batch Size**: Raise error if len(detection_ids) > 16 (GPU memory constraint)
2. **Load All Detections**: Bulk query database
3. **Batch Feature Extraction**:
   - Load images and crop all bounding boxes
   - Run ResNet50 on batch (batch_size=16)
   - Run EfficientNet-B3 on batch (if ensemble mode)
   - Run ViT-B/16 on batch (if ensemble mode)
   - Run MMPose on batch (if pose enabled)
4. **Individual Matching**: For each detection, match against deer database
5. **Bulk Database Updates**: Update all detections and deer profiles in single transaction
6. **Return Batch Result**: Aggregated success/failure counts

### Error Handling

- **Partial Failure**: If some detections fail, continue processing others
- **All Failure**: If batch extraction fails entirely, fallback to individual processing
- **Retry Logic**: Retry batch once, then fallback to individual tasks

---

## Task: extract_antler_features

**Purpose**: Extract antler geometric and visual features from deer detection crop.

**Queue**: `reid` (low priority)

**Module**: `src/worker/tasks/antler_features.py`

### Signature

```python
@celery_app.task(name='extract_antler_features')
def extract_antler_features(
    detection_id: str
) -> Dict[str, Any]:
    """
    Extract antler pattern fingerprint from buck detection.

    Args:
        detection_id: UUID of buck detection with visible antlers

    Returns:
        {
            "detection_id": str,
            "antler_fingerprint": List[float],  # 64-dim vector
            "point_count_estimate": int,
            "spread_width_px": float,
            "symmetry_score": float,  # 0-1
            "extraction_success": bool,
            "inference_time_ms": float
        }

    Raises:
        AntlerNotVisibleError: Rear view or antlers occluded
        DetectionNotBuckError: Classification is not buck/mature/mid/young
    """
```

### Behavior

1. **Validate Classification**: Ensure detection.classification in buck classes
2. **Load Image Crop**: Extract upper 30% of bounding box (antler region)
3. **Detect Antler Presence**: Use edge detection + contour analysis (OpenCV)
4. **Extract Geometric Features**: Point count, spread, symmetry, tine angles
5. **Create Fingerprint Vector**: Normalize to 64-dim vector
6. **Return Result**: Vector + metadata

---

## Task: extract_pose_features

**Purpose**: Detect deer pose and extract normalized feature vector.

**Queue**: `reid`

**Module**: `src/worker/tasks/pose_estimation.py`

### Signature

```python
@celery_app.task(name='extract_pose_features')
def extract_pose_features(
    detection_id: str
) -> Dict[str, Any]:
    """
    Estimate deer pose and extract normalized features.

    Args:
        detection_id: UUID of detection

    Returns:
        {
            "detection_id": str,
            "pose_classification": str,  # frontal/profile_left/profile_right/rear/angled
            "pose_angle": float,  # Degrees (0-360)
            "pose_confidence": float,  # 0-1
            "keypoints": {
                "nose": [x, y, confidence],
                "left_ear": [x, y, confidence],
                "right_ear": [x, y, confidence],
                "shoulder": [x, y, confidence],
                "hip": [x, y, confidence],
                "tail_base": [x, y, confidence]
            },
            "normalized_features": List[float],  # Pose-corrected body features
            "extraction_success": bool,
            "inference_time_ms": float
        }
    """
```

### Behavior

1. **Load MMPose Model**: AP-10K animal pose checkpoint
2. **Run Keypoint Detection**: Detect 6 keypoints (nose, ears, shoulder, hip, tail)
3. **Classify Pose**: Calculate viewing angle from keypoint geometry
4. **Normalize Features**: Apply pose-specific transformation to align to canonical profile
5. **Return Result**: Pose metadata + normalized features

---

## Task: extract_coat_patterns

**Purpose**: Extract coat color patterns and detect unique markings.

**Queue**: `reid`

**Module**: `src/worker/tasks/coat_patterns.py`

### Signature

```python
@celery_app.task(name='extract_coat_patterns')
def extract_coat_patterns(
    detection_id: str
) -> Dict[str, Any]:
    """
    Extract coat color patterns from deer detection.

    Args:
        detection_id: UUID of detection

    Returns:
        {
            "detection_id": str,
            "coat_pattern_vector": List[float],  # 192-dim vector
            "detected_markings": [
                {
                    "type": "white_chest_patch" | "facial_blaze" | "scar",
                    "region": "chest" | "face" | "flank" | "leg",
                    "size_px": int,
                    "contrast_ratio": float
                }
            ],
            "extraction_success": bool,
            "inference_time_ms": float
        }
    """
```

### Behavior

1. **Segment Body Regions**: Divide crop into chest/flanks/face/legs (25%/50%/15%/15%)
2. **Extract Color Histograms**: 16 bins per RGB channel = 48-dim per region
3. **Normalize Illumination**: Histogram equalization
4. **Detect High-Contrast Markings**: White patches, blazes, scars (>2x brightness difference)
5. **Create Pattern Vector**: Concatenate 4 region histograms (192-dim)
6. **Return Result**: Vector + marking metadata

---

## Task: calculate_temporal_score

**Purpose**: Calculate temporal similarity between new detection and candidate deer profiles.

**Queue**: `reid` (high priority, <5ms)

**Module**: `src/worker/tasks/temporal_scoring.py`

### Signature

```python
@celery_app.task(name='calculate_temporal_score')
def calculate_temporal_score(
    detection_id: str,
    candidate_deer_ids: List[str]
) -> Dict[str, float]:
    """
    Calculate temporal context scores for candidate matches.

    Args:
        detection_id: UUID of new detection
        candidate_deer_ids: List of candidate deer UUIDs from visual matching

    Returns:
        {
            "deer_id_1": 0.85,  # High alignment (same location, same time-of-day)
            "deer_id_2": 0.42,  # Low alignment (different patterns)
            "deer_id_3": 0.0    # Temporal conflict (simultaneous detection at different location)
        }
    """
```

### Behavior

1. **Load Detection Metadata**: Timestamp, location_id from detection.image
2. **Load Deer Temporal Profiles**: Query deer.temporal_profile JSONB for each candidate
3. **Calculate Location Similarity**: Frequency overlap between detection location and deer's location distribution
4. **Calculate Time-of-Day Similarity**: Histogram overlap (detection hour vs deer's hourly activity)
5. **Detect Temporal Conflicts**: Check for simultaneous detections at distant locations (<5min apart, >1km distance)
6. **Return Scores**: Dict mapping deer_id to temporal similarity (0-1)

---

## Task: update_deer_temporal_profile

**Purpose**: Incrementally update deer activity patterns after new sighting.

**Queue**: `background` (low priority)

**Module**: `src/worker/tasks/temporal_scoring.py`

### Signature

```python
@celery_app.task(name='update_deer_temporal_profile')
def update_deer_temporal_profile(
    deer_id: str,
    detection_id: str
) -> Dict[str, Any]:
    """
    Update deer's temporal profile with new sighting information.

    Args:
        deer_id: UUID of deer profile
        detection_id: UUID of new detection matched to this deer

    Returns:
        {
            "deer_id": str,
            "updated_profile": {
                # Updated temporal_profile JSONB content
            },
            "profile_updated": bool
        }
    """
```

### Behavior

1. **Load Deer Profile**: Query deer.temporal_profile
2. **Load Detection**: Get timestamp, location_id
3. **Update Location Frequency**: Increment location_frequency[location_id]
4. **Update Time-of-Day Histogram**: Increment hour bin (0-23)
5. **Update Seasonal Presence**: Add current season if not present
6. **Recalculate Favorites**: Find most frequent location and time window
7. **Save Updated Profile**: Update deer.temporal_profile JSONB
8. **Return Result**: Confirmation + updated profile

---

## Configuration Management

### Environment Variables

```bash
# Feature toggles (docker-compose.yml or .env)
ENHANCED_REID_ENABLE_ANTLER=true
ENHANCED_REID_ENABLE_POSE=true
ENHANCED_REID_ENABLE_TEMPORAL=true
ENHANCED_REID_ENABLE_COAT=true
ENHANCED_REID_ENABLE_ENSEMBLE=false  # Expensive, opt-in

# Performance tuning
ENHANCED_REID_SIMILARITY_THRESHOLD=0.85
ENHANCED_REID_BATCH_SIZE=16
ENHANCED_REID_PARALLEL_WORKERS=4

# Model paths
MMPOSE_MODEL_PATH=/app/src/models/pose/ap10k_mobilenetv2.pth
ENSEMBLE_EFFICIENTNET_PATH=/app/src/models/reid/efficientnet_b3_reid.pt
ENSEMBLE_VIT_PATH=/app/src/models/reid/vit_b16_reid.pt
```

### Runtime Configuration (Per-Task)

```python
# Example: Disable antler extraction for doe detections
enhanced_reidentify_detection.apply_async(
    args=[detection_id],
    kwargs={
        "config": {
            "enable_antler": False,  # Override for this detection
            "enable_pose": True,
            "enable_coat": True,
            "enable_temporal": True,
            "similarity_threshold": 0.80  # More lenient threshold
        }
    }
)
```

---

## Task Routing

### Celery Queue Configuration

```python
# src/worker/celery_app.py

CELERY_TASK_ROUTES = {
    # High priority: Quick temporal scoring
    'calculate_temporal_score': {'queue': 'reid', 'priority': 10},

    # Normal priority: Main re-ID tasks
    'enhanced_reidentify_detection': {'queue': 'reid', 'priority': 5},
    'batch_enhanced_reidentify': {'queue': 'reid', 'priority': 5},

    # Low priority: Feature extraction (can be async)
    'extract_antler_features': {'queue': 'reid', 'priority': 2},
    'extract_pose_features': {'queue': 'reid', 'priority': 2},
    'extract_coat_patterns': {'queue': 'reid', 'priority': 2},

    # Background: Profile updates (non-blocking)
    'update_deer_temporal_profile': {'queue': 'background', 'priority': 1},
}
```

---

## Testing Contracts

### Unit Test Requirements

Each task must have unit tests covering:
1. **Success Case**: Valid input, successful execution
2. **Invalid Input**: Raise appropriate error (DetectionNotFoundError, etc.)
3. **Graceful Degradation**: Feature extraction fails, fallback to baseline
4. **Retry Logic**: Transient failure triggers retry
5. **Timeout**: Task completes within performance budget (antler <0.2s, pose <0.15s, etc.)

### Integration Test Requirements

1. **End-to-End Pipeline**: Image upload → detection → enhanced re-ID → deer profile created
2. **Batch Processing**: 16 detections processed in single batch, all matched correctly
3. **Temporal Scoring**: Deer's temporal profile updated after new sighting
4. **Seasonal Archiving**: Buck's antler fingerprint archived by season

---

## Phase 1 Exit Criteria

- [X] Task signatures defined with type annotations
- [X] Input/output contracts documented
- [X] Error handling strategy specified
- [X] Configuration management defined
- [X] Task routing and priority specified
- [X] Testing requirements outlined

**Status**: COMPLETE - Celery task contracts defined

---

## Next Steps

1. Generate contracts/api_endpoints.md: REST API updates for deer enhancement metadata
2. Generate quickstart.md: Developer setup guide
