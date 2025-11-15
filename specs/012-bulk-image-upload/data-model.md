# Data Model: Bulk Image Upload

**Feature**: 009-bulk-image-upload
**Date**: 2025-11-11
**Phase**: 1 - Design

## Overview

The bulk upload feature introduces one new entity (`upload_batches`) and modifies the existing `images` table to track upload batch provenance. This enables upload history tracking, batch-level statistics, and troubleshooting failed uploads.

## Database Schema

### New Table: `upload_batches`

Tracks metadata for each upload operation (individual files or ZIP archive).

```sql
CREATE TABLE upload_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    upload_type VARCHAR(10) NOT NULL CHECK (upload_type IN ('files', 'zip')),
    total_files INTEGER NOT NULL DEFAULT 0,
    successful_files INTEGER NOT NULL DEFAULT 0,
    failed_files INTEGER NOT NULL DEFAULT 0,
    zip_filename VARCHAR(255),  -- NULL for individual file uploads
    zip_size_bytes BIGINT,      -- NULL for individual file uploads
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100) DEFAULT 'web_user',  -- Future: actual user ID

    -- Indexes
    INDEX idx_upload_batches_location (location_id),
    INDEX idx_upload_batches_created (created_at DESC),
    INDEX idx_upload_batches_status (status)
);

COMMENT ON TABLE upload_batches IS 'Tracks bulk upload operations for trail camera images';
COMMENT ON COLUMN upload_batches.upload_type IS 'Type of upload: files (individual) or zip (archive)';
COMMENT ON COLUMN upload_batches.status IS 'Upload processing status: pending, processing, completed, failed';
```

**Field Descriptions**:
- `id`: UUID primary key for batch tracking
- `location_id`: Foreign key to locations table (required - all uploads must specify location)
- `upload_type`: Discriminator for upload method ('files' vs 'zip')
- `total_files`: Total images in batch (known upfront for ZIP, counted for individual files)
- `successful_files`: Count of images successfully stored and recorded in DB
- `failed_files`: Count of images that failed validation or storage
- `zip_filename`: Original ZIP filename (NULL for individual file uploads)
- `zip_size_bytes`: ZIP archive size in bytes (NULL for individual file uploads)
- `status`: Processing state machine (pending → processing → completed/failed)
- `error_message`: Stack trace or error details if batch failed
- `created_at`: Upload initiation timestamp
- `completed_at`: Upload completion timestamp (for duration calculation)
- `created_by`: User identifier (defaults to 'web_user', future auth integration)

### Modified Table: `images`

Add foreign key to track which upload batch created each image.

```sql
ALTER TABLE images
ADD COLUMN upload_batch_id UUID REFERENCES upload_batches(id) ON DELETE SET NULL;

CREATE INDEX idx_images_upload_batch ON images(upload_batch_id);

COMMENT ON COLUMN images.upload_batch_id IS 'Links image to its originating upload batch (NULL for legacy images)';
```

**Rationale**: Optional foreign key allows:
- Batch-level queries (all images from upload XYZ)
- Upload history analysis (which batches succeeded/failed)
- Troubleshooting (identify problematic upload sources)
- Legacy compatibility (existing images have NULL batch_id)

### Existing Table: `images` (reference)

Current schema (no changes except batch_id):

```sql
CREATE TABLE images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    exif_data JSONB,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    upload_batch_id UUID REFERENCES upload_batches(id) ON DELETE SET NULL,  -- NEW COLUMN

    CONSTRAINT unique_filename_per_location UNIQUE (filename, location_id)
);
```

### Existing Table: `locations` (reference)

Current schema (no changes):

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    image_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

## Entity Relationships

```text
┌──────────────┐
│  locations   │
│ (existing)   │
└───────┬──────┘
        │ 1
        │
        │ N
┌───────┴────────────┐
│  upload_batches    │
│  (new)             │
│                    │
│ - id (PK)          │
│ - location_id (FK) │
│ - upload_type      │
│ - total_files      │
│ - status           │
│ - created_at       │
└───────┬────────────┘
        │ 1
        │
        │ N
┌───────┴────────────┐
│  images            │
│  (modified)        │
│                    │
│ - id (PK)          │
│ - filename         │
│ - location_id (FK) │
│ - upload_batch_id  │  ← NEW COLUMN
│ - timestamp        │
│ - processing_status│
└────────────────────┘
```

