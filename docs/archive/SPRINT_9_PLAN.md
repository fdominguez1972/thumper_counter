# Sprint 9: Re-Identification GPU Acceleration

**Branch:** 005-reid-gpu-optimization
**Start Date:** November 7, 2025
**Duration:** 4-6 hours (estimated)
**Status:** Planning

## Sprint Goal

**Accelerate re-identification from 2s per detection to <0.2s by moving ResNet50 inference to GPU.**

## Current Bottleneck Analysis

### Performance Profile (After Sprint 8)
```
Detection pipeline breakdown:
- GPU inference (YOLOv8):  0.04s  (2%)
- Database writes:         0.03s  (1%)
- Re-ID (ResNet50):        2.00s  (97%)  <- BOTTLENECK
----------------------------------------
Total per image:           2.07s
```

### Root Cause
**ResNet50 is running on CPU instead of GPU.**

Evidence from code review (`src/worker/tasks/reidentification.py:175`):
```python
# Line 48: DEVICE set correctly
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Line 101: Model moved to GPU in get_reid_model()
_reid_model = _reid_model.to(DEVICE)

# Line 175: Tensor moved to GPU
img_tensor = transform(crop).unsqueeze(0).to(DEVICE)
```

**Analysis:** Code looks correct. Model should be on GPU. Need to verify actual execution.

## Sprint Objectives

### Primary Goals

1. **Verify GPU utilization during re-ID**
   - Add GPU memory monitoring
   - Confirm model is actually running on GPU
   - Measure actual GPU vs CPU performance

2. **Optimize ResNet50 inference**
   - Enable TensorRT/ONNX if beneficial
   - Implement batch processing (process multiple detections at once)
   - Test different batch sizes (1, 4, 8, 16, 32)

3. **Measure performance improvements**
   - Benchmark re-ID with GPU vs CPU
   - Target: <0.2s per detection (10x improvement from 2s)
   - Verify accuracy not degraded

### Secondary Goals

4. **Batch re-ID processing**
   - Process multiple detections in single forward pass
   - Reduces overhead from model invocation
   - Potential 5-10x speedup for multi-detection images

5. **Model optimization**
   - Convert ResNet50 to half precision (FP16) if supported
   - Enable CUDA optimizations (cuDNN autotuner)
   - Test TorchScript compilation

## Technical Approach

### Phase 1: Diagnosis (1 hour)

**Verify current GPU usage:**
```python
# Add to reidentification.py
import torch

def extract_feature_vector(crop):
    model, transform = get_reid_model()

    # Log device info
    logger.info(f"[DEBUG] Model device: {next(model.parameters()).device}")

    img_tensor = transform(crop).unsqueeze(0).to(DEVICE)
    logger.info(f"[DEBUG] Tensor device: {img_tensor.device}")

    # Monitor GPU memory
    if torch.cuda.is_available():
        logger.info(f"[DEBUG] GPU memory: {torch.cuda.memory_allocated() / 1024**2:.1f}MB")
```

**Benchmark current performance:**
```bash
# Time 100 re-ID operations
docker-compose exec worker python3 scripts/benchmark_reid.py --num-detections 100
```

### Phase 2: GPU Optimization (2 hours)

**Enable CUDA optimizations:**
```python
# In get_reid_model()
torch.backends.cudnn.benchmark = True  # Auto-tune for best kernels
torch.backends.cudnn.enabled = True
```

**Test mixed precision (FP16):**
```python
# Convert model to half precision
_reid_model = _reid_model.half()

# Process with autocast
with torch.cuda.amp.autocast():
    features = model(img_tensor)
```

**Batch processing implementation:**
```python
def extract_feature_vectors_batch(crops: List[PILImage.Image]) -> np.ndarray:
    """
    Extract feature vectors for multiple crops in single batch.

    Args:
        crops: List of PIL images

    Returns:
        np.ndarray: (N, 512) array of feature vectors
    """
    model, transform = get_reid_model()

    # Stack all crops into single batch
    batch = torch.stack([transform(crop) for crop in crops]).to(DEVICE)

    with torch.no_grad():
        features = model(batch)  # Single forward pass for all

    return features.cpu().numpy()
```

### Phase 3: Integration & Testing (1-2 hours)

**Modify detection task to batch re-ID:**
```python
# In detection.py, after creating all detections
if detection_count > 0:
    # Option 1: Queue single batch re-ID task (faster)
    batch_reidentify_task.delay(detections_created)

    # Option 2: Keep current individual tasks (more flexible)
    for detection_id in detections_created:
        reidentify_deer_task.delay(detection_id)
```

**Create batch re-ID task:**
```python
@app.task(bind=True, name='worker.tasks.reidentification.batch_reidentify')
def batch_reidentify_task(self, detection_ids: List[str]) -> Dict:
    """
    Process multiple detections in single batch for efficiency.

    Args:
        detection_ids: List of detection UUIDs to process

    Returns:
        dict: Results summary
    """
    # Load all detections
    # Extract all crops
    # Batch process feature vectors (single GPU call)
    # Match all vectors to deer profiles
    # Update database in bulk
```

### Phase 4: Benchmarking (1 hour)

**Performance targets:**
```
Operation          | Current | Target  | Speedup
-------------------|---------|---------|--------
Single re-ID       | 2.0s    | 0.2s    | 10x
Batch re-ID (16)   | 32.0s   | 1.0s    | 32x
Full image (3 det) | 6.0s    | 0.6s    | 10x
```

