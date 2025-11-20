# Data Model: Re-ID Enhancement

**Feature**: 009-reid-enhancement
**Date**: 2025-11-14
**Phase**: 1 (Design)
**Status**: Complete

## Overview

This document specifies the database schema changes and data migration strategy for the Re-ID enhancement feature. The enhancement adds multi-scale and ensemble embeddings while maintaining backward compatibility with the existing single-layer ResNet50 embeddings.

## Database Schema Changes

### Deer Table Modifications

**Table**: `deer`
**Changes**: Add 3 new columns for multi-scale and ensemble embeddings

```sql
-- Multi-scale ResNet50 embedding (512 dimensions)
-- Combines features from layer2, layer3, layer4, and avgpool
ALTER TABLE deer
ADD COLUMN feature_vector_multiscale VECTOR(512);

COMMENT ON COLUMN deer.feature_vector_multiscale IS
'Multi-scale ResNet50 embedding combining texture (layer2), shapes (layer3), parts (layer4), and semantics (avgpool). 512 dimensions, L2 normalized.';

-- EfficientNet-B0 ensemble embedding (512 dimensions)
-- Provides architectural diversity for ensemble matching
ALTER TABLE deer
ADD COLUMN feature_vector_efficientnet VECTOR(512);

COMMENT ON COLUMN deer.feature_vector_efficientnet IS
'EfficientNet-B0 embedding for ensemble learning. Captures complementary features using compound scaling architecture. 512 dimensions, L2 normalized.';

-- Embedding version tracking
-- Tracks which embedding extraction version was used
ALTER TABLE deer
ADD COLUMN embedding_version VARCHAR(20) DEFAULT 'v1_resnet50';

COMMENT ON COLUMN deer.embedding_version IS
'Version identifier for embedding extraction. Values: v1_resnet50 (original), v2_multiscale (multi-scale), v3_ensemble (multi-scale + EfficientNet).';
```

### Indexes for Performance

**HNSW Indexes for Vector Similarity Search**:

```sql
-- Multi-scale embedding index
-- Uses HNSW (Hierarchical Navigable Small World) algorithm
-- Optimized for cosine similarity search
CREATE INDEX ix_deer_feature_vector_multiscale_hnsw
ON deer
USING hnsw (feature_vector_multiscale vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

COMMENT ON INDEX ix_deer_feature_vector_multiscale_hnsw IS
'HNSW index for fast cosine similarity search on multi-scale embeddings. Parameters: m=16 (connections per layer), ef_construction=64 (build quality).';

-- EfficientNet ensemble embedding index
CREATE INDEX ix_deer_feature_vector_efficientnet_hnsw
ON deer
USING hnsw (feature_vector_efficientnet vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

COMMENT ON INDEX ix_deer_feature_vector_efficientnet_hnsw IS
'HNSW index for fast cosine similarity search on EfficientNet embeddings. Parameters: m=16 (connections per layer), ef_construction=64 (build quality).';

-- Embedding version index for filtering queries
CREATE INDEX ix_deer_embedding_version
ON deer (embedding_version);

COMMENT ON INDEX ix_deer_embedding_version IS
'B-tree index for filtering deer by embedding version (e.g., find all v3_ensemble deer).';
```

**Index Performance Analysis**:
- HNSW parameters (m=16, ef_construction=64) balance build time vs search quality
- Expected index build time: ~1 second for 165 deer profiles
- Search performance: O(log N) vs O(N) for sequential scan
- Memory overhead: ~5KB per deer profile (acceptable for 165 profiles)

---

## Data Types

### Vector Embeddings

**Type**: `VECTOR(512)` (pgvector extension)
**Storage**: 512 × 4 bytes = 2,048 bytes per embedding
**Per Deer**: 3 embeddings × 2,048 bytes = 6,144 bytes (~6KB)
**Total Dataset (165 deer)**: 165 × 6KB = 1,014KB (~1MB)

**Properties**:
- L2 normalized (magnitude = 1.0)
- Cosine similarity via `<=>` operator
- HNSW indexable for fast search

### Embedding Version

