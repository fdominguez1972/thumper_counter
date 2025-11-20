-- Backfill antler_processing_log with existing processing results
-- Created: 2025-11-20
-- Purpose: Populate log table with detections that already have antler keypoints

-- Insert log entries for detections that have antler keypoints
-- Use the earliest keypoint created_at as the processed_at timestamp
INSERT INTO antler_processing_log (
    detection_id,
    processed_at,
    antlers_detected,
    keypoints_count,
    model_version,
    processing_notes
)
SELECT
    ak.detection_id,
    MIN(ak.created_at) as processed_at,  -- Use earliest keypoint timestamp
    TRUE as antlers_detected,  -- True (antlers were detected)
    COUNT(*) as keypoints_count,  -- Count of keypoints for this detection
    'antler_detection_20251116' as model_version,
    NULL as processing_notes
FROM antler_keypoints ak
GROUP BY ak.detection_id
ON CONFLICT (detection_id) DO NOTHING;

-- Display summary
SELECT
    'Backfill complete' as status,
    COUNT(*) as entries_created
FROM antler_processing_log;
