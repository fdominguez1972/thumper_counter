-- Migration: Add best_photo_id to deer table
-- Sprint 7: UI image display
-- Date: 2025-11-07

-- Add best_photo_id column to deer table
ALTER TABLE deer
ADD COLUMN IF NOT EXISTS best_photo_id UUID;

-- Add foreign key constraint
ALTER TABLE deer
ADD CONSTRAINT fk_deer_best_photo
FOREIGN KEY (best_photo_id)
REFERENCES images(id)
ON DELETE SET NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS ix_deer_best_photo_id
ON deer(best_photo_id);

-- Update existing deer with their first/best detection image
-- (use the image with highest confidence detection for each deer)
UPDATE deer d
SET best_photo_id = (
    SELECT i.id
    FROM detections det
    JOIN images i ON det.image_id = i.id
    WHERE det.deer_id = d.id
    AND det.confidence IS NOT NULL
    ORDER BY det.confidence DESC, i.timestamp DESC
    LIMIT 1
)
WHERE d.best_photo_id IS NULL
AND EXISTS (
    SELECT 1 FROM detections det WHERE det.deer_id = d.id
);
