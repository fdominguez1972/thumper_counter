# Feature Specification: Bulk Image Upload System

**Feature Branch**: `009-bulk-image-upload`
**Created**: 2025-11-11
**Status**: Draft
**Input**: User description: "Create a bulk image upload system that allows uploading trail camera images (individual files or ZIP archives) through a web interface with automatic location assignment, EXIF timestamp extraction, and ML pipeline integration for detection and re-identification"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Individual Trail Camera Images (Priority: P1)

As a ranch manager, I want to upload trail camera images through a web interface so that I can add new photos to the tracking system without needing technical assistance.

**Why this priority**: This is the core MVP functionality that eliminates manual import processes. Without this, users cannot add new images to the system independently, requiring developer intervention for every upload batch.

**Independent Test**: Can be fully tested by navigating to the Upload page, selecting image files from the file picker, choosing a location from the dropdown, and clicking upload. Delivers immediate value by allowing self-service image uploads.

**Acceptance Scenarios**:

1. **Given** the user is on the Upload page, **When** they select 5 JPG files via file picker and choose "Sanctuary" location, **Then** all 5 images are uploaded successfully and appear in the image browser
2. **Given** the user has selected 10 images, **When** they click upload without selecting a location, **Then** the system displays a validation error requiring location selection
3. **Given** the user uploads an image, **When** the upload completes, **Then** the system shows upload progress (0-100%) and success confirmation with image count
4. **Given** the user uploads trail camera images, **When** processing completes, **Then** images are stored with location assignment and visible in the Images page

---

### User Story 2 - Upload ZIP Archives Containing Multiple Images (Priority: P2)

As a ranch manager, I want to upload ZIP archives containing hundreds of trail camera images so that I can efficiently transfer large batches without selecting individual files.

**Why this priority**: This is critical for operational efficiency. Ranch managers collect thousands of images per camera dump (8,000-10,000 per location), making individual file selection impractical. ZIP upload reduces upload time from hours to minutes.

**Independent Test**: Can be tested by creating a ZIP archive with 100 test images, uploading it via the web interface, and verifying all images are extracted and processed. Delivers value by handling realistic bulk upload volumes.

**Acceptance Scenarios**:

1. **Given** the user has a ZIP file with 1,000 trail camera images, **When** they upload the ZIP and select location "Hayfield", **Then** all 1,000 images are extracted and stored with the specified location
2. **Given** the user uploads a ZIP archive, **When** extraction begins, **Then** the system shows real-time progress (files extracted / total files)
3. **Given** a ZIP file contains both JPG images and other file types (TXT, MP4), **When** the ZIP is uploaded, **Then** only JPG/JPEG files are imported and other files are ignored
4. **Given** a ZIP file is 500MB in size, **When** the user uploads it, **Then** the system processes it without timeout or memory errors

---

### User Story 3 - Automatic Timestamp Extraction from Images (Priority: P3)

As a wildlife researcher, I want the system to automatically extract timestamps from trail camera images so that sighting data reflects actual capture time rather than upload time.

**Why this priority**: Accurate timestamps are essential for wildlife behavior analysis (rut season patterns, nocturnal activity, etc.). This ensures data integrity without manual timestamp entry, which is error-prone at scale.

**Independent Test**: Can be tested by uploading images with EXIF timestamps and verifying the database records match the camera capture time, not upload time. Delivers scientific accuracy for research applications.

**Acceptance Scenarios**:

1. **Given** an image has EXIF DateTimeOriginal metadata, **When** the image is uploaded, **Then** the system stores the timestamp from EXIF (not current time)
2. **Given** an image filename is "Sanctuary_20251031_143022_001.jpg", **When** EXIF data is missing, **Then** the system extracts timestamp from filename pattern (2025-10-31 14:30:22)
3. **Given** an image has neither EXIF nor parseable filename, **When** the image is uploaded, **Then** the system uses current UTC time and logs a warning
4. **Given** batch upload of 500 images, **When** processing completes, **Then** 95%+ of images have accurate EXIF-based timestamps

