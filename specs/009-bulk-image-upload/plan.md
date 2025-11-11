# Implementation Plan: Bulk Image Upload System

**Branch**: `009-bulk-image-upload` | **Date**: 2025-11-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-bulk-image-upload/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a web-based bulk image upload system for trail camera images with automatic location assignment, EXIF timestamp extraction, ZIP archive support, and automatic ML pipeline integration. This feature enables ranch managers to self-serve image uploads without developer intervention, processing up to 10,000 images per batch with drag-and-drop interface and real-time progress tracking.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, React 18, Material-UI v5, Celery, Pillow, zipfile
**Storage**: PostgreSQL 15 (metadata), local filesystem (images at /mnt/images/{location}/)
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Linux server (Docker), desktop web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (existing backend + frontend)
**Performance Goals**: Handle 10,000 image uploads without timeout, process 100 images in <5 minutes, 500MB ZIP extraction without memory overflow
**Constraints**: 2GB max upload size, 30-second database write time for upload batch, asynchronous ML processing (non-blocking), existing file storage structure (/mnt/images/{location}/)
**Scale/Scope**: 23,934 immediate upload need, ongoing batches of 5,000-10,000 images per location dump, 7 camera locations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Review

| Principle | Requirement | Compliance Status |
|-----------|-------------|-------------------|
| **Wildlife Conservation First** | No real-time location, delay public data 48+ hours | PASS - Upload system stores images without public broadcast, location data secured |
| **Data Sovereignty** | Local-first storage, no cloud dependencies | PASS - Images stored on /mnt/images/ local filesystem, no cloud upload |
| **Operational Simplicity** | Single-button upload, location dropdown, clear indicators | PASS - File picker + location dropdown + progress bar design |
| **Scientific Rigor** | Confidence levels, manual verification support | PASS - Integrates with existing detection system (confidence >0.5), manual review via Images page |
| **Modular Architecture** | Independently deployable, standard REST APIs | PASS - New API endpoints, reuses existing detection/re-ID services |
| **Performance Efficiency** | Process 35,000+ images in 24 hours | PASS - Upload system feeds existing 840 images/min pipeline, non-blocking |
| **Open Development** | Open-source components, MIT license | PASS - Uses open-source FastAPI, React, no proprietary dependencies |

### Technical Standards Compliance

| Standard | Requirement | Compliance Status |
|----------|-------------|-------------------|
| **Python 3.11+** | Backend code version | PASS - Existing backend is Python 3.11 |
| **PostgreSQL 15+** | Data persistence | PASS - Existing database for image records |
| **Docker** | Deployment | PASS - Backend/frontend containers already configured |
| **Git** | Branching strategy | PASS - Feature branch 009-bulk-image-upload created |
| **ASCII-only** | Logs and CLI output | PASS - No Unicode/emoji in upload progress or error messages |

### Prohibited Practices Check

| Prohibition | Compliance Status |
|-------------|-------------------|
| No credentials in code | PASS - Uses existing .env configuration |
| No direct DB access from frontend | PASS - All uploads via backend API |
| No synchronous ML in API | PASS - Celery tasks queued asynchronously |
| No hardcoded paths | PASS - Location-based paths from database |
| No Unicode in output | PASS - ASCII-only status messages |

### Data Governance Compliance

| Requirement | Compliance Status |
|-------------|-------------------|
| Images: indefinite retention | PASS - Upload system preserves all images |
| Backups: 3-2-1 rule | N/A - Upload feature doesn't change backup strategy |
| No PII in wildlife data | PASS - No user identification in image metadata |
| Camera locations obscured | PASS - Location stored as name, not coordinates |

### Gate Decision: **APPROVED** ✓

