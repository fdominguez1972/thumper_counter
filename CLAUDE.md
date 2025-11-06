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
```bash
git add .
git commit -m "feat: implement deer detection pipeline"
git push origin main
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

## SESSION STATUS - Updated November 5, 2025

### Current Sprint: 3 of 6
**Phase:** Sprint 2 Complete - Phase 1 MVP Complete
**Focus:** GPU enablement + Batch processing

### Sprint 2 Completed (Nov 5, 2025)
- [OK] Phase 1 MVP detection pipeline end-to-end
- [OK] YOLOv8 detection integrated with database
- [OK] Celery task queue operational
- [OK] Backend/Worker integration via send_task()
- [OK] Processing status tracking (pending -> processing -> completed)
- [OK] End-to-end test: 1 deer @ 87% confidence in 0.4s
- [OK] All major blockers resolved (4 issues fixed)

### Sprint 2 Issues Resolved
1. [FIXED] Backend Pillow dependency - Added to requirements.txt
2. [FIXED] Backend/Worker Celery imports - Used send_task() method
3. [FIXED] PYTHONPATH mismatch - Unified to /app/src
4. [FIXED] SQLAlchemy enum values - Added values_callable
5. [TEMP] CUDA multiprocessing - Disabled GPU, using CPU mode

### Next Session Tasks (Sprint 3)
1. Enable GPU support (fix CUDA multiprocessing issue)
2. Create batch processing endpoint (POST /api/processing/batch)
3. Add progress monitoring (GET /api/processing/status)
4. Process test batch of 1000 images
5. Deer management API (POST/GET/PUT/DELETE /api/deer)

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

### Performance Baseline (CPU Mode)
- Detection speed: 0.4s per image
- Throughput: ~150 images/minute
- Model: YOLOv8n (21.5MB)
- Accuracy: 87% average confidence
- Database: 35,234+ images ready for batch processing

### Performance Target (GPU Mode - Sprint 3)
- Detection speed: 0.05s per image (8x faster)
- Throughput: ~1200 images/minute
- Batch: 1000 images in <1 minute
- Full dataset: ~30 minutes (vs 4 hours CPU)

### File Paths
- Project: /mnt/i/projects/thumper_counter
- Images: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics
- Models: src/models/yolov8n_deer.pt (22MB)
- Branch: 001-detection-pipeline (feature branch)
- Remotes: origin (GitHub), ubuntu (local)

## SESSION STATUS - Updated November 5, 2025

### Current Sprint: 3 of 6
**Phase:** Sprint 2 Complete - Phase 1 MVP Complete
**Focus:** GPU enablement + Batch processing

### Sprint 2 Completed (Nov 5, 2025)
- [OK] Phase 1 MVP detection pipeline end-to-end
- [OK] YOLOv8 detection integrated with database
- [OK] Celery task queue operational
- [OK] Backend/Worker integration via send_task()
- [OK] Processing status tracking (pending -> processing -> completed)
- [OK] End-to-end test: 1 deer @ 87% confidence in 0.4s
- [OK] All major blockers resolved (4 issues fixed)

### Sprint 2 Issues Resolved
1. [FIXED] Backend Pillow dependency - Added to requirements.txt
2. [FIXED] Backend/Worker Celery imports - Used send_task() method
3. [FIXED] PYTHONPATH mismatch - Unified to /app/src
4. [FIXED] SQLAlchemy enum values - Added values_callable
5. [TEMP] CUDA multiprocessing - Disabled GPU, using CPU mode

### Next Session Tasks (Sprint 3)
1. Enable GPU support (fix CUDA multiprocessing issue)
2. Create batch processing endpoint (POST /api/processing/batch)
3. Add progress monitoring (GET /api/processing/status)
4. Process test batch of 1000 images
5. Deer management API (POST/GET/PUT/DELETE /api/deer)

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

### Performance Baseline (CPU Mode)
- Detection speed: 0.4s per image
- Throughput: ~150 images/minute
- Model: YOLOv8n (21.5MB)
- Accuracy: 87% average confidence
- Database: 35,234+ images ready for batch processing

### Performance Target (GPU Mode - Sprint 3)
- Detection speed: 0.05s per image (8x faster)
- Throughput: ~1200 images/minute
- Batch: 1000 images in <1 minute
- Full dataset: ~30 minutes (vs 4 hours CPU)

### File Paths
- Project: /mnt/i/projects/thumper_counter
- Images: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics
- Models: src/models/yolov8n_deer.pt (22MB)
- Branch: 001-detection-pipeline (feature branch)
- Remotes: origin (GitHub), ubuntu (local)