---

### User Story 4 - Automatic Processing Queue Integration (Priority: P4)

As a ranch manager, I want uploaded images to automatically enter the detection and re-identification pipeline so that new deer sightings are identified without manual queuing.

**Why this priority**: Completes the end-to-end automation. Without this, images sit unprocessed until manually queued, defeating the purpose of self-service upload. This enables "upload and forget" workflow.

**Independent Test**: Can be tested by uploading 10 images, waiting 2 minutes, and verifying that detections appear with deer classifications and profiles assigned. Delivers complete automation from upload to identified sightings.

**Acceptance Scenarios**:

1. **Given** the user uploads 20 images, **When** upload completes, **Then** all 20 images are automatically queued for detection processing
2. **Given** images are queued for processing, **When** the detection worker is running, **Then** images progress from "pending" to "processing" to "completed" status
3. **Given** a user uploads images during peak hours, **When** the queue has 5,000 images already, **Then** new images are added to queue without blocking upload
4. **Given** detection completes on an image, **When** deer are detected, **Then** the re-identification task is automatically queued for each detection

---

### User Story 5 - Drag-and-Drop Upload Interface (Priority: P5)

As a ranch manager, I want to drag image files directly onto the upload page so that I can quickly add images without navigating file pickers.

**Why this priority**: Improves user experience but not essential for MVP functionality. Nice-to-have that makes frequent uploads more convenient.

**Independent Test**: Can be tested by dragging a folder of images from desktop onto the upload page and verifying files are added to upload queue. Delivers improved UX for power users.

**Acceptance Scenarios**:

1. **Given** the user has the Upload page open, **When** they drag 50 JPG files onto the drop zone, **Then** all files are added to the upload queue
2. **Given** the user drags files onto the page, **When** files include non-image types, **Then** only JPG/JPEG files are accepted and others are rejected with a message
3. **Given** the drag-drop zone is visible, **When** the user hovers files over it, **Then** the zone highlights to indicate drop target

---

### Edge Cases

- What happens when a ZIP archive exceeds maximum upload size (e.g., 2GB)?
  - System should reject uploads above size limit and display error message with maximum allowed size

- How does the system handle duplicate images (same filename, same location)?
  - System should detect duplicates by filename+location and either skip or append unique identifier to avoid overwrites

- What happens when EXIF timestamp is in the future or clearly invalid (year 1970)?
  - System should validate timestamp ranges (1990-2030) and fall back to filename or current time if invalid

- How does the system handle corrupted or unreadable image files?
  - System should validate image integrity, skip corrupted files, and report failures in upload summary

- What happens when the ML processing queue is offline during upload?
  - Images should still be uploaded and stored successfully; processing queue can be triggered later without re-upload

- How does the system handle simultaneous uploads from multiple users?
  - System should handle concurrent uploads independently, queuing all images without conflicts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a web-based Upload page accessible from the main navigation menu
- **FR-002**: System MUST accept individual image files in JPG and JPEG formats via file picker
- **FR-003**: System MUST accept ZIP archives containing multiple image files
- **FR-004**: System MUST require users to select a location (camera site) for uploaded images before upload can proceed
- **FR-005**: System MUST extract all JPG/JPEG files from uploaded ZIP archives and ignore non-image files
- **FR-006**: System MUST display real-time upload progress showing percentage complete and file counts
- **FR-007**: System MUST extract EXIF DateTimeOriginal metadata from images when available
- **FR-008**: System MUST parse timestamps from filenames matching pattern "{Location}_{YYYYMMDD}_{HHMMSS}_{seq}.jpg" when EXIF is unavailable
- **FR-009**: System MUST fall back to current UTC timestamp when both EXIF and filename parsing fail
- **FR-010**: System MUST store uploaded images in location-specific directories (e.g., /mnt/images/Sanctuary/)
- **FR-011**: System MUST create database records for each uploaded image with filename, path, timestamp, and location
- **FR-012**: System MUST automatically queue uploaded images for detection processing when "Process Immediately" option is enabled
- **FR-013**: System MUST support upload sizes up to 2GB for individual files or ZIP archives
- **FR-014**: System MUST validate image file integrity before storing to prevent corrupted files
- **FR-015**: System MUST detect duplicate filenames within the same location and handle appropriately (skip or rename)
- **FR-016**: System MUST display upload summary showing: total files uploaded, successful count, failed count, and error details
- **FR-017**: System MUST support drag-and-drop file upload in addition to file picker
- **FR-018**: System MUST validate timestamp ranges (1990-2030) and flag invalid dates
- **FR-019**: System MUST allow users to view upload history showing recent batches with counts and timestamps
- **FR-020**: System MUST integrate with existing location management to populate location dropdown

