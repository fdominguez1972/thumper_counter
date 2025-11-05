# API Specification
# Version: 1.0.0
# Date: 2025-11-04

## Overview

RESTful API providing access to the deer tracking system's data and processing capabilities. Designed for both frontend consumption and third-party integrations.

## API Design Principles

1. **RESTful Architecture**
   - WHY: Industry standard, well-understood
   - Resources as nouns, HTTP verbs for actions
   - Stateless requests

2. **JSON:API Format**  
   - WHY: Standardized response structure
   - Includes relationships and metadata
   - Consistent error handling

3. **Versioning Strategy**
   - WHY: Backward compatibility
   - URL versioning: `/api/v1/`
   - Deprecation notices in headers

4. **Pagination**
   - WHY: Large datasets (40k+ images)
   - Cursor-based for consistency
   - Configurable page size (max 100)

## Base Configuration

```yaml
api_config:
  base_url: "http://localhost:8000"
  version: "v1"
  prefix: "/api/v1"
  timeout: 30
  max_request_size: "100MB"
  rate_limit: 
    requests_per_minute: 100
    burst: 20
```

## Authentication & Authorization

### Method: API Key
```http
Authorization: Bearer <api_key>
```

### WHY API Keys:
- Simple for single-tenant system
- No complex OAuth flow needed
- Easy to rotate/revoke
- Sufficient for ranch operations

### Key Management
```yaml
api_keys:
  format: "tk_[environment]_[random32]"
  example: "tk_prod_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
  scopes: 
    - read: View data
    - write: Modify data  
    - process: Trigger processing
    - admin: System management
```

## Core Endpoints

### 1. Images Resource

#### List Images
```http
GET /api/v1/images
```

**Query Parameters:**
```yaml
parameters:
  - name: location_id
    type: uuid
    required: false
    description: Filter by camera location
  
  - name: status
    type: enum
    values: [queued, processing, completed, failed]
    required: false
    
  - name: date_from
    type: iso8601
    required: false
    
  - name: date_to
    type: iso8601
    required: false
    
  - name: has_detections
    type: boolean
    required: false
    
  - name: page_size
    type: integer
    default: 20
    max: 100
    
  - name: cursor
    type: string
    required: false
```

**Response:**
```json
{
  "data": [{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "image",
    "attributes": {
      "filename": "CAM01_20250101_120000.jpg",
      "timestamp": "2025-01-01T12:00:00Z",
      "location_id": "loc_123",
      "processing_status": "completed",
      "detection_count": 3,
      "exif_data": {...}
    },
    "relationships": {
      "detections": {
        "data": [
          {"type": "detection", "id": "det_1"},
          {"type": "detection", "id": "det_2"}
        ]
      }
    }
  }],
  "meta": {
    "total_count": 40617,
    "page_size": 20,
    "cursor": "eyJvZmZzZXQiOiAyMH0="
  }
}
```

#### Get Single Image
```http
GET /api/v1/images/{image_id}
```

**Response includes:**
- Full EXIF data
- All detections with bounding boxes
- Processing history
- Signed URL for image access

#### Upload Image
```http
POST /api/v1/images
Content-Type: multipart/form-data
```

**Request:**
```yaml
fields:
  - name: file
    type: binary
    required: true
    max_size: 50MB
    
  - name: location_id
    type: uuid
    required: false
    
  - name: process_immediately
    type: boolean
    default: false
```

**Response:**
```json
{
  "data": {
    "id": "new_image_id",
    "type": "image",
    "attributes": {
      "processing_status": "queued",
      "queue_position": 42
    }
  }
}
```

### 2. Deer Resource

#### List Deer Profiles
```http
GET /api/v1/deer
```

**Query Parameters:**
```yaml
parameters:
  - name: sex
    type: enum
    values: [buck, doe, fawn, unknown]
    
  - name: min_sightings
    type: integer
    description: Minimum number of sightings
    
  - name: location_id
    type: uuid
    description: Seen at specific location
    
  - name: active_since
    type: iso8601
    description: Seen after this date
```

**Response:**
```json
{
  "data": [{
    "id": "deer_001",
    "type": "deer",
    "attributes": {
      "name": "Big Buck",
      "sex": "buck",
      "first_seen": "2024-10-01T08:00:00Z",
      "last_seen": "2025-01-15T18:30:00Z",
      "sighting_count": 47,
      "confidence": 0.92,
      "primary_location": "loc_sanctuary"
    },
    "relationships": {
      "sightings": {
        "data": [...]
      }
    }
  }]
}
```

#### Get Deer Details
```http
GET /api/v1/deer/{deer_id}
```

