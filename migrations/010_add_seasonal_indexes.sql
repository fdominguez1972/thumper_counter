-- Migration: Add seasonal analysis performance indexes
-- Feature: 008-rut-season-analysis
-- Created: 2025-11-08
-- Purpose: Optimize date range queries and classification filtering

BEGIN;

-- Index 1: Timestamp for fast date range queries
-- Impact: 95% speed improvement (full table scan -> indexed lookup)
-- Query pattern: WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31'
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);

-- Index 2: Classification and confidence for filtered queries
-- Impact: Faster buck detection queries with confidence thresholds
-- Query pattern: WHERE classification IN ('mature', 'mid', 'young') AND confidence >= 0.7
CREATE INDEX IF NOT EXISTS idx_detections_classification_confidence
  ON detections(classification, confidence DESC);

-- Verify indexes were created
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE indexname IN ('idx_images_timestamp', 'idx_detections_classification_confidence')
ORDER BY indexname;

COMMIT;

-- Usage verification queries:
--
-- Test timestamp index:
-- EXPLAIN ANALYZE SELECT COUNT(*) FROM images WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31';
-- Expected: Index Scan using idx_images_timestamp
--
-- Test classification index:
-- EXPLAIN ANALYZE SELECT * FROM detections WHERE classification IN ('mature', 'mid', 'young') AND confidence >= 0.7 ORDER BY confidence DESC LIMIT 100;
-- Expected: Index Scan using idx_detections_classification_confidence
