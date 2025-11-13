# Architecture Decision Records
**Last Updated:** November 12, 2025 at 22:52

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
