-- Migration: Add user correction fields to detections table
-- Date: 2025-11-08
-- Purpose: Allow users to correct/verify detection data for data quality

-- Add correction and quality control fields
ALTER TABLE detections ADD COLUMN IF NOT EXISTS is_reviewed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS is_valid BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS corrected_classification VARCHAR(20);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS correction_notes TEXT;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;

-- Add index for querying reviewed/valid detections
CREATE INDEX IF NOT EXISTS ix_detections_is_reviewed ON detections(is_reviewed);
CREATE INDEX IF NOT EXISTS ix_detections_is_valid ON detections(is_valid);

-- Comments for new fields
COMMENT ON COLUMN detections.is_reviewed IS 'True if a user has reviewed and verified this detection';
COMMENT ON COLUMN detections.is_valid IS 'False if detection is unusable (rear-end, wrong species, poor quality, etc.)';
COMMENT ON COLUMN detections.corrected_classification IS 'User-corrected classification if ML was wrong (buck/doe/fawn/unknown)';
COMMENT ON COLUMN detections.correction_notes IS 'User notes explaining correction or why detection is invalid';
COMMENT ON COLUMN detections.reviewed_by IS 'Username or identifier of who reviewed this detection';
COMMENT ON COLUMN detections.reviewed_at IS 'Timestamp when detection was reviewed';
