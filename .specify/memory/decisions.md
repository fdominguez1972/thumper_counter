# Architecture Decision Records
**Last Updated:** November 12, 2025 at 23:02

## ADR-001: YOLOv8 Multi-Class Detection
- **Date:** 2025-11-04
- **Decision:** Use single YOLOv8 model for detection + classification
- **Rationale:** Model has 11 built-in classes
- **Impact:** 30% faster, 33% less memory

## ADR-002: Folder-Based Locations
- **Date:** 2025-11-04
- **Decision:** Extract location from folder name
- **Rationale:** Cameras lack GPS EXIF data
- **Impact:** Simpler, matches reality

## ADR-003: Port Configuration
- **Date:** 2025-11-05
- **Decision:** Use ports 5433, 6380, 8001
- **Rationale:** Avoid conflicts with deer_tracker
- **Impact:** Both projects can run simultaneously

## ADR-004: Simple Pagination
- **Date:** 2025-11-05
- **Decision:** Use skip/limit instead of cursors
- **Rationale:** Simpler implementation
- **Impact:** Less efficient for large datasets

## ADR-005: Redis for Export Job Status
- **Date:** 2025-11-12
- **Decision:** Use Redis with 1-hour TTL for export job tracking
- **Rationale:** Persistent storage across API restarts, automatic expiration
- **Impact:** Job status survives API container restarts, no manual cleanup needed
- **Implementation:** Feature 010 Option A

## ADR-006: Fail-Fast Validation
- **Date:** 2025-11-12
- **Decision:** Return first validation error only (fail-fast)
- **Rationale:** Simpler error handling, faster response times
- **Impact:** Users see one error at a time, must fix and retry
- **Alternative Considered:** Return all validation errors at once
- **Implementation:** Feature 010 Option B

## ADR-007: Backup Strategy
- **Date:** 2025-11-12
- **Decision:** Exclude large model files and images from backups
- **Rationale:** Models can be re-downloaded, images stored separately
- **Impact:** Faster backups (3.4GB vs 100GB+), easier restoration
- **Script:** scripts/quick_backup.sh
