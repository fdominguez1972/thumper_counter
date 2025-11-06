"""
Thumper Counter - FastAPI Application

Main application entry point for the deer tracking system.
Provides REST API for image upload, deer profiles, and detection results.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.database import (
    init_db,
    close_db,
    test_connection,
    get_db_info,
    engine
)
from backend.api import locations, images, processing, deer

# Celery app for sending tasks from backend
# WHY: Backend cannot import worker modules directly, use send_task() instead
import os
from celery import Celery

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

celery_app = Celery(
    'thumper_counter',
    broker=REDIS_URL,
    backend=REDIS_URL,
)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.

    Startup:
    - Test database connection
    - Initialize database tables

    Shutdown:
    - Close database connections
    """
    # Startup
    print("=" * 60)
    print("[INFO] Starting Thumper Counter API...")
    print("=" * 60)

    # Test database connection
    print("[INFO] Testing database connection...")
    if not test_connection():
        print("[FAIL] Database connection failed - exiting")
        raise RuntimeError("Cannot connect to database")

    # Initialize database tables
    print("[INFO] Initializing database tables...")
    try:
        init_db()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[FAIL] Database initialization failed: {e}")
        raise

    # Display database info
    db_info = get_db_info()
    print(f"[INFO] Connected to: {db_info['database']}@{db_info['host']}:{db_info['port']}")
    print(f"[INFO] Pool size: {db_info['pool_size']} (max overflow: {db_info['max_overflow']})")

    print("=" * 60)
    print("[OK] Thumper Counter API is ready!")
    print("=" * 60)

    yield

    # Shutdown
    print("[INFO] Shutting down Thumper Counter API...")
    close_db()
    print("[OK] Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Thumper Counter API",
    description="Deer tracking system with ML-based re-identification",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS middleware configuration
# Allow frontend to access API from different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:80",     # Frontend in Docker
        "http://localhost:8001",   # API access
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(locations.router)
app.include_router(images.router)
app.include_router(processing.router)
app.include_router(deer.router)


# Health check endpoint
@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
    summary="Health check endpoint",
    description="Check if the API and database are operational"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Health status including database connectivity
    """
    # Test database connection
    db_healthy = False
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
            db_healthy = True
    except Exception as e:
        print(f"[WARN] Database health check failed: {e}")

    # Build health response
    health_status = {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "thumper_counter_api",
        "version": "1.0.0",
        "database": {
            "connected": db_healthy,
            "type": "postgresql",
        }
    }

    if db_healthy:
        db_info = get_db_info()
        health_status["database"].update({
            "host": db_info["host"],
            "port": db_info["port"],
            "database": db_info["database"],
        })

    # Return 200 OK even if degraded (some systems want this)
    # Monitoring systems can check the status field
    return health_status


# Root endpoint
@app.get(
    "/",
    tags=["System"],
    response_model=Dict[str, Any],
    summary="API information",
    description="Get basic information about the API"
)
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.

    Returns:
        dict: API metadata and available endpoints
    """
    return {
        "name": "Thumper Counter API",
        "version": "1.0.0",
        "description": "Deer tracking system with ML-based re-identification",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "images": "/api/images",
            "locations": "/api/locations",
            "deer": "/api/deer",
            "detections": "/api/detections",
        }
    }


# API version endpoint
@app.get(
    "/api/version",
    tags=["System"],
    response_model=Dict[str, str],
    summary="Get API version",
    description="Returns the current API version and build information"
)
async def get_version() -> Dict[str, str]:
    """
    Get API version information.

    Returns:
        dict: Version details
    """
    return {
        "api_version": "1.0.0",
        "build_date": "2024-11-04",
        "python_version": "3.11",
        "framework": "FastAPI",
    }


# Catch-all 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler with helpful message."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint {request.url.path} does not exist",
            "documentation": "/docs",
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Logs the error and returns a generic 500 response.
    """
    print(f"[ERROR] Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please contact support.",
        }
    )


# Startup message
if __name__ == "__main__":
    import uvicorn

    print("[INFO] Starting Thumper Counter API in development mode...")
    print("[INFO] API will be available at: http://localhost:8000")
    print("[INFO] Documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info",
    )
