#!/bin/bash
# generate-specs-from-code.sh - Generate specifications from existing code using spec-kit
# This analyzes your current implementation and creates specs documenting what was built

# Get the project root directory (parent of scripts folder)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

echo "=========================================="
echo "Spec-Kit: Generate Specs from Existing Code"
echo "=========================================="
echo "Working directory: $PROJECT_ROOT"
echo ""

# Check if spec-kit is installed
if ! command -v specify &> /dev/null; then
    echo "[WARN] spec-kit CLI not found"
    echo ""
    echo "The 'specify' command might not be available or might work differently."
    echo "Let's try alternative approaches..."
    echo ""
fi

# Create generated specs directory
mkdir -p specs/generated
echo "[INFO] Output directory: specs/generated/"
echo ""

echo "=========================================="
echo "Creating Documentation from Code Analysis"
echo "=========================================="
echo ""

# Generate comprehensive documentation
{
    echo "# Thumper Counter - Implementation Documentation"
    echo "Generated: $(date)"
    echo ""
    
    echo "## Project Structure"
    echo '```'
    tree -I '__pycache__|*.pyc|node_modules' -L 3 2>/dev/null || {
        echo "Project structure:"
        find . -type f -name "*.py" | grep -v __pycache__ | sort
    }
    echo '```'
    echo ""
    
    echo "## Database Models"
    echo "Location: src/backend/models/"
    echo '```python'
    for model in src/backend/models/*.py; do
        if [ -f "$model" ]; then
            echo "# File: $model"
            grep "^class\|def \|    def " "$model" | grep -v "__"
            echo ""
        fi
    done
    echo '```'
    echo ""
    
    echo "## API Endpoints"
    echo "Location: src/backend/api/"
    echo '```python'
    for api in src/backend/api/*.py; do
        if [ -f "$api" ]; then
            echo "# File: $api"
            grep "@router\.\|@app\.\|def \|async def " "$api" | grep -v "__pycache__"
            echo ""
        fi
    done
    echo '```'
    echo ""
    
    echo "## Worker Tasks"
    echo "Location: src/worker/"
    echo '```python'
    for task in src/worker/tasks/*.py; do
        if [ -f "$task" ]; then
            echo "# File: $task"
            grep "@celery\|@task\|def \|class " "$task" 2>/dev/null
            echo ""
        fi
    done
    echo '```'
    echo ""
    
    echo "## Configuration Files"
    echo '```'
    ls -la *.yml *.yaml *.env* *.json 2>/dev/null | grep -v ".env"
    echo '```'
    echo ""
    
    echo "## Python Dependencies"
    echo '```'
    if [ -f "requirements.txt" ]; then
        echo "Main requirements:"
        grep -E "^[^#]" requirements.txt | head -20
    fi
    if [ -f "src/backend/requirements.txt" ]; then
        echo ""
        echo "Backend requirements:"
        grep -E "^[^#]" src/backend/requirements.txt | head -10
    fi
    echo '```'
    
} > specs/generated/implementation.md

echo "[OK] Implementation documentation saved to specs/generated/implementation.md"
echo ""

# Try to extract actual implementation details
echo "=========================================="
echo "Extracting Implementation Details"
echo "=========================================="

# Models summary
echo ""
echo "Database Models Found:"
ls -1 src/backend/models/*.py 2>/dev/null | grep -v __init__ | xargs -I {} basename {} .py | sed 's/^/  - /'

# API routes summary
echo ""
echo "API Routes Found:"
grep -h "@router\." src/backend/api/*.py 2>/dev/null | sed 's/.*@router\./  - /' | sort -u

# Worker tasks summary
echo ""
echo "Worker Tasks Found:"
grep -h "@task\|@celery" src/worker/tasks/*.py 2>/dev/null | sed 's/.*def /  - /' | sed 's/(.*//'

echo ""
echo "=========================================="
echo "Comparing with Original Specs"
echo "=========================================="
echo ""
echo "Original specifications:"
for spec in specs/*.spec; do
    if [ -f "$spec" ] && [[ ! "$spec" == *"generated"* ]]; then
        lines=$(wc -l < "$spec")
        echo "  - $(basename "$spec"): $lines lines"
    fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Since 'specify' command didn't work as expected, we created:"
echo "  - specs/generated/implementation.md (full documentation)"
echo ""
echo "You can:"
echo "1. Review the implementation doc: cat specs/generated/implementation.md"
echo "2. Compare with original specs manually"
echo "3. Update specs based on what was actually built"
echo "4. Use Claude to analyze differences"
echo ""
echo "To see what was built vs planned:"
echo "  diff -u specs/system.spec specs/generated/implementation.md"
echo ""
echo "[OK] Documentation generation complete!"
