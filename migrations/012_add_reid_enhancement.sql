-- Migration: Add Multi-Scale and Ensemble Embeddings for Re-ID Enhancement
-- Feature: 009-reid-enhancement
-- Date: 2025-11-14
-- Description: Adds feature_vector_multiscale, feature_vector_efficientnet, and embedding_version columns
--              to deer table with HNSW indexes for fast similarity search

BEGIN;

-- Check pgvector extension is installed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension not installed. Run: CREATE EXTENSION vector;';
    END IF;
END
$$;

-- T006: Add feature_vector_multiscale VECTOR(512) column
ALTER TABLE deer
ADD COLUMN IF NOT EXISTS feature_vector_multiscale VECTOR(512);

-- T007: Add feature_vector_efficientnet VECTOR(512) column
ALTER TABLE deer
ADD COLUMN IF NOT EXISTS feature_vector_efficientnet VECTOR(512);

-- T008: Add embedding_version VARCHAR(20) column with default 'v1_resnet50'
ALTER TABLE deer
ADD COLUMN IF NOT EXISTS embedding_version VARCHAR(20) DEFAULT 'v1_resnet50';

-- T009: Create HNSW index ix_deer_feature_vector_multiscale_hnsw
-- Parameters: m=16 (connections per layer), ef_construction=64 (build quality)
CREATE INDEX IF NOT EXISTS ix_deer_feature_vector_multiscale_hnsw
ON deer
USING hnsw (feature_vector_multiscale vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- T010: Create HNSW index ix_deer_feature_vector_efficientnet_hnsw
-- Parameters: m=16 (connections per layer), ef_construction=64 (build quality)
CREATE INDEX IF NOT EXISTS ix_deer_feature_vector_efficientnet_hnsw
ON deer
USING hnsw (feature_vector_efficientnet vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- T011: Create B-tree index ix_deer_embedding_version
CREATE INDEX IF NOT EXISTS ix_deer_embedding_version
ON deer (embedding_version);

-- T012: Add column comments documenting multi-scale and ensemble embeddings
COMMENT ON COLUMN deer.feature_vector_multiscale IS
'Multi-scale ResNet50 embedding combining texture (layer2), shapes (layer3), parts (layer4), and semantics (avgpool). 512 dimensions, L2 normalized. Feature 009-reid-enhancement.';

COMMENT ON COLUMN deer.feature_vector_efficientnet IS
'EfficientNet-B0 embedding for ensemble learning. Captures complementary features using compound scaling architecture. 512 dimensions, L2 normalized. Feature 009-reid-enhancement.';

COMMENT ON COLUMN deer.embedding_version IS
'Version identifier for embedding extraction. Values: v1_resnet50 (original), v2_multiscale (multi-scale only), v3_ensemble (multi-scale + EfficientNet). Feature 009-reid-enhancement.';

-- T013: Add migration validation checks (verify 3 columns and 3 indexes created)
DO $$
DECLARE
    col_count INTEGER;
    idx_count INTEGER;
BEGIN
    -- Check columns exist
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'deer'
      AND column_name IN ('feature_vector_multiscale', 'feature_vector_efficientnet', 'embedding_version');

    IF col_count != 3 THEN
        RAISE EXCEPTION 'Column creation failed. Expected 3 columns, found %', col_count;
    END IF;

    -- Check indexes exist
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE tablename = 'deer'
      AND indexname IN (
          'ix_deer_feature_vector_multiscale_hnsw',
          'ix_deer_feature_vector_efficientnet_hnsw',
          'ix_deer_embedding_version'
      );

    IF idx_count != 3 THEN
        RAISE EXCEPTION 'Index creation failed. Expected 3 indexes, found %', idx_count;
    END IF;

    RAISE NOTICE 'Migration successful: 3 columns and 3 indexes created';
END
$$;

COMMIT;

-- Rollback script (for reference, do not execute):
-- BEGIN;
-- DROP INDEX IF EXISTS ix_deer_feature_vector_multiscale_hnsw;
-- DROP INDEX IF EXISTS ix_deer_feature_vector_efficientnet_hnsw;
-- DROP INDEX IF EXISTS ix_deer_embedding_version;
-- ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_multiscale;
-- ALTER TABLE deer DROP COLUMN IF EXISTS feature_vector_efficientnet;
-- ALTER TABLE deer DROP COLUMN IF EXISTS embedding_version;
-- COMMIT;
