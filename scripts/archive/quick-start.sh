#!/bin/bash
# quick-start.sh - Generate first working component

echo "[INFO] Quick Start - Generating your first component..."

# Create necessary directories
mkdir -p src/backend/core
mkdir -p src/backend/models
mkdir -p src/backend/app

# Generate a simple working example
echo "[INFO] Generating database configuration..."

# Use claude to generate
claude chat << 'EOF'
Read this specification and generate a complete SQLAlchemy database configuration:

From specs/system.spec:
- PostgreSQL 15 database
- Connection pooling with 100 max connections
- Async support
- Base model with common fields

Create a complete database.py file with:
1. Database URL construction from environment variables
2. Session management
3. Base model class
4. Database initialization function

Output only the Python code, no explanations.
EOF

echo ""
echo "[OK] Check the output above and save it to src/backend/core/database.py"
echo ""
echo "Next: Run 'claude chat --context specs/' for interactive development"