**Cardinality**:
- 1 Location : N Upload Batches (one location has many upload batches)
- 1 Upload Batch : N Images (one batch contains many images)
- 1 Location : N Images (existing relationship, unchanged)

## Data Validation Rules

### Upload Batch Validation

1. **Location Required**: `location_id` must reference existing location
2. **Upload Type**: Must be 'files' or 'zip' (enforced by CHECK constraint)
3. **Status Transitions**: pending → processing → completed|failed (enforced in application logic)
4. **File Counts**: `successful_files + failed_files <= total_files`
5. **ZIP Metadata**: If `upload_type='zip'`, then `zip_filename` and `zip_size_bytes` must be NOT NULL
6. **Completion Timestamp**: `completed_at` must be >= `created_at`

### Image Validation (existing + new)

1. **Filename + Location Unique**: Enforced by `unique_filename_per_location` constraint
2. **File Extension**: Validated in application (must be .jpg or .jpeg)
3. **File Size**: Validated in application (must be <= 50MB per image)
4. **Timestamp Range**: Validated in application (1990 <= year <= 2030)
5. **Batch Reference**: `upload_batch_id` can be NULL (legacy images) or valid UUID

## State Machine: Upload Batch Status

```text
[pending] ────▶ [processing] ────▶ [completed]
                      │
                      │ (on error)
                      ▼
                  [failed]
```

**State Definitions**:
- `pending`: Batch created, files not yet processed
- `processing`: Files are being extracted/validated/stored
- `completed`: All files processed (successful_files + failed_files = total_files)
- `failed`: Batch-level failure (e.g., ZIP extraction error, database connection lost)

**Transition Rules**:
1. Create batch → status='pending'
2. Start processing → status='processing'
3. All files processed successfully → status='completed', failed_files=0
4. Some files processed → status='completed', failed_files>0
5. Batch-level error → status='failed', error_message populated

## Query Patterns

### 1. Upload History (Latest 10 Batches)

```sql
SELECT
    ub.id,
    ub.upload_type,
    ub.total_files,
    ub.successful_files,
    ub.failed_files,
    ub.status,
    ub.created_at,
    ub.completed_at,
    l.name AS location_name,
    (ub.completed_at - ub.created_at) AS duration
FROM upload_batches ub
JOIN locations l ON ub.location_id = l.id
ORDER BY ub.created_at DESC
LIMIT 10;
```

**Performance**: Index on `created_at DESC` ensures fast ORDER BY, <10ms query time

### 2. Batch Detail with Images

```sql
SELECT
    i.id,
    i.filename,
    i.timestamp,
    i.processing_status,
    i.exif_data->>'DateTimeOriginal' AS exif_timestamp
FROM images i
WHERE i.upload_batch_id = :batch_id
ORDER BY i.timestamp ASC;
```

**Performance**: Index on `upload_batch_id` ensures fast filtering, <50ms for 1000 images

### 3. Failed Uploads in Last 24 Hours

```sql
SELECT
    ub.id,
    ub.zip_filename,
    ub.error_message,
    ub.created_at,
    l.name AS location_name
FROM upload_batches ub
JOIN locations l ON ub.location_id = l.id
WHERE ub.status = 'failed'
  AND ub.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY ub.created_at DESC;
```

**Performance**: Composite index on `(status, created_at)` for efficient filtering

### 4. Location Upload Statistics

```sql
SELECT
    l.name AS location_name,
    COUNT(ub.id) AS total_uploads,
    SUM(ub.total_files) AS total_images,
    SUM(ub.successful_files) AS successful_images,
    SUM(ub.failed_files) AS failed_images,
    ROUND(100.0 * SUM(ub.successful_files) / NULLIF(SUM(ub.total_files), 0), 2) AS success_rate
FROM locations l
LEFT JOIN upload_batches ub ON l.id = ub.location_id
WHERE ub.created_at >= NOW() - INTERVAL '30 days'
GROUP BY l.id, l.name
ORDER BY total_uploads DESC;
```

