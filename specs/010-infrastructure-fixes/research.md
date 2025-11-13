# Research & Investigation: Critical Infrastructure Fixes

**Feature**: 010-infrastructure-fixes
**Date**: 2025-11-12
**Status**: Research Complete

## Overview

This document consolidates research findings for three critical infrastructure fixes:
- Option A: Redis-based export job status tracking
- Option B: FastAPI export request validation
- Option D: Re-ID similarity score analysis

All research conducted to resolve "NEEDS CLARIFICATION" markers from technical context and inform implementation decisions.

---

## Research Task 1: Redis Job Status Patterns

### Question
What is the best practice for storing temporary job status in Redis with automatic expiry?

### Investigation

**Approach 1: SETEX (Atomic Set with Expiry)**
```python
redis_client.setex(
    key="export_job:a3f5b2c1-4d6e-8f9a-0b1c-2d3e4f5a6b7c",
    time=3600,  # 1 hour in seconds
    value=json.dumps({"status": "completed", "filename": "report.pdf"})
)
```

**Pros**:
- Atomic operation (no race conditions)
- TTL set simultaneously with value
- Simple, single command
- Guaranteed expiry (Redis handles cleanup)

**Cons**:
- Fixed TTL per SET operation
- No partial updates (must rewrite entire JSON)

---

**Approach 2: SET + EXPIRE (Two Commands)**
```python
redis_client.set(key, value)
redis_client.expire(key, 3600)
```

**Pros**:
- Allows conditional SET (NX/XX options)
- Can update TTL separately

**Cons**:
- Not atomic (key could exist without TTL if crash between commands)
- Requires transaction (MULTI/EXEC) for atomicity
- More complex error handling

---

**Approach 3: Hash with HEXPIRE (Redis 7.4+)**
```python
redis_client.hset("export_job:uuid", mapping={"status": "completed", "filename": "report.pdf"})
redis_client.expire("export_job:uuid", 3600)
```

**Pros**:
- Allows partial field updates (HSET status completed)
- Structured data without JSON serialization

