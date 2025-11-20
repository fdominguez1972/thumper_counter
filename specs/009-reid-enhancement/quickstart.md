# Quickstart: Re-ID Enhancement

**Feature**: 009-reid-enhancement
**Date**: 2025-11-14
**Purpose**: Fast operational guide for deploying and validating the enhanced re-identification system

## Prerequisites

- Docker and docker-compose running
- PostgreSQL database with pgvector extension
- RTX 4080 Super GPU (16GB VRAM)
- Python 3.11 in worker container
- PyTorch with CUDA support

## Quick Deploy (5 Minutes)

### Step 1: Run Database Migration

```bash
# Navigate to project root
cd /mnt/i/projects/thumper_counter

# Apply migration
docker-compose exec db psql -U deertrack deer_tracking -f /app/migrations/011_add_reid_enhancement.sql

# Verify migration
docker-compose exec db psql -U deertrack deer_tracking -c "\d deer"
# Expected: See feature_vector_multiscale, feature_vector_efficientnet, embedding_version columns
```

**Success Indicator**: Migration completes with "Migration successful: 3 columns and 3 indexes created"

---

### Step 2: Re-Embed Existing Deer

```bash
# Run re-embedding script for all existing deer profiles
docker-compose exec backend python3 /app/scripts/reembed_deer_enhanced.py

# Monitor progress (logs every 10 deer)
# Expected output:
# [INFO] Re-embedding deer profiles with enhanced features
# [INFO] Found 165 deer with detections
# [INFO] Progress: 10/165 deer processed (6.1%)
# ...
# [INFO] Complete: 165/165 deer processed (100.0%)
# [INFO] Re-embedding complete in 30.2 seconds
```

**Expected Time**: 30-60 seconds
**Success Indicator**: All 165 deer processed with no errors

---

### Step 3: Validate Enhanced Embeddings

```bash
# Run validation script
docker-compose exec backend python3 /app/scripts/validate_enhanced_embeddings.py

# Check results
# Expected output:
# [VALIDATION] Known Pair Similarity Analysis
# True matches (same deer):
#   - Old embeddings: avg=0.62, min=0.48, max=0.78
#   - New multi-scale: avg=0.71, min=0.58, max=0.86 (+14.5% improvement)
#   - New ensemble: avg=0.73, min=0.61, max=0.89 (+17.7% improvement)
#
# False positives (different deer):
#   - Old embeddings: avg=0.28, max=0.42
#   - New ensemble: avg=0.24, max=0.38 (maintained separation)
#
# [PASS] Enhanced embeddings show 10-15% improvement
# [PASS] False positive rate remains <5%
```

**Success Criteria**:
- True match similarity increases by 10-15%
- False positive rate <5%
- Clear separation in similarity scores

**If Validation Fails**: See "Troubleshooting" section below

---

### Step 4: Enable Enhanced Re-ID

```bash
# Update environment variable
echo "USE_ENHANCED_REID=true" >> .env

# Restart worker to load new configuration
docker-compose restart worker

# Verify worker started successfully
docker-compose logs worker | grep "Enhanced Re-ID enabled"
# Expected: [INFO] Enhanced Re-ID enabled (multi-scale + ensemble)
```

**Success Indicator**: Worker logs show enhanced Re-ID active

---

### Step 5: Monitor Results (24 Hours)

```bash
# Check assignment rate (before vs after)
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT
  COUNT(*) FILTER (WHERE deer_id IS NOT NULL) AS assigned,
  COUNT(*) AS total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE deer_id IS NOT NULL) / COUNT(*), 1) AS assignment_rate
FROM detections
WHERE created_at > NOW() - INTERVAL '24 hours';
"

# Expected: assignment_rate increases from ~60% to 70-75%
```

**Monitor Dashboard**: http://localhost:3000 (check deer profile counts, assignment rates)

---

## Validation Commands

### Check Database Schema

