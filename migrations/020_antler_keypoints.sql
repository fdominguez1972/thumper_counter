-- Migration 020: Antler Keypoints Detection
-- Date: 2025-11-19
-- Purpose: Store antler keypoint detection results for enhanced buck Re-ID

-- Create antler_keypoints table
CREATE TABLE IF NOT EXISTS antler_keypoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    keypoint_index INTEGER NOT NULL,
    keypoint_name VARCHAR(50) NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    visibility INTEGER NOT NULL DEFAULT 2,  -- 0=not visible, 1=occluded, 2=visible
    confidence FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure keypoint_index is valid (0-15 for 16 keypoints)
    CONSTRAINT valid_keypoint_index CHECK (keypoint_index >= 0 AND keypoint_index <= 15),
    CONSTRAINT valid_visibility CHECK (visibility >= 0 AND visibility <= 2),
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Unique constraint: one keypoint per detection per index
    CONSTRAINT unique_detection_keypoint UNIQUE (detection_id, keypoint_index)
);

-- Create index for fast detection lookups
CREATE INDEX idx_antler_keypoints_detection_id ON antler_keypoints(detection_id);

-- Create index for querying by keypoint type
CREATE INDEX idx_antler_keypoints_name ON antler_keypoints(keypoint_name);

-- Add comment
COMMENT ON TABLE antler_keypoints IS 'Stores 16-point antler keypoint detections from YOLOv8-pose model for enhanced buck Re-ID';

-- Keypoint names (for reference):
-- 0: left_main_beam
-- 1: left_brow_tine
-- 2: left_g2
-- 3: left_g3
-- 4: left_g4
-- 5: left_tip
-- 6: left_bez_tine
-- 7: left_royal_tine
-- 8: right_main_beam
-- 9: right_brow_tine
-- 10: right_g2
-- 11: right_g3
-- 12: right_g4
-- 13: right_tip
-- 14: right_bez_tine
-- 15: right_royal_tine
