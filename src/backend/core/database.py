"""
Database configuration and session management for Thumper Counter.

This module provides SQLAlchemy setup with connection pooling for PostgreSQL.
Based on specs/system.spec requirements:
- PostgreSQL 15
- Max 100 connections
- Connection pooling
- SSL support for production
"""

import os
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


# Database configuration from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "deertrack")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "deer_tracking")

# SSL mode for production (disable for local development)
POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "prefer")

# Connection pooling configuration
# Per system.spec: max 100 connections
# Reserve capacity for workers and monitoring tools
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Construct database URL
# Format: postgresql://user:password@host:port/database
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Add SSL parameters for production
if POSTGRES_SSL_MODE != "disable":
    DATABASE_URL += f"?sslmode={POSTGRES_SSL_MODE}"


# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries in debug mode
    future=True,  # Use SQLAlchemy 2.0 style
)


# Enable UUID extension on PostgreSQL connection
@event.listens_for(Engine, "connect")
def set_postgresql_extensions(dbapi_conn, connection_record):
    """
    Enable PostgreSQL extensions when a new connection is established.

    This ensures uuid-ossp extension is available for UUID generation.
    Future: Will also enable pgvector extension for feature vector storage.
    """
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        cursor.execute("COMMIT")
    except Exception as e:
        print(f"[WARN] Could not enable PostgreSQL extensions: {e}")
    finally:
        cursor.close()


# Session factory
# Each request will get its own session via dependency injection
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Allow accessing objects after commit
)


# Base class for all models
# All database models will inherit from this
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI routes.

    Provides a database session that automatically closes after the request.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This should be called once during application startup.
    In production, use Alembic migrations instead.

    Note: This will NOT drop existing tables, only create missing ones.
    """
    # Import all models here to ensure they are registered with Base
    # This must happen before create_all() is called
    from backend.models import Location, Image, Deer, Detection  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created")


def close_db() -> None:
    """
    Close all database connections.

    This should be called during application shutdown.
    """
    engine.dispose()
    print("[INFO] Database connections closed")


def get_db_info() -> dict:
    """
    Get database connection information for health checks.

    Returns:
        dict: Database connection details (without password)
    """
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "ssl_mode": POSTGRES_SSL_MODE,
    }


def test_connection() -> bool:
    """
    Test database connectivity.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection successful")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False


# Export commonly used objects
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "get_db_info",
    "test_connection",
]