**Response includes:**
- Complete sighting history
- Movement patterns
- Associated group members
- Best quality images

#### Update Deer Profile  
```http
PATCH /api/v1/deer/{deer_id}
```

**Request:**
```json
{
  "data": {
    "type": "deer",
    "id": "deer_001",
    "attributes": {
      "name": "Updated Name",
      "sex": "buck",
      "notes": "Injured left hind leg"
    }
  }
}
```

#### Merge Deer Profiles
```http
POST /api/v1/deer/{deer_id}/merge
```

**WHY:** Correct false splits in re-identification

**Request:**
```json
{
  "source_deer_ids": ["deer_002", "deer_003"],
  "keep_name": true,
  "strategy": "newest"  
}
```

### 3. Processing Resource

#### Trigger Batch Processing
```http
POST /api/v1/process/batch
```

**Request:**
```json
{
  "filters": {
    "status": "queued",
    "location_id": "loc_123",
    "date_from": "2025-01-01"
  },
  "limit": 100,
  "priority": "high"
}
```

**Response:**
```json
{
  "data": {
    "job_id": "job_20250104_123456",
    "images_queued": 100,
    "estimated_time": 120,
    "priority": "high"
  }
}
```

#### Check Processing Status
```http
GET /api/v1/process/status
```

**Response:**
```json
{
  "data": {
    "queue_depth": 234,
    "processing": 16,
    "completed_today": 1532,
    "failed_today": 3,
    "average_time": 1.8,
    "workers_active": 4
  }
}
```

#### Reprocess Image
```http
POST /api/v1/images/{image_id}/reprocess
```

**WHY:** Handle updates to ML models

**Request:**
```json
{
  "stages": ["detection", "classification"],
  "clear_existing": true
}
```

### 4. Detection Resource

#### List Detections
```http
GET /api/v1/detections
```

**Query Parameters:**
```yaml
parameters:
  - name: image_id
    type: uuid
    
  - name: deer_id  
    type: uuid
    
  - name: confidence_min
    type: float
    min: 0.0
    max: 1.0
```

#### Update Detection
```http
PATCH /api/v1/detections/{detection_id}
```

**WHY:** Manual verification/correction

**Request:**
```json
{
  "data": {
    "type": "detection",
    "attributes": {
      "deer_id": "deer_001",
      "verified": true,
      "verified_by": "user_123"
    }
  }
}
```

### 5. Location Resource

#### List Locations
```http
GET /api/v1/locations
```

**Response:**
```json
{
  "data": [{
    "id": "loc_sanctuary",
    "type": "location",
    "attributes": {
      "name": "Sanctuary",
      "coordinates": {
        "lat": 30.1234,
        "lon": -97.5678
      },
      "camera_model": "Reconyx HC500",
      "active": true,
      "total_images": 5823,
      "last_image": "2025-01-04T06:00:00Z"
    }
  }]
}
```

#### Get Location Statistics
```http
GET /api/v1/locations/{location_id}/stats
```

**Query Parameters:**
```yaml
parameters:
  - name: period
    type: enum
    values: [day, week, month, year]
    default: month
    
  - name: group_by
    type: enum  
    values: [hour, day, week]
    default: day
```

**Response:**
```json
{
  "data": {
    "location_id": "loc_sanctuary",
    "period": "month",
    "stats": {
      "total_detections": 234,
      "unique_deer": 18,
      "by_sex": {
        "buck": 5,
        "doe": 8,
        "fawn": 3,
        "unknown": 2
      },
      "peak_activity": {
        "hour": 6,
        "day": "Tuesday"
      },
      "timeline": [...]
    }
  }
}
```

### 6. Analytics Resource

#### Population Report
```http
GET /api/v1/analytics/population
```

**Query Parameters:**
```yaml
parameters:
  - name: start_date
    type: iso8601
    required: true
    
  - name: end_date
    type: iso8601
    required: true
    
  - name: location_ids
    type: array[uuid]
    required: false
```

**Response:**
```json
{
  "data": {
    "period": {
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "summary": {
      "total_unique": 47,
      "buck_to_doe_ratio": 0.625,
      "fawn_recruitment": 0.23,
      "average_group_size": 2.3
    },
    "by_location": [...],
    "trends": [...]
  }
}
```

#### Movement Patterns
```http
GET /api/v1/analytics/movement
```

**Response:**
```json
{
  "data": {
    "transitions": [
      {
        "from": "loc_sanctuary",
        "to": "loc_hayfield",
        "count": 12,
        "deer": ["deer_001", "deer_002"]
      }
    ],
    "corridors": [...],
    "home_ranges": [...]
  }
}
```

#### Activity Patterns
```http
GET /api/v1/analytics/activity
```

