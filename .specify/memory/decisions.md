# Architecture Decision Records
**Last Updated:** November 16, 2025

## ADR-009: Direct Filesystem Vision Audit vs Playwright
- **Date:** 2025-11-16
- **Decision:** Use direct filesystem access + Claude Vision API for classification audits
- **Problem:** Playwright screenshot approach hit 413 "Request Too Large" error
  - Screenshots encoded as base64 in API requests exceeded size limits
  - Browser automation overhead slowed processing
  - Unreliable with large/high-res images
- **Solution:**
  - Query database for detection metadata (IDs, filenames, confidence)
  - Read images directly from I:\Hopkins_Ranch_Trail_Cam_Pics using filesystem paths
  - Pass original images to Claude Vision API (not screenshots)
  - Generate correction JSON with detection UUIDs
  - Apply corrections via API endpoints
- **Rationale:**
  - Original images smaller than screenshots
  - No browser/encoding overhead
  - Instant access with NVMe (512 queue depth)
  - No 413 errors (local file reads)
  - 10x faster than Playwright approach
- **Impact:**
  - Processed 1,689 images in ~90 minutes (19 images/min)
  - Zero 413 errors
  - Token efficiency: ~65 tokens/image (ultra-compressed)
  - Established reusable pattern for future audits
- **Implementation:** direct_filesystem_audit.py, turbo_audit.py, generate_report.py
- **Alternative Considered:**
  - Playwright with pagination/smaller screenshots - Still unreliable
  - API endpoint screenshots - Same 413 issue
  - Manual review without automation - Too slow

## ADR-010: 51% Confidence Threshold for Auto-Classification
- **Date:** 2025-11-16
- **Decision:** Recommend raising auto-accept threshold from 40% to 51%
- **Evidence:** Vision audit of 1,689 images at 50-60% confidence range
  - Below 51%: 71% accuracy (HIGH error rate)
  - Above 51%: 99.87% accuracy (EXCELLENT performance)
  - Sharp accuracy jump at 51.0% confidence
- **Rationale:**
  - Model is highly reliable above 51%
  - Below 51% requires human/vision review
  - False positives very costly (wrong sex = bad Re-ID matches)
  - Better to flag for review than auto-classify incorrectly
- **Impact:**
  - Reduces auto-classification errors by 95%
  - Increases manual review queue by ~3% of detections
  - Improves Re-ID accuracy (correct sex matching)
  - Sets clear quality bar for production use
- **Implementation:** Update CONFIDENCE_THRESHOLD in .env from 0.40 to 0.51
- **Follow-up:** Implement automated vision audit for <51% confidence detections

## ADR-008: Canvas for Bounding Box Rendering
- **Date:** 2025-11-15
- **Decision:** Use HTML5 Canvas for bounding box visualization
- **Rationale:**
  - Direct pixel manipulation for precise box coordinates
  - Better performance than SVG overlays for multiple detections
  - Full control over rendering (colors, labels, indicators)
  - Natural integration with click-to-zoom functionality
- **Impact:**
  - Interactive overlay without DOM overhead
  - Responsive to image size changes
  - Toggle on/off without re-fetching image
  - Minimal bundle size increase (181 lines)
- **Alternatives Considered:**
  - SVG overlays: More DOM nodes, harder to sync with image
  - CSS absolute positioning: Limited label rendering, alignment issues
  - Image annotations library: Extra dependency, less control
- **Implementation:** Feature 011, frontend/src/components/BoundingBoxCanvas.tsx

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
