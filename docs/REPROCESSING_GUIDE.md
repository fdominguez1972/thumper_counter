# Dataset Reprocessing Guide

## Overview

This guide explains how to reprocess the entire dataset with the newly trained YOLOv8 model after deploying model improvements.

## New Model Details

- **Model Name**: corrected_final_buck_doe
- **Accuracy**: mAP50=0.851 (85.1%), mAP50-95=0.667
- **Classes**: buck, doe, fawn, cattle, pig, raccoon
- **Training Data**: 779 manually corrected images (526 train, 253 val)
- **Deployment Date**: November 11, 2025
- **Location**: `src/models/yolov8n_deer.pt` (deployed from `src/models/runs/corrected_final_buck_doe/weights/best.pt`)

## Why Reprocess?

After training and deploying a new model, you should reprocess existing images to:

1. **Fix Misclassifications**: Old model incorrectly classified does as bucks (~30-40% error rate)
2. **Improve Accuracy**: New model has 85.1% accuracy vs previous model
3. **Consistent Classifications**: All images classified with same model version
4. **Better Re-ID**: More accurate sex classification improves deer re-identification

## Reprocessing Options

### Option 1: Bash Script (Quickest)

Simple, automated script that handles the entire workflow:

```bash
./scripts/reprocess_all_images.sh
```

**What it does:**
1. Shows current statistics
2. Asks which detections to clear (all/unreviewed/none)
3. Resets image processing status
4. Queues all images for processing
5. Displays progress monitoring instructions

**Recommended for:** Quick, hands-off reprocessing

### Option 2: Python Script (More Control)

Interactive script with detailed statistics and step-by-step control:

```bash
docker-compose exec backend python3 /app/scripts/reprocess_with_new_model.py
```

**What it does:**
1. Shows detailed before/after statistics
2. Interactive prompts for each step
3. Detailed classification breakdowns
4. Progress tracking with ETA calculations
5. Comprehensive monitoring instructions

**Recommended for:** Understanding changes, detailed reporting

### Option 3: Manual Commands

For maximum control, run each step manually:

```bash
# Step 1: Check current status
curl http://localhost:8001/api/processing/status

# Step 2: Clear detections (if desired)
docker-compose exec -T db psql -U deertrack deer_tracking -c "DELETE FROM detections;"

# Step 3: Reset image status
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "UPDATE images SET processing_status = 'pending', processed_at = NULL WHERE processing_status IN ('completed', 'failed');"

# Step 4: Queue images
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"
# Repeat until all images queued

# Step 5: Monitor progress
curl http://localhost:8001/api/processing/status
```

**Recommended for:** Debugging, custom workflows

## Detection Cleanup Options

When reprocessing, you have three options for existing detections:

### 1. Keep All Detections (Default)
- **What happens**: Old detections remain, new detections added
- **Use case**: Comparing old vs new model performance
- **Pros**: Can analyze model improvements
- **Cons**: Database grows, mixed model versions

### 2. Clear ALL Detections (Recommended)
- **What happens**: All detections deleted, fresh start
- **Use case**: Clean slate with new model
- **Pros**: Consistent dataset, easy to analyze
- **Cons**: Loses manually corrected detections

### 3. Clear Unreviewed Only
- **What happens**: Keep manually reviewed/corrected detections
- **Use case**: Preserve human corrections, reprocess ML predictions
- **Pros**: Keeps valuable manual work
- **Cons**: Mixed model versions for unreviewed data

## Processing Performance

Expected throughput based on current configuration:

- **GPU**: RTX 4080 Super (16GB VRAM)
- **Worker Concurrency**: 32 threads
- **Throughput**: 840 images/minute (14 images/second)
- **Full Dataset**: 35,251 images
- **Estimated Time**: ~42 minutes

Bottleneck is database writes, not GPU processing.

## Monitoring Progress

### 1. API Status Endpoint

Real-time processing statistics:

```bash
curl http://localhost:8001/api/processing/status
```

Returns:
```json
{
  "total_images": 35251,
  "completed_images": 15000,
  "pending_images": 20251,
  "processing_images": 32,
  "failed_images": 0,
  "completion_rate": 42.5,
  "queue_status": {
    "total_tasks": 20251,
    "active_tasks": 32
  }
}
```

### 2. Worker Logs

Watch detection completions in real-time:

```bash
docker-compose logs -f worker | grep "Detection complete"
```

Example output:
```
worker_1  | [OK] Detection complete: image_id=..., detections=2, time=0.05s
```

### 3. Flower UI

Visual task monitoring at http://localhost:5555

- Active tasks
- Task success/failure rates
- Worker status
- Queue lengths

### 4. GPU Usage

Monitor GPU utilization:

```bash
docker stats worker
```

Or inside container:
```bash
docker-compose exec worker nvidia-smi
```

Expected: ~31% GPU utilization (optimal for concurrency=32)

## Post-Processing Validation

After reprocessing completes, validate the results:

### 1. Check Processing Status

```bash
curl http://localhost:8001/api/processing/status
```

Verify:
- `completion_rate` = 100%
- `failed_images` = 0 (or very low)

### 2. Verify Classifications

