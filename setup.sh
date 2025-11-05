#!/bin/bash
# setup.sh - Setup script for thumper_counter project

echo "[INFO] Setting up Thumper Counter project..."

# Check if running in WSL
if [ ! -f /proc/version ] || ! grep -q Microsoft /proc/version; then
    echo "[WARN] Not running in WSL - some commands may not work"
fi

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "[INFO] Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Spec-kit project structure"
    echo "[OK] Git repository initialized"
else
    echo "[INFO] Git already initialized"
fi

# Install Python dependencies
echo "[INFO] Installing Python dependencies..."
pip install anthropic sqlalchemy fastapi uvicorn celery redis pytest

# Install Node dependencies for frontend (when ready)
# echo "[INFO] Installing Node dependencies..."
# cd src/frontend && npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "[INFO] Creating .env file..."
    cat > .env << 'EOF'
# Anthropic API Configuration
ANTHROPIC_API_KEY=your-api-key-here

# Database Configuration
POSTGRES_USER=deertrack
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=deer_tracking
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Image Processing
IMAGE_PATH=I:/Hopkins_Ranch_Trail_Cam_Pics
BATCH_SIZE=16
NUM_WORKERS=4

# ML Configuration
CONFIDENCE_THRESHOLD=0.7
REID_THRESHOLD=0.85
IOU_THRESHOLD=0.45

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
EOF
    echo "[OK] .env file created - Please update with your API key"
else
    echo "[INFO] .env file already exists"
fi

echo ""
echo "=========================================="
echo "[OK] Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your ANTHROPIC_API_KEY"
echo "2. Use the generation script:"
echo "   python3 scripts/generate.py specs/system.spec 'Create SQLAlchemy models'"
echo "3. Or manually implement based on specifications"
echo ""
echo "Available specs:"
echo "- specs/system.spec - Overall architecture"
echo "- specs/ml.spec - ML pipeline"
echo "- specs/api.spec - API endpoints"
echo "- specs/ui.spec - Frontend components"
echo "=========================================="