### Key Entities

- **Upload Batch**: Represents a single upload operation containing one or more images
  - Attributes: batch ID, upload timestamp, user identifier, total file count, success count, failure count, location assignment
  - Relationships: Contains multiple Image records

- **Image Record**: Represents a single trail camera photograph (already exists in system)
  - Attributes: filename, file path, capture timestamp, location, EXIF data, processing status, upload batch ID
  - Relationships: Belongs to one Location, belongs to one Upload Batch, has many Detections

- **Location**: Camera site where images were captured (already exists in system)
  - Attributes: location name, description, coordinates, image count
  - Relationships: Has many Images

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload 100 individual images in under 5 minutes without errors
- **SC-002**: Users can upload a 500MB ZIP archive containing 1,000 images and all images are successfully extracted and stored
- **SC-003**: System correctly extracts EXIF timestamps from 95% of trail camera images (based on standard trail camera EXIF formats)
- **SC-004**: System processes filename-based timestamps with 100% accuracy for standard naming pattern
- **SC-005**: Upload progress indicator updates at least every 5 seconds during active upload
- **SC-006**: System handles uploads of 10,000 images without memory overflow or timeout errors
- **SC-007**: Uploaded images appear in the Images browser within 30 seconds of upload completion
- **SC-008**: Reduce manual image import requests to zero (users can self-serve all uploads)
- **SC-009**: Detection processing automatically begins within 60 seconds of upload completion when "Process Immediately" is enabled
- **SC-010**: Upload interface is accessible and functional on desktop browsers (Chrome, Firefox, Safari, Edge)
- **SC-011**: System correctly handles duplicate filenames without data loss or silent failures
- **SC-012**: Upload error messages are clear and actionable (e.g., "File exceeds 2GB limit" instead of generic "Upload failed")

## Assumptions *(optional)*

- Users have reliable internet connection capable of uploading large files (500MB+)
- Trail camera images follow standard JPEG format with typical EXIF metadata structure
- User authentication and authorization are handled by existing system (no new auth requirements)
- File storage has sufficient capacity for ongoing image uploads (currently 40,000+ images, expecting 25,000+ new images)
- Backend API can handle concurrent uploads from multiple users (load testing to be validated)
- ZIP archives are unencrypted and standard format (ZIP, not RAR/7Z/other formats)

## Out of Scope *(optional)*

- Video upload support (MP4, AVI, etc.) - trail cameras capture video but this feature focuses on still images only
- Image editing or cropping before upload - users upload raw camera captures without modification
- Manual timestamp override - system uses automatic extraction only, no user editing of timestamps
- Multi-user collaboration features (shared uploads, comments) - single-user upload workflow
- Mobile app upload - web browser interface only
- Cloud storage integration (Google Drive, Dropbox) - local file upload only
- Automatic location detection from GPS EXIF tags - user must manually select location
- Image quality validation or filtering (blurry images, night shots) - all valid JPEGs accepted
- Bulk delete or edit of uploaded images - upload-only interface, management via Images page
- Upload scheduling or automation - on-demand uploads only

## Dependencies *(optional)*

