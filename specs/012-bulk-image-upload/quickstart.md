# Developer Quickstart: Bulk Image Upload

**Feature**: 009-bulk-image-upload
**Date**: 2025-11-11
**Audience**: Developers implementing or testing the upload feature

## Prerequisites

- Docker and Docker Compose installed
- Backend and frontend containers running (`docker-compose up -d`)
- PostgreSQL database initialized with migrations
- At least 5GB free disk space for testing uploads

## Quick Start (5 Minutes)

### 1. Apply Database Migration

```bash
# From project root
docker-compose exec db psql -U deertrack deer_tracking -f /migrations/011_add_upload_batches.sql

# Verify tables created
docker-compose exec db psql -U deertrack deer_tracking -c "\dt upload_batches"
```

**Expected Output**:
```
                List of relations
 Schema |      Name       | Type  |   Owner
--------+-----------------+-------+-----------
 public | upload_batches  | table | deertrack
```

### 2. Create Test Location

```bash
# Create "TestLocation" if it doesn't exist
curl -X POST http://localhost:8001/api/locations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestLocation",
    "description": "Location for upload testing"
  }'
```

**Expected Response**:
```json
{
  "id": "12345678-1234-1234-1234-123456789012",
  "name": "TestLocation",
  "image_count": 0
}
```

Save the `id` value for use in upload tests.

### 3. Test Individual File Upload

```bash
# Download sample trail camera image
wget https://example.com/sample_trail_camera.jpg -O test_image.jpg

# Upload single file
curl -X POST http://localhost:8001/api/upload/files \
  -F "files=@test_image.jpg" \
  -F "location_id=12345678-1234-1234-1234-123456789012" \
  -F "process_immediately=false"
```

**Expected Response**:
```json
{
  "batch_id": "abcd1234-5678-90ab-cdef-1234567890ab",
  "total_files": 1,
  "successful_files": 1,
  "failed_files": 0,
  "status": "completed",
  "location_name": "TestLocation"
}
```

### 4. Verify Upload in Database

```bash
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT id, filename, timestamp, location_id FROM images WHERE upload_batch_id IS NOT NULL LIMIT 5;"
```

## Testing Scenarios

### Scenario 1: Upload Multiple Individual Files

```bash
# Create test images directory
mkdir test_images
cd test_images

# Generate 10 test JPG files (requires ImageMagick)
for i in {1..10}; do
  convert -size 640x480 xc:blue "test_$i.jpg"
done

# Upload all files
curl -X POST http://localhost:8001/api/upload/files \
  -F "files=@test_1.jpg" \
  -F "files=@test_2.jpg" \
  -F "files=@test_3.jpg" \
  -F "files=@test_4.jpg" \
  -F "files=@test_5.jpg" \
  -F "files=@test_6.jpg" \
  -F "files=@test_7.jpg" \
  -F "files=@test_8.jpg" \
  -F "files=@test_9.jpg" \
  -F "files=@test_10.jpg" \
  -F "location_id=12345678-1234-1234-1234-123456789012" \
  -F "process_immediately=false"
```

**Verify Success**:
```bash
# Count uploaded images
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FROM images WHERE location_id='12345678-1234-1234-1234-123456789012';"
```

### Scenario 2: Upload ZIP Archive

```bash
# Create ZIP archive from test images
zip test_images.zip test_images/*.jpg

# Upload ZIP
curl -X POST http://localhost:8001/api/upload/zip \
  -F "file=@test_images.zip" \
  -F "location_id=12345678-1234-1234-1234-123456789012" \
  -F "process_immediately=false"
```

**Expected Response**:
```json
{
  "batch_id": "xyz123-4567-89ab-cdef-0123456789ab",
  "total_files": 10,
  "successful_files": 10,
  "failed_files": 0,
  "status": "completed",
  "location_name": "TestLocation",
  "duration_seconds": 2.3
}
```

### Scenario 3: Test EXIF Timestamp Extraction

```bash
# Create image with EXIF timestamp (requires exiftool)
convert -size 640x480 xc:green exif_test.jpg
exiftool -DateTimeOriginal="2025:10:31 14:30:22" exif_test.jpg

# Upload and verify timestamp
curl -X POST http://localhost:8001/api/upload/files \
  -F "files=@exif_test.jpg" \
  -F "location_id=12345678-1234-1234-1234-123456789012"

# Check extracted timestamp
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT filename, timestamp FROM images WHERE filename='exif_test.jpg';"
```

**Expected Output**:
```
    filename    |      timestamp
----------------+---------------------
 exif_test.jpg  | 2025-10-31 14:30:22+00
```

### Scenario 4: Test Duplicate Detection

```bash
# Upload same file twice
curl -X POST http://localhost:8001/api/upload/files \
  -F "files=@test_1.jpg" \
  -F "location_id=12345678-1234-1234-1234-123456789012"

curl -X POST http://localhost:8001/api/upload/files \
  -F "files=@test_1.jpg" \
  -F "location_id=12345678-1234-1234-1234-123456789012"

# Verify filename was renamed
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT filename FROM images WHERE filename LIKE 'test_1%';"
```

**Expected Output**:
```
  filename
-------------
 test_1.jpg
 test_1_1.jpg
```

### Scenario 5: Test Error Handling (Corrupted ZIP)

```bash
# Create fake corrupted ZIP
echo "This is not a ZIP file" > corrupted.zip

# Attempt upload
curl -X POST http://localhost:8001/api/upload/zip \
  -F "file=@corrupted.zip" \
  -F "location_id=12345678-1234-1234-1234-123456789012"
```

**Expected Response** (HTTP 400):
```json
{
  "detail": "ZIP file is corrupted or unreadable",
  "error_code": "INVALID_ZIP"
}
```

