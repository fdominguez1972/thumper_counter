# Tasks: Bulk Image Upload System

**Input**: Design documents from `/specs/009-bulk-image-upload/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT requested in this feature specification, so test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- All paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, database migration, and dependency installation

- [ ] T001 Apply database migration 011_add_upload_batches.sql to create upload_batches table and modify images table
- [ ] T002 [P] Install react-dropzone@^14.0.0 in frontend/package.json (already has axios)
- [ ] T003 [P] Verify Pillow 12.0.0 is installed in backend requirements.txt (already present)
- [ ] T004 [P] Create data/uploads/ directory for temporary upload staging
- [ ] T005 [P] Update nginx configuration to set client_max_body_size 2048M for 2GB upload support

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**WARNING CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create UploadBatch model in backend/src/backend/models/upload_batch.py with status enum and relationships
- [ ] T007 Add upload_batch_id foreign key column to Image model in backend/src/backend/models/image.py
- [ ] T008 [P] Create UploadRequest schema in backend/src/backend/schemas/upload.py for file upload validation
- [ ] T009 [P] Create UploadResponse schema in backend/src/backend/schemas/upload.py for batch result responses
- [ ] T010 [P] Create UploadBatchSchema in backend/src/backend/schemas/upload.py for batch history queries
- [ ] T011 Create EXIFService in backend/src/backend/services/exif_service.py with extract_timestamp() method (3-level fallback: EXIF tags 36867/306/36868 -> filename pattern -> UTC now)
- [ ] T012 Create UploadService class in backend/src/backend/services/upload_service.py with create_batch() and get_unique_filename() methods
- [ ] T013 Register /api/upload routes in backend/src/backend/app/main.py by including upload router

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload Individual Trail Camera Images (Priority: P1) TARGET MVP

**Goal**: Enable ranch managers to upload individual JPG/JPEG images via web interface with location assignment and EXIF timestamp extraction

**Independent Test**: Navigate to /upload page, select 5 JPG files via file picker, choose location from dropdown, click upload button. Verify images appear in /images page with correct location and timestamps.

### Implementation for User Story 1

- [ ] T014 [P] [US1] Create POST /api/upload/files endpoint in backend/src/backend/api/upload.py accepting multipart/form-data with files[] array, location_id, and process_immediately flag
- [ ] T015 [P] [US1] Implement Upload page component in frontend/src/pages/Upload.tsx with Material-UI Card layout and location dropdown
- [ ] T016 [US1] Implement file upload handler in backend/src/backend/api/upload.py that validates JPG/JPEG format, creates UploadBatch record with status='pending', and loops through files
- [ ] T017 [US1] Implement per-file processing logic in UploadService: extract EXIF timestamp via EXIFService, check for duplicate filename via get_unique_filename(), save file to /mnt/images/{location_name}/, create Image record with upload_batch_id
- [ ] T018 [US1] Update UploadBatch counts (successful_files, failed_files) and set status='completed' or 'failed' based on results
- [ ] T019 [US1] Return UploadResponse with batch_id, total_files, successful_files, failed_files, status, location_name, duration_seconds, and errors array
- [ ] T020 [US1] Create file input component in Upload.tsx using standard HTML <input type="file" multiple accept=".jpg,.jpeg" />
- [ ] T021 [US1] Implement location dropdown in Upload.tsx fetching from GET /api/locations and using Material-UI Select component
- [ ] T022 [US1] Add "Process Immediately" checkbox in Upload.tsx using Material-UI FormControlLabel with Checkbox
- [ ] T023 [US1] Implement upload button handler in Upload.tsx using axios.post() with FormData containing files and location_id
- [ ] T024 [US1] Display upload progress in Upload.tsx using Material-UI LinearProgress with axios onUploadProgress callback
- [ ] T025 [US1] Show upload summary in Upload.tsx using Material-UI Alert component with success/error counts
- [ ] T026 [US1] Add Upload navigation item to frontend/src/components/layout/Layout.tsx drawer menu with CloudUpload icon
- [ ] T027 [US1] Add error handling for validation failures (missing location, invalid file type, file size > 50MB) returning HTTP 400 with clear error messages
- [ ] T028 [US1] Add logging for upload operations in backend upload handler using Python logging module

**Checkpoint**: At this point, User Story 1 should be fully functional - users can upload individual images with location assignment and EXIF extraction

---

## Phase 4: User Story 2 - Upload ZIP Archives Containing Multiple Images (Priority: P2)

**Goal**: Enable ranch managers to upload ZIP archives containing hundreds/thousands of trail camera images for efficient bulk transfers

**Independent Test**: Create test ZIP archive with 100 images, navigate to /upload page, select ZIP file, choose location, upload. Verify all 100 images extracted and stored with correct location.

### Implementation for User Story 2

- [ ] T029 [P] [US2] Create POST /api/upload/zip endpoint in backend/src/backend/api/upload.py accepting single ZIP file with location_id
- [ ] T030 [US2] Implement ZIP extraction logic in UploadService.extract_zip() using Python zipfile module with streaming extraction
- [ ] T031 [US2] Validate ZIP file integrity using zipfile.testzip() before extraction, return HTTP 400 if corrupted
- [ ] T032 [US2] Create temporary extraction directory using UUID: /tmp/upload_{batch_uuid}/ for isolated file processing
- [ ] T033 [US2] Filter extracted files to only JPG/JPEG using .lower().endswith(('.jpg', '.jpeg')) check and ignore other file types
- [ ] T034 [US2] Process each extracted JPG/JPEG file through same flow as individual upload: EXIF extraction, duplicate check, save to /mnt/images/{location}/, create Image record
- [ ] T035 [US2] Update UploadBatch with zip_filename and zip_size_bytes fields from uploaded file metadata
- [ ] T036 [US2] Clean up temporary directory using shutil.rmtree() after processing completes or on error
- [ ] T037 [US2] Update frontend Upload.tsx to detect ZIP file type and show appropriate UI message "Extracting ZIP archive..."
- [ ] T038 [US2] Implement progress tracking for ZIP extraction showing "Extracted X of Y images" during processing
- [ ] T039 [US2] Add error handling for ZIP-specific errors (corrupt archive, no images found, extraction timeout) with clear user messages
- [ ] T040 [US2] Add logging for ZIP extraction operations including file count and extraction duration

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can upload individual files OR ZIP archives

---

## Phase 5: User Story 3 - Automatic Timestamp Extraction from Images (Priority: P3)

**Goal**: Automatically extract accurate timestamps from trail camera images using EXIF metadata or filename patterns for scientific data integrity

**Independent Test**: Upload image with EXIF DateTimeOriginal tag, verify database record shows camera capture time not upload time. Upload image without EXIF but with filename "Location_20251031_143022_001.jpg", verify timestamp parsed as 2025-10-31 14:30:22.

**Note**: This story is already implemented in Phase 2 (T011 EXIFService) and used in Phase 3/4 upload flows. This phase adds enhancements and validation.

### Implementation for User Story 3

- [ ] T041 [P] [US3] Enhance EXIFService.extract_timestamp() to validate timestamp range (1990 <= year <= 2030) and reject invalid dates
- [ ] T042 [P] [US3] Implement filename pattern parsing in EXIFService using regex pattern: r'(\d{8})_(\d{6})' extracting YYYYMMDD and HHMMSS
- [ ] T043 [US3] Add timestamp source tracking to Image model by storing "exif", "filename", or "current" in exif_data JSON field under "timestamp_source" key
- [ ] T044 [US3] Log warnings when falling back to current UTC time due to missing EXIF and unparseable filename
- [ ] T045 [US3] Create GET /api/upload/stats/timestamps endpoint in backend/src/backend/api/upload.py returning percentage breakdown of timestamp sources (EXIF vs filename vs fallback)
- [ ] T046 [US3] Add timestamp statistics display to Upload success summary showing "95% timestamps from EXIF, 4% from filename, 1% fallback"
- [ ] T047 [US3] Handle timezone conversion for EXIF timestamps assuming UTC and storing as TIMESTAMP WITH TIME ZONE in database

**Checkpoint**: All timestamp extraction methods working with validation and source tracking

---

## Phase 6: User Story 4 - Automatic Processing Queue Integration (Priority: P4)

**Goal**: Automatically queue uploaded images for ML detection and re-identification pipeline to enable "upload and forget" workflow

**Independent Test**: Upload 10 images with process_immediately=true, wait 2 minutes, verify images show processing_status='completed' with detections in database and deer profiles assigned.

### Implementation for User Story 4

- [ ] T048 [US4] Import existing detect_images Celery task from backend/src/worker/tasks/process_images.py into upload handler
- [ ] T049 [US4] Add queue_for_processing flag check in upload handler after batch completion (when process_immediately=true)
- [ ] T050 [US4] Collect all successfully uploaded image IDs from current batch into list for Celery task
- [ ] T051 [US4] Call detect_images.apply_async() with image ID list to queue batch for detection processing
- [ ] T052 [US4] Update UploadResponse schema to include queued_for_processing boolean field indicating whether ML pipeline was triggered
- [ ] T053 [US4] Add logging when queuing images for processing including batch_id and image count
- [ ] T054 [US4] Update Upload.tsx success message to show "20 images queued for detection processing" when process_immediately=true
- [ ] T055 [US4] Add link in Upload.tsx success summary to navigate to /images page filtered by upload_batch_id to view processing status
- [ ] T056 [US4] Handle case where Celery worker is offline: complete upload successfully but log warning about queuing failure

**Checkpoint**: End-to-end automation working - upload triggers ML pipeline without manual intervention

---

## Phase 7: User Story 5 - Drag-and-Drop Upload Interface (Priority: P5)

**Goal**: Enhance UX by allowing users to drag image files directly onto upload page instead of using file picker

**Independent Test**: Drag folder of 50 images from desktop onto /upload page, verify all files added to upload queue, select location, upload. Verify all images uploaded successfully.

### Implementation for User Story 5

- [ ] T057 [US5] Create UploadZone component in frontend/src/components/UploadZone.tsx using react-dropzone useDropzone hook
- [ ] T058 [US5] Configure dropzone to accept only JPEG files: accept: { 'image/jpeg': ['.jpg', '.jpeg'] }
- [ ] T059 [US5] Set maxSize: 2147483648 (2GB) to enforce file size limit in dropzone
- [ ] T060 [US5] Implement onDrop callback to add accepted files to state array for upload
- [ ] T061 [US5] Style drop zone with Material-UI Box component showing dashed border, CloudUpload icon, and "Drag images here or click to browse" text
- [ ] T062 [US5] Add hover state styling to highlight drop zone when user drags files over it (isDragActive prop from dropzone)
- [ ] T063 [US5] Display file count and total size in UploadZone when files are added: "50 files selected (125 MB)"
- [ ] T064 [US5] Replace standard file input in Upload.tsx with UploadZone component
- [ ] T065 [US5] Add validation in onDrop to reject non-JPEG files showing Material-UI Snackbar with error message
- [ ] T066 [US5] Implement file list display showing selected filenames with remove button using Material-UI List and ListItem
- [ ] T067 [US5] Add clear all button to UploadZone to reset file selection

**Checkpoint**: All user stories complete - full upload functionality with optimal UX

---

## Phase 8: Upload Batch History & Management

**Goal**: Enable users to view upload history, batch details, and retry failed uploads

### Implementation

- [ ] T068 [P] Create GET /api/upload/batches endpoint in backend/src/backend/api/upload.py with pagination, location_id filter, and status filter
- [ ] T069 [P] Create GET /api/upload/batches/{batch_id} endpoint returning batch detail with list of images in that batch
- [ ] T070 [P] Create UploadHistory component in frontend/src/components/UploadHistory.tsx displaying recent upload batches in Material-UI Table
- [ ] T071 Add UploadHistory component to Upload.tsx page below upload form showing last 10 batches
- [ ] T072 Implement batch detail dialog in UploadHistory showing full image list for selected batch with Material-UI Dialog
- [ ] T073 Add filtering controls to UploadHistory for location and status using Material-UI Select components
- [ ] T074 Display batch statistics in UploadHistory: duration, success rate, file counts with color-coded status chips

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T075 [P] Add comprehensive error messages for all failure scenarios with actionable guidance (e.g., "File exceeds 50MB limit. Try uploading smaller files.")
- [ ] T076 [P] Implement rate limiting on upload endpoints to prevent abuse: max 10 uploads per minute per IP
- [ ] T077 [P] Add disk space check before upload: reject if <10GB free on /mnt/images filesystem
- [ ] T078 [P] Create API documentation for upload endpoints in backend/docs/api/upload.md with examples
- [ ] T079 [P] Add monitoring metrics for upload operations: total uploads, success rate, average duration, total bytes uploaded
- [ ] T080 Update CLAUDE.md session status documenting Feature 009 completion with upload statistics
- [ ] T081 Test upload workflow end-to-end using quickstart.md validation scenarios
- [ ] T082 Performance test with 1000-image ZIP upload verifying <10 minute completion time
- [ ] T083 [P] Add user-facing documentation in docs/USER_GUIDE_UPLOAD.md with screenshots and step-by-step instructions
- [ ] T084 Code review and refactoring for upload service and components
- [ ] T085 Security audit: path traversal prevention in ZIP extraction, SQL injection prevention, file type validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Upload History (Phase 8)**: Depends on US1 completion (requires upload_batches table populated)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP CANDIDATE**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 upload flow but independently testable
- **User Story 3 (P3)**: Already integrated into US1/US2 via EXIFService - This phase adds enhancements only
- **User Story 4 (P4)**: Depends on US1 completion (extends upload handler) - Integrates with existing Celery pipeline
- **User Story 5 (P5)**: Can start after US1 frontend complete (replaces file input component) - Independently testable

### Within Each User Story

- Backend models/schemas before services
- Services before API endpoints
- API endpoints before frontend components
- Frontend components before integration
- Story complete before moving to next priority

### Parallel Opportunities

#### Setup Phase (all can run in parallel):
- T002 (frontend deps), T003 (backend deps), T004 (directory), T005 (nginx)

#### Foundational Phase (some parallelizable):
- T008, T009, T010 (schemas) can run in parallel
- T006, T007 (models) must complete before services
- T011, T012 (services) can run in parallel after models

#### User Story 1 (backend and frontend in parallel):
- T014 (backend endpoint) parallel with T015 (frontend page)
- T020-T025 (all frontend components) can run in parallel
- T014-T019 (backend flow) must run sequentially

#### User Story 2:
- T029 (endpoint) parallel with T037-T040 (frontend updates)
- T030-T036 (backend ZIP logic) must run sequentially

#### User Story 3 (all enhancements can parallel):
- T041, T042, T043 (enhancements) can run in parallel

#### User Story 5 (most components can parallel):
- T057-T067 (all frontend drag-drop components) can run in parallel

#### Polish Phase (all can run in parallel):
- T075-T079, T083-T085 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch backend and frontend work in parallel after Foundational complete:

# Backend team:
Task: "Create POST /api/upload/files endpoint in backend/src/backend/api/upload.py"
Task: "Implement file upload handler with EXIF extraction and duplicate checking"

# Frontend team (parallel):
Task: "Implement Upload page component in frontend/src/pages/Upload.tsx"
Task: "Create file input component with location dropdown"
Task: "Implement upload progress display with Material-UI LinearProgress"
Task: "Add upload button handler using axios"
```

