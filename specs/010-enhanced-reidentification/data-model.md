# Data Model: Enhanced Re-Identification Pipeline

**Feature**: 010-enhanced-reidentification
**Date**: 2025-11-11
**Phase**: 1 - Design
**Status**: Complete

## Purpose

This document defines the database schema extensions required for Feature 010. It details new columns, tables, indexes, and migration strategy to support antler recognition, pose normalization, temporal context, and coat pattern analysis.

## Schema Overview

Enhanced re-identification extends the existing `deer` table with four new vector columns and adds a new `detections.enhancement_metadata` JSONB column to store per-detection feature extraction results.

### Existing Baseline (Sprint 5)

```sql
CREATE TABLE deer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100),
    sex VARCHAR(20) NOT NULL DEFAULT 'unknown',
    status VARCHAR(20) NOT NULL DEFAULT 'alive',
    species VARCHAR(100) NOT NULL DEFAULT 'white_tailed_deer',
    notes VARCHAR(1000),
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    feature_vector VECTOR(512),  -- ResNet50 body features
    confidence REAL NOT NULL DEFAULT 0.0,
    sighting_count INTEGER NOT NULL DEFAULT 1,
    best_photo_id UUID REFERENCES images(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_deer_feature_vector_hnsw ON deer USING hnsw (feature_vector vector_cosine_ops);
CREATE INDEX ix_deer_last_seen_sex ON deer (last_seen, sex);
CREATE INDEX ix_deer_sighting_count ON deer (sighting_count);
```

---

## New Schema Extensions

### 1. Deer Table - Enhanced Feature Vectors

#### 1.1 Antler Fingerprint Column

```sql
ALTER TABLE deer ADD COLUMN antler_fingerprint VECTOR(64);
COMMENT ON COLUMN deer.antler_fingerprint IS 'Antler pattern feature vector (64-dim): point count, spread width, symmetry, tine angles, unique formations. NULL for does/fawns or when antlers not visible. Seasonal: archived by year-season (e.g., 2024-rut).';
```

**Design Rationale**:
- **Vector(64)**: Sufficient for geometric features (point count, spread, symmetry) + visual features (tine angles, formations)
- **Nullable**: Does, fawns, and rear-view detections will not have antler features
- **Seasonal archiving**: Store antler fingerprints by season (Aug-Feb) in separate table for multi-year tracking

**Feature Composition** (64 dimensions):
- Dimensions 0-15: Geometric features (point count, spread width, symmetry score, antler height ratio, base diameter, curvature)
- Dimensions 16-47: Tine angle vectors (8 tines x 4 features: length, angle, thickness, position)
- Dimensions 48-63: Unique formation flags (brow tine presence, drop tine, sticker points, beam curvature, asymmetry patterns)

#### 1.2 Coat Pattern Column

```sql
ALTER TABLE deer ADD COLUMN coat_pattern VECTOR(192);
COMMENT ON COLUMN deer.coat_pattern IS 'Coat marking and color pattern feature vector (192-dim): 4 body regions x 48-dim color histogram. Used for doe/fawn identification and detecting unique markings (white patches, blazes, scars).';
```

**Design Rationale**:
- **Vector(192)**: 4 body regions (chest, flanks, face, legs) x 48-dim color histogram (16 bins per RGB channel)
- **Always populated**: Applicable to all deer (bucks, does, fawns)
- **Illumination invariant**: Histograms normalized before storage

**Feature Composition** (192 dimensions):
- Dimensions 0-47: Chest region color histogram (16R + 16G + 16B bins)
- Dimensions 48-95: Flank region color histogram
- Dimensions 96-143: Face region color histogram
- Dimensions 144-191: Leg region color histogram

#### 1.3 Temporal Profile Column

```sql
ALTER TABLE deer ADD COLUMN temporal_profile JSONB;
COMMENT ON COLUMN deer.temporal_profile IS 'Activity pattern metadata: location frequency distribution, time-of-day histogram, seasonal presence. Used for temporal context scoring. Updated incrementally with each new sighting.';
```

