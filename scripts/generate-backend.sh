#!/bin/bash
# generate-backend.sh - Generate backend components with claude-cli

echo "[INFO] Generating backend components with Claude CLI..."
echo ""

# Function to generate and save file
generate_file() {
    local spec=$1
    local output=$2
    local prompt=$3
    
    echo "[INFO] Generating $output..."
    
    # Create directory if it doesn't exist
    mkdir -p $(dirname $output)
    
    # Generate with claude
    claude generate --context "$spec" "$prompt" > "$output"
    
    if [ -s "$output" ]; then
        echo "[OK] Generated $output"
    else
        echo "[FAIL] Failed to generate $output"
    fi
}

# Check if claude is available
if ! command -v claude &> /dev/null; then
    echo "[FAIL] claude command not found. Please install claude-cli first."
    exit 1
fi

echo "=========================================="
echo "Starting Backend Generation"
echo "=========================================="
echo ""

# 1. Database Configuration
generate_file "specs/system.spec" \
    "src/backend/core/database.py" \
    "Create a production-ready SQLAlchemy database configuration for PostgreSQL with connection pooling, async support, and a base model class. Include session management and database initialization functions."

# 2. Base Models
generate_file "specs/system.spec" \
    "src/backend/models/base.py" \
    "Create base SQLAlchemy model class with common fields (id, created_at, updated_at) and helper methods for all models to inherit from."

# 3. Image Model
generate_file "specs/system.spec" \
    "src/backend/models/image.py" \
    "Create the Image SQLAlchemy model with: UUID primary key, filename, path, timestamp, location_id foreign key, EXIF data as JSON, processing_status enum (QUEUED, PROCESSING, COMPLETED, FAILED), and created_at timestamp."

# 4. Deer Model  
generate_file "specs/system.spec" \
    "src/backend/models/deer.py" \
    "Create the Deer SQLAlchemy model with: UUID primary key, optional name, sex enum (buck/doe/fawn/unknown), first_seen, last_seen, feature_vector as Array of Float, confidence score, sighting_count, and relationship to detections."

# 5. Detection Model
generate_file "specs/system.spec" \
    "src/backend/models/detection.py" \
    "Create the Detection SQLAlchemy model with: UUID primary key, image_id foreign key, deer_id foreign key (nullable), bounding box as JSON object with x,y,width,height, confidence float, classification string, and created_at timestamp."

# 6. Location Model
generate_file "specs/system.spec" \
    "src/backend/models/location.py" \
    "Create the Location SQLAlchemy model with: UUID primary key, name string, coordinates as JSON with lat/lon, camera_model, active boolean, image_count integer, and relationships to images."

# 7. FastAPI Main App
generate_file "specs/api.spec" \
    "src/backend/app/main.py" \
    "Create the main FastAPI application with: CORS configuration for localhost:3000, health check endpoint, metrics endpoint, API routers setup, error handlers, and startup/shutdown events for database connection."

# 8. API Configuration
generate_file "specs/api.spec" \
    "src/backend/core/config.py" \
    "Create a Pydantic settings configuration class that loads from environment variables: database URL, Redis URL, API keys, ML thresholds, CORS origins, and processing parameters."

echo ""
echo "=========================================="
echo "Generation Complete!"
echo "=========================================="
echo ""
echo "Files generated in src/backend/"
echo ""
echo "Next steps:"
echo "1. Review generated files"
echo "2. Install dependencies: pip install -r src/backend/requirements.txt"
echo "3. Run tests: pytest tests/"
echo "4. Start development server: uvicorn src.backend.app.main:app --reload"
echo ""
echo "To generate more components:"
echo "  claude chat --context specs/"
echo "=========================================="