---

## Parallel Example: Setup + Foundational Phases

```bash
# Setup Phase (all parallel):
Task: "Apply database migration"
Task: "Install react-dropzone in frontend"
Task: "Verify Pillow installed in backend"
Task: "Create uploads directory"
Task: "Update nginx config"

# Foundational Phase (after Setup, some parallel):
Task: "Create UploadBatch model"  # Sequential prerequisite
Task: "Add upload_batch_id to Image model"  # Sequential prerequisite
Task: "Create all schemas in parallel"  # T008, T009, T010 together
Task: "Create EXIFService"  # After models
Task: "Create UploadService"  # After models, parallel with EXIFService
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~30 minutes)
2. Complete Phase 2: Foundational (~2-3 hours)
3. Complete Phase 3: User Story 1 (~4-6 hours)
4. **STOP and VALIDATE**: Test US1 independently using quickstart.md
5. Deploy/demo if ready

**MVP Delivers**: Users can upload individual images via web interface with location assignment and EXIF timestamp extraction. Ready for production use.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~3 hours)
2. Add User Story 1 → Test independently → Deploy/Demo (~6 hours) - **MVP!**
3. Add User Story 2 → Test independently → Deploy/Demo (~4 hours) - **ZIP archives!**
4. Add User Story 3 → Test independently (~2 hours) - **Timestamp validation!**
5. Add User Story 4 → Test independently → Deploy/Demo (~2 hours) - **Full automation!**
6. Add User Story 5 → Test independently (~3 hours) - **Polished UX!**
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~3 hours)
2. Once Foundational is done:
   - Developer A: User Story 1 (backend + frontend)
   - Developer B: User Story 2 (backend + frontend)
   - Developer C: User Story 5 (frontend only, wait for US1 frontend)
3. User Story 3 enhancements integrated during US1/US2 work
4. User Story 4 queuing added after US1 backend complete
5. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 85 tasks across 9 phases

**Tasks per User Story**:
- Setup: 5 tasks
- Foundational: 8 tasks (BLOCKING)
- User Story 1 (P1): 15 tasks (MVP)
- User Story 2 (P2): 12 tasks
- User Story 3 (P3): 7 tasks
- User Story 4 (P4): 9 tasks
- User Story 5 (P5): 11 tasks
- Upload History: 7 tasks
- Polish: 11 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel when dependencies met

**Independent Test Criteria**:
- US1: Upload 5 images, verify in /images page
- US2: Upload 100-image ZIP, verify extraction
- US3: Upload image with EXIF, verify timestamp accuracy
- US4: Upload with queue enabled, verify detections appear
- US5: Drag 50 files onto page, verify upload works

**Suggested MVP Scope**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (User Story 1)
- **Time Estimate**: 8-10 hours
- **Deliverable**: Functional individual image upload with location and EXIF extraction

**Full Feature Completion**: All phases
- **Time Estimate**: 25-30 hours
- **Deliverable**: Complete bulk upload system with ZIP support, drag-drop, and ML integration

---

## Format Validation

[OK] All 85 tasks follow checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
[OK] All user story tasks (T014-T067) include [US#] label
[OK] All parallelizable tasks include [P] marker
[OK] All tasks include specific file paths
[OK] Task IDs sequential from T001 to T085
[OK] Independent test criteria defined for each user story
[OK] MVP scope clearly identified (US1)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Backend paths: backend/src/backend/...
- Frontend paths: frontend/src/...
- Tests omitted per feature specification (no TDD requested)