**Design Rationale**:
- **JSONB**: Flexible structure for temporal data that doesn't require vector similarity search
- **Incrementally updated**: Recalculated after each new sighting (low cost: O(1) update)
- **Not indexed**: Small payload (<1KB), accessed only during re-ID scoring

**JSON Structure**:
```json
{
    "location_frequency": {
        "uuid-location-1": 45,  // Detection count at each location
        "uuid-location-2": 12,
        "uuid-location-3": 8
    },
    "time_of_day_histogram": [
        0, 0, 1, 3, 8, 12, 15, 10, 5, 2, 1, 0,  // Hours 0-11
        0, 1, 2, 5, 10, 18, 22, 15, 8, 3, 1, 0   // Hours 12-23
    ],
    "seasonal_presence": [
        "2024-fall",
        "2024-rut",
        "2025-spring"
    ],
    "first_seen": "2024-09-15T06:30:00Z",
    "last_seen": "2025-01-20T18:15:00Z",
    "sighting_count": 65,
    "favorite_location_id": "uuid-location-1",
    "favorite_time_window": "17:00-19:00"  // Most active period
}
```

#### 1.4 Best Pose Metadata

```sql
ALTER TABLE deer ADD COLUMN best_pose_metadata JSONB;
COMMENT ON COLUMN deer.best_pose_metadata IS 'Reference to best quality detection for each pose type (frontal, profile-left, profile-right, rear). Used for selecting representative images in UI and improving pose-normalized matching. Structure: {pose_type: {detection_id, image_id, confidence, timestamp}}.';
```

**Design Rationale**:
- **JSONB**: Store references to best detection for each pose type
- **UI support**: Frontend can display multiple representative images (frontal + profile)
- **Matching improvement**: Use best profile pose as canonical reference for normalization

**JSON Structure**:
```json
{
    "frontal": {
        "detection_id": "uuid-det-123",
        "image_id": "uuid-img-456",
        "confidence": 0.92,
        "timestamp": "2024-11-15T14:30:00Z",
        "pose_angle": 15
    },
    "profile_left": {
        "detection_id": "uuid-det-789",
        "image_id": "uuid-img-012",
        "confidence": 0.89,
        "timestamp": "2024-11-18T07:45:00Z",
        "pose_angle": 90
    },
    "profile_right": null,  // Not yet captured
    "rear": {
        "detection_id": "uuid-det-345",
        "image_id": "uuid-img-678",
        "confidence": 0.75,
        "timestamp": "2024-11-20T18:00:00Z",
        "pose_angle": 180
    }
}
```

---

### 2. Detections Table - Enhancement Metadata

```sql
ALTER TABLE detections ADD COLUMN enhancement_metadata JSONB;
COMMENT ON COLUMN detections.enhancement_metadata IS 'Per-detection feature extraction metadata: pose classification, antler visibility, temporal score, coat features extracted, enhancement flags. Used for debugging, UI display, and selective re-processing.';
```

**Design Rationale**:
- **Per-detection**: Each detection has unique pose, antler visibility, extraction success
- **Debugging**: Understand why re-ID matched or failed
- **UI display**: Show pose classification, antler presence, confidence breakdown
- **Selective re-processing**: Re-run enhancements on specific detections if models improve

