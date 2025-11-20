# Database Migrations

Manual SQL migrations for Thumper Counter database schema changes.

## Migration History

| Migration | Date | Sprint | Description |
|-----------|------|--------|-------------|
| 001_initial_schema.sql | 2025-11-04 | 1 | Initial database schema (locations, images, detections, deer) |
| 002_add_deer_status.sql | 2025-11-05 | 3 | Add status, species, notes, timestamps to deer table |
| 003_add_processing_status.sql | 2025-11-05 | 3 | Add processing_status enum to images table |
| 004_add_deer_classification.sql | 2025-11-06 | 4 | Update detection.classification for multi-class model |
| 005_migrate_to_pgvector.sql | 2025-11-06 | 5 | Convert feature_vector to pgvector type with HNSW index |

## Applying Migrations

### From Host Machine
```bash
# Apply specific migration
docker-compose exec -T db psql -U deertrack deer_tracking < migrations/005_migrate_to_pgvector.sql

# Apply all migrations in order
for f in migrations/*.sql; do
    echo "[INFO] Applying $f..."
    docker-compose exec -T db psql -U deertrack deer_tracking < "$f"
done
```

### From Inside Container
```bash
# Enter database container
docker-compose exec db psql -U deertrack deer_tracking

# Run migration
\i /migrations/005_migrate_to_pgvector.sql
```

## Migration Guidelines

1. **Naming Convention**: `NNN_description.sql` (e.g., `005_migrate_to_pgvector.sql`)
2. **Transaction Wrapper**: Always use BEGIN/COMMIT for atomicity
3. **Idempotency**: Use IF EXISTS/IF NOT EXISTS where possible
4. **Comments**: Document WHY changes are needed, not just WHAT
5. **Validation**: Include validation queries at bottom of migration
6. **Rollback**: Consider creating matching rollback migration

## Current Schema Version

Check current schema version:
```sql
SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1;
```

Note: schema_version table will be added in future migration for automated tracking.

## pgvector Setup (Sprint 5)

The pgvector extension is required for Sprint 5 re-identification features.

### Enable Extension
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Verify Installation
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Test Vector Operations
```sql
-- Create test vector
SELECT '[1,2,3]'::vector(3);

-- Test cosine distance
SELECT '[1,2,3]'::vector(3) <=> '[4,5,6]'::vector(3) AS distance;
```

## Troubleshooting

### pgvector Extension Not Found
If you see error: `extension "vector" is not available`, ensure you're using the pgvector-enabled PostgreSQL image:
```yaml
# docker-compose.yml
db:
  image: ankane/pgvector:v0.5.1
```

### Array to Vector Conversion
If migration 005 fails with type conversion error, check for NULL or invalid array values:
```sql
SELECT id, array_length(feature_vector, 1) AS dims
FROM deer
WHERE feature_vector IS NOT NULL
  AND array_length(feature_vector, 1) != 512;
```

### Index Build Time
HNSW index creation can take several minutes for large datasets:
- <1,000 deer: ~seconds
- 1,000-10,000 deer: ~1-5 minutes
- >10,000 deer: ~5-30 minutes

Monitor progress:
```sql
SELECT schemaname, tablename, indexname
FROM pg_stat_progress_create_index;
```
