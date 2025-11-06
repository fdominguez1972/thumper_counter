-- Migration: 001_add_processing_status.sql
-- Feature: Detection Pipeline Integration (001-detection-pipeline)
-- Purpose: Add processing status tracking and error message fields to images table
-- Date: 2025-11-05

-- Add error_message column (new field for Sprint 2)
-- This stores error details when processing fails
ALTER TABLE images
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Update processing_status enum type
-- Current state: UPPERCASE values with QUEUED state (PENDING, QUEUED, PROCESSING, COMPLETED, FAILED)
-- Target state: lowercase values without QUEUED (pending, processing, completed, failed)

DO $$
BEGIN
    -- Drop and recreate enum with correct values
    -- First, create a temporary column to hold the data
    ALTER TABLE images ADD COLUMN processing_status_temp VARCHAR(20);

    -- Copy and convert existing data to lowercase (PENDING -> pending, etc.)
    UPDATE images SET processing_status_temp = LOWER(processing_status::text);

    -- Drop the old column (this also drops the enum type if not used elsewhere)
    ALTER TABLE images DROP COLUMN processing_status;

    -- Drop the old enum type if it still exists
    DROP TYPE IF EXISTS processingstatus;

    -- Create new enum type with correct lowercase values (no QUEUED)
    CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed');

    -- Add the column back with the new type and default
    ALTER TABLE images ADD COLUMN processing_status processingstatus NOT NULL DEFAULT 'pending'::processingstatus;

    -- Copy data from temp column
    UPDATE images SET processing_status = processing_status_temp::processingstatus;

    -- Drop temp column
    ALTER TABLE images DROP COLUMN processing_status_temp;

    -- Recreate index for status queries (required for performance)
    CREATE INDEX IF NOT EXISTS idx_images_processing_status ON images(processing_status);
END$$;

-- Add comment to error_message column for documentation
COMMENT ON COLUMN images.error_message IS 'Error message if processing failed (populated when status=FAILED)';

-- Add comment to processing_status column
COMMENT ON COLUMN images.processing_status IS 'Current state in ML pipeline: pending -> processing -> completed/failed';

-- Verify migration
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'images'
AND column_name IN ('processing_status', 'error_message')
ORDER BY column_name;

-- Show current processing status distribution
SELECT processing_status, COUNT(*) as count FROM images GROUP BY processing_status;