**JSON Structure**:
```json
{
    "pose_estimation": {
        "classification": "profile_left",  // frontal/profile_left/profile_right/rear/angled
        "angle_degrees": 85,
        "confidence": 0.87,
        "keypoints": {
            "nose": [120, 45, 0.92],  // [x, y, confidence]
            "left_ear": [115, 30, 0.88],
            "right_ear": [125, 28, 0.85],
            "shoulder": [140, 80, 0.90],
            "hip": [180, 85, 0.89],
            "tail_base": [200, 90, 0.75]
        },
        "inference_time_ms": 52
    },
    "antler_features": {
        "visible": true,
        "point_count_estimate": 8,
        "spread_width_px": 245,
        "symmetry_score": 0.78,
        "extraction_success": true,
        "inference_time_ms": 185
    },
    "coat_patterns": {
        "white_chest_patch": true,
        "facial_blaze": false,
        "visible_scars": [],
        "extraction_success": true,
        "inference_time_ms": 95
    },
    "temporal_context": {
        "location_match_score": 0.65,  // Alignment with deer's location preferences
        "time_of_day_match_score": 0.82,  // Alignment with deer's activity pattern
        "temporal_conflict_detected": false,
        "inference_time_ms": 3
    },
    "enhancement_flags": {
        "antler_enhancement_used": true,
        "pose_normalization_used": true,
        "coat_analysis_used": true,
        "temporal_scoring_used": true,
        "ensemble_mode_used": false
    },
    "reid_result": {
        "matched_deer_id": "uuid-deer-123",
        "visual_similarity": 0.88,
        "temporal_similarity": 0.73,
        "antler_similarity": 0.91,
        "coat_similarity": 0.76,
        "final_confidence": 0.87,
        "match_method": "enhanced_weighted_fusion",  // vs "baseline_resnet50"
        "inference_time_ms": 450
    }
}
```

---

### 3. Seasonal Antler Archive Table (New)

```sql
CREATE TABLE deer_antler_archive (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deer_id UUID NOT NULL REFERENCES deer(id) ON DELETE CASCADE,
    season_tag VARCHAR(20) NOT NULL,  -- Format: "YYYY-season" (e.g., "2024-rut")
    antler_fingerprint VECTOR(64) NOT NULL,
    representative_detection_id UUID NOT NULL REFERENCES detections(id) ON DELETE SET NULL,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    sighting_count INTEGER NOT NULL DEFAULT 1,
    average_confidence REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    UNIQUE (deer_id, season_tag)
);

CREATE INDEX ix_deer_antler_archive_deer_id ON deer_antler_archive (deer_id);
CREATE INDEX ix_deer_antler_archive_season_tag ON deer_antler_archive (season_tag);
CREATE INDEX ix_deer_antler_archive_fingerprint_hnsw ON deer_antler_archive USING hnsw (antler_fingerprint vector_cosine_ops);

COMMENT ON TABLE deer_antler_archive IS 'Seasonal archiving of buck antler patterns. Bucks shed antlers Feb-Mar and regrow with different point counts. This table enables cross-year tracking: match 2024-rut antlers separately from 2025-rut. Used for mature buck longitudinal studies.';
```

**Design Rationale**:
- **Cross-year tracking**: Bucks shed antlers annually, new growth may differ
- **Seasonal matching**: Match current rut season (Aug-Feb) antlers only within that season
- **HNSW index**: Fast similarity search when matching new buck detections to archive
- **CASCADE delete**: If deer profile deleted, remove all seasonal archives

**Season Tag Format**:
- `"2024-rut"`: Aug 2024 - Jan 2025 (primary rut and hunting season)
- `"2024-post-rut"`: Feb 2024 - Jul 2024 (antlers shed, use body-only matching)
- `"2025-rut"`: Aug 2025 - Jan 2026

---

## Indexes

### Vector Similarity Indexes

```sql
-- Antler fingerprint search (buck re-ID within season)
CREATE INDEX ix_deer_antler_fingerprint_hnsw ON deer USING hnsw (antler_fingerprint vector_cosine_ops)
WHERE antler_fingerprint IS NOT NULL;

-- Coat pattern search (all deer, especially does/fawns)
CREATE INDEX ix_deer_coat_pattern_hnsw ON deer USING hnsw (coat_pattern vector_cosine_ops);
```

**Index Strategy**:
- **HNSW (Hierarchical Navigable Small World)**: Approximate nearest neighbor search in O(log N) time
- **Cosine distance**: vector_cosine_ops for normalized feature vectors
- **Partial index**: antler_fingerprint only indexed when NOT NULL (does/fawns excluded)
- **Full index**: coat_pattern always populated, all deer indexed

### JSONB Indexes