**Type**: `VARCHAR(20)`
**Values**:
- `v1_resnet50`: Original single-layer ResNet50 avgpool embedding
- `v2_multiscale`: Multi-scale ResNet50 (layer2 + layer3 + layer4 + avgpool)
- `v3_ensemble`: Multi-scale + EfficientNet ensemble

**Usage**: Filter queries during migration and A/B testing

---

## Migration Strategy

### Phase 1: Schema Migration (Immediate)

**Goal**: Add new columns without disrupting existing system

```sql
-- Migration script: migrations/011_add_reid_enhancement.sql
BEGIN;

-- Add new columns (nullable for backward compatibility)
ALTER TABLE deer
ADD COLUMN feature_vector_multiscale VECTOR(512),
ADD COLUMN feature_vector_efficientnet VECTOR(512),
ADD COLUMN embedding_version VARCHAR(20) DEFAULT 'v1_resnet50';

-- Add indexes
CREATE INDEX ix_deer_feature_vector_multiscale_hnsw
ON deer
USING hnsw (feature_vector_multiscale vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX ix_deer_feature_vector_efficientnet_hnsw
ON deer
USING hnsw (feature_vector_efficientnet vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX ix_deer_embedding_version
ON deer (embedding_version);

-- Add comments
COMMENT ON COLUMN deer.feature_vector_multiscale IS
'Multi-scale ResNet50 embedding combining texture, shapes, parts, and semantics. 512 dimensions, L2 normalized.';

COMMENT ON COLUMN deer.feature_vector_efficientnet IS
'EfficientNet-B0 embedding for ensemble learning. 512 dimensions, L2 normalized.';

COMMENT ON COLUMN deer.embedding_version IS
'Version identifier for embedding extraction. Values: v1_resnet50, v2_multiscale, v3_ensemble.';

COMMIT;
```

**Execution Time**: ~2 seconds
**Downtime**: None (additive changes)
**Rollback**: Drop columns and indexes

---

### Phase 2: Re-Embedding Existing Deer (Background)

**Goal**: Generate new embeddings for all existing deer profiles

**Script**: `scripts/reembed_deer_enhanced.py`

**Process**:
1. Query all deer with assigned detections (165 deer, 6,982 detections)
2. For each deer:
   - Find best quality detection (highest confidence, largest bbox)
   - Extract deer crop from image
   - Generate multi-scale embedding (ResNet50)
   - Generate ensemble embedding (EfficientNet-B0)
   - Update database with new embeddings
   - Set `embedding_version = 'v3_ensemble'`
3. Log progress every 10 deer
4. Validate embeddings (L2 norm = 1.0)

**Estimated Time**:
- 165 deer × 131ms/deer = 21.6 seconds (feature extraction)
- Database updates: ~5 seconds
- Total: ~30 seconds

**Data Preservation**:
- Original `feature_vector` column preserved (for rollback)
- New embeddings stored in separate columns
- Embedding version tracked

---

### Phase 3: Validation (Manual)

**Goal**: Verify new embeddings improve accuracy before cutover

**Script**: `scripts/validate_enhanced_embeddings.py`

**Validation Steps**:
1. **Known Pair Validation**:
   - Select 20 deer with 5+ sightings
   - For each deer, compare similarity scores:
     - Old embedding vs old embedding (baseline)
     - New multi-scale vs new multi-scale
     - New ensemble (weighted) vs new ensemble
   - Expected: New embeddings show 10-15% higher similarity for true matches

2. **False Positive Check**:
   - Select 20 pairs of different deer (same sex)
   - Compare similarity scores
   - Expected: New embeddings maintain low similarity (<0.40) for non-matches

3. **Distribution Analysis**:
   - Plot histogram of similarity scores (old vs new)
   - Expected: Better separation between matches and non-matches

**Success Criteria**:
- True match similarity increases by 10-15%
- False positive rate remains <5%
- Clear separation in similarity score distribution

**Failure Response**:
- Analyze failure cases (which deer? which images?)
- Adjust ensemble weights (0.6/0.4 → 0.7/0.3 or 0.5/0.5)
- If persistent failure, rollback to v1 embeddings

---

### Phase 4: Cutover (Gradual)

**Goal**: Transition Re-ID pipeline to use new embeddings

