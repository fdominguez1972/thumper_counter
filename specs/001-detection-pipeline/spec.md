# Feature Specification: Detection Pipeline Integration

**Feature Branch**: `001-detection-pipeline`
**Created**: 2025-11-05
**Status**: Draft
**Input**: Sprint 2 ML Integration - Integrate YOLOv8 detection with database and batch processing

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process Uploaded Images Through Detection (Priority: P1)

As a wildlife researcher, I need uploaded images to be automatically processed through the YOLOv8 deer detection model so that I can identify which images contain deer without manual review.

**Why this priority**: This is the core ML pipeline functionality that delivers the primary value proposition - automated deer detection. Without this, the system is just a file storage service.

**Independent Test**: Upload a single image via API with `process_immediately=true` flag. Verify that Detection records are created in the database with bounding boxes and confidence scores. Can be tested end-to-end without requiring batch processing or monitoring.

**Acceptance Scenarios**:

1. **Given** an image with one deer is uploaded via POST /api/images with `process_immediately=true`, **When** the processing completes, **Then** exactly one Detection record exists with bbox coordinates, confidence > 0.5, and class_id=0 (deer)
2. **Given** an image with no deer is uploaded and processed, **When** processing completes, **Then** zero Detection records are created and image status is "completed"
3. **Given** an image upload without `process_immediately` flag, **When** image is saved, **Then** processing_status is "pending" and no detection task is queued

---

### User Story 2 - Batch Process Existing Images (Priority: P2)

As a wildlife researcher with 35,000 existing images, I need to trigger batch processing of all pending images so that I can analyze my historical trail camera data.

**Why this priority**: Enables processing of the large existing dataset. Depends on US1 detection working but adds batch orchestration capabilities.

**Independent Test**: Call POST /api/processing/batch with image_ids for 100 images. Verify all 100 images transition from "pending" to "processing" to "completed" and have Detection records created. Can be tested independently once US1 detection logic works.

**Acceptance Scenarios**:

1. **Given** 100 images with status "pending", **When** POST /api/processing/batch is called with those image_ids, **Then** all 100 images are queued as Celery tasks and processing_status updates to "processing"
2. **Given** a batch of 32 images being processed, **When** GPU processes them, **Then** detections are written to database and image statuses update to "completed" within 5 seconds
3. **Given** one image fails during batch processing, **When** error occurs, **Then** that image status is "failed" with error_message populated, but other images in batch continue processing

---

### User Story 3 - Monitor Processing Progress (Priority: P3)

As a wildlife researcher, I need to monitor the progress of batch processing jobs so that I can estimate completion time and identify stuck jobs.

**Why this priority**: Operational visibility for long-running batch jobs. Nice-to-have for user experience but not required for core functionality.

**Independent Test**: Start batch processing of 1000 images. Call GET /api/processing/status endpoint. Verify response shows total images, completed count, processing count, failed count, and estimated time remaining. Can be tested independently once US2 batch processing exists.

**Acceptance Scenarios**:

1. **Given** 1000 images in "processing" status, **When** GET /api/processing/status is called, **Then** response includes counts by status (pending/processing/completed/failed) and processing rate (images/second)
2. **Given** no images are being processed, **When** GET /api/processing/status is called, **Then** response shows all zero counts and "idle" state
3. **Given** batch processing has been running for 60 seconds, **When** status is requested, **Then** response includes estimated time remaining based on current processing rate

---

### Edge Cases

- What happens when YOLOv8 model file is missing or corrupted?
- How does system handle images with corrupted data that PIL cannot read?
- What happens when GPU runs out of memory during batch processing?
- What happens when Redis connection fails during task queueing? [OUT OF SCOPE: Celery connection retry handles this automatically; manual restart required for persistent failures]
- How does system handle extremely large images (>50MB)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load YOLOv8 model from `src/models/yolov8n_deer.pt` on worker startup; worker MUST fail to start with descriptive error if model cannot be loaded
- **FR-002**: System MUST accept single image processing via `process_immediately=true` flag in upload endpoint
- **FR-003**: System MUST create Detection database records with bbox (x1,y1,x2,y2), confidence, and class_id for each detected deer
- **FR-004**: System MUST update Image.processing_status through state transitions: pending -> processing -> completed/failed
- **FR-005**: System MUST provide batch processing endpoint accepting list of image_ids
- **FR-006**: System MUST process images in batches of 32 (configurable via BATCH_SIZE env var)
- **FR-007**: System MUST provide processing status endpoint showing counts by status and processing rate
- **FR-008**: System MUST handle detection failures gracefully without crashing worker
- **FR-009**: System MUST store error messages in Image.error_message field when processing fails
- **FR-010**: System MUST use Celery task queue with Redis backend for async processing
- **FR-011**: System MUST validate YOLOv8 model file exists at startup and fail with descriptive error if missing or corrupted
- **FR-012**: System MUST reject image uploads larger than 50MB with HTTP 413 error

### Non-Functional Requirements

- **NFR-001**: Detection processing MUST achieve minimum 70 images/second throughput on RTX 4080 Super
- **NFR-002**: API response time for status endpoint MUST be under 200ms
- **NFR-003**: Worker MUST recover from GPU OOM errors without requiring container restart by dynamically reducing batch size (32 -> 16 -> 8 -> 1) and retrying failed batch
- **NFR-004**: Database write operations MUST use connection pooling to handle concurrent batch writes
- **NFR-005**: System MUST log all processing errors with image_id and error details for debugging

### Key Entities

- **Image**: Existing entity - added fields: processing_status (enum: pending/processing/completed/failed), error_message (text, nullable)
- **Detection**: Existing entity - populated by detection pipeline with bbox coordinates (x1, y1, x2, y2), confidence (float 0-1), class_id (integer, 0=deer)
- **ProcessingJob**: Virtual entity (not stored in database) - represented by Celery task group ID returned from batch endpoint; tracks batch processing state across multiple images

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Single image upload with immediate processing completes within 3 seconds from upload to detection records created
- **SC-002**: Batch processing achieves minimum 70 images/second sustained throughput for batches of 100+ images
- **SC-003**: Detection accuracy matches YOLOv8n baseline (>80% precision at 0.5 IoU on deer class) [POST-DEPLOYMENT: Validated against manually labeled test set after Sprint 2]
- **SC-004**: System processes all 35,234 existing images without worker crashes or database errors
- **SC-005**: Processing status endpoint response time remains under 200ms even with 10,000 images in "processing" state
- **SC-006**: Error rate for valid JPEG images is under 1% (excluding corrupted files)