```sql
-- Query detections by pose classification (e.g., "find all profile-left bucks")
CREATE INDEX ix_detections_enhancement_pose ON detections
USING gin ((enhancement_metadata -> 'pose_estimation' -> 'classification'));

-- Query detections with antler visibility (e.g., "find all antler-visible detections")
CREATE INDEX ix_detections_enhancement_antler ON detections
USING gin ((enhancement_metadata -> 'antler_features' -> 'visible'));

-- Query deer by favorite location (temporal profile)
CREATE INDEX ix_deer_temporal_favorite_location ON deer
USING gin ((temporal_profile -> 'favorite_location_id'));
```

---

## Data Types and Constraints

### Enum Types (No Changes Required)

Existing enums remain unchanged:
- `DeerSex`: buck, doe, fawn, unknown
- `DeerStatus`: alive, deceased, unknown

### Vector Dimensions

| Column | Dimensions | Rationale |
|--------|-----------|-----------|
| feature_vector (existing) | 512 | ResNet50 body features (baseline) |
| antler_fingerprint | 64 | Geometric (16) + tine angles (32) + formations (16) |
| coat_pattern | 192 | 4 regions x 48-dim histogram |

**Storage Overhead**:
- Per deer: 512*4 + 64*4 + 192*4 = 2048 + 256 + 768 = 3072 bytes (3KB vectors)
- Per detection (JSONB): ~500 bytes average (enhancement_metadata)
- 50 deer x 3KB = 150KB total (negligible)
- 35,000 detections x 500 bytes = 17.5MB (acceptable)

---

## Migration Strategy

### Migration 011: Add Enhanced Re-ID Columns

**File**: `migrations/011_add_enhanced_reid_columns.sql`

```sql
-- Migration: 011_add_enhanced_reid_columns
-- Feature: 010-enhanced-reidentification
-- Description: Add antler fingerprint, coat pattern, temporal profile, and pose metadata columns
-- Date: 2025-11-11

BEGIN;

-- Step 1: Add new vector columns to deer table (nullable for backward compatibility)
ALTER TABLE deer ADD COLUMN IF NOT EXISTS antler_fingerprint VECTOR(64);
ALTER TABLE deer ADD COLUMN IF NOT EXISTS coat_pattern VECTOR(192);
ALTER TABLE deer ADD COLUMN IF NOT EXISTS temporal_profile JSONB;
ALTER TABLE deer ADD COLUMN IF NOT EXISTS best_pose_metadata JSONB;

-- Step 2: Add comments
COMMENT ON COLUMN deer.antler_fingerprint IS 'Antler pattern feature vector (64-dim): point count, spread width, symmetry, tine angles, unique formations. NULL for does/fawns or when antlers not visible. Seasonal: archived by year-season (e.g., 2024-rut).';
COMMENT ON COLUMN deer.coat_pattern IS 'Coat marking and color pattern feature vector (192-dim): 4 body regions x 48-dim color histogram. Used for doe/fawn identification and detecting unique markings (white patches, blazes, scars).';
COMMENT ON COLUMN deer.temporal_profile IS 'Activity pattern metadata: location frequency distribution, time-of-day histogram, seasonal presence. Used for temporal context scoring. Updated incrementally with each new sighting.';
COMMENT ON COLUMN deer.best_pose_metadata IS 'Reference to best quality detection for each pose type (frontal, profile-left, profile-right, rear). Structure: {pose_type: {detection_id, image_id, confidence, timestamp}}.';

-- Step 3: Add enhancement metadata to detections table
ALTER TABLE detections ADD COLUMN IF NOT EXISTS enhancement_metadata JSONB;
COMMENT ON COLUMN detections.enhancement_metadata IS 'Per-detection feature extraction metadata: pose classification, antler visibility, temporal score, coat features extracted, enhancement flags. Used for debugging, UI display, and selective re-processing.';

-- Step 4: Create seasonal antler archive table
CREATE TABLE IF NOT EXISTS deer_antler_archive (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deer_id UUID NOT NULL REFERENCES deer(id) ON DELETE CASCADE,
    season_tag VARCHAR(20) NOT NULL,
    antler_fingerprint VECTOR(64) NOT NULL,
    representative_detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    sighting_count INTEGER NOT NULL DEFAULT 1,
    average_confidence REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_deer_antler_archive_deer_season UNIQUE (deer_id, season_tag)
);

COMMENT ON TABLE deer_antler_archive IS 'Seasonal archiving of buck antler patterns. Bucks shed antlers Feb-Mar and regrow with different point counts. This table enables cross-year tracking: match 2024-rut antlers separately from 2025-rut. Used for mature buck longitudinal studies.';

-- Step 5: Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS ix_deer_antler_fingerprint_hnsw ON deer USING hnsw (antler_fingerprint vector_cosine_ops)
WHERE antler_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_deer_coat_pattern_hnsw ON deer USING hnsw (coat_pattern vector_cosine_ops);

CREATE INDEX IF NOT EXISTS ix_deer_antler_archive_deer_id ON deer_antler_archive (deer_id);
CREATE INDEX IF NOT EXISTS ix_deer_antler_archive_season_tag ON deer_antler_archive (season_tag);
CREATE INDEX IF NOT EXISTS ix_deer_antler_archive_fingerprint_hnsw ON deer_antler_archive USING hnsw (antler_fingerprint vector_cosine_ops);

-- Step 6: Create JSONB indexes for common queries
CREATE INDEX IF NOT EXISTS ix_detections_enhancement_pose ON detections
USING gin ((enhancement_metadata -> 'pose_estimation' -> 'classification'));

CREATE INDEX IF NOT EXISTS ix_detections_enhancement_antler ON detections
USING gin ((enhancement_metadata -> 'antler_features' -> 'visible'));

CREATE INDEX IF NOT EXISTS ix_deer_temporal_favorite_location ON deer
USING gin ((temporal_profile -> 'favorite_location_id'));

-- Step 7: Initialize temporal_profile for existing deer (empty structure)
UPDATE deer
SET temporal_profile = '{
    "location_frequency": {},
    "time_of_day_histogram": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    "seasonal_presence": [],
    "sighting_count": 0
}'::jsonb
WHERE temporal_profile IS NULL;

COMMIT;
```