**Implementation**:

1. **Update Re-ID Task** (`src/worker/tasks/reidentification.py`):
   ```python
   # Add configuration flag
   USE_ENHANCED_REID = os.getenv('USE_ENHANCED_REID', 'true').lower() == 'true'

   if USE_ENHANCED_REID:
       # Use multi-scale + ensemble pipeline
       similarity = compute_ensemble_similarity(
           detection_embedding,
           deer.feature_vector_multiscale,
           deer.feature_vector_efficientnet,
           weights=(0.6, 0.4)
       )
   else:
       # Fallback to original single-layer embedding
       similarity = cosine_similarity(
           detection_embedding,
           deer.feature_vector
       )
   ```

2. **A/B Testing** (Optional):
   - Process 50% of new detections with enhanced Re-ID
   - Process 50% with original Re-ID
   - Compare assignment rates after 1 week
   - Full cutover if enhanced system shows improvement

3. **Full Cutover**:
   - Set `USE_ENHANCED_REID=true` in .env
   - Restart worker container
   - Monitor assignment rate for 24 hours
   - Validate results

**Monitoring**:
- Assignment rate dashboard (before/after comparison)
- Similarity score distribution (log to database)
- False positive rate tracking
- Processing time metrics

---

### Phase 5: Cleanup (Deferred)

**Goal**: Remove legacy embeddings after validation (3+ months)

**Actions**:
1. Confirm enhanced system stable (no rollbacks in 90 days)
2. Drop original `feature_vector` column:
   ```sql
   ALTER TABLE deer DROP COLUMN feature_vector;
   DROP INDEX ix_deer_feature_vector_hnsw;
   ```
3. Rename new columns (optional):
   ```sql
   ALTER TABLE deer RENAME COLUMN feature_vector_multiscale TO feature_vector_primary;
   ALTER TABLE deer RENAME COLUMN feature_vector_efficientnet TO feature_vector_secondary;
   ```

**Benefits**:
- Reduce storage by 2KB per deer (165 × 2KB = 330KB)
- Simplify schema (fewer columns)
- Finalize migration

---

## Data Validation

### Embedding Quality Checks

**L2 Normalization Validation**:
```sql
-- Check that all embeddings are L2 normalized (magnitude = 1.0)
SELECT id, name,
    ABS(1.0 - (feature_vector_multiscale <#> feature_vector_multiscale)) AS multiscale_norm_error,
    ABS(1.0 - (feature_vector_efficientnet <#> feature_vector_efficientnet)) AS efficientnet_norm_error
FROM deer
WHERE feature_vector_multiscale IS NOT NULL
  AND feature_vector_efficientnet IS NOT NULL;

-- Expected: All errors < 0.0001 (floating point tolerance)
```

**Null Check**:
```sql
-- Verify all deer with detections have new embeddings
SELECT COUNT(*) FROM deer
WHERE sighting_count > 0
  AND (feature_vector_multiscale IS NULL OR feature_vector_efficientnet IS NULL);

-- Expected: 0 rows
```

**Version Consistency**:
```sql
-- Verify embedding_version updated correctly
SELECT embedding_version, COUNT(*) FROM deer
GROUP BY embedding_version;

-- Expected:
-- v3_ensemble: 165 (all deer with detections)
-- v1_resnet50: 0 (if re-embedding complete)
```

---

## Rollback Plan

### Scenario 1: Enhanced Embeddings Perform Worse

**Symptoms**:
- Assignment rate decreases
- False positive rate increases
- User reports poor matching quality

**Rollback Steps**:
1. Set `USE_ENHANCED_REID=false` in .env
2. Restart worker: `docker-compose restart worker`
3. Revert to original embeddings
4. Investigate failure (analyze validation data)

**Recovery Time**: 2 minutes
**Data Loss**: None (old embeddings preserved)

---

### Scenario 2: Migration Script Fails

**Symptoms**:
- SQL errors during migration
- Incomplete index creation
- Database corruption

**Rollback Steps**:
1. Restore database from backup:
   ```bash
   docker-compose exec db pg_restore -U deertrack -d deer_tracking /backups/pre_migration.sql
   ```
