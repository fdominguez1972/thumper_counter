# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT: Thumper Counter (Deer Tracking System Rebuild)

**Rebuild using:** spec-kit + claude-cli  
**Original project:** I:\deer_tracker  
**Purpose:** Learn spec-kit workflow while rebuilding the deer tracking ML pipeline  

## CRITICAL: User Preferences & Working Style

### ASCII-ONLY OUTPUT (HIGHEST PRIORITY)
**ALL output must use ASCII characters only - NO Unicode, emojis, or special characters**

- NO Unicode characters (checkmarks, crosses, arrows, etc.)
- NO Emojis (deer, party, checkmark, etc.)  
- NO Smart quotes (use straight quotes: ' and ")
- NO Special dashes (use regular hyphen: -)
- NO Box-drawing characters

**Allowed for emphasis:**
- Use [OK], [FAIL], [WARN], [INFO] for status indicators
- Use ASCII art with dashes, equals, asterisks for borders
- Use ALL CAPS for important headers

### User Technical Profile
- **Level**: Advanced (independently catches bugs, reviews code)
- **Preferences**: Comprehensive documentation, understands WHY not just WHAT
- **Platform**: Windows 10/11 with Docker Desktop + WSL2
- **Editor**: vi (not nano)
- **Style**: Prefers "turbo mode" (multithreaded operations when possible)
- **Approach**: One-step-at-a-time with approval
- **Learning Goal**: Gain proficiency with spec-kit methodology

### IMPORTANT LESSONS FROM PAST SESSIONS

**Filesystem Issues to Avoid:**
- Always use Filesystem MCP for file creation (not Python pathlib)
- Files created in Docker/WSL may not sync to Windows filesystem
- Always verify file creation with `ls` or `dir` commands
- Use explicit paths with Windows drive letters (I:\) when needed

**Known Issues from deer_tracker build:**
- Filesystem naming conflicts (files getting stuck in virtual filesystem)
- Token waste from trying multiple approaches to file operations
- Use Filesystem:write_file FIRST TIME instead of trying alternatives

## Project Structure (spec-kit driven)

```
thumper_counter/
├── specs/              # spec-kit specifications
│   ├── system.spec     # Overall system architecture
│   ├── ml.spec         # ML pipeline specification
│   ├── api.spec        # Backend API specification
│   └── ui.spec         # Frontend specification
├── src/
│   ├── backend/        # FastAPI application
│   ├── worker/         # Celery + ML processing
│   ├── frontend/       # React dashboard
│   └── models/         # ML model storage
├── docker/
│   ├── docker-compose.yml
│   └── dockerfiles/
├── tests/
├── docs/
├── .env
├── .gitignore
├── README.md
└── CLAUDE.md
```

## Architecture Overview

### Three-Tier Processing Pipeline
The system uses asynchronous processing with clear separation:

1. **API Layer (FastAPI)** - Accepts uploads, serves results
   - Stores images with metadata
   - Queues processing jobs
   - Returns real-time status via WebSocket

2. **Worker Layer (Celery)** - Executes ML pipeline
   - Detection -> Classification -> Re-identification
   - Each stage is a separate Celery task
   - Results stored incrementally for fault tolerance

3. **Data Layer** - Dual storage strategy
   - PostgreSQL: Structured data (deer profiles, detections)
   - Filesystem: Original images and crops
   - Redis: Queue state and caching

### ML Pipeline Flow
```
Image Upload -> Queue -> Detection (YOLOv8) -> Crop Bounding Boxes
                             |
                             v
                    Classification (CNN) -> Sex determination
                             |
                             v
                    Re-ID (ResNet50) -> Match to existing deer OR create new profile
                             |
                             v
                    Update database with sighting
```

### Key Design Decisions

**Why Celery?** Heavy ML processing must not block API responses. Celery provides retry logic, monitoring via Flower, and horizontal scaling.

**Why separate detection/classification/re-id?** Each model has different resource requirements. Separation allows:
- Independent model updates
- Different batch sizes per stage
- Better error isolation

**Why feature vectors in DB?** Re-identification requires comparing new detections against ALL known deer. Storing embeddings in PostgreSQL with pgvector extension enables efficient similarity search.

## Spec-Kit Workflow

### WHY spec-kit?
- **Separation of concerns**: Design decisions separate from implementation
- **Documentation-driven**: Specs become living documentation
- **Iterative refinement**: Easy to modify specs before coding
- **Team collaboration**: Clear contracts between components
- **Testing foundation**: Specs drive test creation

### Our Approach
1. **Define specs first** - Clear understanding before coding
2. **Validate specs** - Ensure completeness and consistency
3. **Generate scaffolding** - Use claude-cli/scripts/generate.py to create boilerplate
4. **Implement incrementally** - One component at a time
5. **Test against specs** - Verify implementation matches design

## Original System Components

### ML Pipeline (to rebuild)
- **Detection**: YOLOv8 for deer detection
- **Classification**: CNN for buck/doe/fawn classification  
- **Re-identification**: ResNet50 for individual tracking
- **GPU acceleration**: NVIDIA CUDA support

### Infrastructure (to rebuild)
- **Backend**: FastAPI (port 8000)
- **Database**: PostgreSQL 15
- **Queue**: Redis + Celery
- **Frontend**: React (port 3000)
- **Monitoring**: Flower (port 5555)

### Data
- **Images**: 40,617 trail camera photos
- **Locations**: 7 camera sites
- **Database**: Deer profiles, detections, sightings

## Development Commands

### Project Initialization
```bash
# Initialize or update git repository
./init-git.sh

# Run project setup (creates .env, installs dependencies)
./setup.sh
```

### Spec-Kit Workflow
```bash
# Generate code from specifications
python3 scripts/generate.py specs/system.spec "Create SQLAlchemy models"
python3 scripts/generate.py specs/ml.spec "Implement YOLOv8 detection service"
python3 scripts/generate.py specs/api.spec "Create FastAPI endpoints for /api/images"

# View specifications
cat specs/system.spec    # System architecture
cat specs/ml.spec        # ML pipeline details
cat specs/api.spec       # API endpoint contracts
cat specs/ui.spec        # Frontend component specs
```

### Docker Operations
```bash
# Use docker-compose (not 'docker compose')
docker-compose up -d                           # Start all services
docker-compose up -d backend worker            # Start specific services
docker-compose logs -f                         # Follow all logs
docker-compose logs -f worker                  # Follow worker logs
docker-compose exec backend python3 script.py  # Run command in container
docker-compose down                            # Stop all services
docker-compose down -v                         # Stop and remove volumes

# Check service status
docker-compose ps

# Rebuild after code changes
docker-compose up -d --build
```

### Python/Development
```bash
# ALWAYS use python3 (not python)
python3 scripts/generate.py <spec> <prompt>
docker-compose exec backend python3 -m pytest
docker-compose exec worker python3 -m celery inspect active

# Install dependencies locally (for IDE support)
pip install -r requirements.txt
```

### Testing
```bash
# Run tests in containers (when implemented)
docker-compose exec backend pytest tests/
docker-compose exec backend pytest tests/api/test_images.py -v
docker-compose exec worker pytest tests/ml/ -v

# Run specific test
docker-compose exec backend pytest tests/api/test_deer.py::test_create_deer
```

### Database Management
```bash
# Access PostgreSQL
docker-compose exec db psql -U deertrack deer_tracking

# Run migrations (when implemented)
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic revision --autogenerate -m "description"

# Database backup
docker-compose exec db pg_dump -U deertrack deer_tracking > backup.sql
```

### Monitoring
```bash
# View Celery tasks (Flower UI at http://localhost:5555)
# View API docs (Swagger at http://localhost:8000/docs)

# Check Redis queue
docker-compose exec redis redis-cli
> LLEN celery
> KEYS *
```

### Git Workflow

**Branching Strategy (Starting Sprint 5):**
- One branch per sprint: 00X-feature-name
- Branch from: previous sprint branch or main
- Merge/close: at end of each sprint
- Example: 003-re-identification (Sprint 5)

**Completed Branches:**
- 002-batch-processing (Sprints 3-4: GPU, batch processing, multi-class)

**Common Commands:**
```bash
# Create new sprint branch
git checkout -b 00X-feature-name

# Commit changes
git add .
git commit -m "feat: implement feature"

# Push to both remotes
git push origin branch-name
git push ubuntu branch-name

# Switch branches
git checkout branch-name
```

## Development Standards

### Status Indicators
- [OK] - Success
- [FAIL] - Error  
- [WARN] - Warning
- [INFO] - Information
- [TODO] - Pending task

### Error Handling
Always include try-catch with clear ASCII messages:
```python
try:
    # operation
except Exception as e:
    print(f"[FAIL] Operation failed: {e}")
```

### Multi-threading
Use parallel processing when appropriate:
```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_function, items)
```

## Session Goals

1. **Learn spec-kit workflow** - Understanding the methodology
2. **Create cleaner architecture** - Modular, maintainable design
3. **Document for GitHub** - Publication-ready documentation
4. **Avoid past issues** - No filesystem sync problems
5. **Build proficiency** - Master claude-cli integration

## Common Development Patterns

### Adding a New API Endpoint
1. Define endpoint contract in `specs/api.spec`
2. Generate boilerplate: `python3 scripts/generate.py specs/api.spec "Create endpoint /api/new"`
3. Implement business logic in `src/backend/services/`
4. Add SQLAlchemy queries in `src/backend/models/`
5. Create tests in `tests/api/test_new.py`
6. Update OpenAPI docs (auto-generated from FastAPI decorators)

### Adding a New ML Model
1. Define model specs in `specs/ml.spec`
2. Create Celery task in `src/worker/tasks/`
3. Add model loading in `src/worker/models/`
4. Update pipeline flow if adding new stage
5. Add GPU memory considerations to docker config
6. Test with sample images before full dataset

### Database Schema Changes
1. Modify model in `src/backend/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration for correctness
4. Test on dev: `alembic upgrade head`
5. Update specs to reflect schema changes
6. Regenerate any affected API endpoints

### Processing Large Image Batches
1. Use Celery canvas for parallelization (group, chain, chord)
2. Batch images in groups of 16 (BATCH_SIZE in .env)
3. Monitor GPU memory via `docker stats`
4. Use Flower UI to track progress: `http://localhost:5555`
5. Implement checkpointing for long-running jobs

## Critical Implementation Notes

### GPU Access in Docker
- Requires NVIDIA Container Toolkit installed
- Docker Compose must include `runtime: nvidia`
- CUDA version must match PyTorch requirements
- Test GPU access: `docker-compose exec worker nvidia-smi`

### Image Path Handling
- Windows paths use backslashes: `I:\path\to\images`
- Container paths use forward slashes: `/mnt/i/path/to/images`
- Use `pathlib.Path` for cross-platform compatibility
- Mount Windows drives in docker-compose: `/mnt/i:/mnt/i`

### Model File Management
- Models stored in `src/models/` directory
- Download from Hugging Face on first run
- Cache to avoid re-downloading (use volumes)
- Large files tracked via Git LFS (when implemented)

## Current Session State (Updated: 2025-11-05)

### Completed Tasks

1. **Database Models** [COMPLETED]
   - Created SQLAlchemy models: Location, Image, Detection, Deer
   - Implemented proper relationships and constraints
   - Added utility methods (increment_image_count, etc.)
   - Files: src/backend/models/*.py

2. **Database Core** [COMPLETED]
   - Database connection setup with pooling
   - Connection testing and initialization
   - Database info utilities
   - File: src/backend/core/database.py

3. **Location API** [COMPLETED]
   - POST /api/locations - Create location
   - GET /api/locations - List all locations
   - GET /api/locations/{id} - Get specific location
   - PUT /api/locations/{id} - Update location
   - DELETE /api/locations/{id} - Delete location
   - Files: src/backend/api/locations.py, src/backend/schemas/location.py

4. **Image Upload API** [COMPLETED]
   - POST /api/images - Batch upload with EXIF extraction
   - GET /api/images - List with filters (location, status, date range, detections)
   - GET /api/images/{id} - Get specific image
   - Location name/ID lookup functionality
   - Timestamp extraction from EXIF and filename
   - Files: src/backend/api/images.py, src/backend/schemas/image.py

5. **Celery Worker Setup** [COMPLETED]
   - Celery app configuration with Redis backend
   - Task routing and queuing setup
   - Model loading infrastructure
   - Detection task implementation (YOLOv8)
   - Files: src/worker/celery_app.py, src/worker/tasks/*.py

6. **ML Models** [COMPLETED]
   - Copied YOLOv8 model from original project
   - Created model testing script
   - Verified detection on sample images
   - Files: src/models/yolov8n_deer.pt, scripts/test_detection.py

7. **Docker Infrastructure** [COMPLETED]
   - Backend container with Pillow installed
   - Worker container with CUDA support
   - PostgreSQL database container
   - Redis container
   - All services operational

### Current System Status

**Running Services:**
- Backend API: http://localhost:8001 [HEALTHY]
- PostgreSQL: localhost:5432 [HEALTHY]
- Redis: localhost:6379 [HEALTHY]
- Worker: Running (processing images)

**Recent Fixes:**
- Fixed PIL import error by rebuilding backend with Pillow 12.0.0
- Backend now successfully handles image uploads with EXIF extraction

### Next Steps (Not Started)

1. **Deer Profile API** - POST/GET/PUT/DELETE endpoints for deer profiles
2. **Detection API** - Endpoints to retrieve and manage detections
3. **Re-ID Model Integration** - ResNet50 for individual deer identification
4. **Sex Classification Model** - CNN for buck/doe/fawn classification
5. **Frontend Dashboard** - React application for viewing results
6. **Batch Processing** - Scripts to process existing 40k+ images
7. **Testing Suite** - pytest tests for all endpoints and services

### Key Files and Locations

**Backend API:**
- src/backend/app/main.py - FastAPI application entry point
- src/backend/api/locations.py - Location endpoints
- src/backend/api/images.py - Image upload endpoints
- src/backend/models/*.py - SQLAlchemy database models
- src/backend/schemas/*.py - Pydantic validation schemas
- src/backend/core/database.py - Database connection management

**Worker:**
- src/worker/celery_app.py - Celery configuration
- src/worker/tasks/process_images.py - Image processing tasks
- src/worker/tasks/detection.py - YOLOv8 detection task

**Models:**
- src/models/yolov8n_deer.pt - YOLOv8 detection model (copied from I:\deer_tracker)

**Configuration:**
- docker-compose.yml - Service orchestration
- .env - Environment variables (DB credentials, paths, etc.)
- requirements.txt - Python dependencies (includes Pillow 12.0.0)

### Important Implementation Details

**Image Upload Flow:**
1. Client uploads image(s) via POST /api/images
2. Backend validates file type and size (max 50MB)
3. EXIF data extracted using PIL/Pillow
4. Timestamp extracted from EXIF → filename → current time (fallback)
5. Location looked up by name or UUID
6. Image saved to /mnt/images/{location_name}/
7. Database record created with metadata
8. Optional: Queue for immediate processing (process_immediately=true)

**EXIF Extraction Strategy:**
- Uses PIL.Image._getexif() to read metadata
- Converts binary values to strings for JSON storage
- Graceful fallback if EXIF data unavailable

**Timestamp Extraction Priority:**
1. EXIF DateTimeOriginal (preferred - from camera)
2. EXIF DateTime
3. EXIF DateTimeDigitized
4. Filename pattern: LOCATION_YYYYMMDD_HHMMSS.jpg
5. Current UTC time (last resort)

### Known Working Endpoints

```bash
# Health check
curl http://localhost:8001/health

# API info
curl http://localhost:8001/

# Create location
curl -X POST http://localhost:8001/api/locations \
  -H "Content-Type: application/json" \
  -d '{"name": "Sanctuary", "description": "Main feeding area"}'

# Upload images
curl -X POST http://localhost:8001/api/images \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=false"

# List images
curl "http://localhost:8001/api/images?location_id=UUID&status=completed&page_size=20"
```

### Database Schema

**Tables Created:**
- locations (id, name, description, coordinates, image_count, etc.)
- images (id, filename, path, timestamp, location_id, exif_data, processing_status, etc.)
- detections (id, image_id, bbox coordinates, confidence, class_id, etc.)
- deer (id, name, sex, species, first_seen, last_seen, sighting_count, etc.)

**Key Relationships:**
- Location -> Images (one-to-many)
- Image -> Detections (one-to-many)
- Deer -> Detections (one-to-many via deer_id)

## Notes

- Always explain WHY we're doing something, not just what
- One step at a time with user approval
- Use ASCII-only output (critical requirement)
- Be aware of filesystem sync issues from past sessions
- Multi-threaded operations when beneficial
- Verify file creation immediately with `ls` or `dir`

## SESSION STATUS - Updated November 8, 2025 (Evening Session)

### Current Sprint: Post-Sprint 8 - Performance Optimization COMPLETE
**Phase:** Infrastructure Optimization & Volume Mount Fix
**Branch:** main
**Next Sprint:** Sprint 9 - Rut Season Analysis & Buck Detection Validation

### Performance Optimization Session (Nov 8, 2025 - Evening)
**Focus:** Critical infrastructure fixes and performance optimization

**Major Issues Resolved:**
1. [CRITICAL FIX] Volume Mount Paths - Changed from Linux paths to Windows paths
   - docker-compose.yml used /mnt/i/ paths (broken on Windows Docker Desktop)
   - Fixed to I:\ format - ALL 35,251 images now accessible
   - This was causing "Image file not found" errors on every image

2. [PERFORMANCE] Worker Concurrency Optimization
   - Tested concurrency: 1 -> 16 -> 64 -> 32 (optimal)
   - Concurrency=64 caused GPU lock contention (18s/task vs 0.7s)
   - Concurrency=32 is sweet spot: 31% GPU util, 840 images/min
   - **13x speed improvement** over initial configuration

3. [DATA VALIDATION] Rut Season Image Verification
   - Created verify_and_queue_rut_season.py script
   - Verified 6,115 rut season images (Sept-Jan) exist on disk
   - Queued 7,000 images for processing
   - Goal: Find mature buck detections from rut season

**Performance Results:**
- Before: "Processing going on for days" (volume mounts broken)
- After: 840 images/min (14/sec), ~22 minutes for remaining 18,409 images
- GPU: RTX 4080 Super at 31% utilization (optimal, no contention)
- VRAM: 3.15GB / 16.4GB (19%)
- Bottleneck: Database writes (70% of time), not GPU

**Files Modified:**
- docker-compose.yml: Windows path format (I:\ instead of /mnt/i/)
- docker/dockerfiles/Dockerfile.worker: concurrency=32
- New: scripts/verify_and_queue_rut_season.py
- New: docs/SESSION_20251108_PERFORMANCE_OPTIMIZATION.md

**Database Status (End of Session):**
- Total: 35,251 images
- Completed: 16,285 (46.2%)
- Pending: 18,409
- Failed: 557
- Processing at: 840 images/min

**Next Actions:**
1. Monitor rut season image processing completion
2. Query for mature buck detections (classification='mature', 'mid', 'young')
3. Analyze buck detection patterns by season
4. Validate model performance on rut season images

---

### Previous Session: Sprint 8 - COMPLETE
**Phase:** Detection Correction & Multi-Species Classification
**Branch:** main (merged)

### Sprint 8 Completed (Nov 8, 2025)
**Focus:** Manual correction system and multi-species wildlife tracking

**Completed Features:**
- [OK] Detection correction system (single and batch editing)
- [OK] Backend: PATCH /api/detections/{id}/correct (single correction)
- [OK] Backend: PATCH /api/detections/batch/correct (up to 1000 detections)
- [OK] Frontend: DetectionCorrectionDialog.tsx (199 lines, single image review)
- [OK] Frontend: BatchCorrectionDialog.tsx (183 lines, multi-image review)
- [OK] Frontend: DeerImages.tsx (415 lines, image browser with multi-select)
- [OK] Multi-species classification expanded (7 classes: 4 deer + 3 non-deer)
- [OK] Species statistics API: GET /api/deer/stats/species
- [OK] Image filtering by classification: GET /api/images?classification=X
- [OK] Database migration: 009_add_detection_corrections.sql
- [OK] Feral hog dedicated counter in population statistics

**Results:**
- Detection correction workflow: 100% functional
- Multi-species support: buck, doe, fawn, unknown, cattle, pig, raccoon
- Batch editing: Up to 1000 detections per batch
- All features tested and verified working
- Documentation: docs/SESSION_20251108_HANDOFF.md (comprehensive session handoff)

**Current System Statistics:**
- Total images: 35,251
- Images processed: ~1,200 (3.4%)
- Total detections: 37,522
- Deer profiles: 14
- Species breakdown:
  - Deer: 37,514 (99.98%)
  - Cattle: 8
  - Feral Hogs: 0
  - Raccoons: 0

### Sprint 3 Completed (Nov 6, 2025)
- [OK] GPU acceleration enabled (10x faster: 0.04s vs 0.4s per image)
- [OK] CUDA fork issue resolved (threads pool + thread-safe model loading)
- [OK] Batch processing API operational (POST /api/processing/batch)
- [OK] Processing status monitoring (GET /api/processing/status)
- [OK] Tested with 1000+ image batches successfully
- [OK] Deer management API complete (full CRUD operations)
- [OK] Database schema enhanced (status, species, notes, timestamps)
- [OK] All enum issues resolved (lowercase values with values_callable)

### Sprint 3 Issues Resolved
1. [FIXED] CUDA fork error - Changed from prefork to threads pool (concurrency=1)
2. [FIXED] Thread-safe model loading - Double-checked locking pattern
3. [FIXED] DeerSex enum values - Recreated with lowercase (buck, doe, fawn, unknown)
4. [FIXED] DeerStatus enum values - Verified lowercase (alive, deceased, unknown)
5. [FIXED] feature_vector NOT NULL - Made nullable for manual profiles
6. [FIXED] Celery integration - Added celery_app to main.py

### Sprint 3 Features
**Batch Processing** (src/backend/api/processing.py):
- POST /api/processing/batch - Queue 1-10000 images
- GET /api/processing/status - Real-time stats with completion rate

**Deer Management** (src/backend/api/deer.py):
- Full CRUD API with filtering, pagination, sorting
- Manual deer profile creation (name, sex, species, notes, status)

### Sprint 4 Complete (Nov 6-7, 2025)
**Focus:** Multi-class YOLOv8 model training for sex/age classification

**Completed:**
- [OK] Dataset selection: Roboflow Whitetail Deer v46 (15,574 images, 11 classes)
- [OK] Dataset verification: 5 deer classes (doe, fawn, mature, mid, young)
- [OK] Training infrastructure: Docker volume mount for /mnt/training_data
- [OK] Configuration: YOLOv8n, batch=32, epochs=200, patience=20
- [OK] GPU memory test: Batch 32 fits comfortably (uses ~4GB of 16GB available)
- [OK] Training started: Nov 7, 03:06 UTC

**Training Results:**
```
Overall (Test Set - 347 images):
  mAP50:     0.804
  mAP50-95:  0.620
  Precision: 0.896
  Recall:    0.701

Deer Classes (mAP50):
  doe (female):    0.769
  fawn (unknown):  0.796
  mature (male):   0.673
  mid (male):      0.581
  young (male):    0.676
```

**Pipeline Verification (Real-World):**
```
Recent 21 detections:
  doe (female):   19 detections (90.5%)
  fawn (unknown):  1 detection  (4.8%)
  young (male):    1 detection  (4.8%)

Average Confidence:
  doe:   0.72
  fawn:  0.51
  young: 0.51
```

**Class Mapping:**
- Class 3 (doe) -> Female
- Class 4 (fawn) -> Unknown sex (too young)
- Class 5 (mature) -> Male (mature buck)
- Class 6 (mid) -> Male (mid-age buck)
- Class 10 (young) -> Male (young buck)

**Key Files:**
- Model: src/models/runs/deer_multiclass/weights/best.pt
- Dataset config: src/models/training_data/deer_multiclass.yaml
- Training script: scripts/train_deer_multiclass.py
- Evaluation script: scripts/evaluate_multiclass_model.py
- Summary doc: docs/SPRINT_4_SUMMARY.md

**Next Sprint (5 of 6):**
1. Re-identification engine (ResNet50 feature extraction)
2. Automatic deer profile creation
3. Sex/age aggregation logic
4. Vector similarity search (pgvector)

### Quick Commands
```bash
# Start everything
docker-compose up -d

# Check health
curl http://localhost:8001/health

# Test detection pipeline
curl -X POST http://localhost:8001/api/images \
  -F "files=@test.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=true"

# Monitor worker
docker-compose logs -f worker | grep "Detection complete"

# Check processing stats
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"
```

### Performance Achieved (GPU Mode - Sprint 3)
- GPU: RTX 4080 Super (16GB VRAM)
- Detection speed: 0.04-0.05s per image (10x faster than CPU)
- GPU throughput: 20-25 images/second (GPU inference only)
- Real-world throughput: 1.2 images/second (including DB writes)
- Bottleneck: Database writes (70% of time), not GPU
- Model: YOLOv8n (21.5MB), threads pool, concurrency=1
- Database: 35,251 images total, 1,108+ completed (3.14%)
- Estimated time for full dataset: ~8 hours

### Performance Comparison
| Mode | Speed/Image | Throughput | Full Dataset |
|------|-------------|------------|--------------|
| CPU  | 0.4s        | 150/min    | ~4 hours     |
| GPU  | 0.04s       | 1.2/sec    | ~8 hours     |

Note: Real-world slower than GPU capability due to DB write bottleneck.

### File Paths
- Project: I:\projects\thumper_counter
- Images: I:\Hopkins_Ranch_Trail_Cam_Pics (mounted as /mnt/images in containers)
- Models: src/models/yolov8n_deer.pt (22MB)
- Branch: main (current)
- Remotes: origin (GitHub), ubuntu (local)

**IMPORTANT:** Docker volume mounts must use Windows path format (I:\) not Linux format (/mnt/i/)

## SESSION STATUS - Updated November 6, 2025

### Current Sprint: 6 of 6 - COMPLETE
**Phase:** Sprint 6 Complete - Pipeline Integration & API Enhancements
**Branch:** 004-pipeline-integration

### Sprint 6 Completed (Nov 6, 2025)
- [OK] Integrated re-ID into detection pipeline (automatic chaining)
- [OK] Batch re-ID processing script (batch_reidentify.py)
- [OK] Processed 313 detections, created 14 deer profiles
- [OK] API endpoint: GET /api/deer/{id}/timeline (activity patterns)
- [OK] API endpoint: GET /api/deer/{id}/locations (movement patterns)
- [OK] Fixed detection ID collection (flush before collecting)
- [OK] Documentation: docs/SPRINT_6_SUMMARY.md

### Sprint 6 Technical Details
**Pipeline Integration:**
- Detection task auto-queues re-ID for each deer detection
- Fully automated: Image → Detection → Re-ID → Deer Profile
- Performance: 0.05s detection + 2s re-ID = 2.05s total per image

**Batch Processing:**
- Script: scripts/batch_reidentify.py
- Filters: bbox >= 50x50, deer classes only, unassigned deer_id
- Queuing speed: 0.11s for 100 tasks
- Throughput: 30-50 detections/minute

**Analysis APIs:**
- Timeline: Group sightings by hour/day/week/month
- Locations: Movement patterns across camera sites
- Response time: 15-50ms (indexed joins)
- Use cases: Activity patterns, territory mapping, re-ID validation

**Database Status:**
- Total images: 35,251
- Images processed: ~1,200 (3.4%)
- Total detections: 29,735
- Detections with deer_id: 13
- Deer profiles: 14 (11 with feature vectors)

**Key Files:**
- src/worker/tasks/detection.py: Auto-chain re-ID (modified)
- src/backend/api/deer.py: Timeline/locations endpoints (modified)
- scripts/batch_reidentify.py: Batch processing (new)
- docs/SPRINT_6_SUMMARY.md: Complete documentation (new)

### Sprint 5 Completed (Nov 6, 2025)
**Branch:** 003-re-identification
- [OK] pgvector extension enabled in PostgreSQL (ankane/pgvector:v0.5.1)
- [OK] Deer model updated with vector(512) column for embeddings
- [OK] ResNet50 feature extraction implemented (512-dim embeddings)
- [OK] Thread-safe model loading (singleton with double-checked locking)
- [OK] Cosine similarity search with pgvector HNSW index
- [OK] Sex-based filtering for improved matching accuracy
- [OK] Automatic deer profile creation when no match found
- [OK] Re-identification pipeline tested successfully
- [OK] Database migration documented (migrations/005_migrate_to_pgvector.sql)

### Sprint 5 Technical Details
**Re-Identification Architecture:**
- Model: ResNet50 pretrained on ImageNet
- Output: 512-dim embeddings (reduced from 2048 via linear layer)
- Normalization: L2 normalization for cosine similarity
- Similarity metric: Cosine distance (1 - cosine similarity)
- Matching threshold: 0.85 (conservative to avoid false matches)
- Search: pgvector HNSW index for O(log N) query performance
- Sex filtering: Match only within same sex category

**Performance (First Test):**
- Feature extraction: 0.88s total
- ResNet50 model loading: ~2-3s (first time, then cached)
- Feature vector: 512 dimensions, L2 normalized
- Database: Created first deer profile successfully
- GPU: CUDA enabled for ResNet50 inference

**Key Files:**
- Task: src/worker/tasks/reidentification.py (556 lines)
- Model: ResNet50 (torchvision.models.resnet50)
- Migration: migrations/005_migrate_to_pgvector.sql
- Test script: scripts/test_reidentification.py

### Sprint 4 Completed (Nov 6, 2025)
- [OK] Multi-class deer model trained (YOLOv8n, 5 classes)
- [OK] Model evaluation: mAP50=0.711, mAP50-95=0.461
- [OK] Classes: doe/fawn/mature/mid/young
- [OK] Sex mapping: doe=female, fawn=unknown, mature/mid/young=male
- [OK] Real-world validation: 90.5% doe, 4.8% fawn, 4.8% young (21 images)
- [OK] Model integrated into detection pipeline
- [OK] Documentation: docs/SPRINT_4_SUMMARY.md

### Sprint 3 Completed (Nov 6, 2025)
- [OK] GPU acceleration enabled (10x faster: 0.04s vs 0.4s per image)
- [OK] CUDA fork issue resolved (threads pool + thread-safe model loading)
- [OK] Batch processing API operational (POST /api/processing/batch)
- [OK] Processing status monitoring (GET /api/processing/status)
- [OK] Tested with 1000+ image batches successfully
- [OK] Deer management API complete (full CRUD operations)
- [OK] Database schema enhanced (status, species, notes, timestamps)
- [OK] All enum issues resolved (lowercase values with values_callable)

### Sprint 3 Issues Resolved
1. [FIXED] CUDA fork error - Changed from prefork to threads pool (concurrency=1)
2. [FIXED] Thread-safe model loading - Double-checked locking pattern
3. [FIXED] DeerSex enum values - Recreated with lowercase (buck, doe, fawn, unknown)
4. [FIXED] DeerStatus enum values - Verified lowercase (alive, deceased, unknown)
5. [FIXED] feature_vector NOT NULL - Made nullable for manual profiles
6. [FIXED] Celery integration - Added celery_app to main.py

### Sprint 3 Features
**Batch Processing** (src/backend/api/processing.py):
- POST /api/processing/batch - Queue 1-10000 images
- GET /api/processing/status - Real-time stats with completion rate

**Deer Management** (src/backend/api/deer.py):
- Full CRUD API with filtering, pagination, sorting
- Manual deer profile creation (name, sex, species, notes, status)

### Sprint 4 Complete (Nov 6-7, 2025)
**Focus:** Multi-class YOLOv8 model training for sex/age classification

**Completed:**
- [OK] Dataset selection: Roboflow Whitetail Deer v46 (15,574 images, 11 classes)
- [OK] Dataset verification: 5 deer classes (doe, fawn, mature, mid, young)
- [OK] Training infrastructure: Docker volume mount for /mnt/training_data
- [OK] Configuration: YOLOv8n, batch=32, epochs=200, patience=20
- [OK] GPU memory test: Batch 32 fits comfortably (uses ~4GB of 16GB available)
- [OK] Training started: Nov 7, 03:06 UTC

**Training Results:**
```
Overall (Test Set - 347 images):
  mAP50:     0.804
  mAP50-95:  0.620
  Precision: 0.896
  Recall:    0.701

Deer Classes (mAP50):
  doe (female):    0.769
  fawn (unknown):  0.796
  mature (male):   0.673
  mid (male):      0.581
  young (male):    0.676
```

**Pipeline Verification (Real-World):**
```
Recent 21 detections:
  doe (female):   19 detections (90.5%)
  fawn (unknown):  1 detection  (4.8%)
  young (male):    1 detection  (4.8%)

Average Confidence:
  doe:   0.72
  fawn:  0.51
  young: 0.51
```

**Class Mapping:**
- Class 3 (doe) -> Female
- Class 4 (fawn) -> Unknown sex (too young)
- Class 5 (mature) -> Male (mature buck)
- Class 6 (mid) -> Male (mid-age buck)
- Class 10 (young) -> Male (young buck)

**Key Files:**
- Model: src/models/runs/deer_multiclass/weights/best.pt
- Dataset config: src/models/training_data/deer_multiclass.yaml
- Training script: scripts/train_deer_multiclass.py
- Evaluation script: scripts/evaluate_multiclass_model.py
- Summary doc: docs/SPRINT_4_SUMMARY.md

**Next Sprint (5 of 6):**
1. Re-identification engine (ResNet50 feature extraction)
2. Automatic deer profile creation
3. Sex/age aggregation logic
4. Vector similarity search (pgvector)

### Quick Commands
```bash
# Start everything
docker-compose up -d

# Check health
curl http://localhost:8001/health

# Test detection pipeline
curl -X POST http://localhost:8001/api/images \
  -F "files=@test.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=true"

# Monitor worker
docker-compose logs -f worker | grep "Detection complete"

# Check processing stats
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"
```

### Performance Achieved (GPU Mode - Sprint 3)
- GPU: RTX 4080 Super (16GB VRAM)
- Detection speed: 0.04-0.05s per image (10x faster than CPU)
- GPU throughput: 20-25 images/second (GPU inference only)
- Real-world throughput: 1.2 images/second (including DB writes)
- Bottleneck: Database writes (70% of time), not GPU
- Model: YOLOv8n (21.5MB), threads pool, concurrency=1
- Database: 35,251 images total, 1,108+ completed (3.14%)
- Estimated time for full dataset: ~8 hours

### Performance Comparison
| Mode | Speed/Image | Throughput | Full Dataset |
|------|-------------|------------|--------------|
| CPU  | 0.4s        | 150/min    | ~4 hours     |
| GPU  | 0.04s       | 1.2/sec    | ~8 hours     |

Note: Real-world slower than GPU capability due to DB write bottleneck.

### File Paths
- Project: /mnt/i/projects/thumper_counter
- Images: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics
- Models: src/models/yolov8n_deer.pt (22MB)
- Branch: 003-re-identification (current, Sprint 5)
- Remotes: origin (GitHub), ubuntu (local)
## SPRINT 10: Frontend Dashboard (NEXT)

### Planning Documents Created (Nov 7, 2025)
- [NEW] docs/FRONTEND_REQUIREMENTS.md - Comprehensive frontend specification
- [NEW] docs/SPRINT_10_PLAN.md - Detailed sprint plan with task breakdown

### Frontend Goals
1. Dashboard with population metrics (clickable cards)
2. Deer Gallery (browse individual deer profiles)
3. Deer Profile detail page (timeline, locations, image gallery)
4. Image Upload interface (files + ZIP archives, location selection)
5. Image Browser (detection overlays, filtering)
6. Location management (CRUD operations)

### Technology Stack
- React 18+ with TypeScript
- Material-UI (MUI) for components
- React Query for API integration
- Recharts for visualizations
- Vite for build tooling

### Key Features
- Real-time processing queue status
- Clickable metric cards navigating to filtered views
- Sex/age breakdown visualization (bucks: young/mid/mature)
- Detection bounding box overlays
- Activity timeline charts
- Location movement patterns

### API Enhancements Needed
- GET /api/stats/dashboard - Dashboard metrics
- GET /api/stats/population - Population breakdown
- Existing endpoints already support all filtering needs

### Next Steps
1. Review frontend requirements with user
2. Create branch: 006-frontend-dashboard
3. Begin Task 1: Project setup and configuration
4. Implement pages incrementally (Dashboard -> Gallery -> Upload -> Browser)

### Current System State
- Backend: Fully operational (http://localhost:8001)
- Database: 35,251 images, 29,735 detections, 14 deer profiles
- ML Pipeline: 13.5 images/second throughput
- Frontend: Basic scaffold exists, ready for rebuild


## SPRINT 10: Frontend Dashboard (NEXT - November 7, 2025)

### Planning Documents Created
- docs/FRONTEND_REQUIREMENTS.md - Comprehensive frontend specification
- docs/SPRINT_10_PLAN.md - Detailed sprint plan with task breakdown
- front_end_thoughts.txt - User requirements (converted to formal specs)

### Sprint 9 Summary (COMPLETED November 7, 2025)
**Focus:** Re-ID GPU Optimization and Performance Investigation

**Key Findings:**
- Re-ID was already on GPU since Sprint 5 (not a bottleneck)
- Actual Re-ID inference: 5.57ms per image (GPU) or 0.46ms (batch mode)
- Perceived "2s bottleneck" was full pipeline (image I/O + DB + Re-ID combined)
- Burst optimization provides 98% hit rate (reuses deer_id for photo bursts)
- System throughput: 13.5 images/second (bottleneck is image I/O, not GPU)

**Optimizations Implemented:**
- Enabled cuDNN auto-tuning (8-12% improvement)
- Implemented batch feature extraction function (12x speedup)
- Created benchmark tool (scripts/benchmark_reid.py)

**Documentation:** docs/SPRINT_9_REID_GPU.md

### Frontend Requirements Summary

**Dashboard Page:**
- Population metrics with clickable cards
- Total Deer (unique Re-ID profiles)
- Total Sightings (all detections)
- Buck count with age breakdown (young/mid/mature)
- Does vs Bucks population chart
- Buck age distribution chart
- Cards navigate to filtered Deer Gallery views

**Deer Gallery:**
- Grid of individual deer profile cards
- Filters: sex, age class, location, activity
- Sort: most seen, recently seen, first discovered, alphabetical
- Search by name or UUID
- Click card to view detailed profile

**Deer Profile Detail:**
- Primary photo with thumbnail gallery
- Editable: name, status, notes
- Metrics: sightings, first/last seen, favorite location
- Image gallery: all detection crops for this deer
- Activity timeline: sightings over time (hour/day/week/month grouping)
- Location movement: locations visited with visit counts
- Delete profile option

**Image Upload:**
- Drag-drop or file browser
- Support: individual images, multiple files, ZIP archives
- Location dropdown selection (required)
- "Process Immediately" checkbox
- Progress tracking during upload
- OCR pipeline (FUTURE - Sprint 11): Extract metadata from trail camera footer

**Image Browser:**
- Grid of uploaded images with thumbnails
- Detection count badges
- Filters: location, date range, processing status, has detections, sex/class
- Sort: newest, oldest, most detections
- Click image opens lightbox with:
  - Full-resolution display
  - Detection bounding boxes overlay (toggle on/off)
  - Box labels: sex/class, confidence, deer name
  - Click box to navigate to deer profile
  - Metadata panel

**Location Management:**
- List of camera locations
- Add/edit/delete locations
- View images per location
- Map view (FUTURE if coordinates available)

### Technology Stack

**Frontend:**
- React 18+ with TypeScript
- Vite (build tool)
- Material-UI (MUI) for components
- React Router for navigation
- React Query for API calls and caching
- Recharts for visualizations
- Axios for HTTP client
- Port: 3000 (Docker container: thumper_frontend)

**Backend APIs to Integrate:**
- GET /api/deer - List deer profiles
- GET /api/deer/{id} - Deer detail
- GET /api/deer/{id}/timeline - Activity timeline
- GET /api/deer/{id}/locations - Movement patterns
- POST /api/deer, PUT /api/deer/{id}, DELETE /api/deer/{id}
- GET /api/images - List images with filters
- GET /api/images/{id} - Image detail
- POST /api/images - Upload images
- GET /api/locations, POST /api/locations, PUT /api/locations/{id}, DELETE /api/locations/{id}
- GET /api/processing/status - Queue status
- POST /api/processing/batch - Queue batch processing

**New Endpoints to Create:**
- GET /api/stats/dashboard - Dashboard metrics
- GET /api/stats/population - Population breakdown by sex/age

### Sprint 10 Task Breakdown

**Task 1:** Project Setup (2 hours)
- Install dependencies (MUI, React Query, Recharts, etc.)
- Configure Vite, TypeScript, routing
- Create directory structure

**Task 2:** Dashboard Page (6 hours)
- MetricCard component (clickable with navigation)
- 5 metric cards with real data
- Recent activity feed
- Processing queue status (real-time polling)
- Location status list

**Task 3:** Deer Gallery (5 hours)
- DeerCard component
- Grid layout with filters and sort
- Pagination
- Search functionality

**Task 4:** Deer Profile Detail (7 hours)
- Profile header with editable fields
- Metrics display
- Image gallery for this deer
- Activity timeline chart
- Location movement analysis

**Task 5:** Image Upload (6 hours)
- Drag-drop upload zone
- File list with previews
- Location dropdown
- Upload progress tracking
- Results display

**Task 6:** Image Browser (6 hours)
- Image grid with lazy loading
- Lightbox viewer with detection overlays
- Bounding box rendering (Canvas or SVG)
- Filters and pagination

**Task 7:** Location Management (4 hours)
- Location list/table
- Add/edit/delete modals
- Form validation

**Task 8:** Backend Stats Endpoints (3 hours)
- Create /api/stats/dashboard
- Create /api/stats/population
- Implement caching

**Task 9:** Testing & Polish (4 hours)
- Manual testing with real data
- Edge case handling
- Responsive design
- Performance optimization
- Documentation

**Total Estimated Time:** 43 hours (2-3 weeks)

### Success Criteria (Sprint 10)
- [ ] All 6 pages functional and accessible
- [ ] Dashboard displays accurate population metrics
- [ ] All metric cards clickable with correct navigation
- [ ] Deer Gallery filtering and sorting works
- [ ] Deer Profile shows complete history and timeline
- [ ] Image Upload accepts files/archives with location selection
- [ ] Image Browser displays detections with bounding box overlays
- [ ] Locations CRUD operations working
- [ ] Real-time processing status updates
- [ ] Responsive design (desktop + tablet)
- [ ] ASCII-only text throughout (no emojis/Unicode)
- [ ] No console errors in production build
- [ ] Page load time < 2 seconds

### Current System State (Post-Sprint 9)
- Backend API: Operational at http://localhost:8001
- Database: 35,251 images, 29,735 detections, 14 deer profiles
- ML Pipeline: YOLOv8 detection (0.04s) + ResNet50 Re-ID (5.57ms)
- System Throughput: 13.5 images/second end-to-end
- GPU: RTX 4080 Super (16GB VRAM), CUDA enabled, cuDNN optimized
- Frontend: Basic scaffold exists on port 3000, ready for rebuild

### Branch Strategy
- Current: main
- Next: Create 006-frontend-dashboard for Sprint 10 work
- Merge to main after Sprint 10 completion

### Next Steps
1. User review of frontend requirements and Sprint 10 plan
2. Create new branch: 006-frontend-dashboard
3. Begin Task 1: Project setup and configuration
4. Implement pages incrementally with user approval at each stage


## SESSION STATUS - Updated November 7, 2025

### Current Sprint: 10 of 10 - COMPLETE
**Phase:** Sprint 10 Complete - Frontend Dashboard (Material-UI Migration)
**Branch:** main (006-frontend-dashboard merged)

### Sprint 10 Completed (Nov 7, 2025)
- [OK] Complete Tailwind to Material-UI v5 migration
- [OK] Custom theme with earth-tone colors (olive green, saddle brown)
- [OK] React Query v5 setup with optimal caching
- [OK] Dashboard page with clickable stat cards
- [OK] Deer Gallery with filters and responsive grid
- [OK] Deer Detail page with timeline and location analysis
- [OK] Placeholder pages for Upload, Images, Locations
- [OK] Responsive design (xs/sm/md/lg breakpoints)
- [OK] Zero build errors, production-ready

### Sprint 10 Technical Details
**Material-UI Integration:**
- Theme: frontend/src/theme/index.ts (earth-tone palette)
- React Query: frontend/src/api/queryClient.ts (5min cache)
- Types: frontend/src/types/index.ts (comprehensive API types)
- Layout: MUI AppBar + Drawer with responsive mobile menu

**Pages Completed:**
- Dashboard: Stat cards, population bars, recent deer list
- Deer Gallery: Filters, sort, responsive grid, sex badges
- Deer Detail: Stats, timeline chart (Recharts), location patterns
- Placeholders: Upload, Images, Locations (MUI cards with feature lists)

**Key Changes:**
- +4,461 lines added (MUI components, theme, types)
- -498 lines removed (Tailwind classes)
- 15 files modified
- 5 commits pushed to main
- Bundle: 865KB (gzipped: 257KB)

**Documentation:**
- docs/SPRINT_10_SUMMARY.md: Complete sprint documentation
- docs/SPRINT_10_PLAN.md: Original task planning
- docs/FRONTEND_REQUIREMENTS.md: MUI component specifications

### Database Status (Sprint 10 End)
- Total images: 35,251
- Completed: 12,533 (35.55%)
- Pending: 22,718
- Failed: 0
- Deer profiles: 14
- Background processing: Active (continuous_queue.sh)

### Quick Commands
```bash
# Start everything
docker-compose up -d

# View frontend
http://localhost:3000

# Build frontend
docker-compose exec frontend npm run build

# Check processing
curl http://localhost:8001/api/processing/status

# View backend docs
http://localhost:8001/docs
```

### Frontend Stack
- React 18 + TypeScript
- Material-UI v5 (complete migration)
- React Query v5 (API state management)
- React Router v6 (navigation)
- Recharts (timeline visualization)
- Vite (build tool)

### Backend Endpoints (Sprint 6)
- GET /api/deer - List with filters
- GET /api/deer/{id} - Detail
- GET /api/deer/{id}/timeline - Activity patterns
- GET /api/deer/{id}/locations - Movement analysis
- POST /api/processing/batch - Queue images
- GET /api/processing/status - Real-time stats

### File Paths
- Project: /mnt/i/projects/thumper_counter
- Images: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics
- Frontend: http://localhost:3000
- Backend: http://localhost:8001
- Branch: main
- Remotes: origin (GitHub), ubuntu (local)
