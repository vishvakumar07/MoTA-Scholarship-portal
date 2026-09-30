-- ================================================================
-- MoTA Scholarship System — PostgreSQL Initialisation Script
-- ================================================================
-- This script runs ONCE when the postgres container starts for the
-- first time (via /docker-entrypoint-initdb.d/).
--
-- Alembic migrations handle all table creation.
-- This script only sets up prerequisites (extensions, settings).
-- ================================================================

-- Enable the pgvector extension for RAG/embedding support
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for efficient fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set the timezone
SET timezone = 'Asia/Kolkata';

-- Create a read-only reporting role (for future analytics/reporting tools)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mota_readonly') THEN
        CREATE ROLE mota_readonly;
    END IF;
END
$$;

-- Grant read-only access to the reporting role
GRANT CONNECT ON DATABASE mota_scholarship TO mota_readonly;
GRANT USAGE ON SCHEMA public TO mota_readonly;

-- Audit: notify on startup
DO $$
BEGIN
    RAISE NOTICE 'MoTA Scholarship database initialized with pgvector, pg_trgm, uuid-ossp extensions.';
END
$$;