**Test scenarios:**
1. Single detection re-ID (baseline)
2. Batch of 16 detections (multi-deer image)
3. Full pipeline with 100 images

## Implementation Checklist

### Code Changes

- [ ] Add GPU monitoring to `reidentification.py`
- [ ] Enable CUDA optimizations in `get_reid_model()`
- [ ] Implement `extract_feature_vectors_batch()` function
- [ ] Create `batch_reidentify_task()` Celery task
- [ ] Modify detection task to use batch re-ID (optional)
- [ ] Add FP16 mixed precision support (if beneficial)

### Testing

- [ ] Benchmark current CPU performance
- [ ] Benchmark GPU performance (single)
- [ ] Benchmark GPU performance (batch)
- [ ] Verify accuracy not degraded
- [ ] Test memory usage (GPU VRAM)
- [ ] Load test with 1000+ detections

### Documentation

- [ ] Update `SPRINT_9_REID_GPU.md` with results
- [ ] Document batch processing usage
- [ ] Add performance comparison tables
- [ ] Update main README with new metrics

## Success Criteria

- [x] GPU verification complete (CUDA available: RTX 4080 Super)
- [ ] Re-ID time reduced from 2s to <0.2s (10x improvement)
- [ ] Batch processing implemented and tested
- [ ] No degradation in re-ID accuracy (>85% threshold maintained)
- [ ] GPU memory usage <50% (8GB of 16GB available)
- [ ] Documentation complete with benchmark results
- [ ] Full pipeline throughput >5 images/second (currently ~0.5)

## Risks & Mitigations

### Risk 1: GPU Memory Overflow
**Impact:** OOM errors during batch processing

**Mitigation:**
- Start with small batch sizes (4-8)
- Monitor GPU memory usage
- Implement dynamic batch sizing based on available memory
- Fall back to single processing if OOM occurs

### Risk 2: Accuracy Degradation
**Impact:** FP16 precision loss affecting re-ID accuracy

**Mitigation:**
- Test FP16 vs FP32 accuracy on validation set
- Keep FP32 if FP16 causes >2% accuracy drop
- Document precision trade-offs

### Risk 3: Minimal Improvement
**Impact:** GPU not significantly faster than CPU for this model

**Likelihood:** Low (ResNet50 is well-optimized for GPU)

**Mitigation:**
- Profile CPU vs GPU with torch.profiler
- Identify bottlenecks (I/O vs compute)
- Optimize data loading pipeline if needed

## Timeline

**Day 1 (4-6 hours):**
- [x] Sprint planning (30 min)
- [ ] Phase 1: Diagnosis (1 hour)
- [ ] Phase 2: GPU Optimization (2 hours)
- [ ] Phase 3: Integration (1-2 hours)
- [ ] Phase 4: Benchmarking (1 hour)
- [ ] Documentation (30 min)

## Expected Outcomes

### Performance Improvement
```
BEFORE (Sprint 8):
- Detection: 0.04s (GPU)
- DB writes: 0.03s
- Re-ID:     2.00s (CPU)  <- Bottleneck
- Total:     2.07s per image
- Throughput: 0.48 images/second

AFTER (Sprint 9 - Target):
- Detection: 0.04s (GPU)
- DB writes: 0.03s
- Re-ID:     0.20s (GPU)  <- Optimized
- Total:     0.27s per image
- Throughput: 3.7 images/second

Speedup: 7.7x end-to-end improvement
```

### With Batch Processing
```
OPTIMIZED (3 detections per image avg):
- Detection: 0.04s (GPU)
- DB writes: 0.03s
- Re-ID (batch of 3): 0.30s total = 0.10s per detection
- Total:     0.37s per image
- Throughput: 2.7 images/second

Speedup: 5.6x end-to-end improvement
```

## Tools to Create

1. **`scripts/benchmark_reid.py`**
   - Benchmark re-ID performance
   - Compare CPU vs GPU
   - Test different batch sizes
   - Report GPU memory usage

2. **`scripts/test_reid_accuracy.py`**
   - Validate re-ID accuracy
   - Compare FP32 vs FP16
   - Test on known deer pairs

3. **`scripts/profile_reid.py`**
   - Profile re-ID with torch.profiler
   - Identify bottlenecks
   - Generate performance report

## Dependencies

**Required:**
- PyTorch with CUDA support (already installed)
- torchvision (already installed)
- NVIDIA GPU with 8GB+ VRAM (RTX 4080 Super - 16GB available)

**Optional:**
- torch.cuda.amp for mixed precision
- TensorRT for model optimization (future)
- ONNX Runtime for cross-platform optimization (future)

## References

- PyTorch CUDA Best Practices: https://pytorch.org/docs/stable/notes/cuda.html
- Mixed Precision Training: https://pytorch.org/docs/stable/amp.html
- TorchScript: https://pytorch.org/docs/stable/jit.html
- ResNet50 optimization: https://pytorch.org/vision/stable/models.html

## Next Sprint Preview

**Sprint 10 (Future):**
- Frontend polish (image zoom, galleries)
- Automated testing suite (pytest)
- Production monitoring (Prometheus/Grafana)
- Deployment automation

---

**Created:** November 7, 2025
**Status:** Ready to start
**Estimated completion:** Same day (4-6 hours)
