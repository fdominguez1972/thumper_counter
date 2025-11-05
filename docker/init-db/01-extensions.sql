-- Initialize PostgreSQL extensions for Thumper Counter
-- This script runs automatically when the database is first created

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Future: Enable pgvector for efficient similarity search
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Create database info
SELECT version();

-- Verify extensions
SELECT * FROM pg_extension;
