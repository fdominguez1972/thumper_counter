-- PostgreSQL Performance Optimizations for Thumper Counter
-- Sprint 8: Database Write Bottleneck Fix
-- Date: 2025-11-07
--
-- WHY: Current settings are conservative defaults. Our workload is:
--   - Heavy INSERTS (detections, deer profiles)
--   - Frequent UPDATEs (image status, deer_id linking)
--   - Medium SELECT queries (re-ID similarity search)
--   - 16GB RAM available on host
--
-- References:
--   - https://pgtune.leopard.in.ua/ (DB Type: Data warehouse)
--   - PostgreSQL 15 documentation

-- Memory Settings
-- shared_buffers: RAM for caching data (25% of system RAM = 4GB)
ALTER SYSTEM SET shared_buffers = '4GB';

-- effective_cache_size: Estimate of OS + PG cache (75% of RAM = 12GB)
ALTER SYSTEM SET effective_cache_size = '12GB';

-- work_mem: RAM per operation (sorting, hashing)
-- Increased from 4MB to 64MB for complex re-ID queries
ALTER SYSTEM SET work_mem = '64MB';

-- maintenance_work_mem: RAM for VACUUM, CREATE INDEX
-- Increased from 64MB to 1GB for faster maintenance
ALTER SYSTEM SET maintenance_work_mem = '1GB';

-- Write Performance
-- wal_buffers: Write-ahead log buffer (-1 = auto-tune to 1/32 of shared_buffers)
ALTER SYSTEM SET wal_buffers = '-1';

-- checkpoint_completion_target: Spread checkpoint writes (0.9 = 90% of checkpoint interval)
-- Already optimal at 0.9
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- max_wal_size: Maximum WAL size before checkpoint
-- Increased from 1GB to 4GB to reduce checkpoint frequency
ALTER SYSTEM SET max_wal_size = '4GB';

-- min_wal_size: Minimum WAL size to keep
ALTER SYSTEM SET min_wal_size = '1GB';

-- Connection Settings
-- max_connections: Already at 100 (sufficient)
-- ALTER SYSTEM SET max_connections = 100;

-- Query Planner
-- random_page_cost: SSD vs HDD cost (4.0 = HDD, 1.1 = SSD)
-- Assuming SSD storage
ALTER SYSTEM SET random_page_cost = 1.1;

-- effective_io_concurrency: Number of concurrent disk I/O operations
-- 200 for SSD (vs 1-2 for HDD)
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Parallel Query Settings
-- max_worker_processes: Background workers (default 8 is fine)
ALTER SYSTEM SET max_worker_processes = 8;

-- max_parallel_workers_per_gather: Workers per Gather node
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- max_parallel_workers: Total parallel workers
ALTER SYSTEM SET max_parallel_workers = 8;

-- Vacuum Settings
-- autovacuum_max_workers: Concurrent autovacuum processes
ALTER SYSTEM SET autovacuum_max_workers = 4;

-- autovacuum_naptime: Time between autovacuum runs
-- Reduced from 1min to 30s for heavy INSERT workload
ALTER SYSTEM SET autovacuum_naptime = '30s';

-- Logging (for debugging - disable in production)
-- log_min_duration_statement: Log slow queries (> 1s)
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- log_line_prefix: Add timestamp and process info
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Print current settings for verification
SELECT name, setting, unit, source
FROM pg_settings
WHERE name IN (
    'shared_buffers',
    'effective_cache_size',
    'work_mem',
    'maintenance_work_mem',
    'max_wal_size',
    'random_page_cost',
    'effective_io_concurrency'
)
ORDER BY name;