### Rollback Strategy

```sql
-- Rollback: 011_add_enhanced_reid_columns
-- WARNING: This will delete all enhanced re-ID data. Feature vectors cannot be recovered.

BEGIN;

-- Drop indexes first
DROP INDEX IF EXISTS ix_deer_antler_fingerprint_hnsw;
DROP INDEX IF EXISTS ix_deer_coat_pattern_hnsw;
DROP INDEX IF EXISTS ix_deer_antler_archive_deer_id;
DROP INDEX IF EXISTS ix_deer_antler_archive_season_tag;
DROP INDEX IF EXISTS ix_deer_antler_archive_fingerprint_hnsw;
DROP INDEX IF EXISTS ix_detections_enhancement_pose;
DROP INDEX IF EXISTS ix_detections_enhancement_antler;
DROP INDEX IF EXISTS ix_deer_temporal_favorite_location;

-- Drop seasonal archive table
DROP TABLE IF EXISTS deer_antler_archive CASCADE;

-- Remove columns
ALTER TABLE deer DROP COLUMN IF EXISTS antler_fingerprint;
ALTER TABLE deer DROP COLUMN IF EXISTS coat_pattern;
ALTER TABLE deer DROP COLUMN IF EXISTS temporal_profile;
ALTER TABLE deer DROP COLUMN IF EXISTS best_pose_metadata;
ALTER TABLE detections DROP COLUMN IF EXISTS enhancement_metadata;

COMMIT;
```

---

## Backward Compatibility

### Existing Code Compatibility

1. **Deer Model**: New columns are nullable, existing queries unaffected
2. **Detection Model**: enhancement_metadata is optional, NULL for baseline detections
3. **Re-ID Pipeline**: Existing reidentify_detection task continues using feature_vector only
4. **API Endpoints**: GET /api/deer returns same fields (new fields excluded by default)

### Migration Safety

- **Zero downtime**: ALTER TABLE ADD COLUMN (nullable) does not lock table
- **Incremental adoption**: Enhanced re-ID enabled per-detection via configuration
- **Fallback**: If enhancement fails, system uses baseline ResNet50 features
- **Data preservation**: Baseline feature_vector always populated as primary identifier

