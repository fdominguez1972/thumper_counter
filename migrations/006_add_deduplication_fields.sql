-- Migration 006: Add deduplication fields to detections table
-- Created: 2025-11-07
-- Purpose: Support within-image and burst-level deduplication

BEGIN;

-- Add is_duplicate field
ALTER TABLE detections
ADD COLUMN is_duplicate BOOLEAN NOT NULL DEFAULT FALSE;

-- Add burst_group_id field
ALTER TABLE detections
ADD COLUMN burst_group_id UUID;

-- Add indexes for efficient querying
CREATE INDEX idx_detections_is_duplicate ON detections(is_duplicate);
CREATE INDEX idx_detections_burst_group ON detections(burst_group_id);

-- Add comments
COMMENT ON COLUMN detections.is_duplicate IS 'True if this detection overlaps significantly with another in same image';
COMMENT ON COLUMN detections.burst_group_id IS 'Groups detections from same photo burst/event (same timestamp + location)';

COMMIT;

-- Verify changes
\d detections;

-- Show stats
SELECT
    COUNT(*) as total_detections,
    COUNT(*) FILTER (WHERE is_duplicate = TRUE) as duplicates,
    COUNT(DISTINCT burst_group_id) as burst_groups
FROM detections;