```bash
# Verify new columns exist
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'deer'
  AND column_name IN ('feature_vector_multiscale', 'feature_vector_efficientnet', 'embedding_version');
"

# Expected output:
#       column_name          | data_type
# ---------------------------+-----------
#  feature_vector_multiscale | USER-DEFINED (vector)
#  feature_vector_efficientnet | USER-DEFINED (vector)
#  embedding_version          | character varying
```

---

### Check Embedding Quality

```bash
# Verify L2 normalization (all embeddings should have magnitude ~1.0)
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT
  COUNT(*) AS total_deer,
  COUNT(*) FILTER (WHERE feature_vector_multiscale IS NOT NULL) AS multiscale_count,
  COUNT(*) FILTER (WHERE feature_vector_efficientnet IS NOT NULL) AS efficientnet_count,
  COUNT(*) FILTER (WHERE embedding_version = 'v3_ensemble') AS v3_count
FROM deer;
"

# Expected: All counts match (165 deer with all embeddings)
```

---

### Check HNSW Indexes

```bash
# Verify indexes created
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'deer'
  AND indexname LIKE '%hnsw%';
"

# Expected: 2 HNSW indexes (multiscale and efficientnet)
```

---

### Test Similarity Search Performance

```bash
# Run benchmark query (cosine similarity search)
docker-compose exec db psql -U deertrack deer_tracking -c "
EXPLAIN ANALYZE
SELECT id, name, (feature_vector_multiscale <=> '[0.1, 0.2, ...]'::vector) AS distance
FROM deer
WHERE sex = 'buck'
ORDER BY distance
LIMIT 10;
"

# Expected: Execution time <10ms, using HNSW index
```

---

## Manual Testing Workflow

### Test Multi-Scale Feature Extraction

```bash
# Run test script on sample image
docker-compose exec backend python3 /app/scripts/test_multiscale_extraction.py \
  --image /mnt/images/Sanctuary/IMG_0001.JPG

# Expected output:
# [INFO] Loading multi-scale ResNet50 model
# [INFO] Extracting features from image
# [INFO] Layer 2 features: (512, 4, 4) → pooled to (128,)
# [INFO] Layer 3 features: (1024, 2, 2) → pooled to (128,)
# [INFO] Layer 4 features: (2048, 1, 1) → pooled to (128,)
# [INFO] Avgpool features: (2048,) → pooled to (128,)
# [INFO] Concatenated: (512,)
# [INFO] L2 normalized: magnitude=1.0000
# [PASS] Multi-scale extraction successful
```

---

### Test Ensemble Matching

```bash
# Run test script with two deer images (same deer)
docker-compose exec backend python3 /app/scripts/test_ensemble_matching.py \
  --image1 /mnt/images/Sanctuary/IMG_0001.JPG \
  --image2 /mnt/images/Sanctuary/IMG_0002.JPG

# Expected output:
# [INFO] Extracting features from image 1
# [INFO] Multi-scale embedding 1: (512,)
# [INFO] EfficientNet embedding 1: (512,)
# [INFO] Extracting features from image 2
# [INFO] Multi-scale embedding 2: (512,)
# [INFO] EfficientNet embedding 2: (512,)
# [INFO] Multi-scale similarity: 0.78
# [INFO] EfficientNet similarity: 0.81
# [INFO] Ensemble similarity (0.6/0.4 weights): 0.79
# [PASS] High similarity indicates same deer
```

---

### Test Different Deer (Negative Case)

```bash
# Run test with two different deer
docker-compose exec backend python3 /app/scripts/test_ensemble_matching.py \
  --image1 /mnt/images/Sanctuary/IMG_0001.JPG \
  --image2 /mnt/images/Hayfield/IMG_0100.JPG

# Expected output:
# [INFO] Multi-scale similarity: 0.32
# [INFO] EfficientNet similarity: 0.28
# [INFO] Ensemble similarity (0.6/0.4 weights): 0.30
# [PASS] Low similarity indicates different deer
```