---

## Data Access Patterns

### Query 1: Find Similar Deer (Enhanced Re-ID)

```sql
-- Find deer with similar body features, antler patterns, and coat patterns
SELECT
    d.id,
    d.name,
    d.sex,
    1 - (d.feature_vector <=> :body_vector) AS body_similarity,
    1 - (d.antler_fingerprint <=> :antler_vector) AS antler_similarity,
    1 - (d.coat_pattern <=> :coat_vector) AS coat_similarity,
    d.temporal_profile,
    (
        0.6 * (1 - (d.feature_vector <=> :body_vector)) +
        0.25 * COALESCE(1 - (d.antler_fingerprint <=> :antler_vector), 0) +
        0.15 * (1 - (d.coat_pattern <=> :coat_vector))
    ) AS weighted_similarity
FROM deer d
WHERE
    d.sex = :sex  -- Match within same sex
    AND (d.feature_vector <=> :body_vector) < 0.3  -- Cosine distance < 0.3 (similarity > 0.7)
ORDER BY weighted_similarity DESC
LIMIT 10;
```

**Performance**: HNSW indexes enable O(log N) search, ~5-10ms for 100 deer

### Query 2: Find Detections by Pose

```sql
-- Find all profile-left detections of bucks with antlers visible
SELECT
    d.id,
    d.image_id,
    d.bbox,
    d.enhancement_metadata -> 'pose_estimation' ->> 'angle_degrees' AS pose_angle,
    d.enhancement_metadata -> 'antler_features' ->> 'point_count_estimate' AS point_count
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE
    d.classification = 'buck'
    AND d.enhancement_metadata -> 'pose_estimation' ->> 'classification' = 'profile_left'
    AND (d.enhancement_metadata -> 'antler_features' ->> 'visible')::boolean = true
ORDER BY i.timestamp DESC
LIMIT 100;
```

**Performance**: GIN index on JSONB enables fast filtering, ~10-20ms

### Query 3: Temporal Activity Pattern

```sql
-- Get deer's favorite locations and active hours
SELECT
    d.id,
    d.name,
    d.temporal_profile -> 'favorite_location_id' AS favorite_location,
    d.temporal_profile -> 'favorite_time_window' AS active_hours,
    d.temporal_profile -> 'time_of_day_histogram' AS hourly_activity
FROM deer d
WHERE d.id = :deer_id;
```

**Performance**: Direct JSONB access, <1ms

---

## Testing Strategy

### Unit Tests

1. **Migration**: Test 011 applies cleanly on test database
2. **Rollback**: Verify rollback removes all new columns/tables
3. **Indexes**: Confirm HNSW and GIN indexes created successfully
4. **Constraints**: Test UNIQUE constraint on deer_antler_archive(deer_id, season_tag)

### Integration Tests

1. **Vector Search**: Insert test vectors, verify similarity search returns correct matches
2. **JSONB Queries**: Test filtering by pose classification, antler visibility
3. **Temporal Profile**: Test incremental updates after new sightings
4. **Seasonal Archive**: Test archiving antler fingerprints across multiple seasons

### Performance Benchmarks

1. **Similarity Search**: <10ms for 100 deer, <50ms for 1000 deer
2. **JSONB Filtering**: <20ms for 35,000 detections
3. **Temporal Update**: <5ms per sighting
4. **Storage Overhead**: <20MB for 35,000 detections + 50 deer

---

## Phase 1 Exit Criteria

- [X] Database schema defined with all new columns
- [X] Seasonal antler archive table designed
- [X] Indexes specified for vector similarity and JSONB queries
- [X] Migration SQL written with rollback strategy
- [X] Backward compatibility verified
- [X] Data access patterns documented with query examples
- [X] Testing strategy outlined

**Status**: COMPLETE - Ready for contracts/ generation

---

## Next Steps

1. Generate contracts/enhanced_reid_task.md: Celery task specification
2. Generate contracts/deer_api.md: Updated API endpoints with enhancement metadata
3. Generate quickstart.md: Developer setup guide for MMPose and model downloads
