-- Migration 011: Add Re-ID Similarity Scores Tracking Table
-- Feature: 010-infrastructure-fixes, Option D (Hybrid Approach - Phase 1)
-- Purpose: Enable ongoing Re-ID performance monitoring and analysis
-- Created: 2025-11-14

-- ============================================================================
-- TABLE: reid_similarity_scores
-- ============================================================================
-- Stores all similarity calculations performed during re-identification
-- to enable performance analysis, threshold tuning, and monitoring.

CREATE TABLE IF NOT EXISTS reid_similarity_scores (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    detection_id UUID NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    deer_id UUID NOT NULL REFERENCES deer(id) ON DELETE CASCADE,

    -- Similarity metrics
    similarity_score NUMERIC(5, 4) NOT NULL CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0),
    -- Cosine similarity between detection and deer feature vectors (0.0 - 1.0)

    -- Matching context
    sex_match BOOLEAN NOT NULL,
    -- Whether detection and deer have same sex (used for filtering)

    matched BOOLEAN NOT NULL,
    -- Whether this similarity score resulted in assignment (score >= threshold)

    threshold_used NUMERIC(5, 4) NOT NULL,
    -- REID_THRESHOLD value used at time of calculation

    -- Detection metadata (denormalized for analysis performance)
    detection_classification VARCHAR(50),
    deer_sex VARCHAR(20),

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT reid_similarity_scores_detection_deer_unique UNIQUE (detection_id, deer_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for finding all attempts for a specific detection
CREATE INDEX idx_reid_similarity_detection
ON reid_similarity_scores(detection_id, similarity_score DESC);

-- Index for finding all matches against a specific deer
CREATE INDEX idx_reid_similarity_deer
ON reid_similarity_scores(deer_id, similarity_score DESC);

-- Index for time-series analysis
CREATE INDEX idx_reid_similarity_timestamp
ON reid_similarity_scores(calculated_at DESC);

-- Index for threshold analysis queries
CREATE INDEX idx_reid_similarity_score
ON reid_similarity_scores(similarity_score DESC);

-- Index for matched vs unmatched analysis
CREATE INDEX idx_reid_similarity_matched
ON reid_similarity_scores(matched, similarity_score DESC);

-- Index for sex-based performance analysis
CREATE INDEX idx_reid_similarity_sex_match
ON reid_similarity_scores(sex_match, matched);

-- Composite index for common filter pattern
CREATE INDEX idx_reid_similarity_analysis
ON reid_similarity_scores(calculated_at DESC, matched, sex_match);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE reid_similarity_scores IS
'Stores all similarity calculations from re-identification process for performance monitoring and threshold tuning';

COMMENT ON COLUMN reid_similarity_scores.similarity_score IS
'Cosine similarity (0.0-1.0) between detection feature vector and deer profile feature vector';

COMMENT ON COLUMN reid_similarity_scores.sex_match IS
'Whether detection classification sex matches deer sex (affects matching eligibility)';

COMMENT ON COLUMN reid_similarity_scores.matched IS
'Whether this similarity score resulted in deer_id assignment (score >= threshold)';

COMMENT ON COLUMN reid_similarity_scores.threshold_used IS
'REID_THRESHOLD environment variable value at time of calculation';

COMMENT ON COLUMN reid_similarity_scores.detection_classification IS
'Detection classification (buck/doe/fawn) at time of matching - denormalized for analysis';

COMMENT ON COLUMN reid_similarity_scores.deer_sex IS
'Deer sex (buck/doe/fawn/unknown) at time of matching - denormalized for analysis';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Find all similarity attempts for a detection (ordered by score)
-- SELECT * FROM reid_similarity_scores
-- WHERE detection_id = 'uuid'
-- ORDER BY similarity_score DESC;

-- Calculate assignment rate by threshold
-- SELECT
--   threshold_used,
--   COUNT(*) as total_attempts,
--   SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matches,
--   ROUND(100.0 * SUM(CASE WHEN matched THEN 1 ELSE 0 END) / COUNT(*), 2) as assignment_rate
-- FROM reid_similarity_scores
-- GROUP BY threshold_used
-- ORDER BY threshold_used DESC;

-- Find "near miss" detections (high score but below threshold)
-- SELECT
--   detection_id,
--   deer_id,
--   similarity_score,
--   threshold_used,
--   (threshold_used - similarity_score) as score_gap
-- FROM reid_similarity_scores
-- WHERE matched = false
--   AND similarity_score >= (threshold_used - 0.05)
-- ORDER BY similarity_score DESC
-- LIMIT 100;

-- Histogram data for similarity score distribution
-- SELECT
--   ROUND(similarity_score, 1) as score_bucket,
--   COUNT(*) as frequency,
--   SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matched_count
-- FROM reid_similarity_scores
-- GROUP BY score_bucket
-- ORDER BY score_bucket DESC;

-- Performance by sex matching
-- SELECT
--   sex_match,
--   COUNT(*) as attempts,
--   AVG(similarity_score) as avg_score,
--   SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matches,
--   ROUND(100.0 * SUM(CASE WHEN matched THEN 1 ELSE 0 END) / COUNT(*), 2) as match_rate
-- FROM reid_similarity_scores
-- GROUP BY sex_match;

-- ============================================================================
-- ROLLBACK
-- ============================================================================

-- To rollback this migration:
-- DROP INDEX IF EXISTS idx_reid_similarity_analysis;
-- DROP INDEX IF EXISTS idx_reid_similarity_sex_match;
-- DROP INDEX IF EXISTS idx_reid_similarity_matched;
-- DROP INDEX IF EXISTS idx_reid_similarity_score;
-- DROP INDEX IF EXISTS idx_reid_similarity_timestamp;
-- DROP INDEX IF EXISTS idx_reid_similarity_deer;
-- DROP INDEX IF EXISTS idx_reid_similarity_detection;
-- DROP TABLE IF EXISTS reid_similarity_scores;