- Existing location management system must provide list of valid camera sites for dropdown
- Image storage file system must be mounted and accessible to backend with write permissions
- Database must support bulk insert operations for efficient batch uploads
- Celery task queue must be running to accept processing jobs for uploaded images
- EXIF parsing library must support standard trail camera metadata formats
- Existing detection pipeline (YOLOv8) must be operational to process uploaded images

---

## Implementation Notes - Automated Queue Management

### Problem Statement

During initial implementation (Nov 11, 2025), a critical issue was discovered: images imported into the database were not automatically queued for ML processing. This resulted in 24,188 images sitting in "pending" status indefinitely, despite the worker being operational. Manual API calls were required to queue batches, defeating the automation goal.

### Root Cause

The image import process (via scripts/register_copied_images.py) creates database records with `processing_status='pending'` but does not trigger the Celery task queue. The ML worker only processes images that are explicitly queued via the `/api/processing/batch` endpoint.

### Solution: Continuous Queue Monitor

Implemented an automatic queue monitoring script (`scripts/continuous_queue.sh`) that:

1. **Monitors Queue Status**: Polls `/api/processing/status` every 60 seconds
2. **Detects Idle State**: Identifies when pending images exist but processing queue is empty (processing=0)
3. **Auto-Queues Batches**: Automatically queues 10,000 images when idle condition detected
4. **Continuous Operation**: Runs as background daemon until all images processed

**Script Location**: `scripts/continuous_queue.sh`

**Usage**:
```bash
# Start in background
nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &

# Monitor progress
tail -f queue_monitor.log
```

**Key Parameters**:
- `CHECK_INTERVAL`: 60 seconds (configurable)
- `BATCH_SIZE`: 10,000 images (API maximum)
- `API_URL`: http://localhost:8001

### Bulk Import Workflow (Implemented)

For large-scale imports (23,934+ images), the following workflow is now documented:

1. **File Copy**: Use `scripts/copy_and_queue_images.sh` to rsync images from source to target storage
   - Source: `/mnt/i/Hopkins_Ranch_Trail_Cam_Dumps/{location}/`
   - Target: `/mnt/i/Hopkins_Ranch_Trail_Cam_Pics/{location}/`
   - Preserves timestamps with `rsync -av`

2. **Database Registration**: Use `scripts/register_copied_images.py` to create database records
   - Extracts EXIF timestamps (3-level fallback: EXIF → filename → current UTC)
   - Detects duplicates by filename+location
   - Batch commits every 100 images for performance
   - Example: Registered 23,934 images in ~5 minutes with 100% EXIF timestamp success

3. **Automatic Queueing**: Start continuous queue monitor
   - Detects 24,188 pending images with empty queue
   - Auto-queues 10,000 images immediately
   - Continues monitoring and queuing until all processed

4. **ML Processing**: Worker processes queued images
   - Concurrency: 32 threads (optimal for RTX 4080 Super)
   - Throughput: 840 images/minute sustained
   - Pipeline: Detection (YOLOv8) → Classification → Re-identification (ResNet50)

### Lessons Learned

**Issue**: Images stuck in pending status for 36+ hours after import
**Cause**: No automatic mechanism to queue pending images
**Solution**: Continuous queue monitor script
**Prevention**: Add automatic queuing to image import API endpoints (Future enhancement)

**Recommendation**: Update Feature 009 implementation to include automatic queueing in the upload API endpoint itself, eliminating need for external monitoring script.
- Re-identification pipeline (ResNet50) must be operational for deer matching

## Constraints *(optional)*

- Maximum file size: 2GB per upload (individual file or ZIP archive)
- Supported formats: JPG and JPEG only (no PNG, TIFF, RAW, etc.)
- Upload interface must work without browser plugins or extensions (pure web technologies)
- Processing queue integration must not block upload completion (asynchronous processing)
- File storage must use existing directory structure: /mnt/images/{location_name}/
- Upload feature must not disrupt ongoing detection processing of existing images
- EXIF parsing must not modify original image files (read-only operations)

## Open Questions *(optional)*

None at this time. All critical decisions have been made with reasonable defaults documented in Assumptions section.