All constitution principles and technical standards are satisfied. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/009-bulk-image-upload/
├── spec.md              # Feature specification (/speckit.specify output)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0: Technology research and decisions
├── data-model.md        # Phase 1: Database schema additions
├── quickstart.md        # Phase 1: Developer quickstart guide
├── contracts/           # Phase 1: API contracts (OpenAPI spec)
│   └── upload-api.yaml
├── checklists/          # Quality validation checklists
│   └── requirements.md
└── tasks.md             # Phase 2: Implementation tasks (/speckit.tasks)
```

### Source Code (repository root)

```text
# Web application structure (existing)
backend/
├── src/
│   ├── backend/
│   │   ├── api/
│   │   │   ├── images.py         # [MODIFY] Add bulk upload endpoint
│   │   │   ├── upload.py         # [NEW] Dedicated upload endpoints
│   │   │   └── locations.py      # [EXISTING] Reuse for dropdown
│   │   ├── models/
│   │   │   ├── image.py          # [EXISTING] Image model
│   │   │   ├── upload_batch.py   # [NEW] Upload batch tracking
│   │   │   └── location.py       # [EXISTING] Location model
│   │   ├── services/
│   │   │   ├── upload_service.py # [NEW] Upload orchestration
│   │   │   └── exif_service.py   # [NEW] EXIF extraction
│   │   ├── schemas/
│   │   │   └── upload.py         # [NEW] Upload request/response schemas
│   │   └── app/
│   │       └── main.py           # [MODIFY] Register upload routes
│   └── worker/
│       └── tasks/
│           └── process_images.py  # [EXISTING] Reuse for queuing
├── migrations/
│   └── 011_add_upload_batches.sql # [NEW] Upload batch table
└── tests/
    ├── api/
    │   └── test_upload.py         # [NEW] Upload endpoint tests
    └── services/
        └── test_exif.py           # [NEW] EXIF extraction tests

frontend/
├── src/
│   ├── pages/
│   │   └── Upload.tsx             # [MODIFY] Implement upload UI
│   ├── components/
│   │   ├── UploadZone.tsx         # [NEW] Drag-drop component
│   │   ├── UploadProgress.tsx     # [NEW] Progress tracker
│   │   └── UploadSummary.tsx      # [NEW] Results display
│   ├── api/
│   │   └── upload.ts              # [NEW] Upload API client
│   └── App.tsx                    # [MODIFY] Add Upload route
└── tests/
    └── pages/
        └── Upload.test.tsx         # [NEW] Upload page tests

data/
├── uploads/                        # [NEW] Temporary upload staging
└── exports/                        # [EXISTING] Export storage
```

**Structure Decision**: Web application structure (Option 2 from template). Feature extends existing backend/frontend split with new upload-specific endpoints and UI components. Reuses existing image storage (/mnt/images/), database models (Image, Location), and ML pipeline (Celery tasks).

## Complexity Tracking

> No violations - complexity tracking not required. Feature maintains constitutional compliance.

---

## Phase 0: Research & Technology Decisions

### Research Questions

1. **ZIP Extraction Strategy**: What are best practices for extracting large ZIP archives (500MB+) in Python without memory overflow?
2. **Large File Upload Handling**: How should FastAPI handle 2GB file uploads with progress tracking?
3. **EXIF Parsing Library**: Which Python library provides most reliable EXIF extraction for trail camera images?
4. **Frontend Upload Component**: What are best practices for React drag-and-drop file upload with progress tracking?
5. **Duplicate Detection Strategy**: How should the system detect and handle duplicate image filenames?
6. **Concurrent Upload Handling**: How should the backend handle simultaneous uploads from multiple users without conflicts?

### Technology Research Tasks

- Research Python ZIP extraction libraries (zipfile vs rarfile vs py7zr)
- Research FastAPI streaming upload best practices
- Evaluate EXIF libraries (Pillow, exifread, piexif)
- Research React file upload libraries (react-dropzone, react-uploady)
- Research duplicate file detection strategies (hash-based vs filename-based)
- Research database batch insert performance for 10,000 records

---

## Phase 1: Design Artifacts

### Data Model Design
- `upload_batches` table schema
- Relationship to existing `images` table
- Indexing strategy for upload history queries

### API Contracts
- POST /api/upload/files - Individual file upload
- POST /api/upload/zip - ZIP archive upload
- GET /api/upload/batches - Upload history
- GET /api/upload/batches/{id} - Batch detail with progress
- WebSocket /ws/upload/{batch_id} - Real-time progress updates

### Quickstart Guide
- Developer setup for testing uploads
- How to test with sample images
- How to test ZIP extraction
- How to monitor upload progress

---

## Phase 2: Task Breakdown

Generated by `/speckit.tasks` command (not created by this plan).

Tasks will be prioritized by user story (P1-P5) from spec.md:
1. P1: Individual file upload (MVP)
2. P2: ZIP archive upload
3. P3: EXIF timestamp extraction
4. P4: ML pipeline integration
5. P5: Drag-and-drop interface