2. Drop partially created columns:
   ```sql
   ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_multiscale;
   ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_efficientnet;
   ALTER TABLE deer DROP COLUMN IF EXISTS embedding_version;
   ```
3. Investigate error logs
4. Fix migration script
5. Retry migration

**Recovery Time**: 10 minutes
**Data Loss**: None (backup restored)

---

### Scenario 3: Re-Embedding Script Crashes

**Symptoms**:
- Script exits with error
- Partial embeddings generated
- Some deer have NULL embeddings

**Rollback Steps**:
1. Identify failed deer:
   ```sql
   SELECT id, name, sighting_count
   FROM deer
   WHERE sighting_count > 0
     AND (feature_vector_multiscale IS NULL OR feature_vector_efficientnet IS NULL);
   ```
2. Re-run script with `--resume` flag:
   ```bash
   python scripts/reembed_deer_enhanced.py --resume
   ```
3. Script skips deer with existing embeddings
4. Completes remaining deer

**Recovery Time**: 1 minute (script resumes automatically)
**Data Loss**: None (partial progress preserved)

---

## Performance Considerations

### Storage Impact

**Current Database Size**: ~50MB (35,251 images, 11,570 detections, 165 deer)

**Additional Storage**:
- 3 new columns × 165 deer × 6KB = 3.0MB
- HNSW indexes × 2 × 5KB = 1.6MB
- **Total**: +4.6MB (9% increase)

**Impact**: Negligible (database has GBs of headroom)

---

### Query Performance

**Similarity Search (Current)**:
```sql
SELECT id, name, (feature_vector <=> %s::vector) AS distance
FROM deer
WHERE sex = %s
ORDER BY distance
LIMIT 10;

-- Execution time: ~5ms (HNSW index)
```

**Similarity Search (Enhanced)**:
```sql
-- Multi-scale search
SELECT id, name, (feature_vector_multiscale <=> %s::vector) AS distance_ms
FROM deer
WHERE sex = %s
ORDER BY distance_ms
LIMIT 10;

-- EfficientNet search
SELECT id, name, (feature_vector_efficientnet <=> %s::vector) AS distance_en
FROM deer
WHERE sex = %s
ORDER BY distance_en
LIMIT 10;

-- Expected execution time: ~10ms (2 queries × 5ms)
```

**Ensemble Query (Application-Level)**:
- Fetch top 20 candidates from each model
- Compute weighted similarity in Python
- Sort and return top 10
- Total time: ~15ms (acceptable)

**Alternative (Database-Level)**:
```sql
-- Computed column for ensemble similarity (future optimization)
SELECT id, name,
    (0.6 * (feature_vector_multiscale <=> %s::vector) +
     0.4 * (feature_vector_efficientnet <=> %s::vector)) AS ensemble_distance
FROM deer
WHERE sex = %s
ORDER BY ensemble_distance
LIMIT 10;

-- Execution time: ~8ms (single query, computed on-the-fly)
```

---

### Index Maintenance

**HNSW Index Build Time**:
- Initial build (165 deer): ~1 second
- Incremental insert (new deer): <1ms per deer

**Index Rebuild** (if needed):
```sql
REINDEX INDEX ix_deer_feature_vector_multiscale_hnsw;
REINDEX INDEX ix_deer_feature_vector_efficientnet_hnsw;

-- Time: ~2 seconds (165 deer)
```

**When to Rebuild**:
- After bulk re-embedding (done automatically)
- Database corruption (rare)
- Performance degradation (if search slows down)

---

## Testing Checklist

### Pre-Migration
- [ ] Backup database: `pg_dump -U deertrack deer_tracking > pre_migration.sql`
- [ ] Verify pgvector extension installed: `SELECT * FROM pg_extension WHERE extname = 'vector';`
- [ ] Test migration script on dev database
- [ ] Validate rollback procedure

### Post-Migration
- [ ] Verify new columns exist: `\d deer`
- [ ] Verify indexes created: `\di`
- [ ] Check embedding_version default: `SELECT embedding_version FROM deer LIMIT 10;`
- [ ] Validate storage impact: `SELECT pg_size_pretty(pg_total_relation_size('deer'));`

