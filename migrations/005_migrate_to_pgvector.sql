-- Migration 005: Migrate deer.feature_vector to pgvector
-- Sprint 5: Re-identification with ResNet50 embeddings
-- Date: 2025-11-06
--
-- WHY: The deer.feature_vector column was initially created as double precision[]
-- but needs to be the native pgvector 'vector' type for:
-- 1. HNSW index support (fast similarity search)
-- 2. Cosine distance operator (<=>)
-- 3. Optimized storage and query performance
--
-- This migration:
-- 1. Converts existing feature_vector data from array to vector type
-- 2. Creates HNSW index for cosine similarity search
-- 3. Validates vector dimensionality (512 dimensions)

-- Prerequisites: pgvector extension must be enabled
-- Run: CREATE EXTENSION IF NOT EXISTS vector;

BEGIN;

-- Step 1: Convert feature_vector column from double precision[] to vector(512)
-- USING clause handles data conversion for existing rows
ALTER TABLE deer
ALTER COLUMN feature_vector TYPE vector(512)
USING feature_vector::vector(512);

-- Step 2: Create HNSW index for fast approximate nearest neighbor search
-- HNSW (Hierarchical Navigable Small World) provides O(log N) search complexity
-- vector_cosine_ops: Use cosine distance metric (1 - cosine similarity)
CREATE INDEX IF NOT EXISTS ix_deer_feature_vector_hnsw
ON deer
USING hnsw (feature_vector vector_cosine_ops);

-- Step 3: Add comment to column for documentation
COMMENT ON COLUMN deer.feature_vector IS
'ML embedding for re-identification (ResNet50 output, 512 dimensions). Uses pgvector for fast similarity search.';

COMMIT;

-- Validation queries:
-- 1. Check column type:
--    SELECT column_name, data_type FROM information_schema.columns
--    WHERE table_name = 'deer' AND column_name = 'feature_vector';
--
-- 2. Verify index exists:
--    SELECT indexname, indexdef FROM pg_indexes
--    WHERE tablename = 'deer' AND indexname = 'ix_deer_feature_vector_hnsw';
--
-- 3. Test cosine distance query:
--    SELECT id, sex, 1 - (feature_vector <=> '[0.1, 0.2, ...]'::vector(512)) AS similarity
--    FROM deer
--    WHERE feature_vector IS NOT NULL
--    ORDER BY feature_vector <=> '[0.1, 0.2, ...]'::vector(512)
--    LIMIT 5;

-- Performance notes:
-- - HNSW index build time: ~O(N log N) for N deer profiles
-- - Query time: ~O(log N) approximate nearest neighbor
-- - Index memory overhead: ~10-15% of vector data size
-- - Recommended for databases with >1000 deer profiles