**Performance**: Aggregation over indexed columns, <100ms for 7 locations

## Migration Script

```sql
-- migrations/011_add_upload_batches.sql

BEGIN;

-- Create upload_batches table
CREATE TABLE upload_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    upload_type VARCHAR(10) NOT NULL CHECK (upload_type IN ('files', 'zip')),
    total_files INTEGER NOT NULL DEFAULT 0,
    successful_files INTEGER NOT NULL DEFAULT 0,
    failed_files INTEGER NOT NULL DEFAULT 0,
    zip_filename VARCHAR(255),
    zip_size_bytes BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100) DEFAULT 'web_user'
);

-- Create indexes for upload_batches
CREATE INDEX idx_upload_batches_location ON upload_batches(location_id);
CREATE INDEX idx_upload_batches_created ON upload_batches(created_at DESC);
CREATE INDEX idx_upload_batches_status ON upload_batches(status);

-- Add comments
COMMENT ON TABLE upload_batches IS 'Tracks bulk upload operations for trail camera images';
COMMENT ON COLUMN upload_batches.upload_type IS 'Type of upload: files (individual) or zip (archive)';
COMMENT ON COLUMN upload_batches.status IS 'Upload processing status: pending, processing, completed, failed';

-- Add upload_batch_id to images table
ALTER TABLE images
ADD COLUMN upload_batch_id UUID REFERENCES upload_batches(id) ON DELETE SET NULL;

-- Create index for upload_batch_id
CREATE INDEX idx_images_upload_batch ON images(upload_batch_id);

-- Add comment
COMMENT ON COLUMN images.upload_batch_id IS 'Links image to its originating upload batch (NULL for legacy images)';

COMMIT;
```

**Rollback Script**:

```sql
-- migrations/011_rollback_upload_batches.sql

BEGIN;

-- Remove upload_batch_id from images
DROP INDEX IF EXISTS idx_images_upload_batch;
ALTER TABLE images DROP COLUMN IF EXISTS upload_batch_id;

-- Drop upload_batches table (CASCADE removes foreign keys)
DROP TABLE IF EXISTS upload_batches CASCADE;

COMMIT;
```

## Storage Estimates

### Database Storage

**upload_batches table**:
- Row size: ~200 bytes (UUID + metadata + indexes)
- Expected volume: 10 batches/day × 365 days = 3,650 batches/year
- Storage/year: 3,650 × 200 bytes = 730KB

**images.upload_batch_id column**:
- Additional storage: 16 bytes (UUID) per image
- Expected volume: 25,000 images/year
- Storage/year: 25,000 × 16 bytes = 400KB

**Total Additional Storage**: ~1.13MB/year (negligible)

### Filesystem Storage

No change to image storage (images still stored in `/mnt/images/{location}/`)

## Data Retention

- **upload_batches**: Retain indefinitely (small table, valuable for auditing)
- **images.upload_batch_id**: Retain indefinitely (links to batch provenance)
- **Archived batches**: Option to soft-delete batches >1 year old (set status='archived')

## Security Considerations

1. **Batch Isolation**: Each batch uses isolated UUID to prevent enumeration attacks
2. **Location Validation**: Enforce that `location_id` exists before accepting upload
3. **SQL Injection**: Parameterized queries prevent injection via filename/metadata
4. **Path Traversal**: Validate filenames to prevent `../` directory traversal in ZIP extraction
5. **User Attribution**: `created_by` field ready for user authentication (future enhancement)

## Future Enhancements

1. **User Authentication**: Replace `created_by='web_user'` with actual user ID from auth system
2. **Batch Tags**: Add `tags` JSONB column for custom metadata (e.g., rut season, camera model)
3. **Batch Sharing**: Add `is_public` flag for sharing upload batches with external users
4. **Scheduled Cleanup**: Archive batches older than 1 year with status='completed' and no errors
5. **Batch Replay**: Add endpoint to re-queue failed batches for processing retry

---

**Status**: Phase 1 complete - Ready for API contract design
