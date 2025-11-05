#!/usr/bin/env python3
"""
Quick database connection test for Thumper Counter.

Tests:
1. Environment variables are loaded
2. Database configuration is correct
3. PostgreSQL connection works
4. All models can be imported
5. Tables can be created (if database is running)
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("THUMPER COUNTER - DATABASE CONNECTION TEST")
print("=" * 60)
print()

# Test 1: Load environment variables
print("[1/5] Testing environment variables...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] .env file loaded")
except ImportError:
    print("[INFO] python-dotenv not installed, reading .env manually")
    # Manually load .env if dotenv not installed
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("[OK] .env file loaded manually")
    else:
        print("[WARN] .env file not found")

# Check database environment variables
required_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"[FAIL] Missing environment variables: {', '.join(missing_vars)}")
else:
    print(f"[OK] All required environment variables present")
    print(f"     User: {os.getenv('POSTGRES_USER')}")
    print(f"     Host: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}")
    print(f"     Database: {os.getenv('POSTGRES_DB')}")

print()

# Test 2: Import database module
print("[2/5] Testing database module import...")
try:
    from backend.core.database import engine, Base, get_db_info, test_connection
    print("[OK] Database module imported")

    # Show connection info
    info = get_db_info()
    print(f"     Connection pool size: {info['pool_size']}")
    print(f"     Max overflow: {info['max_overflow']}")
    print(f"     SSL mode: {info['ssl_mode']}")
except Exception as e:
    print(f"[FAIL] Could not import database module: {e}")
    sys.exit(1)

print()

# Test 3: Import all models
print("[3/5] Testing model imports...")
try:
    from backend.models import Location, Image, Deer, Detection
    from backend.models import ProcessingStatus, DeerSex
    print("[OK] All models imported successfully")
    print(f"     Location: {Location.__tablename__}")
    print(f"     Image: {Image.__tablename__}")
    print(f"     Deer: {Deer.__tablename__}")
    print(f"     Detection: {Detection.__tablename__}")
except Exception as e:
    print(f"[FAIL] Could not import models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Test database connection
print("[4/5] Testing PostgreSQL connection...")
try:
    connection_ok = test_connection()
    if not connection_ok:
        print("[FAIL] Database connection failed")
        print()
        print("TROUBLESHOOTING:")
        print("- Is PostgreSQL running?")
        print("  - Start with Docker: docker-compose up -d db")
        print("  - Or install locally: sudo apt install postgresql")
        print("- Are credentials in .env correct?")
        print("- Is port 5432 accessible?")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Database connection error: {e}")
    print()
    print("TROUBLESHOOTING:")
    print("- PostgreSQL is not running or not accessible")
    print("- Start with: docker-compose up -d db")
    print(f"- Check connection: psql -h {os.getenv('POSTGRES_HOST')} -U {os.getenv('POSTGRES_USER')} -d {os.getenv('POSTGRES_DB')}")
    sys.exit(1)

print()

# Test 5: Create tables (optional, only if database is running)
print("[5/5] Testing table creation...")
try:
    from backend.core.database import init_db
    init_db()

    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = ['locations', 'images', 'deer', 'detections']
    created_tables = [t for t in expected_tables if t in tables]

    if len(created_tables) == len(expected_tables):
        print(f"[OK] All {len(created_tables)} tables created:")
        for table in created_tables:
            columns = inspector.get_columns(table)
            print(f"     - {table} ({len(columns)} columns)")
    else:
        missing = [t for t in expected_tables if t not in tables]
        print(f"[WARN] Some tables missing: {missing}")

except Exception as e:
    print(f"[FAIL] Could not create tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("[OK] ALL TESTS PASSED!")
print("=" * 60)
print()
print("Database is ready for use!")
print()
print("Next steps:")
print("1. Use Alembic for migrations: alembic init alembic")
print("2. Create FastAPI application")
print("3. Start building API endpoints")
print()
