-- Migration 021: Add antler processing log table
-- Created: 2025-11-20
-- Purpose: Track which detections have been processed for antler detection,
--          including cases where no antlers were found

-- Create antler processing log table
CREATE TABLE IF NOT EXISTS antler_processing_log (
    detection_id UUID PRIMARY KEY REFERENCES detections(id) ON DELETE CASCADE,
    processed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    antlers_detected BOOLEAN NOT NULL,
    keypoints_count INTEGER NOT NULL DEFAULT 0,
    model_version VARCHAR(100) NOT NULL,
    processing_notes TEXT,
    CONSTRAINT valid_keypoints_count CHECK (keypoints_count >= 0)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_antler_processing_detected
    ON antler_processing_log(antlers_detected);

CREATE INDEX IF NOT EXISTS idx_antler_processing_timestamp
    ON antler_processing_log(processed_at);

CREATE INDEX IF NOT EXISTS idx_antler_processing_model
    ON antler_processing_log(model_version);

-- Add comment for documentation
COMMENT ON TABLE antler_processing_log IS
    'Tracks antler detection processing status for all buck detections, including cases where no antlers were found';

COMMENT ON COLUMN antler_processing_log.detection_id IS
    'Foreign key to detections table';

COMMENT ON COLUMN antler_processing_log.processed_at IS
    'Timestamp when antler detection was performed';

COMMENT ON COLUMN antler_processing_log.antlers_detected IS
    'Whether antlers were detected in the crop (true) or not (false)';

COMMENT ON COLUMN antler_processing_log.keypoints_count IS
    'Number of keypoints saved (typically 16 for successful detection, 0 for none)';

COMMENT ON COLUMN antler_processing_log.model_version IS
    'Version/name of the antler detection model used';

COMMENT ON COLUMN antler_processing_log.processing_notes IS
    'Optional notes about processing (errors, warnings, quality issues)';