---

## Rollback Procedures

### Scenario 1: Validation Fails (Before Cutover)

```bash
# DO NOT enable enhanced Re-ID
# Keep USE_ENHANCED_REID=false (default)

# Investigate validation failures
docker-compose exec backend python3 /app/scripts/analyze_validation_failures.py

# Adjust ensemble weights if needed
# Edit src/worker/tasks/reidentification.py:
# ENSEMBLE_WEIGHTS = (0.7, 0.3)  # Try different ratios

# Re-run validation
docker-compose exec backend python3 /app/scripts/validate_enhanced_embeddings.py
```

**Recovery Time**: 5 minutes
**Impact**: None (enhanced Re-ID not enabled)

---

### Scenario 2: Enhanced Re-ID Performs Worse (After Cutover)

```bash
# Disable enhanced Re-ID immediately
sed -i 's/USE_ENHANCED_REID=true/USE_ENHANCED_REID=false/' .env

# Restart worker
docker-compose restart worker

# Verify rollback
docker-compose logs worker | grep "Enhanced Re-ID"
# Expected: No "Enhanced Re-ID enabled" message

# System now uses original single-layer embeddings
```

**Recovery Time**: 2 minutes
**Impact**: Revert to 60% assignment rate (original performance)

---

### Scenario 3: Database Migration Fails

```bash
# Restore from backup
docker-compose exec db psql -U deertrack deer_tracking < /backups/pre_migration.sql

# Drop partially created objects
docker-compose exec db psql -U deertrack deer_tracking -c "
DROP INDEX IF EXISTS ix_deer_feature_vector_multiscale_hnsw;
DROP INDEX IF EXISTS ix_deer_feature_vector_efficientnet_hnsw;
DROP INDEX IF EXISTS ix_deer_embedding_version;
ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_multiscale;
ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_efficientnet;
ALTER TABLE deer DROP COLUMN IF EXISTS embedding_version;
"

# Investigate error logs
docker-compose logs db | grep ERROR

# Fix migration script and retry
```

**Recovery Time**: 10 minutes
**Impact**: None (backup restored)

---

## Troubleshooting

### Issue: Re-Embedding Script Crashes

**Symptoms**:
- Script exits with error
- Some deer have NULL embeddings

**Diagnosis**:
```bash
# Check which deer failed
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT id, name, sighting_count, embedding_version
FROM deer
WHERE sighting_count > 0
  AND (feature_vector_multiscale IS NULL OR feature_vector_efficientnet IS NULL);
"
```

**Fix**:
```bash
# Re-run script with --resume flag (skips completed deer)
docker-compose exec backend python3 /app/scripts/reembed_deer_enhanced.py --resume
```

---

### Issue: GPU Out of Memory

**Symptoms**:
- CUDA error: out of memory
- Worker crashes during re-embedding

**Diagnosis**:
```bash
# Check GPU memory usage
docker-compose exec worker nvidia-smi
```

**Fix**:
```bash
# Reduce batch size in re-embedding script
# Edit scripts/reembed_deer_enhanced.py:
# BATCH_SIZE = 8  # Default: 16

# Or process sequentially (batch_size=1)
docker-compose exec backend python3 /app/scripts/reembed_deer_enhanced.py --batch-size 1
```

---

### Issue: Validation Shows No Improvement

**Symptoms**:
- New embeddings similarity scores not higher
- Less than 10% improvement

**Diagnosis**:
```bash
# Check similarity score distribution
docker-compose exec backend python3 /app/scripts/analyze_similarity_distribution.py

# Expected: Two distinct peaks (matches vs non-matches)
# If overlapping: embeddings not discriminative enough
```

