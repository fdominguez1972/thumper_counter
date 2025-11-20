# Thumper Counter - Deer Tracking System

**Automated trail camera analysis system for wildlife monitoring at Hopkins Ranch**

[![Phase](https://img.shields.io/badge/Project-95%25%20Complete-success)](https://github.com/fdominguez1972/thumper_counter)
[![Pipeline](https://img.shields.io/badge/Detection-Active-blue)](https://github.com/fdominguez1972/thumper_counter)
[![Processing](https://img.shields.io/badge/Images-58.8K%20%2F%2059.2K-green)](https://github.com/fdominguez1972/thumper_counter)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://github.com/fdominguez1972/thumper_counter)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://github.com/fdominguez1972/thumper_counter)

> **Status:** Sprints 1-12 complete (95% overall). Full ML pipeline operational: GPU-accelerated multi-class detection (0.04s/image), enhanced multi-scale Re-ID with ensemble scoring, React Material-UI dashboard, bulk ZIP upload, detection correction UI. Processing: 58,753 of 59,187 images (99.3%), 11,578 detections, 172 deer profiles tracked.

## Overview

Thumper Counter automatically processes trail camera images to detect, classify, and track individual deer across time. Built using a spec-driven methodology with Docker containerization and ML pipeline optimization.

**Current Capabilities:**
- ✅ Upload images via REST API with EXIF/filename timestamp extraction
- ✅ Bulk ZIP archive upload with automatic extraction
- ✅ GPU-accelerated YOLOv8 multi-class detection (0.04s/image, RTX 4080 Super)
- ✅ Enhanced multi-scale Re-ID (ResNet50 + EfficientNet-B0 ensemble)
- ✅ Sex/age classification (buck, doe, fawn, mature, mid, young)
- ✅ Automatic individual deer tracking with similarity scoring
- ✅ Database storage with PostgreSQL + pgvector extension (HNSW indexing)
- ✅ Celery task queue with Redis backend (32 worker threads)
- ✅ Batch processing API with real-time progress monitoring
- ✅ Automated queue monitoring and replenishment
- ✅ React Material-UI frontend dashboard
- ✅ Detection bounding box visualization with toggle
- ✅ Single and batch detection correction UI
- ✅ Deer profile timeline and location movement analytics
- ✅ Seasonal analysis and PDF/ZIP export generation
- ⏳ Re-ID model fine-tuning with triplet loss (planned)

**Dataset:** 59,187 images from 6 active camera locations at Hopkins Ranch, Texas

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

### Recent Features (Sprints 9-12)

**Feature 009 - Enhanced Re-ID (Complete)**
- Multi-scale ResNet50 feature extraction (layer2, layer3, layer4, avgpool)
- EfficientNet-B0 ensemble scoring (architectural diversity)
- CUDA device optimization (fixed critical device mismatch bug)
- Threshold tuning from 0.60 to 0.50 (reduced profile explosion 364x)
- Automated queue monitoring and replenishment
- See: `specs/009-reid-enhancement/` and `specs/011-reid-cuda-optimization/`

**Feature 011 - Bounding Box Visualization (Complete)**
- Canvas-based detection overlay rendering
- Toggle visibility with eye icon
- Color-coded classifications (buck=blue, doe=pink, fawn=orange)
- Green checkmark for reviewed detections
- Click-to-zoom functionality preserved

**Feature 012 - Bulk Image Upload (Complete)**
- ZIP archive extraction support (up to 2GB files)
- Individual and batch file uploads
- Location selection with automatic organization
- EXIF timestamp extraction
- Progress tracking and validation

**Current Focus (Sprint 13)**
1. Re-ID model fine-tuning with triplet loss
2. Production monitoring and alerting
3. Performance optimization (database write bottleneck)

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
- `POST /api/images` - Upload images or ZIP archives with location assignment
- `GET /api/images` - List images with filtering (status, location, date, classification)
- `GET /api/images/{id}` - Get image details with detections and bounding boxes

### Locations
- `POST /api/locations` - Create camera location
- `GET /api/locations` - List all locations with statistics
- `GET /api/locations/{id}` - Get location details
- `PUT /api/locations/{id}` - Update location
- `DELETE /api/locations/{id}` - Delete location

### Processing
- `POST /api/processing/batch` - Queue batch of images for detection
- `GET /api/processing/status` - Get real-time processing statistics

### Deer
- `POST /api/deer` - Create deer profile (manual)
- `GET /api/deer` - List deer with filters (sex, status, location)
- `GET /api/deer/{id}` - Get deer profile with sighting history
- `GET /api/deer/{id}/timeline` - Activity timeline (hourly/daily/weekly/monthly)
- `GET /api/deer/{id}/locations` - Movement patterns across locations
- `PUT /api/deer/{id}` - Update deer profile (name, status, notes)
- `DELETE /api/deer/{id}` - Delete deer profile

### Detections
- `GET /api/detections` - List all detections with filtering
- `PATCH /api/detections/{id}/correct` - Correct single detection classification
- `PATCH /api/detections/batch/correct` - Batch correction (up to 1000 detections)

### Seasonal Analysis
- `GET /api/seasonal/images` - Filter images by season/year
- `GET /api/seasonal/detections` - Filter detections by season/year
- `GET /api/reports/seasonal/activity` - Aggregate seasonal activity statistics
- `GET /api/reports/seasonal/comparison` - Compare multiple seasonal periods

### Exports
- `POST /api/exports/pdf` - Generate PDF activity report
- `POST /api/exports/zip` - Create ZIP archive with detection crops
- `GET /api/exports/{job_id}` - Poll export job status
- `GET /api/static/exports/{filename}` - Download generated files
- `DELETE /api/exports/{job_id}` - Cancel/delete export job

### Statistics
- `GET /api/stats/dashboard` - Dashboard metrics and population stats
- `GET /api/deer/stats/species` - Species-level statistics

Full API documentation available at: http://localhost:8001/docs

## Performance Metrics

### Current System (November 2025)
- **Detection Speed:** 0.04s per image (GPU inference, YOLOv8n)
- **Re-ID Speed:** 5.57ms per detection (GPU ensemble: ResNet50 + EfficientNet-B0)
- **Throughput:** 840 images/minute (14 images/second with 32 worker threads)
- **Processing Status:** 58,753 of 59,187 images complete (99.3%)
- **Detections:** 11,578 total detections identified
- **Deer Profiles:** 172 unique individuals tracked
- **Re-ID Assignment Rate:** 60.1% (6,956 detections assigned to profiles)
- **GPU:** RTX 4080 Super (16GB VRAM, 3.15GB used, 31% utilization)

### Re-ID System Performance
- **Ensemble Scoring:** 0.6 x ResNet50 + 0.4 x EfficientNet-B0
- **Similarity Threshold:** 0.50 (optimized from 0.60 after threshold analysis)
- **Profile Reduction:** 364x improvement (7,242 → 172 profiles after CUDA fix)
- **Sex Distribution:** 76.7% does, 23.3% bucks (matches detection data)
- **Feature Extraction:** Multi-scale (layer2, layer3, layer4, avgpool) + EfficientNet
- **Vector Search:** pgvector HNSW indexing (~3ms query time)

### Bottleneck Analysis
- GPU inference: 0.04s (optimal, no contention at 32 threads)
- Re-ID inference: 5.57ms (GPU-accelerated, ensemble model)
- Database writes: 70% of processing time
- Primary bottleneck: PostgreSQL transaction commits (not ML inference)

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

**Last Updated:** November 15, 2025
**Version:** 2.0.0 (Enhanced Re-ID System Operational)
**Status:** Active Development - Sprint 13 (95% Complete)
