# Implementation Plan: Detection Pipeline Integration

**Branch**: `001-detection-pipeline` | **Date**: 2025-11-05 | **Spec**: [spec.md](./spec.md)

## Summary

Integrate YOLOv8 deer detection model with the existing API and database infrastructure to enable both on-demand single image processing and batch processing of large image datasets. This feature builds on completed Sprint 1 work (database models, location API, image upload API) and implements the core ML pipeline capability.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**:
- FastAPI 0.104.1 (API framework)
- Celery 5.3.4 (async task queue)
- Redis 5.0.1 (Celery broker/backend)
- ultralytics 8.0.200 (YOLOv8)
- torch 2.1.0+cu121 (CUDA 12.1)
- Pillow 12.0.0 (image processing)
- SQLAlchemy 2.0.23 (ORM)

**Storage**:
- PostgreSQL 15 (structured data: images, detections, locations, deer)
- Filesystem /mnt/images/ (original images and crops)
- Redis (Celery task queue and results)

**Testing**: pytest (not included in this feature - future work)

**Target Platform**: Linux Docker containers on Windows 11 WSL2 with NVIDIA GPU passthrough

**Project Type**: Web application (FastAPI backend + Celery worker)

**Performance Goals**:
- 70+ images/second sustained throughput
- <3 second single image end-to-end latency
- <200ms API status endpoint response time

**Constraints**:
- GPU: RTX 4080 Super (16GB VRAM) - batch size limited to 32 images
- Database connection pool: max 20 connections
- Celery concurrency: 4 workers
- Max image size: 50MB

**Scale/Scope**:
- Initial dataset: 35,234 images
- Expected processing: 100-1000 images/day ongoing
- Detection records: ~50,000 expected (1.4 deer/image average)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Status**: Project constitution template exists but is not fully populated. No MUST principles defined yet. This feature proceeds with industry-standard practices:
- Error handling with proper logging
- Database transactions for data integrity
- Graceful degradation on failures
- Performance monitoring and metrics

## Project Structure

### Documentation (this feature)

```text
specs/001-detection-pipeline/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file - implementation plan
└── tasks.md             # Task breakdown (completed)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── app/
│   │   └── main.py                  # FastAPI app - add processing endpoints
│   ├── api/
│   │   ├── images.py                # EXISTING - modify to add process_immediately
│   │   └── processing.py            # NEW - batch and status endpoints
│   ├── models/
│   │   ├── image.py                 # EXISTING - add processing_status, error_message
│   │   └── detection.py             # EXISTING - already defined, will be populated
│   ├── schemas/
│   │   ├── image.py                 # EXISTING - add processing fields
│   │   ├── detection.py             # EXISTING - response schemas
│   │   └── processing.py            # NEW - batch request/response schemas
│   └── core/
│       └── database.py              # EXISTING - connection pooling already configured

worker/
├── src/
│   ├── celery_app.py                # EXISTING - Celery configuration
│   ├── tasks/
│   │   ├── detection.py             # EXISTING - basic structure, needs integration
│   │   └── process_images.py        # EXISTING - modify for batch processing
│   └── models/
│       └── yolov8_detector.py       # EXISTING - YOLOv8 loading, needs GPU optimization

models/
└── yolov8n_deer.pt                  # EXISTING - 22MB model file copied from original project

tests/                                # Not included in this feature
```

**Structure Decision**: Using existing web application structure with backend (FastAPI) and worker (Celery) directories. All foundational code from Sprint 1 is in place. This feature adds processing logic and new API endpoints.

## Existing Infrastructure (Sprint 1 Completed)

### Database Models (100% Complete)
- **Location**: id, name, description, coordinates, image_count, created_at, updated_at
- **Image**: id, filename, path, timestamp, location_id, exif_data, created_at, updated_at
  - **NEEDS**: processing_status enum field, error_message text field
- **Detection**: id, image_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, confidence, class_id, deer_id, created_at
  - **NEEDS**: Population from detection pipeline
- **Deer**: id, name, sex, species, first_seen, last_seen, sighting_count, feature_vector, created_at, updated_at

### API Endpoints (40% Complete)
- POST /api/locations - Create location ✅
- GET /api/locations - List locations ✅
- POST /api/images - Upload images with EXIF extraction ✅
  - **NEEDS**: process_immediately parameter
- GET /api/images - List with filters ✅
- GET /health - Health check ✅

### Worker Infrastructure (30% Complete)
- Celery app configured with Redis ✅
- YOLOv8 model loading code ✅
- Basic detection task structure ✅
  - **NEEDS**: Database integration, batch processing, error handling

### Docker Environment (100% Complete)
- backend container with Pillow installed ✅
- worker container with CUDA support ✅
- PostgreSQL 15 ✅
- Redis ✅
- All services operational ✅

