# Thumper Counter - Deer Tracking System

**Automated trail camera analysis system for wildlife monitoring at Hopkins Ranch**

[![Phase](https://img.shields.io/badge/Phase-1%20MVP%20Complete-success)](https://github.com/fdominguez1972/thumper_counter)
[![Pipeline](https://img.shields.io/badge/Detection-87%25%20Confidence-blue)](https://github.com/fdominguez1972/thumper_counter)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://github.com/fdominguez1972/thumper_counter)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://github.com/fdominguez1972/thumper_counter)

> **Status:** Phase 1 MVP complete (55% overall). YOLOv8 detection pipeline operational with end-to-end database integration. Currently detecting deer at 87% confidence in 0.4s per image (CPU mode).

## Overview

Thumper Counter automatically processes trail camera images to detect, classify, and track individual deer across time. Built using a spec-driven methodology with Docker containerization and ML pipeline optimization.

**Current Capabilities:**
- ✅ Upload images via REST API with EXIF extraction
- ✅ YOLOv8 deer detection with bounding boxes
- ✅ Database storage with processing status tracking
- ✅ Celery task queue with Redis backend
- ⏳ Batch processing (Phase 2)
- ⏳ Sex classification (Phase 3)
- ⏳ Individual re-identification (Phase 3)
- ⏳ React frontend dashboard (Phase 4)

**Dataset:** 35,234+ images from 7 camera locations at Hopkins Ranch, Texas

## Quick Start

### Prerequisites

- Docker Desktop with Docker Compose
- 8GB+ RAM recommended
- (Optional) NVIDIA GPU for faster processing

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/fdominguez1972/thumper_counter.git
cd thumper_counter

# Copy environment template
cp .env.example .env
# Edit .env with your settings (database passwords, paths, etc.)

# Create required directories
mkdir -p data/uploads
```

### 2. Start Services

```bash
# Start all services (backend, worker, database, redis)
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### 3. Verify System Health

```bash
# Check API health
curl http://localhost:8001/health

# Expected response:
# {"status":"healthy","timestamp":"...","service":"thumper_counter_api",...}

# Check worker is ready
docker-compose logs worker | grep "celery@.*ready"
```

### 4. Upload Your First Image

```bash
# Upload an image for detection
curl -X POST http://localhost:8001/api/images \
  -F "files=@/path/to/your/image.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=true"

# Check processing status
curl http://localhost:8001/api/images?status=completed
```

### 5. View Results

```bash
# Access API documentation
open http://localhost:8001/docs

# View detections in database
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT i.filename, d.confidence, d.bbox
   FROM detections d
   JOIN images i ON d.image_id = i.id
   LIMIT 10;"
```

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   FastAPI   │─────▶│    Redis     │◀─────│   Celery    │
│   Backend   │      │    Queue     │      │   Worker    │
│  (Port 8001)│      └──────────────┘      │  (YOLOv8)   │
└─────┬───────┘                            └──────┬──────┘
      │                                           │
      │         ┌──────────────────┐             │
      └────────▶│   PostgreSQL     │◀────────────┘
                │    Database      │
                └──────────────────┘
```

**Components:**
- **Backend** (FastAPI): REST API for image upload, queries, processing control
- **Worker** (Celery): Asynchronous ML processing with YOLOv8
- **Database** (PostgreSQL): Image metadata, detections, deer profiles
- **Queue** (Redis): Task distribution and result caching

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI 0.104+ | REST endpoints, async support |
| **Database** | PostgreSQL 15 | Structured data storage |
| **Queue** | Redis 7 + Celery 5 | Async task processing |
| **Detection** | YOLOv8n (Ultralytics) | Deer detection (21MB model) |
| **Image Processing** | Pillow, OpenCV | EXIF extraction, transformations |
| **Containerization** | Docker Compose | Service orchestration |
| **Documentation** | Spec-kit methodology | Living specifications |

## Project Structure

```
thumper_counter/
├── src/
│   ├── backend/              # FastAPI application
│   │   ├── api/              # REST endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── core/             # Database, config
│   └── worker/               # Celery worker
│       ├── tasks/            # Detection, classification
│       └── celery_app.py     # Worker configuration
├── docker/
│   ├── docker-compose.yml    # Service definitions
│   └── dockerfiles/          # Container configs
├── docs/                     # Documentation
│   ├── NEXT_STEPS.md         # Resume guide
│   └── SESSION_*_HANDOFF.md  # Session notes
├── .specify/                 # Spec-kit planning
│   ├── plan.md               # Sprint plan
│   └── constitution.md       # Project principles
├── CLAUDE.md                 # AI assistant context
└── requirements.txt          # Python dependencies
```

## Development Guide

### For Developers

See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed development instructions including:
- How to resume development
- GPU enablement (8x performance improvement)
- Batch processing implementation
- Testing procedures

### Current Sprint (Sprint 3)

**Focus:** GPU enablement + Batch processing

**High Priority Tasks:**
1. Enable GPU support (fix CUDA multiprocessing)
2. Create batch processing endpoint (POST /api/processing/batch)
3. Add progress monitoring (GET /api/processing/status)

**Performance Targets:**
- Detection speed: 0.05s per image (GPU, 8x improvement)
- Throughput: 1200 images/minute
- Batch: Process 1000 images in <1 minute

### Testing

```bash
# Run API tests (when implemented)
docker-compose exec backend pytest tests/api/

# Run worker tests
docker-compose exec worker pytest tests/worker/

# Test detection pipeline
curl -X POST http://localhost:8001/api/images \
  -F "files=@test_image.jpg" \
  -F "process_immediately=true"
```

## API Endpoints

### Images
- `POST /api/images` - Upload images with optional immediate processing
- `GET /api/images` - List images with filtering (status, location, date)
- `GET /api/images/{id}` - Get specific image details

### Locations
- `POST /api/locations` - Create camera location
- `GET /api/locations` - List all locations
- `GET /api/locations/{id}` - Get location details
- `PUT /api/locations/{id}` - Update location
- `DELETE /api/locations/{id}` - Delete location

### Processing (Phase 2 - Coming Soon)
- `POST /api/processing/batch` - Queue batch of images
- `GET /api/processing/status` - Get processing statistics

### Deer (Phase 3 - Coming Soon)
- `POST /api/deer` - Create deer profile
- `GET /api/deer` - List deer with filters
- `GET /api/deer/{id}` - Get deer details with sightings

Full API documentation available at: http://localhost:8001/docs

## Performance Metrics

### Current (Phase 1 - CPU Mode)
- **Detection Speed:** 0.4s per image
- **Throughput:** ~150 images/minute
- **Accuracy:** 87% average confidence
- **Database:** 35,234+ images ready for processing

### Target (Phase 2 - GPU Mode)
- **Detection Speed:** 0.05s per image (8x faster)
- **Throughput:** ~1200 images/minute
- **Batch Processing:** 35k images in ~30 minutes
- **With 4 workers:** ~7-8 minutes

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs backend worker

# Restart specific service
docker-compose restart backend

# Rebuild if needed
docker-compose up -d --build
```

### Database connection issues
```bash
# Check database is running
docker-compose exec db pg_isready

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### Worker not processing
```bash
# Check worker logs
docker-compose logs -f worker

# Check Redis queue
docker-compose exec redis redis-cli LLEN celery

# Restart worker
docker-compose restart worker
```

## Documentation

- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Complete guide for resuming development
- **[CLAUDE.md](CLAUDE.md)** - AI assistant instructions and preferences
- **[.specify/plan.md](.specify/plan.md)** - Sprint plan and project metrics
- **[docs/](docs/)** - Additional documentation and session notes

## Contributing

This is a personal project for wildlife monitoring at Hopkins Ranch. The codebase is open for reference but not actively seeking contributions.

## Original System

This is a rebuild of the original deer tracking system (`I:\deer_tracker`) with improvements:
- **Better Architecture:** Modular, testable components
- **Spec-Driven:** Living documentation with spec-kit
- **Docker-Native:** Consistent environments
- **Scalable:** Async processing, GPU support
- **Documented:** GitHub-ready with clear explanations

**Original Dataset:** 40,617 images processed across 28 development sessions

## License

MIT License - See [LICENSE](LICENSE) for details

## Contact

- **GitHub:** [@fdominguez1972](https://github.com/fdominguez1972)
- **Project:** Hopkins Ranch Wildlife Monitoring
- **Location:** Hopkins Ranch, Texas

---

**Last Updated:** November 5, 2025
**Version:** 1.0.0 (Phase 1 MVP Complete)
**Status:** Active Development - Sprint 3