**Fix**:
```bash
# Try different ensemble weights
# Edit src/worker/tasks/reidentification.py:
# ENSEMBLE_WEIGHTS = (0.7, 0.3)  # More weight to ResNet50
# or
# ENSEMBLE_WEIGHTS = (0.5, 0.5)  # Equal weights

# Re-run validation
docker-compose exec backend python3 /app/scripts/validate_enhanced_embeddings.py
```

---

### Issue: Slow Similarity Search

**Symptoms**:
- Re-ID takes >3 seconds per detection
- Database queries slow (>50ms)

**Diagnosis**:
```bash
# Check HNSW index usage
docker-compose exec db psql -U deertrack deer_tracking -c "
EXPLAIN ANALYZE
SELECT id, (feature_vector_multiscale <=> '[...]'::vector) AS distance
FROM deer
ORDER BY distance
LIMIT 10;
"

# Expected: "Index Scan using ix_deer_feature_vector_multiscale_hnsw"
# If "Seq Scan": index not being used
```

**Fix**:
```bash
# Rebuild HNSW indexes
docker-compose exec db psql -U deertrack deer_tracking -c "
REINDEX INDEX ix_deer_feature_vector_multiscale_hnsw;
REINDEX INDEX ix_deer_feature_vector_efficientnet_hnsw;
"

# Increase index quality (higher ef_construction)
docker-compose exec db psql -U deertrack deer_tracking -c "
DROP INDEX ix_deer_feature_vector_multiscale_hnsw;
CREATE INDEX ix_deer_feature_vector_multiscale_hnsw
ON deer
USING hnsw (feature_vector_multiscale vector_cosine_ops)
WITH (m = 16, ef_construction = 128);
"
```

---

## Performance Benchmarks

### Expected Metrics

**Re-Embedding (165 deer)**:
- Time: 30-60 seconds
- GPU utilization: 40-60%
- VRAM: ~2GB

**Feature Extraction (per detection)**:
- Multi-scale ResNet50: 80ms
- EfficientNet-B0: 40ms
- Total: ~120ms (within 3s target)

**Similarity Search (per detection)**:
- Database query: ~10ms (HNSW index)
- Ensemble combination: ~1ms
- Total: ~11ms

**Overall Re-ID (per detection)**:
- Feature extraction: 120ms
- Similarity search: 11ms
- Database update: 5ms
- **Total**: ~136ms (well under 3s requirement)

---

## Success Checklist

### Pre-Deployment
- [ ] Database backup created
- [ ] Migration script tested on dev database
- [ ] Validation script ready
- [ ] Rollback procedure documented

### Deployment
- [ ] Database migration successful
- [ ] Re-embedding completed (165 deer)
- [ ] All deer have v3_ensemble embeddings
- [ ] HNSW indexes created
- [ ] Validation passed (10-15% improvement)

### Post-Deployment
- [ ] Enhanced Re-ID enabled (USE_ENHANCED_REID=true)
- [ ] Worker restarted successfully
- [ ] Assignment rate monitored (24h)
- [ ] False positive rate <5%
- [ ] Processing time <3s/detection

### Long-Term
- [ ] 7-day performance review
- [ ] User feedback collected
- [ ] Legacy embeddings cleanup scheduled (90 days)

---

## Contact & Support

**Documentation**: `/mnt/i/projects/thumper_counter/specs/009-reid-enhancement/`
**Logs**: `docker-compose logs worker | grep "Re-ID"`
**Database**: `docker-compose exec db psql -U deertrack deer_tracking`
**Monitoring**: http://localhost:3000 (frontend dashboard)

**Quick Reference Files**:
- Research: `specs/009-reid-enhancement/research.md`
- Data Model: `specs/009-reid-enhancement/data-model.md`
- Migration Script: `migrations/011_add_reid_enhancement.sql`
- Validation Script: `scripts/validate_enhanced_embeddings.py`

---

**Quickstart Complete**: Ready for deployment
**Estimated Total Time**: 5 minutes (migration + re-embedding + validation)
