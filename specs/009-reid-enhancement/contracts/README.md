# API Contracts

**Feature**: 009-reid-enhancement

## No API Contracts Required

This feature enhances the internal Re-ID worker logic without modifying any public API endpoints. All changes are internal to the ML pipeline.

**Existing Endpoints (No Changes)**:
- GET /api/deer - List deer profiles (returns existing schema)
- GET /api/deer/{id} - Deer detail (returns existing schema)
- POST /api/processing/batch - Queue images (existing behavior)
- GET /api/processing/status - Processing status (existing behavior)

**Internal Changes Only**:
- Multi-scale feature extraction (worker task)
- Ensemble similarity computation (worker task)
- Database schema (3 new columns, backward compatible)

**Frontend Impact**: None (no UI changes required)

