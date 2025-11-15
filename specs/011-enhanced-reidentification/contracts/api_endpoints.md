# API Contract: REST Endpoints - Enhanced Re-Identification

**Feature**: 010-enhanced-reidentification
**Date**: 2025-11-11
**Phase**: 1 - Design
**Version**: 1.0

## Purpose

This contract defines REST API updates for Feature 010. Enhancements are backward-compatible: existing endpoints return same responses by default, with opt-in query parameters to include enhancement metadata.

---

## Endpoint: GET /api/deer/{deer_id}

**Purpose**: Retrieve individual deer profile with optional enhancement metadata.

**Method**: GET

**Path**: `/api/deer/{deer_id}`

**Authentication**: None (public read)

### Request

**Path Parameters**:
- `deer_id` (UUID, required): Deer profile identifier

**Query Parameters**:
- `include_enhancements` (boolean, optional, default=false): Include antler/coat/temporal features
- `include_pose_metadata` (boolean, optional, default=false): Include best pose references
- `include_features` (boolean, optional, default=false): Include feature vectors (large payload)

### Response (Success - 200 OK)

**Default Response** (backward compatible):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Big Buck",
    "sex": "buck",
    "status": "alive",
    "species": "white_tailed_deer",
    "first_seen": "2024-09-15T06:30:00Z",
    "last_seen": "2025-01-20T18:15:00Z",
    "confidence": 0.87,
    "sighting_count": 65,
    "best_photo_id": "uuid-image-123",
    "notes": "8-point buck, left antler has unique drop tine",
    "created_at": "2024-09-15T06:35:00Z",
    "updated_at": "2025-01-20T18:20:00Z"
}
```

**With Enhancements** (`?include_enhancements=true`):
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Big Buck",
    "sex": "buck",
    "status": "alive",
    "species": "white_tailed_deer",
    "first_seen": "2024-09-15T06:30:00Z",
    "last_seen": "2025-01-20T18:15:00Z",
    "confidence": 0.87,
    "sighting_count": 65,
    "best_photo_id": "uuid-image-123",
    "notes": "8-point buck, left antler has unique drop tine",
    "created_at": "2024-09-15T06:35:00Z",
    "updated_at": "2025-01-20T18:20:00Z",

    // NEW: Enhancement metadata
    "enhancements": {
        "antler_features": {
            "has_fingerprint": true,
            "point_count_estimate": 8,
            "spread_width_px": 245,
            "symmetry_score": 0.78,
            "unique_formations": ["drop_tine_left"],
            "season_tag": "2024-rut"
        },
        "coat_patterns": {
            "has_pattern": true,
            "detected_markings": [
                {
                    "type": "white_chest_patch",
                    "region": "chest",
                    "size_px": 1200,
                    "contrast_ratio": 2.8
                }
            ]
        },
        "temporal_profile": {
            "favorite_location": {
                "location_id": "uuid-location-1",
                "location_name": "North Ridge",
                "visit_frequency": 0.69  // 69% of sightings at this location
            },
            "favorite_time_window": "17:00-19:00",
            "activity_peak_hour": 18,
            "seasonal_presence": ["2024-fall", "2024-rut", "2025-spring"]
        }
    }
}
```

**With Pose Metadata** (`?include_pose_metadata=true`):
```json
{
    // ... standard fields ...

    "best_poses": {
        "frontal": {
            "detection_id": "uuid-det-123",
            "image_id": "uuid-img-456",
            "thumbnail_url": "/api/images/uuid-img-456/thumbnail",
            "confidence": 0.92,
            "timestamp": "2024-11-15T14:30:00Z",
            "pose_angle": 15
        },
        "profile_left": {
            "detection_id": "uuid-det-789",
            "image_id": "uuid-img-012",
            "thumbnail_url": "/api/images/uuid-img-012/thumbnail",
            "confidence": 0.89,
            "timestamp": "2024-11-18T07:45:00Z",
            "pose_angle": 90
        },
        "profile_right": null,
        "rear": {
            "detection_id": "uuid-det-345",
            "image_id": "uuid-img-678",
            "thumbnail_url": "/api/images/uuid-img-678/thumbnail",
            "confidence": 0.75,
            "timestamp": "2024-11-20T18:00:00Z",
            "pose_angle": 180
        }
    }
}
```