```sql
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT
    COALESCE(corrected_classification, classification) as class,
    COUNT(*) as count,
    ROUND(AVG(confidence)::numeric, 3) as avg_confidence
FROM detections
GROUP BY class
ORDER BY count DESC;
"
```

Expected results:
- Most detections: doe, buck
- Confidence: >0.7 average
- Minimal "unknown" classifications

### 3. Check Cross-Sex Contamination

```sql
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT
    d.id,
    d.name,
    d.sex,
    COUNT(DISTINCT det.classification) as distinct_classifications,
    STRING_AGG(DISTINCT det.classification, ', ') as classifications
FROM deer d
JOIN detections det ON det.deer_id = d.id
WHERE det.is_valid = true
GROUP BY d.id, d.name, d.sex
HAVING COUNT(DISTINCT det.classification) > 1;
"
```

Expected: 0 rows (no cross-sex contamination)

### 4. Compare Before/After

Compare classification accuracy:

```bash
# Before reprocessing (save this output first)
curl http://localhost:8001/api/images?classification=buck | jq '.total'

# After reprocessing
curl http://localhost:8001/api/images?classification=buck | jq '.total'
```

Expected: ~30-40% reduction in misclassified images

## Troubleshooting

### Issue: Processing Stalled

**Symptoms**: `completion_rate` not increasing

**Solutions**:
1. Check worker status: `docker-compose ps worker`
2. Restart worker: `docker-compose restart worker`
3. Check queue: `curl http://localhost:8001/api/processing/status`
4. Re-queue if needed: `curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"`

### Issue: High Failure Rate

**Symptoms**: `failed_images` increasing

**Solutions**:
1. Check worker logs: `docker-compose logs worker | tail -100`
2. Look for common errors
3. Check image file accessibility
4. Verify model loaded correctly

### Issue: Slow Processing

**Symptoms**: Throughput < 500 images/minute

**Solutions**:
1. Check GPU usage: `docker stats worker`
2. Verify GPU enabled: `docker-compose exec worker nvidia-smi`
3. Check database performance: Connection pooling, indexes
4. Reduce concurrency if GPU contention: Edit `docker/dockerfiles/Dockerfile.worker`

### Issue: Out of Memory

**Symptoms**: Worker crashes, OOM errors

**Solutions**:
1. Reduce batch size in detection task
2. Reduce worker concurrency (currently 32)
3. Increase Docker memory limit
4. Check for memory leaks in logs

## Best Practices

1. **Backup First**: Create database backup before reprocessing
   ```bash
   docker-compose exec db pg_dump -U deertrack deer_tracking > backup_$(date +%Y%m%d).sql
   ```

2. **Test First**: Process a small batch first (100-1000 images)
   ```bash
   curl -X POST "http://localhost:8001/api/processing/batch?limit=100"
   ```

3. **Monitor Closely**: Watch first 5 minutes for errors

4. **Avoid Interruptions**: Don't stop worker mid-processing (queue state preserved)

5. **Clear Option**: Use "Clear ALL" for cleanest results unless you have valuable manual corrections

6. **Validate Results**: Run post-processing validation queries

7. **Document Changes**: Note model version in CLAUDE.md or project log

## Expected Improvements

Based on new model performance (mAP50=0.851):

### Classification Accuracy

- **Buck detection**: 67.3% → expected ~75-80% (improved antler recognition)
- **Doe detection**: 76.9% → expected ~80-85% (reduced false bucks)
- **Fawn detection**: 79.6% → expected ~80-85% (maintained)

### Specific Fixes

1. **Cross-Sex Misclassification**: ~30-40% reduction
   - Rear-end images: Better body shape recognition
   - Does misclassified as bucks: Improved feature extraction

2. **Confidence Scores**: Higher average confidence
   - Previous: 0.6-0.7 average
   - Expected: 0.75-0.85 average

3. **Re-ID Accuracy**: Improved due to correct sex filtering
   - Fewer cross-sex profile contaminations
   - Better burst linking (same-sex only)

## Timeline

1. **Preparation**: 5 minutes (backup, review options)
2. **Execution**: 2 minutes (run script, make choices)
3. **Processing**: ~42 minutes (automated)
4. **Validation**: 10 minutes (check results)

**Total**: ~1 hour for complete reprocessing cycle

## Next Steps After Reprocessing

1. **Validate Results**: Run post-processing checks
2. **Review Frontend**: Check Images page classifications
3. **Spot Check**: Manually verify 50-100 random images
4. **Document**: Update CLAUDE.md with results
5. **Monitor**: Watch for any new misclassifications
6. **Iterate**: If issues found, collect more training data

## Support

If you encounter issues:

1. Check worker logs: `docker-compose logs worker`
2. Check API logs: `docker-compose logs backend`
3. Review this guide's Troubleshooting section
4. Check GitHub issues for similar problems
5. Create new issue with:
   - Error messages
   - Worker logs
   - Processing status output
   - System configuration

## References

- Model Training: `docs/SPRINT_4_SUMMARY.md`
- Deployment Script: `scripts/deploy_new_model.sh`
- Detection API: `src/backend/api/processing.py`
- Worker Tasks: `src/worker/tasks/detection.py`
- Session Notes: `CLAUDE.md` (November 11, 2025 entry)
