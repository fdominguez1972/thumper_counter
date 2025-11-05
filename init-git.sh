#!/bin/bash
# init-git.sh - Initialize git repository for thumper_counter project

echo "[INFO] Initializing git repository for thumper_counter..."

# Navigate to project directory
cd /mnt/i/projects/thumper_counter || {
    echo "[FAIL] Could not navigate to /mnt/i/projects/thumper_counter"
    echo "       Please ensure you're running this from WSL2"
    exit 1
}

# Initialize git
git init

# Configure git (optional - customize with your info)
# git config user.name "Your Name"
# git config user.email "your.email@example.com"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Project structure with spec-kit setup and CLAUDE.md preferences"

echo "[OK] Git repository initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Add remote repository: git remote add origin <your-github-url>"
echo "2. Create specs in the specs/ directory"
echo "3. Start implementing with claude-cli"
