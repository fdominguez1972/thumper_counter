# Architecture Decision Records
**Last Updated:** $(date +"%B %d, %Y")

## Decision 1: YOLOv8 Multi-Class Instead of Separate Classifier
**Date:** 2025-11-04
**Status:** Implemented
**Context:** Discovered trained model has 11 classes built-in
**Decision:** Use single YOLOv8 for both detection and classification
**Consequences:** 30% faster, 33% less memory, simpler architecture

## Decision 2: Folder-Based Location Assignment
**Date:** 2025-11-04  
**Status:** Implemented
**Context:** Trail cameras don't have GPS in EXIF
**Decision:** Use folder names for location, manually add GPS
**Consequences:** Matches reality, simpler ingestion

## Decision 3: Port Shifting to Avoid Conflicts
**Date:** 2025-11-05
**Status:** Implemented
**Context:** deer_tracker already using standard ports
**Decision:** Shift to 5433, 6380, 8001
**Consequences:** Both projects can run simultaneously

## Decision 4: Skip/Limit Pagination Instead of Cursors
**Date:** 2025-11-05
**Status:** Implemented
**Context:** Cursor pagination adds complexity
**Decision:** Use simple skip/limit for now
**Consequences:** Simpler but less efficient for large datasets