**Response includes:**
- Hourly activity distribution
- Peak activity times
- Lunar correlation
- Seasonal patterns

## WebSocket Endpoints

### Real-time Processing Updates
```websocket
ws://localhost:8000/ws/processing
```

**Message Format:**
```json
{
  "event": "processing.update",
  "data": {
    "image_id": "img_123",
    "status": "completed",
    "detections": 3
  }
}
```

**Event Types:**
- `processing.started`
- `processing.progress`
- `processing.completed`
- `processing.failed`

### Live Statistics
```websocket
ws://localhost:8000/ws/stats
```

**Updates every 5 seconds:**
- Queue depth
- Processing rate
- Recent detections

## Error Handling

### Error Response Format
```json
{
  "errors": [{
    "status": "422",
    "source": {"parameter": "location_id"},
    "title": "Invalid Parameter",
    "detail": "Location ID must be a valid UUID"
  }]
}
```

### Standard Error Codes
```yaml
error_codes:
  400: Bad Request - Invalid syntax
  401: Unauthorized - Missing/invalid API key
  403: Forbidden - Insufficient permissions
  404: Not Found - Resource doesn't exist
  409: Conflict - Resource already exists
  422: Unprocessable - Validation failed
  429: Too Many Requests - Rate limit exceeded
  500: Internal Error - Server issue
  503: Service Unavailable - Maintenance mode
```

### Rate Limiting Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1672531200
```

## Performance Requirements

### Response Times (p95)
```yaml
performance_targets:
  list_endpoints: < 200ms
  get_single: < 100ms
  create/update: < 500ms
  analytics: < 2000ms
  file_upload: < 5000ms
```

### Throughput
```yaml
capacity:
  concurrent_requests: 100
  uploads_per_minute: 20
  websocket_connections: 500
```

### Caching Strategy
```yaml
cache_config:
  locations: 1 hour
  deer_profiles: 5 minutes
  analytics: 15 minutes
  images: 1 minute
  
headers:
  Cache-Control: "public, max-age=300"
  ETag: SHA256 hash of response
```

## OpenAPI Documentation

### Auto-generated Documentation
```http
GET /api/v1/docs
```

**Includes:**
- Interactive API explorer (Swagger UI)
- Request/response schemas
- Authentication details
- Example payloads

### Schema Endpoint
```http
GET /api/v1/openapi.json
```

**WHY:** Enable client SDK generation

## Client SDKs

### Supported Languages
```yaml
sdks:
  - language: Python
    package: thumper-counter-py
    
  - language: JavaScript  
    package: @thumper/counter-js
    
  - language: Go
    package: github.com/ranch/thumper-go
```

### SDK Features
- Type-safe requests
- Automatic retry logic
- Response pagination
- WebSocket support

## Monitoring & Logging

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-04T12:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "worker": "healthy"
  }
}
```

### Metrics Endpoint
```http
GET /metrics
```

**Format:** Prometheus metrics
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/images",status="200"} 1234
```

### Request Logging
```json
{
  "timestamp": "2025-01-04T12:00:00Z",
  "method": "GET",
  "path": "/api/v1/images",
  "status": 200,
  "duration_ms": 45,
  "user_agent": "ThumperClient/1.0",
  "api_key_id": "tk_prod_xxx"
}
```

## Security Considerations

### Input Validation
- Strict schema validation
- SQL injection prevention
- XSS protection
- File type verification

### Rate Limiting
- Per-API-key limits
- Graduated backoff
- Burst allowance

### CORS Configuration
```yaml
cors:
  allowed_origins: 
    - "http://localhost:3000"
    - "http://10.0.4.195"
  allowed_methods: ["GET", "POST", "PATCH", "DELETE"]
  allowed_headers: ["Authorization", "Content-Type"]
  max_age: 3600
```

## Deprecation Policy

### Version Lifecycle
1. **Active**: Current version, full support
2. **Deprecated**: 6-month notice period
3. **Sunset**: 30-day final warning
4. **Retired**: No longer available

### Deprecation Headers
```http
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Deprecation: true
Link: </api/v2/docs>; rel="successor-version"
```

## Testing Strategy

### Contract Testing
- Request/response schemas
- Status codes
- Required fields
- Data types

### Integration Testing  
- Database operations
- File uploads
- WebSocket connections
- External services

### Load Testing
- Concurrent requests
- Large file uploads
- Burst traffic
- Sustained load

### Security Testing
- Authentication bypass
- SQL injection
- File upload exploits
- Rate limit bypass

---

**Specification Status**: DRAFT
**Dependencies**: system.spec, ml.spec
**Next Review**: After API implementation