## Implementation Phases

### Phase 0: Foundation Updates (Prerequisites)

**Purpose**: Modify existing models and schemas to support processing status tracking

**Deliverables**:
- Updated Image model with processing_status enum and error_message field
- Database migration script (manual SQL for now)
- Updated Pydantic schemas for image responses

**Estimated Effort**: 1 hour

### Phase 1: User Story 1 - Single Image Detection (P1) 🎯 MVP

**Purpose**: Process uploaded images through YOLOv8 and store detections

**Deliverables**:
- Modified POST /api/images to accept process_immediately parameter
- Enhanced detection.py Celery task with database integration
- Detection record creation with bbox, confidence, class_id
- Image status transitions: pending -> processing -> completed/failed
- Error handling and logging

**Files Modified**:
- src/backend/api/images.py (add process_immediately logic)
- src/worker/tasks/detection.py (add database writes)
- src/backend/schemas/image.py (add processing fields)

**Success Criteria**:
- Upload image with process_immediately=true creates Detection records within 3 seconds
- Image processing_status updates correctly
- Errors populate error_message field and set status to "failed"

**Estimated Effort**: 3 hours

### Phase 2: User Story 2 - Batch Processing (P2)

**Purpose**: Enable processing of large image batches efficiently

**Deliverables**:
- POST /api/processing/batch endpoint accepting image_id list
- Batch processing Celery task with chunking (batch_size=32)
- Celery group/chain for parallel batch execution
- Batch error handling (individual image failures don't stop batch)

**Files Created**:
- src/backend/api/processing.py (new router)
- src/backend/schemas/processing.py (request/response models)

**Files Modified**:
- src/worker/tasks/process_images.py (batch orchestration)
- src/backend/app/main.py (register processing router)

**Success Criteria**:
- Batch of 100 images processes at 70+ images/second
- Individual failures don't crash batch
- All images transition to completed or failed status

**Estimated Effort**: 4 hours

### Phase 3: User Story 3 - Progress Monitoring (P3)

**Purpose**: Provide visibility into processing jobs

**Deliverables**:
- GET /api/processing/status endpoint
- Database aggregation queries for status counts
- Processing rate calculation (images/second)
- Estimated time remaining calculation

**Files Modified**:
- src/backend/api/processing.py (add status endpoint)
- src/backend/schemas/processing.py (add status response model)

**Success Criteria**:
- Status endpoint responds in <200ms
- Accurate counts by processing_status
- Processing rate calculated from recent completions

**Estimated Effort**: 2 hours

## Data Model Changes

### Image Model Updates

```python
# Add to src/backend/models/image.py

from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Add to Image class:
processing_status = Column(
    Enum(ProcessingStatus),
    default=ProcessingStatus.PENDING,
    nullable=False
)
error_message = Column(Text, nullable=True)
```

### Database Migration

```sql
-- Manual migration (Alembic not configured yet)
ALTER TABLE images
ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
ADD COLUMN error_message TEXT;

-- Create index for status queries
CREATE INDEX idx_images_processing_status ON images(processing_status);
```

## API Contracts

### Modified: POST /api/images

**Request**:
```json
{
  "files": ["<binary>"],
  "location_name": "Sanctuary",
  "process_immediately": true  // NEW - optional, default false
}
```

**Response** (unchanged):
```json
{
  "uploaded": [
    {
      "id": "uuid",
      "filename": "deer.jpg",
      "processing_status": "processing",  // NEW field
      "location_id": "uuid",
      "timestamp": "2025-11-05T12:00:00Z"
    }
  ]
}
```

### New: POST /api/processing/batch

**Request**:
```json
{
  "image_ids": ["uuid1", "uuid2", ...],
  "priority": "normal"  // optional: low, normal, high
}
```

**Response**:
```json
{
  "job_id": "task-uuid",
  "queued_count": 100,
  "message": "Batch processing started"
}
```

### New: GET /api/processing/status

**Query Parameters**: None (system-wide status)

**Response**:
```json
{
  "status": "active",
  "counts": {
    "pending": 1234,
    "processing": 32,
    "completed": 33968,
    "failed": 0
  },
  "processing_rate": 78.5,  // images per second
  "estimated_completion": "2025-11-05T12:15:00Z"  // null if idle
}
```

## Processing Pipeline Flow

```
1. Image Upload
   └─> Save to filesystem
   └─> Create Image record (status=pending)
   └─> [IF process_immediately] Queue detection task

2. Detection Task (Celery)
   └─> Update status to "processing"
   └─> Load image from filesystem
   └─> Run YOLOv8 inference
   └─> For each detection:
       └─> Create Detection record (bbox, confidence, class_id)
   └─> Update status to "completed"
   └─> [ON ERROR] Update status to "failed", save error_message

3. Batch Processing
   └─> Receive image_ids list
   └─> Chunk into batches of 32
   └─> Create Celery group for parallel execution
   └─> Each chunk runs detection task
   └─> Return immediately with job_id
```

## Error Handling Strategy

### GPU Out of Memory
- Catch `torch.cuda.OutOfMemoryError`
- Reduce batch size dynamically (32 -> 16 -> 8)
- Retry individual image if batch fails
- Log OOM events for monitoring

### Corrupted Images
- Catch PIL `UnidentifiedImageError`
- Mark image as "failed" with specific error message
- Continue processing next image in batch
- Don't crash worker

### Database Connection Errors
- Use SQLAlchemy connection pool retry logic
- Exponential backoff for transient failures
- Mark image as "failed" after 3 retries
- Alert on persistent connection issues

### Model Loading Failures
- Fail worker startup if model missing
- Log detailed error with model path
- Require manual intervention (don't retry infinitely)

## Performance Optimizations

### Database Write Batching
- Use SQLAlchemy bulk_insert_mappings for detections
- Commit after processing each batch of 32 images
- Use separate DB sessions per Celery task

### GPU Utilization
- Process images in batches of 32 (fills GPU memory)
- Pre-resize images to consistent dimensions
- Use torch.no_grad() context for inference
- Keep model in GPU memory (don't reload)

### API Response Time
- Use COUNT queries with index on processing_status
- Cache processing rate calculation (1-second TTL)
- Avoid joining large tables for status endpoint

## Monitoring and Logging

### Metrics to Track
- Images processed per second (throughput)
- Average detection confidence scores
- Error rate by error type
- GPU memory utilization
- Database connection pool saturation

### Log Events
- Task start/completion with image_id and duration
- Detection results summary (count, avg confidence)
- All errors with full stack trace
- Batch processing job start/end

## Risks and Mitigations

### Risk: GPU Memory Overflow
**Likelihood**: Medium
**Impact**: High (worker crash)
**Mitigation**: Dynamic batch size reduction, memory monitoring, graceful restart

### Risk: Database Write Bottleneck
**Likelihood**: Low
**Impact**: Medium (slow processing)
**Mitigation**: Connection pooling, bulk inserts, index optimization

### Risk: Celery Queue Backup
**Likelihood**: Medium
**Impact**: Medium (delayed processing)
**Mitigation**: Monitor queue depth, alert on threshold, scale workers horizontally

## Dependencies

### External Dependencies (Already Installed)
- ultralytics==8.0.200
- torch==2.1.0+cu121
- torchvision==0.16.0+cu121
- Pillow==12.0.0

### Internal Dependencies (Sprint 1 Complete)
- Database models: Image, Detection, Location
- API infrastructure: FastAPI app, routers
- Worker infrastructure: Celery app, Redis connection
- Docker environment: All services running

### Blocking Prerequisites
- None - all Sprint 1 dependencies complete
- Model file already copied: src/models/yolov8n_deer.pt

## Testing Strategy (Not Implemented This Sprint)

Future testing would include:
- Unit tests for detection task logic
- Integration tests for end-to-end processing
- Load tests with 1000+ image batches
- GPU memory stress tests
- Database transaction isolation tests
- Idempotency tests for duplicate detection requests

## Deployment Considerations

### Configuration Updates
- Add BATCH_SIZE=32 to .env
- Add PROCESSING_TIMEOUT=300 to .env (5 minutes)
- Verify GPU access in worker container

### Database Schema
- Run migration SQL before deploying code
- Verify index creation on processing_status

### Rollback Plan
- Keep old code in git
- Revert database migration if needed
- Clear Celery queue if tasks incompatible

## Success Metrics

### Phase 1 Success (User Story 1)
- Single image processing end-to-end < 3 seconds
- Detection records created correctly
- Error handling works for corrupted images

### Phase 2 Success (User Story 2)
- Batch of 100 images processes at 70+ images/second
- No worker crashes during batch
- Individual failures isolated

### Phase 3 Success (User Story 3)
- Status endpoint < 200ms response time
- Accurate counts match database state
- Processing rate calculation correct

## Timeline Estimate

- Phase 0 (Foundation): 1 hour
- Phase 1 (Single Image): 3 hours
- Phase 2 (Batch Processing): 4 hours
- Phase 3 (Monitoring): 2 hours
- Phase 4 (Polish): 1 hour
- **Total**: 11 hours (~1.5 days)

## Next Steps After This Feature

1. Re-identification model integration (ResNet50)
2. Sex classification model integration (CNN)
3. Deer management API (CRUD endpoints)
4. Frontend dashboard for viewing results
5. Comprehensive testing suite