## Frontend Testing (React)

### 1. Start Frontend Development Server

```bash
cd frontend
npm start
# Opens http://localhost:3000
```

### 2. Navigate to Upload Page

- Open browser to `http://localhost:3000/upload`
- You should see:
  - Location dropdown (populated from `/api/locations`)
  - Drag-drop zone with file picker
  - "Process Immediately" checkbox
  - Upload button (disabled until files selected)

### 3. Test Drag-and-Drop

1. Drag `test_images/` folder onto drop zone
2. Verify files appear in file list (10 files)
3. Select location from dropdown
4. Click "Upload" button
5. Verify progress bar appears (0% → 100%)
6. Verify success message with batch statistics

### 4. Test ZIP Upload

1. Use file picker to select `test_images.zip`
2. Verify ZIP filename appears in file list
3. Select location
4. Click "Upload"
5. Verify progress updates during extraction
6. Verify completion summary shows 10 images extracted

## Performance Testing

### Test Large ZIP Upload (1000 Images, 500MB)

```bash
# Generate 1000 test images (requires ~500MB disk space)
mkdir large_test
cd large_test
for i in {1..1000}; do
  convert -size 640x480 xc:blue "img_$i.jpg"
done

# Create ZIP
zip -r large_test.zip *.jpg

# Time the upload
time curl -X POST http://localhost:8001/api/upload/zip \
  -F "file=@large_test.zip" \
  -F "location_id=12345678-1234-1234-1234-123456789012"
```

**Expected Performance**:
- Upload time: <2 minutes (LAN connection)
- Extraction time: <1 minute
- Database insert: <5 seconds (bulk insert)
- Total: <3 minutes end-to-end

**Monitor Progress**:
```bash
# Watch database inserts in real-time
watch -n 1 'docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FROM images WHERE upload_batch_id='\''YOUR_BATCH_ID'\'';"'
```

## Debugging

### Enable Debug Logging

```bash
# Backend (add to .env)
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart backend

# Watch logs
docker-compose logs -f backend | grep -i upload
```

### Check Upload Batch Status

```bash
# List recent batches
curl http://localhost:8001/api/upload/batches?page_size=10

# Get specific batch detail
curl http://localhost:8001/api/upload/batches/{batch_id}
```

### Inspect Temporary Upload Directory

```bash
# Check for leftover temp files
docker-compose exec backend ls -lah /tmp/upload_*

# Clean up if needed
docker-compose exec backend rm -rf /tmp/upload_*
```

### Database Queries

```sql
-- Failed uploads in last hour
SELECT * FROM upload_batches
WHERE status='failed' AND created_at >= NOW() - INTERVAL '1 hour';

-- Upload statistics by location
SELECT l.name, COUNT(ub.id) AS uploads, SUM(ub.total_files) AS total_images
FROM locations l
LEFT JOIN upload_batches ub ON l.id = ub.location_id
GROUP BY l.name
ORDER BY uploads DESC;

-- Images without batch_id (legacy images)
SELECT COUNT(*) FROM images WHERE upload_batch_id IS NULL;
```

## Troubleshooting

### Issue: "413 Request Entity Too Large"

**Cause**: Nginx client_max_body_size limit exceeded

**Fix**:
```bash
# Update nginx.conf
client_max_body_size 2048M;

# Restart nginx
docker-compose restart nginx
```

### Issue: "OSError: [Errno 28] No space left on device"

**Cause**: Disk space exhausted during upload/extraction

**Fix**:
```bash
# Check disk usage
df -h /mnt/images

# Free up space or expand volume
```

### Issue: "EXIF timestamp extraction returns None"

**Cause**: Image has no EXIF data or uses non-standard tags

**Debugging**:
```bash
# Check EXIF tags in image
docker-compose exec backend python3 -c "
from PIL import Image
img = Image.open('/path/to/image.jpg')
print(img._getexif())
"
```

**Expected Behavior**: Falls back to filename parsing or current UTC time

### Issue: "Upload completes but images not queued for processing"

**Cause**: Celery worker not running or process_immediately=false

**Fix**:
```bash
# Check worker status
docker-compose ps worker

# Restart worker
docker-compose restart worker

# Verify queue
docker-compose exec redis redis-cli LLEN celery
```

## Cleanup

### Remove Test Data

```bash
# Delete test upload batches
docker-compose exec db psql -U deertrack deer_tracking -c \
  "DELETE FROM upload_batches WHERE location_id IN (
     SELECT id FROM locations WHERE name='TestLocation'
   );"

# Delete test images
docker-compose exec db psql -U deertrack deer_tracking -c \
  "DELETE FROM images WHERE location_id IN (
     SELECT id FROM locations WHERE name='TestLocation'
   );"

# Delete test location
docker-compose exec db psql -U deertrack deer_tracking -c \
  "DELETE FROM locations WHERE name='TestLocation';"
```

### Remove Test Files

```bash
# Remove test images and ZIPs
rm -rf test_images/ test_images.zip large_test/ large_test.zip
rm -f test_image.jpg exif_test.jpg corrupted.zip
```

## Next Steps

1. Run full test suite: `docker-compose exec backend pytest tests/api/test_upload.py -v`
2. Test with real trail camera images from `/mnt/i/Hopkins_Ranch_Trail_Cam_Dumps/`
3. Implement frontend Upload page with drag-drop UI
4. Add upload progress WebSocket for real-time updates
5. Test with 10,000-image batch (production scenario)

## Reference Links

- [API Contract](./contracts/upload-api.yaml)
- [Data Model](./data-model.md)
- [Feature Spec](./spec.md)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [react-dropzone Docs](https://react-dropzone.js.org/)
