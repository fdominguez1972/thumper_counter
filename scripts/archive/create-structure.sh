#!/bin/bash
# create-structure.sh - Create project directory structure

echo "[INFO] Creating project directory structure..."

# Backend directories
mkdir -p src/backend/{app,core,models,schemas,api,services}
mkdir -p src/backend/alembic/versions

# Worker directories
mkdir -p src/worker/tasks
mkdir -p src/worker/ml

# Frontend directories
mkdir -p src/frontend/{src,public}
mkdir -p src/frontend/src/{components,pages,services,store}

# Test directories
mkdir -p tests/{unit,integration,e2e}
mkdir -p tests/unit/{backend,worker,frontend}

# Docker directories
mkdir -p docker/dockerfiles

# Create __init__.py files for Python packages
touch src/backend/__init__.py
touch src/backend/app/__init__.py
touch src/backend/core/__init__.py
touch src/backend/models/__init__.py
touch src/backend/schemas/__init__.py
touch src/backend/api/__init__.py
touch src/backend/services/__init__.py
touch src/worker/__init__.py
touch src/worker/tasks/__init__.py
touch src/worker/ml/__init__.py

echo "[OK] Directory structure created!"

# Show the structure
echo ""
echo "Project structure:"
tree src/ -d -L 3 2>/dev/null || find src -type d | sed 's|[^/]*/| |g'
