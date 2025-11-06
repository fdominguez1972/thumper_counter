# Tasks: Detection Pipeline Integration

**Input**: Design documents from `.specify/features/001-detection-pipeline/`
**Prerequisites**: spec.md (complete), plan.md (complete)

**Tests**: Tests are NOT included in this feature - deferred to future Sprint 5 (Testing & Quality)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 0: Foundation Updates (Shared Infrastructure)

**Purpose**: Update existing database models and schemas to support processing status tracking. MUST be complete before any user story work begins.

- [ ] T001 Add ProcessingStatus enum and fields to Image model in `src/backend/models/image.py`
- [ ] T002 Create database migration SQL script in `migrations/001_add_processing_status.sql`
- [ ] T003 [P] Run database migration against PostgreSQL container
- [ ] T004 [P] Update ImageSchema in `src/backend/schemas/image.py` to include processing_status and error_message fields
- [ ] T005 [P] Create DetectionSchema response model in `src/backend/schemas/detection.py` (if not exists)
- [ ] T005a [P] Add model file validation to worker startup in `src/worker/celery_app.py`
  - Check model file exists at src/models/yolov8n_deer.pt
  - Verify file size > 20MB (corruption check)
  - Log clear error with full path if validation fails
  - Exit worker process (don't start with missing model)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 1: User Story 1 - Process Uploaded Images Through Detection (Priority: P1) 🎯 MVP

**Goal**: Enable on-demand processing of uploaded images through YOLOv8 with detection results stored in database

**Independent Test**:
```bash
curl -X POST http://localhost:8001/api/images \
  -F "files=@test_deer.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=true"

# Verify Detection records created with bounding boxes
curl http://localhost:8001/api/images/{image_id}
```

### Implementation for User Story 1

- [ ] T006 [P] [US1] Update POST /api/images endpoint in `src/backend/api/images.py` to accept `process_immediately` boolean parameter
- [ ] T006a [P] [US1] Add file size validation to POST /api/images in `src/backend/api/images.py`
  - Check uploaded file size before saving
  - Return HTTP 413 "Payload Too Large" if >50MB
  - Include max_size in error message
- [ ] T007 [P] [US1] Add Celery task queueing logic in `src/backend/api/images.py` when `process_immediately=true`
- [ ] T008 [US1] Implement database integration in `src/worker/tasks/detection.py` (depends on T006, T007)
  - Update image status to "processing" at task start
  - Load image from filesystem using Image.path
  - Run YOLOv8 inference
  - Create Detection records for each bbox result
  - Update image status to "completed" on success
- [ ] T009 [US1] Add error handling to `src/worker/tasks/detection.py`
  - Catch PIL.UnidentifiedImageError for corrupted images
  - Catch torch.cuda.OutOfMemoryError for GPU issues
  - Update image status to "failed" and populate error_message
  - Log all errors with image_id and stack trace
- [ ] T010 [US1] Add YOLOv8 GPU optimization in `src/worker/models/yolov8_detector.py`
  - Use torch.no_grad() context for inference
  - Verify model stays loaded in GPU memory
  - Add confidence threshold filtering (min 0.5)
- [ ] T011 [US1] Add logging for detection results in `src/worker/tasks/detection.py`
  - Log task start/end with image_id and duration
  - Log detection count and average confidence per image
  - Log status transitions (pending -> processing -> completed/failed)

**Checkpoint**: At this point, single image upload with immediate processing should work end-to-end

---

## Phase 2: User Story 2 - Batch Process Existing Images (Priority: P2)

**Goal**: Enable efficient batch processing of large image sets with parallel execution and fault tolerance

**Independent Test**:
```bash
# Get 100 pending image IDs
curl "http://localhost:8001/api/images?status=pending&page_size=100" | jq -r '.images[].id' > batch_ids.txt

# Trigger batch processing
curl -X POST http://localhost:8001/api/processing/batch \
  -H "Content-Type: application/json" \
  -d '{"image_ids": ['$(cat batch_ids.txt | jq -R -s -c 'split("\n")[:-1]')']}'

# Monitor completion
watch -n 5 'curl http://localhost:8001/api/processing/status'
```

### Implementation for User Story 2

- [ ] T012 [P] [US2] Create ProcessingSchema request/response models in `src/backend/schemas/processing.py`
  - BatchProcessingRequest: image_ids (list), priority (optional)
  - BatchProcessingResponse: job_id, queued_count, message
- [ ] T013 [P] [US2] Create processing router in `src/backend/api/processing.py` with POST /api/processing/batch endpoint
- [ ] T014 [US2] Implement batch orchestration task in `src/worker/tasks/process_images.py` (depends on T012, T013)
  - Accept list of image_ids
  - Chunk into batches of 32 (BATCH_SIZE from env)
  - Create Celery group for parallel batch execution
  - Return task group ID as job_id
- [ ] T015 [US2] Add batch processing logic in `src/worker/tasks/process_images.py`
  - Query images by ID list from database
  - Load images in batch from filesystem
  - Run YOLOv8 batch inference (32 images at once)
  - Bulk insert Detection records using SQLAlchemy bulk_insert_mappings
  - Update all image statuses in single transaction
- [ ] T016 [US2] Implement fault tolerance in `src/worker/tasks/process_images.py`
  - Catch individual image failures without stopping batch
  - Mark failed images as "failed" with error_message
  - Continue processing remaining images in batch
  - Log batch summary (total, succeeded, failed)
- [ ] T017 [US2] Register processing router in `src/backend/app/main.py`
  - Import processing router
  - Add to FastAPI app with /api/processing prefix

**Checkpoint**: At this point, batch processing of 100+ images should work with 70+ images/second throughput

---

## Phase 3: User Story 3 - Monitor Processing Progress (Priority: P3)

**Goal**: Provide real-time visibility into processing job status and progress

**Independent Test**:
```bash
# Start large batch
curl -X POST http://localhost:8001/api/processing/batch \
  -H "Content-Type: application/json" \
  -d '{"image_ids": [...1000 ids...]}'

# Check status
curl http://localhost:8001/api/processing/status | jq

# Verify counts match database
docker-compose exec db psql -U deertrack -d deer_tracking \
  -c "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"
```

### Implementation for User Story 3

- [ ] T018 [P] [US3] Add ProcessingStatusResponse schema in `src/backend/schemas/processing.py`
  - status (idle/active), counts (dict), processing_rate (float), estimated_completion (datetime or null)
- [ ] T019 [US3] Implement GET /api/processing/status endpoint in `src/backend/api/processing.py`
  - Query status counts with GROUP BY processing_status
  - Use index on processing_status for fast counts
  - Calculate processing rate from recent completions
- [ ] T020 [US3] Add processing rate calculation in `src/backend/api/processing.py`
  - Query images completed in last 60 seconds
  - Calculate images per second rate
  - Return 0 if no recent completions (idle state)
- [ ] T021 [US3] Add estimated completion calculation in `src/backend/api/processing.py`
  - Get count of pending + processing images
  - Divide by current processing rate
  - Return null if rate is 0 (idle)
  - Return current_time + estimated_seconds otherwise
- [ ] T022 [US3] Optimize status endpoint performance in `src/backend/api/processing.py`
  - Verify index exists on processing_status
  - Use SQLAlchemy count() queries (no row fetching)
  - Target <200ms response time
  - Add query execution time logging

**Checkpoint**: All user stories should now be independently functional

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements that affect multiple user stories

- [ ] T023 [P] Add environment variable BATCH_SIZE (default 32) to `.env` file
- [ ] T024 [P] Add environment variable PROCESSING_TIMEOUT (default 300) to `.env` file
- [ ] T025 [P] Verify GPU memory usage stays under 14GB with batch_size=32
- [ ] T026 Add database index creation to migration script: `CREATE INDEX idx_images_processing_status ON images(processing_status);`
- [ ] T027 [P] Update API documentation in `src/backend/app/main.py` FastAPI metadata with new endpoints
- [ ] T028 [P] Verify Celery worker logs show task execution details
- [ ] T029 Test end-to-end processing of 1000 images and verify no crashes
- [ ] T030 Document API endpoints in `.specify/features/001-detection-pipeline/api_usage.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation (Phase 0)**: No dependencies - can start immediately - BLOCKS all user stories
- **User Story 1 (Phase 1)**: Depends on Foundation completion - No dependencies on other stories
- **User Story 2 (Phase 2)**: Depends on Foundation completion - Reuses detection task from US1 but should be independently testable
- **User Story 3 (Phase 3)**: Depends on Foundation completion - Can start after US1/US2 or in parallel if desired
- **Polish (Phase 4)**: Depends on all user stories being complete

### Within Each User Story

**User Story 1:**
- T006, T007 can run in parallel (different logic in same file)
- T008 depends on T006, T007 (needs task queueing to be set up)
- T009, T010, T011 depend on T008 (enhance core detection task)

**User Story 2:**
- T012, T013 can run in parallel (schema vs router)
- T014 depends on T012, T013 (needs schema and endpoint)
- T015, T016 can run in parallel with T014 (batch logic)
- T017 depends on T013 (needs router to register)

**User Story 3:**
- T018, T019 can run in parallel (schema vs endpoint structure)
- T020, T021, T022 enhance T019 (sequential refinements)

### Parallel Opportunities

- All Foundation tasks (T001-T005) can run in parallel after T002 migration is created
- User Story 1 and User Story 2 can be developed in parallel by different developers after Foundation completes
- User Story 3 can start in parallel with US2 if desired
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: Foundation Phase

```bash
# Launch all foundation tasks together (after T002 migration created):
Task T001: "Add ProcessingStatus enum to Image model"
Task T003: "Run database migration"
Task T004: "Update ImageSchema with processing fields"
Task T005: "Create DetectionSchema response model"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Foundation (T001-T005) - ~1 hour
2. Complete Phase 1: User Story 1 (T006-T011) - ~3 hours
3. **STOP and VALIDATE**: Test single image upload with immediate processing
4. Deploy/demo if ready

This gives you working detection pipeline for on-demand processing.

### Incremental Delivery

1. Complete Foundation → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Process 35k images
4. Add User Story 3 → Test independently → Deploy/Demo with monitoring
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundation together (~1 hour)
2. Once Foundation is done:
   - Developer A: User Story 1 (T006-T011) - 3 hours
   - Developer B: User Story 2 (T012-T017) - 4 hours
   - Developer C: User Story 3 (T018-T022) - 2 hours
3. Stories complete and integrate independently
4. Team completes Polish together (T023-T030) - 1 hour

**Total Time (Sequential)**: ~10 hours
**Total Time (Parallel 3 devs)**: ~5 hours

---

## Critical Path

```
Foundation (1h) → US1 (3h) → US2 (4h) → US3 (2h) → Polish (1h)
Total Sequential: 11 hours (~1.5 days)

Foundation (1h) → [US1 | US2 | US3] (4h max) → Polish (1h)
Total Parallel: 6 hours (~1 day)
```

---

## Notes

- [P] tasks = different files/logic, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included in this feature (deferred to Sprint 5)
- Database migrations are manual SQL (Alembic not configured yet)