### Post-Re-Embedding
- [ ] Verify all deer have embeddings (NULL check query)
- [ ] Validate L2 normalization (norm check query)
- [ ] Check embedding_version updated to 'v3_ensemble'
- [ ] Run validation script: `python scripts/validate_enhanced_embeddings.py`
- [ ] Review similarity score distribution

### Post-Cutover
- [ ] Monitor assignment rate (first 24 hours)
- [ ] Check processing time metrics
- [ ] Review false positive rate
- [ ] Validate user-reported match quality

---

## Appendix: SQL Migration Script

**File**: `migrations/011_add_reid_enhancement.sql`

```sql
-- Migration: Add Multi-Scale and Ensemble Embeddings for Re-ID Enhancement
-- Feature: 009-reid-enhancement
-- Date: 2025-11-14
-- Description: Adds feature_vector_multiscale, feature_vector_efficientnet, and embedding_version columns to deer table with HNSW indexes

BEGIN;

-- Check pgvector extension is installed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension not installed. Run: CREATE EXTENSION vector;';
    END IF;
END
$$;

-- Add new columns
ALTER TABLE deer
ADD COLUMN IF NOT EXISTS feature_vector_multiscale VECTOR(512),
ADD COLUMN IF NOT EXISTS feature_vector_efficientnet VECTOR(512),
ADD COLUMN IF NOT EXISTS embedding_version VARCHAR(20) DEFAULT 'v1_resnet50';

-- Add HNSW indexes
CREATE INDEX IF NOT EXISTS ix_deer_feature_vector_multiscale_hnsw
ON deer
USING hnsw (feature_vector_multiscale vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS ix_deer_feature_vector_efficientnet_hnsw
ON deer
USING hnsw (feature_vector_efficientnet vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS ix_deer_embedding_version
ON deer (embedding_version);

-- Add column comments
COMMENT ON COLUMN deer.feature_vector_multiscale IS
'Multi-scale ResNet50 embedding combining texture (layer2), shapes (layer3), parts (layer4), and semantics (avgpool). 512 dimensions, L2 normalized.';

COMMENT ON COLUMN deer.feature_vector_efficientnet IS
'EfficientNet-B0 embedding for ensemble learning. Captures complementary features using compound scaling architecture. 512 dimensions, L2 normalized.';

COMMENT ON COLUMN deer.embedding_version IS
'Version identifier for embedding extraction. Values: v1_resnet50 (original), v2_multiscale (multi-scale only), v3_ensemble (multi-scale + EfficientNet).';

-- Validate migration
DO $$
DECLARE
    col_count INTEGER;
    idx_count INTEGER;
BEGIN
    -- Check columns exist
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'deer'
      AND column_name IN ('feature_vector_multiscale', 'feature_vector_efficientnet', 'embedding_version');

    IF col_count != 3 THEN
        RAISE EXCEPTION 'Column creation failed. Expected 3 columns, found %', col_count;
    END IF;

    -- Check indexes exist
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE tablename = 'deer'
      AND indexname IN (
          'ix_deer_feature_vector_multiscale_hnsw',
          'ix_deer_feature_vector_efficientnet_hnsw',
          'ix_deer_embedding_version'
      );

    IF idx_count != 3 THEN
        RAISE EXCEPTION 'Index creation failed. Expected 3 indexes, found %', idx_count;
    END IF;

    RAISE NOTICE 'Migration successful: 3 columns and 3 indexes created';
END
$$;

COMMIT;

-- Rollback script (for reference, do not execute):
-- BEGIN;
-- DROP INDEX IF EXISTS ix_deer_feature_vector_multiscale_hnsw;
-- DROP INDEX IF EXISTS ix_deer_feature_vector_efficientnet_hnsw;
-- DROP INDEX IF EXISTS ix_deer_embedding_version;
-- ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_multiscale;
-- ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_efficientnet;
-- ALTER TABLE deer DROP COLUMN IF EXISTS embedding_version;
-- COMMIT;
```

---

**Data Model Complete**: 2025-11-14
**Reviewed By**: Development Team
**Approved For**: Implementation (Phase 2 - Tasks)
