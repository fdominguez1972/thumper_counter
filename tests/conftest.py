"""
Test Fixtures and Configuration

Provides shared fixtures for pytest test suite.
"""

import os
import pytest
from typing import Generator
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Set test environment variables before any imports
os.environ['REDIS_HOST'] = 'redis'
os.environ['REDIS_PORT'] = '6379'
os.environ['REDIS_DB'] = '0'
os.environ['DATABASE_URL'] = 'postgresql://deertrack:deertrack123@db:5432/deer_tracking'

# Import after setting environment variables
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.core.database import Base


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create test database engine.
    Uses the same database as development but runs in transaction.
    """
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_db_engine) -> Generator[Session, None, None]:
    """
    Create test database session with transaction rollback.
    Each test gets a fresh session that rolls back after completion.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def redis_client() -> Generator[redis.Redis, None, None]:
    """
    Create Redis client for testing.
    Automatically flushes test keys after each test.
    """
    client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )

    # Ensure connection is working
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.skip("Redis not available for testing")

    yield client

    # Cleanup: Remove all test keys after each test
    # Only delete keys starting with "export_job:" to avoid affecting other tests
    for key in client.scan_iter("export_job:*"):
        client.delete(key)

    client.close()


@pytest.fixture(scope="function")
def mock_celery():
    """
    Create mock Celery app for testing.
    Prevents actual task queueing during tests.
    """
    mock = MagicMock()

    # Mock send_task to return a fake task result
    def mock_send_task(task_name, args=None, kwargs=None, **options):
        task_result = Mock()
        task_result.id = "test-task-id-12345"
        task_result.state = "PENDING"
        task_result.ready.return_value = False
        task_result.successful.return_value = False
        return task_result

    mock.send_task = Mock(side_effect=mock_send_task)

    return mock


@pytest.fixture(scope="function")
def api_client() -> TestClient:
    """
    Create FastAPI test client.
    Allows making API requests without running server.
    """
    return TestClient(app)


@pytest.fixture
def sample_export_request():
    """
    Sample valid export request data for testing.
    Includes all required fields for PDFReportRequest schema.
    """
    return {
        "report_type": "seasonal_activity",
        "start_date": "2023-09-01",
        "end_date": "2024-01-31",
        "group_by": "month",
        "include_charts": True,
        "include_tables": True,
        "include_insights": True,
        "title": "Test Seasonal Activity Report"
    }


@pytest.fixture
def sample_job_status():
    """
    Sample export job status for testing.
    """
    return {
        "status": "completed",
        "job_id": "test-job-id-12345",
        "filename": "report_20251112_143022.pdf",
        "download_url": "/api/static/exports/report_20251112_143022.pdf",
        "completed_at": datetime.utcnow().isoformat()
    }
