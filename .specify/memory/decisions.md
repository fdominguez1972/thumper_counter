# Architecture Decision Records
**Last Updated:** November 8, 2025

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

## Decision 5: Threads Pool Instead of Prefork for Celery
**Date:** 2025-11-06
**Status:** Implemented
**Context:** CUDA fork errors with multiprocessing pool
**Decision:** Use threads pool with concurrency=1 for GPU tasks
**Consequences:** Eliminates CUDA errors, thread-safe model loading required

## Decision 6: pgvector for Re-Identification Similarity Search
**Date:** 2025-11-06
**Status:** Implemented
**Context:** Need efficient similarity search for 512-dim embeddings
**Decision:** Use PostgreSQL pgvector extension with HNSW index
**Consequences:** O(log N) query performance, no external vector DB needed

## Decision 7: Two-Stage Deduplication System
**Date:** 2025-11-07
**Status:** Implemented
**Context:** Multiple detections per image, temporal duplicates
**Decision:** Stage 1: Spatial dedup (same image), Stage 2: Temporal (within 10s)
**Consequences:** Reduces false duplicates, preserves true sightings

## Decision 8: Detection Correction System with Batch Support
**Date:** 2025-11-08
**Status:** Implemented
**Context:** ML misclassifications need human review
**Decision:** Build UI for single and batch corrections (up to 1000)
**Consequences:** Enables data quality improvement, training feedback loop

## Decision 9: Multi-Species Classification
**Date:** 2025-11-08
**Status:** Implemented
**Context:** Need to track non-deer wildlife (cattle, pigs, raccoons)
**Decision:** Expand classification system to 7 classes (4 deer + 3 non-deer)
**Consequences:** Comprehensive wildlife monitoring, separate feral hog tracking