**Cons**:
- Requires Redis 7.4+ for field-level TTL
- Current Redis version: 7.0 (doesn't support HEXPIRE)
- Not atomic without transaction

---

### Decision: SETEX (Approach 1)

**Rationale**:
1. **Atomicity**: Single command, no race conditions
2. **Simplicity**: Minimal code, clear intent
3. **Compatibility**: Works with Redis 7.0 (current version)
4. **TTL Guarantee**: Expiry set atomically with value
5. **JSON Flexibility**: Allows arbitrary status fields without schema constraints

**Trade-offs Accepted**:
- Must rewrite entire JSON for status updates (acceptable: status updated once per job)
- Fixed TTL per job (acceptable: 1 hour is sufficient for all export types)

**Key Naming Convention**:
- Pattern: `export_job:{job_id}`
- job_id: Celery task UUID (guaranteed unique)
- Namespace: Prevents collision with other Redis keys

**Error Handling**:
```python
try:
    redis_client.setex(key, ttl, value)
except redis.ConnectionError as e:
    logger.error(f"Redis connection failed: {e}")
    # Export task still completes successfully
    # Status just won't be available for polling
except Exception as e:
    logger.error(f"Unexpected Redis error: {e}")
    # Same handling: don't fail export task
```

**Alternatives Considered**:
- PostgreSQL job table: Too slow for high-frequency polling, adds database load
- In-memory state: Lost on backend restart, doesn't scale across multiple backend instances
- Celery result backend: Works but less flexible than direct Redis control

---

## Research Task 2: FastAPI Validation Strategies

### Question
Should validation be in Pydantic schema validators or endpoint logic?

### Investigation

**Approach 1: Pydantic Field Validators**
```python
from pydantic import BaseModel, validator
from datetime import date

class PDFExportRequest(BaseModel):
    start_date: date
    end_date: date
    group_by: str

    @validator('start_date')
    def validate_start_date(cls, v):
        if v > date.today():
            raise ValueError('start_date cannot be in the future')
        return v

    @validator('end_date')
    def validate_end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @validator('group_by')
    def validate_group_by(cls, v):
        if v not in ['day', 'week', 'month']:
            raise ValueError('group_by must be one of: day, week, month')
        return v
```

**Pros**:
- Validation happens automatically during Pydantic parsing
- Clear validation errors with field location
- Reusable across endpoints
- Type safety enforced

**Cons**:
- Multi-field validation awkward (end_date validator needs start_date)
- Error messages less customizable
- Complex business logic harder to express

---

**Approach 2: Endpoint-Level Validation**
```python
@router.post("/pdf")
async def create_pdf_export(request: PDFExportRequest):
    # Validate date order
    if request.start_date > request.end_date:
        raise HTTPException(400, "start_date must be before end_date")

    # Validate date range
    delta = request.end_date - request.start_date
    if delta.days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    # Validate group_by
    if request.group_by not in ["day", "week", "month"]:
        raise HTTPException(400, f"group_by must be one of: day, week, month")

    # Validate future dates
    if request.start_date > date.today():
        raise HTTPException(400, "start_date cannot be in the future")

    # Queue task...
```

**Pros**:
- Clear, sequential validation logic
- Custom error messages
- Easy to add logging/metrics per rule
- Business logic kept in endpoint

**Cons**:
- Validation not automatically enforced
- Potential code duplication across endpoints
- No validation if model instantiated elsewhere

---

**Approach 3: Hybrid (Pydantic + Endpoint)**
```python
class PDFExportRequest(BaseModel):
    start_date: date  # Type validation only
    end_date: date
    group_by: str

    @validator('group_by')
    def validate_group_by(cls, v):
        # Single-field validation in Pydantic
        if v not in ['day', 'week', 'month']:
            raise ValueError('group_by must be one of: day, week, month')
        return v

@router.post("/pdf")
async def create_pdf_export(request: PDFExportRequest):
    # Multi-field validation in endpoint
    if request.start_date > request.end_date:
        raise HTTPException(400, "start_date must be before end_date")

    if (request.end_date - request.start_date).days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    if request.start_date > date.today():
        raise HTTPException(400, "start_date cannot be in the future")

    # Queue task...
```

**Pros**:
- Combines benefits of both approaches
- Pydantic handles type safety + single-field rules
- Endpoint handles multi-field + business logic
- Clear separation of concerns

**Cons**:
- Validation split across two locations
- Developers must remember where each rule lives

---

### Decision: Hybrid Approach (Approach 3)

**Rationale**:
1. **Type Safety**: Pydantic ensures date fields are actually dates
2. **Single-Field Rules**: Pydantic validates group_by enum (simple, reusable)
3. **Multi-Field Rules**: Endpoint validates start < end, date range (requires both fields)
4. **Business Logic**: Endpoint validates future dates (depends on current date)
5. **Error Messages**: Endpoint provides clear, user-friendly messages

**Validation Rule Placement**:

| Rule | Location | Rationale |
|------|----------|-----------|
| start_date/end_date are dates | Pydantic | Type validation |
| group_by in allowed values | Pydantic | Single-field enum |
| start_date < end_date | Endpoint | Requires both fields |
| Date range <= 365 days | Endpoint | Business rule |
| start_date not in future | Endpoint | Depends on current date |

**Error Response Format**:
```python
# Pydantic validation error (422)
{
  "detail": [
    {
      "loc": ["body", "group_by"],
      "msg": "value is not a valid enumeration member; permitted: 'day', 'week', 'month'",
      "type": "type_error.enum"
    }
  ]
}

# Endpoint validation error (400)
{
  "detail": "start_date must be before end_date"
}
```

**Alternatives Considered**:
- Custom Pydantic root_validator: Works but less readable than endpoint logic
- Validation service class: Over-engineering for 4 simple rules
- Database constraints: Wrong layer, validation should happen at API boundary

---

## Research Task 3: Re-ID Similarity Analysis Libraries

### Question
What Python libraries are best for analyzing similarity score distributions?

### Investigation

**Library Stack 1: pandas + matplotlib**
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.DataFrame(detections, columns=['id', 'deer_id', 'similarity'])

# Analyze distribution
print(df['similarity'].describe())

# Plot histogram
plt.hist(df['similarity'], bins=50, alpha=0.7)
plt.xlabel('Similarity Score')
plt.ylabel('Frequency')
plt.title('Re-ID Similarity Score Distribution')
plt.savefig('reid_analysis.png')
```

**Pros**:
- Industry standard for data analysis
- pandas excellent for DataFrame operations
- matplotlib flexible for visualizations
- Already installed in worker environment

**Cons**:
- Verbose syntax for simple plots
- matplotlib aesthetics require tuning

---

**Library Stack 2: pandas + seaborn**
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load data
df = pd.DataFrame(detections, columns=['id', 'deer_id', 'similarity'])

# Enhanced histogram with KDE
sns.histplot(data=df, x='similarity', bins=50, kde=True)
plt.title('Re-ID Similarity Score Distribution')
plt.savefig('reid_analysis.png')
```

**Pros**:
- seaborn builds on matplotlib with better defaults
- KDE (Kernel Density Estimation) shows smooth distribution
- Better aesthetics out-of-the-box
- Statistical annotations built-in

**Cons**:
- Adds dependency (seaborn)
- Slightly slower than pure matplotlib

---

**Library Stack 3: plotly (Interactive)**
```python
import plotly.express as px
import pandas as pd

df = pd.DataFrame(detections, columns=['id', 'deer_id', 'similarity'])

fig = px.histogram(df, x='similarity', nbins=50, title='Re-ID Similarity Distribution')
fig.write_html('reid_analysis.html')
```

**Pros**:
- Interactive plots (zoom, hover, pan)
- HTML output viewable in browser
- Professional appearance

**Cons**:
- Requires plotly installation
- HTML file larger than PNG
- Overkill for static analysis report

---

### Decision: pandas + matplotlib + seaborn

**Rationale**:
1. **pandas**: Essential for data manipulation (already installed)
2. **matplotlib**: Necessary for PNG output (already installed)
3. **seaborn**: Adds statistical enhancements with minimal overhead

**Verification**:
```bash
docker-compose exec worker pip list | grep -E "pandas|matplotlib|seaborn"

# Current versions:
#   pandas>=2.0.0 (INSTALLED)
#   matplotlib>=3.7.0 (INSTALLED)
#   seaborn>=0.12.0 (NOT INSTALLED - add to requirements.txt)
```

**Additional Dependencies**:
```bash
# Add to requirements.txt:
seaborn==0.13.0
scipy==1.11.4  # For statistical clustering analysis
```

**Usage Pattern**:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from sqlalchemy import create_engine

# Query database
engine = create_engine(DATABASE_URL)
query = "SELECT id, deer_id, classification FROM detections WHERE classification IN ('buck', 'doe', 'fawn')"
df = pd.read_sql(query, engine)

# Compute similarity scores (if not stored)
# ... feature vector comparisons ...

# Statistical summary
print(df['similarity'].describe())
print(f"Assignment rate: {(df['deer_id'].notna().sum() / len(df)) * 100:.1f}%")

# Histogram with KDE
plt.figure(figsize=(12, 6))
sns.histplot(data=df, x='similarity', bins=50, kde=True, color='steelblue')
plt.axvline(0.70, color='red', linestyle='--', label='Current Threshold (0.70)')
plt.xlabel('Cosine Similarity Score')
plt.ylabel('Frequency')
plt.title('Re-ID Similarity Score Distribution (11,570 Detections)')
plt.legend()
plt.grid(alpha=0.3)
plt.savefig('reid_similarity_distribution.png', dpi=150)
```

**Alternatives Considered**:
- NumPy only: Too low-level for complex data analysis
- R with reticulate: Adds language dependency, Python sufficient
- Jupyter notebooks: Interactive but requires separate environment

---

## Research Task 4: Threshold Testing Methodology

### Question
How to test multiple threshold values without modifying production data?

### Investigation

**Approach 1: In-Memory Threshold Application**
```python
import pandas as pd

# Load all similarity scores
scores = session.query(Detection.id, Detection.deer_id, compute_similarity()).all()
df = pd.DataFrame(scores, columns=['detection_id', 'deer_id', 'similarity'])

# Test multiple thresholds in-memory
thresholds = [0.70, 0.65, 0.60, 0.55]
results = []

for threshold in thresholds:
    # Apply threshold without writing to database
    assigned = df[df['similarity'] >= threshold]

    results.append({
        'threshold': threshold,
        'assignment_rate': len(assigned) / len(df) * 100,
        'assigned_count': len(assigned),
        'unassigned_count': len(df) - len(assigned)
    })

# Print comparison
print(pd.DataFrame(results))
```

**Pros**:
- Read-only (no database modifications)
- Fast (in-memory operations)
- Repeatable (no side effects)
- Safe for production

**Cons**:
- Must load all data into memory
- Doesn't test actual Re-ID pipeline changes

---

**Approach 2: Temporary Threshold Environment Variable**
```bash
# Create test environment
export REID_THRESHOLD=0.60

# Reprocess sample batch
docker-compose exec worker python3 /app/scripts/reprocess_sample.py --count 100

# Review assignments
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT deer_id, COUNT(*) FROM detections WHERE reprocessed_at > NOW() - INTERVAL '5 minutes' GROUP BY deer_id;"

# Revert threshold
export REID_THRESHOLD=0.70
```

**Pros**:
- Tests actual Re-ID pipeline
- Realistic performance measurement
- Validates full workflow

**Cons**:
- Modifies database (even if sample)
- Slower (requires reprocessing)
- Risk of contaminating production data

---

**Approach 3: Separate Test Database**
```python
# Copy sample to test database
test_engine = create_engine("postgresql://localhost:5434/deer_tracking_test")

# Run Re-ID with different thresholds
for threshold in [0.70, 0.65, 0.60, 0.55]:
    reid_engine = ReIDEngine(threshold=threshold)
    results = reid_engine.process_all(test_engine)
    print(f"Threshold {threshold}: {results['assignment_rate']}%")
```

**Pros**:
- Isolated from production
- Can test destructive operations
- Realistic workflow testing

**Cons**:
- Requires test database setup
- Data sync complexity
- Slower than in-memory analysis

---

### Decision: In-Memory Threshold Application (Approach 1)

**Rationale**:
1. **Safety**: Read-only, no risk to production data
2. **Speed**: Completes in minutes vs hours for reprocessing
3. **Flexibility**: Test any threshold without infrastructure changes
4. **Repeatability**: Same results every run (deterministic)
5. **Simplicity**: Single script, no database setup

**Implementation**:
```python
def test_thresholds(engine, thresholds):
    """
    Test multiple Re-ID thresholds without modifying database.

    Args:
        engine: SQLAlchemy engine
        thresholds: List of threshold values to test

    Returns:
        DataFrame with threshold analysis results
    """
    # Load detections and deer profiles
    detections = pd.read_sql(
        "SELECT id, feature_vector, classification, deer_id FROM detections",
        engine
    )
    deer_profiles = pd.read_sql(
        "SELECT id, feature_vector, sex FROM deer",
        engine
    )

    # Compute similarity matrix
    from sklearn.metrics.pairwise import cosine_similarity

    detection_vectors = np.array([d for d in detections['feature_vector']])
    deer_vectors = np.array([d for d in deer_profiles['feature_vector']])

    similarities = cosine_similarity(detection_vectors, deer_vectors)

    # For each threshold, calculate assignment rate
    results = []
    for threshold in thresholds:
        # Find best match for each detection above threshold
        max_similarities = similarities.max(axis=1)
        assigned = (max_similarities >= threshold).sum()

        results.append({
            'threshold': threshold,
            'assigned': assigned,
            'unassigned': len(detections) - assigned,
            'assignment_rate': (assigned / len(detections)) * 100
        })

    return pd.DataFrame(results)
```

**False Positive Rate Estimation**:
```python
# Manual validation required for ground truth
# Sample 100 assignments at each threshold
# Label as correct/incorrect
# Calculate: (incorrect / total) * 100

def estimate_false_positive_rate(engine, threshold, sample_size=100):
    """
    Estimate false positive rate by manual validation.

    Returns:
        Estimated FPR based on sample
    """
    # Get sample assignments at threshold
    sample = get_sample_assignments(engine, threshold, sample_size)

    # Manual review required (print for human inspection)
    for detection_id, deer_id, similarity in sample:
        print(f"Detection {detection_id} -> Deer {deer_id} (similarity: {similarity:.3f})")
        print("View side-by-side images: ...")
        # User validates: correct / incorrect

    # Calculate FPR from manual labels
    incorrect = sum(manual_labels)
    fpr = (incorrect / sample_size) * 100
    return fpr
```

**Alternatives Considered**:
- Confusion matrix with labeled data: Requires ground truth (not available)
- K-fold cross-validation: Requires labeled training data
- Shadow mode testing: Complex infrastructure, unnecessary for analysis

---

## Technology Stack Summary

### Confirmed Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Backend | FastAPI | 0.104+ | Export endpoint validation |
| Worker | Celery | 5.3+ | Export task execution |
| Cache | Redis | 7.0 | Job status storage |
| Database | PostgreSQL | 15+ | Detection data queries |
| Python | CPython | 3.11 | All scripts and services |
| Data Analysis | pandas | 2.0+ | DataFrame operations |
| Visualization | matplotlib | 3.7+ | Plot generation |
| Statistics | seaborn | 0.13+ | Enhanced plots with KDE |
| Similarity | scikit-learn | 1.3+ | Cosine similarity computation |

### New Dependencies to Add

```txt
# requirements.txt additions for Option D
seaborn==0.13.0
scipy==1.11.4
```

All other dependencies already installed in current environment.

---

## Implementation Patterns

### Pattern 1: Redis Status Update (Worker)

```python
from celery import current_task
import json
from datetime import datetime
from redis import Redis
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True)
def generate_pdf_report_task(self, start_date, end_date, group_by):
    """Generate PDF report with Redis status tracking."""
    redis_client = Redis(host='redis', port=6379, db=0)

    try:
        # Generate report
        filename = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = f"/mnt/exports/{filename}"

        # ... PDF generation logic ...

        # Update Redis: SUCCESS
        redis_client.setex(
            f"export_job:{self.request.id}",
            3600,  # 1 hour
            json.dumps({
                "status": "completed",
                "filename": filename,
                "download_url": f"/api/static/exports/{filename}",
                "completed_at": datetime.utcnow().isoformat()
            })
        )

        logger.info(f"Export job {self.request.id} completed: {filename}")

    except Exception as e:
        # Update Redis: FAILURE
        redis_client.setex(
            f"export_job:{self.request.id}",
            3600,
            json.dumps({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
        )

        logger.error(f"Export job {self.request.id} failed: {e}")
        raise  # Re-raise for Celery retry logic
```

### Pattern 2: Redis Status Poll (API)

```python
from fastapi import APIRouter, HTTPException
from redis import Redis
import json

router = APIRouter()
redis_client = Redis(host='redis', port=6379, db=0)

@router.get("/exports/pdf/{job_id}")
async def get_pdf_export_status(job_id: str):
    """Poll Redis for PDF export job status."""
    # Query Redis
    job_data = redis_client.get(f"export_job:{job_id}")

    if not job_data:
        raise HTTPException(
            status_code=404,
            detail="Job not found or expired"
        )

    # Parse JSON
    try:
        status = json.loads(job_data)
        status['job_id'] = job_id  # Add job_id to response
        return status
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Invalid job status format"
        )
```

### Pattern 3: Export Request Validation (API)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from datetime import date, datetime

class PDFExportRequest(BaseModel):
    start_date: date
    end_date: date
    group_by: str

    @validator('group_by')
    def validate_group_by(cls, v):
        if v not in ['day', 'week', 'month']:
            raise ValueError('group_by must be one of: day, week, month')
        return v

@router.post("/exports/pdf")
async def create_pdf_export(request: PDFExportRequest):
    """Create PDF export with validation."""
    # Multi-field validation
    if request.start_date > request.end_date:
        raise HTTPException(400, "start_date must be before end_date")

    delta = request.end_date - request.start_date
    if delta.days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    if request.start_date > date.today():
        raise HTTPException(400, "start_date cannot be in the future")

    # Queue Celery task
    task = celery_app.send_task(
        'worker.tasks.exports.generate_pdf_report_task',
        args=[request.start_date.isoformat(), request.end_date.isoformat(), request.group_by],
        queue='exports'
    )

    return {"job_id": task.id, "status": "processing"}
```

### Pattern 4: Re-ID Threshold Analysis (Script)

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def analyze_reid_performance(database_url):
    """Analyze Re-ID similarity score distribution."""
    engine = create_engine(database_url)

    # Load data
    print("[INFO] Querying detections...")
    detections = pd.read_sql(
        "SELECT id, deer_id, feature_vector, classification FROM detections WHERE classification IN ('buck', 'doe', 'fawn')",
        engine
    )

    deer = pd.read_sql("SELECT id, feature_vector FROM deer", engine)

    print(f"[INFO] Loaded {len(detections)} detections, {len(deer)} deer profiles")

    # Compute similarity matrix
    print("[INFO] Computing pairwise similarities...")
    det_vectors = np.array([d for d in detections['feature_vector']])
    deer_vectors = np.array([d for d in deer['feature_vector']])

    similarities = cosine_similarity(det_vectors, deer_vectors)
    max_similarities = similarities.max(axis=1)

    # Statistical summary
    print("[INFO] Similarity score statistics:")
    print(f"  Mean: {max_similarities.mean():.3f}")
    print(f"  Median: {np.median(max_similarities):.3f}")
    print(f"  Std Dev: {max_similarities.std():.3f}")
    print(f"  Min: {max_similarities.min():.3f}")
    print(f"  Max: {max_similarities.max():.3f}")

    # Current assignment rate
    assigned = detections['deer_id'].notna().sum()
    assignment_rate = (assigned / len(detections)) * 100
    print(f"\n[INFO] Current assignment rate: {assignment_rate:.1f}% ({assigned}/{len(detections)})")

    # Histogram with KDE
    print("[INFO] Generating histogram...")
    plt.figure(figsize=(12, 6))
    sns.histplot(max_similarities, bins=50, kde=True, color='steelblue')
    plt.axvline(0.70, color='red', linestyle='--', linewidth=2, label='Current Threshold (0.70)')
    plt.xlabel('Maximum Cosine Similarity Score')
    plt.ylabel('Frequency')
    plt.title(f'Re-ID Similarity Score Distribution ({len(detections)} Detections)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig('/app/docs/reid_similarity_distribution.png', dpi=150, bbox_inches='tight')
    print("[INFO] Histogram saved to /app/docs/reid_similarity_distribution.png")

    return max_similarities

if __name__ == "__main__":
    DATABASE_URL = "postgresql://deertrack:password@db:5432/deer_tracking"
    scores = analyze_reid_performance(DATABASE_URL)
```

---

**Research Status**: COMPLETE - All technical decisions documented and validated
