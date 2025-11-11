#!/bin/bash
# Apply PostgreSQL Performance Optimizations
# Sprint 8: Database Write Bottleneck Fix
# Date: 2025-11-07

set -e

echo "[INFO] Applying PostgreSQL performance optimizations..."

# Run optimization SQL script
docker-compose exec -T db psql -U deertrack deer_tracking < docker/init-db/optimize_postgres.sql

echo "[OK] Optimization settings applied"
echo "[INFO] Settings will take effect after PostgreSQL restart"
echo ""
echo "To restart PostgreSQL:"
echo "  docker-compose restart db"
echo ""
echo "To verify settings after restart:"
echo "  docker-compose exec db psql -U deertrack deer_tracking -c \"SELECT name, setting, unit FROM pg_settings WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem');\""
