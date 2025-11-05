# System Architecture Specification
# Version: 1.0.0
# Date: 2025-11-04

## Overview

The Thumper Counter system is a comprehensive wildlife tracking platform that processes trail camera images to detect, classify, and track individual deer across time and locations.

## System Goals

1. **Automated Processing**: Handle 40,000+ trail camera images without manual intervention
2. **Individual Identification**: Track specific deer across multiple sightings
3. **Population Analysis**: Generate statistics on herd composition and movement
4. **Real-time Dashboard**: Provide visual insights for ranch management
5. **Scalability**: Support additional camera locations and image volumes

## Architecture Pattern

The system follows a microservices architecture with the following principles:
- **Separation of Concerns**: Each service has a single responsibility
- **Async Processing**: Heavy ML tasks run asynchronously via task queue
- **Horizontal Scaling**: Services can be scaled independently
- **Fault Tolerance**: Service failures don't cascade to full system failure

## Core Components

### 1. Data Ingestion Layer
**Purpose**: Import and prepare trail camera images  
**Responsibilities**:
- Extract EXIF metadata (timestamp, camera info)
- Validate image format and quality
- Queue images for processing
- Store original images with metadata

### 2. ML Processing Pipeline
**Purpose**: Apply computer vision models to detect and classify deer  
**Components**:
- Detection Service (YOLOv8)
- Classification Service (Custom CNN)
- Re-identification Service (ResNet50)
- Feature Vector Database

**Processing Flow**:
```
Image -> Detection -> Classification -> Re-ID -> Database
```

### 3. API Gateway
**Purpose**: Unified interface for all client interactions  
**Endpoints**:
- `/api/images` - Image management
- `/api/deer` - Deer profiles and tracking
- `/api/detections` - Detection results
- `/api/locations` - Camera location data
- `/api/analytics` - Statistical analysis

### 4. Data Persistence
**Purpose**: Store and retrieve all system data  
**Databases**:
- PostgreSQL: Structured data (deer profiles, detections, metadata)
- Redis: Cache and task queue
- File Storage: Original and processed images

### 5. Task Orchestration
**Purpose**: Manage async processing workflows  
**Components**:
- Celery Workers: Execute ML tasks
- Celery Beat: Schedule periodic tasks
- Redis Queue: Task distribution
- Flower: Task monitoring

### 6. User Interface
**Purpose**: Visual dashboard for data exploration  
**Features**:
- Real-time processing status
- Image gallery with detections
- Individual deer profiles
- Location heat maps
- Population statistics

## Service Definitions

### Backend Service (FastAPI)
- **Port**: 8000
- **Protocol**: REST/JSON
- **Authentication**: API keys
- **Rate Limiting**: 100 req/min
- **Health Check**: `/health`
- **Metrics**: `/metrics`

### Worker Service (Celery)
- **Concurrency**: 4 workers
- **GPU**: Required (NVIDIA)
- **Memory**: 8GB minimum
- **Batch Size**: 16 images
- **Timeout**: 300 seconds

### Database Service (PostgreSQL)
- **Version**: 15
- **Port**: 5432
- **Connections**: 100 max
- **Storage**: 100GB minimum
- **Backup**: Daily snapshots

### Cache Service (Redis)
- **Version**: 7
- **Port**: 6379
- **Memory**: 2GB
- **Persistence**: AOF enabled
- **Eviction**: LRU

### Frontend Service (React)
- **Port**: 3000 (dev), 80 (prod)
- **Build**: Webpack 5
- **State**: Redux/Context
- **Routing**: React Router
- **UI Library**: Material-UI

## Data Models

### Image
```
- id: UUID
- filename: string
- path: string
- timestamp: datetime
- location_id: UUID
- exif_data: JSON
- processing_status: enum
- created_at: datetime
```

### Deer
```
- id: UUID
- name: string (optional)
- sex: enum (buck/doe/fawn/unknown)
- first_seen: datetime
- last_seen: datetime
- feature_vector: float[]
- confidence: float
- sighting_count: integer
```

### Detection
```
- id: UUID
- image_id: UUID
- deer_id: UUID (nullable)
- bbox: JSON {x, y, width, height}
- confidence: float
- classification: string
- created_at: datetime
```

### Location
```
- id: UUID
- name: string
- coordinates: JSON {lat, lon}
- camera_model: string
- active: boolean
- image_count: integer
```

## Infrastructure Requirements

### Hardware
- **CPU**: 8+ cores
- **RAM**: 32GB minimum
- **GPU**: NVIDIA RTX 4070 or better
- **Storage**: 500GB SSD for images
- **Network**: 1Gbps for LAN access

### Software
- **OS**: Windows 10/11 with WSL2
- **Docker**: Desktop with GPU support
- **CUDA**: 12.0+
- **Python**: 3.11+
- **Node.js**: 18+

## Deployment Strategy

### Development
```yaml
# All services in single docker-compose
docker-compose up -d
```

### Production
```yaml
# Separate compose files per service
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling
- Backend: Load balancer with multiple instances
- Workers: Scale horizontally based on queue depth
- Database: Read replicas for analytics
- Cache: Redis cluster for high availability

## Monitoring & Observability

### Metrics
- Processing throughput (images/minute)
- Detection accuracy
- API response times
- Queue depth
- GPU utilization

### Logging
- Centralized logging via stdout
- Log levels: DEBUG, INFO, WARN, ERROR
- Structured JSON format
- Retention: 30 days

### Alerting
- Processing failures > 5%
- Queue depth > 1000
- API errors > 1%
- GPU memory > 90%
- Disk usage > 80%

## Security Considerations

- API authentication via bearer tokens
- Database connections via SSL
- Image access controlled by API
- No direct file system access
- Regular security updates

## Performance Targets

- Image processing: < 2 seconds per image
- API response: < 200ms p95
- Dashboard load: < 3 seconds
- Batch processing: 100 images/minute
- System availability: 99.9%

## Future Enhancements

1. **Mobile App**: Field access via smartphone
2. **Weather Integration**: Correlate activity with conditions
3. **Advanced Analytics**: Predictive modeling
4. **Multi-species**: Expand beyond deer
5. **Edge Processing**: On-camera ML inference

## Dependencies

### External Services
- Docker Hub: Container images
- PyPI: Python packages
- npm: JavaScript packages
- Hugging Face: ML models

### Critical Libraries
- FastAPI: Web framework
- SQLAlchemy: ORM
- Celery: Task queue
- PyTorch: ML framework
- React: UI framework

## Testing Strategy

- Unit tests: 80% coverage minimum
- Integration tests: API endpoints
- Performance tests: Load testing
- ML tests: Model accuracy validation
- E2E tests: Critical user flows

## Documentation Requirements

- API documentation: OpenAPI/Swagger
- Code documentation: Docstrings
- User guide: Markdown in /docs
- Architecture diagrams: Mermaid/PlantUML
- Deployment guide: Step-by-step

---

**Specification Status**: DRAFT  
**Next Review**: After initial implementation  
**Approval**: Pending