### Response (Error - 404 Not Found)

```json
{
    "detail": "Deer with id '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

---

## Endpoint: GET /api/deer

**Purpose**: List deer profiles with optional filtering by enhancement features.

**Method**: GET

**Path**: `/api/deer`

### Request

**Query Parameters** (all optional):
- `sex` (string): Filter by sex (buck/doe/fawn/unknown)
- `status` (string): Filter by status (alive/deceased/unknown)
- `has_antler_features` (boolean): Filter deer with antler fingerprints
- `has_coat_markings` (boolean): Filter deer with detected markings
- `favorite_location_id` (UUID): Filter deer frequently seen at location
- `min_sighting_count` (integer): Minimum number of sightings
- `since` (ISO datetime): Only deer seen since this date
- `include_enhancements` (boolean, default=false): Include enhancement metadata
- `page` (integer, default=1): Page number
- `page_size` (integer, default=20, max=100): Results per page
- `sort` (string, default="last_seen"): Sort field (last_seen/sighting_count/confidence/name)
- `order` (string, default="desc"): Sort order (asc/desc)

### Response (Success - 200 OK)

```json
{
    "total": 14,
    "page": 1,
    "page_size": 20,
    "results": [
        {
            "id": "uuid-deer-1",
            "name": "Big Buck",
            "sex": "buck",
            "status": "alive",
            "first_seen": "2024-09-15T06:30:00Z",
            "last_seen": "2025-01-20T18:15:00Z",
            "confidence": 0.87,
            "sighting_count": 65,
            "best_photo_id": "uuid-image-123",
            // Enhancement metadata if include_enhancements=true
        },
        // ... more deer ...
    ]
}
```

**Example Queries**:
- `/api/deer?sex=buck&has_antler_features=true` - All bucks with antler fingerprints
- `/api/deer?has_coat_markings=true&sex=doe` - Does with unique markings
- `/api/deer?favorite_location_id=uuid-location-1` - Deer frequently at location
- `/api/deer?since=2025-01-01T00:00:00Z` - Deer seen in 2025

---

## Endpoint: GET /api/deer/{deer_id}/antler_history

**Purpose**: Retrieve seasonal antler fingerprint history for bucks (cross-year tracking).

**Method**: GET

**Path**: `/api/deer/{deer_id}/antler_history`

### Request

**Path Parameters**:
- `deer_id` (UUID, required): Deer profile identifier

### Response (Success - 200 OK)

```json
{
    "deer_id": "550e8400-e29b-41d4-a716-446655440000",
    "deer_name": "Big Buck",
    "total_seasons": 2,
    "antler_records": [
        {
            "season_tag": "2024-rut",
            "point_count_estimate": 8,
            "spread_width_px": 245,
            "symmetry_score": 0.78,
            "first_seen": "2024-08-15T06:00:00Z",
            "last_seen": "2025-01-20T18:15:00Z",
            "sighting_count": 42,
            "average_confidence": 0.88,
            "representative_detection_id": "uuid-det-123",
            "representative_image_id": "uuid-img-456",
            "thumbnail_url": "/api/images/uuid-img-456/thumbnail"
        },
        {
            "season_tag": "2023-rut",
            "point_count_estimate": 6,
            "spread_width_px": 210,
            "symmetry_score": 0.82,
            "first_seen": "2023-09-01T07:00:00Z",
            "last_seen": "2024-01-15T17:30:00Z",
            "sighting_count": 28,
            "average_confidence": 0.85,
            "representative_detection_id": "uuid-det-789",
            "representative_image_id": "uuid-img-012",
            "thumbnail_url": "/api/images/uuid-img-012/thumbnail"
        }
    ]
}
```

### Response (Error - 404 Not Found)

```json
{
    "detail": "Deer with id '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

### Response (Error - 400 Bad Request)

```json
{
    "detail": "Deer is not a buck. Antler history only available for bucks."
}
```

---

## Endpoint: GET /api/detections/{detection_id}

**Purpose**: Retrieve detection with optional enhancement metadata.

**Method**: GET

**Path**: `/api/detections/{detection_id}`

### Request

**Path Parameters**:
- `detection_id` (UUID, required): Detection identifier

**Query Parameters**:
- `include_enhancement_metadata` (boolean, optional, default=false): Include pose/antler/coat/temporal data

### Response (Success - 200 OK)

**Default Response** (backward compatible):
```json
{
    "id": "uuid-det-123",
    "image_id": "uuid-img-456",
    "classification": "buck",
    "confidence": 0.89,
    "bbox": {"x": 120, "y": 45, "width": 200, "height": 300},
    "deer_id": "uuid-deer-1",
    "is_valid": true,
    "is_reviewed": false,
    "created_at": "2024-11-15T14:30:00Z"
}
```

**With Enhancement Metadata** (`?include_enhancement_metadata=true`):
```json
{
    "id": "uuid-det-123",
    "image_id": "uuid-img-456",
    "classification": "buck",
    "confidence": 0.89,
    "bbox": {"x": 120, "y": 45, "width": 200, "height": 300},
    "deer_id": "uuid-deer-1",
    "is_valid": true,
    "is_reviewed": false,
    "created_at": "2024-11-15T14:30:00Z",

    // NEW: Enhancement metadata from JSONB column
    "enhancement_metadata": {
        "pose_estimation": {
            "classification": "profile_left",
            "angle_degrees": 85,
            "confidence": 0.87,
            "keypoints": {
                "nose": [120, 45, 0.92],
                "left_ear": [115, 30, 0.88],
                "right_ear": [125, 28, 0.85],
                "shoulder": [140, 80, 0.90],
                "hip": [180, 85, 0.89],
                "tail_base": [200, 90, 0.75]
            },
            "inference_time_ms": 52
        },
        "antler_features": {
            "visible": true,
            "point_count_estimate": 8,
            "spread_width_px": 245,
            "symmetry_score": 0.78,
            "extraction_success": true,
            "inference_time_ms": 185
        },
        "coat_patterns": {
            "white_chest_patch": true,
            "facial_blaze": false,
            "visible_scars": [],
            "extraction_success": true,
            "inference_time_ms": 95
        },
        "temporal_context": {
            "location_match_score": 0.65,
            "time_of_day_match_score": 0.82,
            "temporal_conflict_detected": false,
            "inference_time_ms": 3
        },
        "enhancement_flags": {
            "antler_enhancement_used": true,
            "pose_normalization_used": true,
            "coat_analysis_used": true,
            "temporal_scoring_used": true,
            "ensemble_mode_used": false
        },
        "reid_result": {
            "matched_deer_id": "uuid-deer-1",
            "visual_similarity": 0.88,
            "temporal_similarity": 0.73,
            "antler_similarity": 0.91,
            "coat_similarity": 0.76,
            "final_confidence": 0.87,
            "match_method": "enhanced_weighted_fusion",
            "inference_time_ms": 450
        }
    }
}
```

---

## Endpoint: GET /api/detections

**Purpose**: List detections with filtering by enhancement features.

**Method**: GET

**Path**: `/api/detections`

### Request

**Query Parameters** (all optional):
- `image_id` (UUID): Filter by image
- `deer_id` (UUID): Filter by matched deer
- `classification` (string): Filter by class (buck/doe/fawn/unknown)
- `pose_classification` (string): Filter by pose (frontal/profile_left/profile_right/rear/angled)
- `has_antler_features` (boolean): Filter detections with antler data
- `has_coat_markings` (boolean): Filter detections with coat markings
- `min_confidence` (float): Minimum re-ID confidence
- `enhancement_mode` (string): Filter by method (baseline_resnet50/enhanced_weighted_fusion/ensemble)
- `include_enhancement_metadata` (boolean, default=false): Include metadata
- `page` (integer, default=1): Page number
- `page_size` (integer, default=50, max=500): Results per page

### Response (Success - 200 OK)

```json
{
    "total": 29735,
    "page": 1,
    "page_size": 50,
    "results": [
        {
            "id": "uuid-det-1",
            "image_id": "uuid-img-1",
            "classification": "buck",
            "confidence": 0.89,
            "bbox": {"x": 120, "y": 45, "width": 200, "height": 300},
            "deer_id": "uuid-deer-1",
            // Enhancement metadata if include_enhancement_metadata=true
        },
        // ... more detections ...
    ]
}
```

**Example Queries**:
- `/api/detections?pose_classification=profile_left&has_antler_features=true` - Profile bucks with antlers
- `/api/detections?enhancement_mode=enhanced_weighted_fusion` - Detections matched with enhancements
- `/api/detections?deer_id=uuid-deer-1&include_enhancement_metadata=true` - All detections for deer with metadata

---

## Endpoint: POST /api/deer/{deer_id}/reprocess_enhancements

**Purpose**: Re-run enhanced re-ID on all detections for a specific deer (model improvement scenario).

**Method**: POST

**Path**: `/api/deer/{deer_id}/reprocess_enhancements`

### Request

**Path Parameters**:
- `deer_id` (UUID, required): Deer profile identifier

**Body**:
```json
{
    "config": {
        "enable_antler": true,
        "enable_pose": true,
        "enable_coat": true,
        "enable_temporal": false,  // Skip temporal (already calculated)
        "enable_ensemble": true     // Use ensemble for maximum accuracy
    }
}
```

### Response (Success - 202 Accepted)

```json
{
    "deer_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_detections": 65,
    "tasks_queued": 65,
    "estimated_time_minutes": 8,
    "job_id": "uuid-job-123"
}
```

### Response (Error - 404 Not Found)

```json
{
    "detail": "Deer with id '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

---

## Endpoint: GET /api/stats/enhancements

**Purpose**: Retrieve enhancement adoption and performance statistics.

**Method**: GET

**Path**: `/api/stats/enhancements`

### Response (Success - 200 OK)

```json
{
    "total_detections": 29735,
    "enhanced_detections": 12450,
    "enhancement_coverage": 0.42,  // 42% of detections have enhancement metadata

    "feature_usage": {
        "antler_features": 3210,  // Buck detections with antler data
        "pose_normalization": 11890,
        "coat_patterns": 12450,
        "temporal_scoring": 12450,
        "ensemble_mode": 0  // Expensive, opt-in only
    },

    "match_methods": {
        "baseline_resnet50": 17285,
        "enhanced_weighted_fusion": 12450,
        "ensemble": 0
    },

    "average_timings_ms": {
        "baseline_reid": 890,
        "enhanced_reid": 1390,
        "overhead": 500
    },

    "pose_distribution": {
        "frontal": 4120,
        "profile_left": 3850,
        "profile_right": 3680,
        "rear": 2100,
        "angled": 1500,
        "unknown": 17485  // Baseline detections without pose data
    },

    "antler_detections": {
        "total_bucks": 8950,
        "antlers_visible": 3210,
        "antler_visibility_rate": 0.36
    },

    "coat_markings": {
        "white_chest_patch": 1850,
        "facial_blaze": 320,
        "visible_scars": 45
    }
}
```

---

## Endpoint: GET /api/deer/{deer_id}/similar

**Purpose**: Find deer visually similar to a specific deer (debugging/validation tool).

**Method**: GET

**Path**: `/api/deer/{deer_id}/similar`

### Request

**Path Parameters**:
- `deer_id` (UUID, required): Reference deer profile

**Query Parameters**:
- `use_antler` (boolean, default=true): Include antler similarity
- `use_coat` (boolean, default=true): Include coat similarity
- `use_temporal` (boolean, default=false): Include temporal similarity
- `limit` (integer, default=10, max=50): Max similar deer to return
- `min_similarity` (float, default=0.5): Minimum similarity threshold

### Response (Success - 200 OK)

```json
{
    "reference_deer_id": "550e8400-e29b-41d4-a716-446655440000",
    "reference_deer_name": "Big Buck",
    "similar_deer": [
        {
            "deer_id": "uuid-deer-2",
            "deer_name": "Spike",
            "similarity_score": 0.78,
            "similarity_breakdown": {
                "body_features": 0.82,
                "antler_features": 0.75,
                "coat_patterns": 0.68,
                "temporal_context": 0.45
            },
            "shared_locations": ["North Ridge", "South Valley"],
            "sighting_overlap_days": 15
        },
        // ... more similar deer ...
    ]
}
```

---

## Schema Updates (Pydantic Models)

### DeerResponse (Modified)

```python
# src/backend/schemas/deer.py

class DeerEnhancements(BaseModel):
    """Enhancement metadata for deer profile."""
    antler_features: Optional[AntlerFeatures] = None
    coat_patterns: Optional[CoatPatterns] = None
    temporal_profile: Optional[TemporalProfile] = None

class AntlerFeatures(BaseModel):
    has_fingerprint: bool
    point_count_estimate: Optional[int] = None
    spread_width_px: Optional[float] = None
    symmetry_score: Optional[float] = None
    unique_formations: List[str] = []
    season_tag: Optional[str] = None

class CoatPatterns(BaseModel):
    has_pattern: bool
    detected_markings: List[CoatMarking] = []

class CoatMarking(BaseModel):
    type: str  # white_chest_patch, facial_blaze, scar
    region: str  # chest, face, flank, leg
    size_px: int
    contrast_ratio: float

class TemporalProfile(BaseModel):
    favorite_location: Optional[FavoriteLocation] = None
    favorite_time_window: Optional[str] = None
    activity_peak_hour: Optional[int] = None
    seasonal_presence: List[str] = []

class FavoriteLocation(BaseModel):
    location_id: UUID
    location_name: str
    visit_frequency: float

class DeerResponse(BaseModel):
    """Deer profile response (backward compatible)."""
    id: UUID
    name: Optional[str] = None
    sex: str
    status: str
    species: str
    first_seen: datetime
    last_seen: datetime
    confidence: float
    sighting_count: int
    best_photo_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # NEW: Optional enhancement metadata
    enhancements: Optional[DeerEnhancements] = None
    best_poses: Optional[Dict[str, Optional[BestPose]]] = None

class BestPose(BaseModel):
    detection_id: UUID
    image_id: UUID
    thumbnail_url: str
    confidence: float
    timestamp: datetime
    pose_angle: float
```

---

## Backward Compatibility Guarantee

1. **Existing Endpoints**: All existing GET /api/deer and GET /api/detections endpoints return same responses
2. **Opt-In Metadata**: Enhancement fields only included when query parameter set
3. **Null Handling**: Enhancement metadata nullable, frontend must handle None values
4. **Performance**: Default queries (without enhancements) have no performance regression

---

## Phase 1 Exit Criteria

- [X] API endpoint specifications defined
- [X] Request/response contracts documented
- [X] Query parameter filtering specified
- [X] Pydantic schema updates outlined
- [X] Backward compatibility verified

**Status**: COMPLETE - API contracts defined

---

## Next Steps

1. Generate quickstart.md: Developer setup guide for MMPose and models
2. Re-evaluate Constitution Check post-design
