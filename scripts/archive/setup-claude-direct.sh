#!/bin/bash
# setup-claude-direct.sh - Setup claude.exe for WSL use

echo "[INFO] Setting up Claude CLI for WSL (using Windows executable)..."

# Create alias to Windows claude.exe
CLAUDE_PATH="/mnt/c/Users/domin/.local/bin/claude.exe"

# Check if claude.exe exists
if [ -f "$CLAUDE_PATH" ]; then
    echo "[OK] Found claude.exe at $CLAUDE_PATH"
    
    # Add alias to bashrc
    if ! grep -q "alias claude=" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Claude CLI alias to Windows executable" >> ~/.bashrc
        echo "alias claude='$CLAUDE_PATH'" >> ~/.bashrc
        echo "[OK] Added claude alias to ~/.bashrc"
    else
        echo "[INFO] Claude alias already exists in ~/.bashrc"
    fi
    
    # Also add to current session
    alias claude="$CLAUDE_PATH"
    
    # Test the command
    echo ""
    echo "[INFO] Testing claude command..."
    claude --version
    
    echo ""
    echo "[OK] Setup complete!"
    echo ""
    echo "You can now use 'claude' in WSL!"
    echo "Note: Authentication will use your Windows credentials"
    echo ""
    echo "Try: claude --help"
    
else
    echo "[FAIL] claude.exe not found at expected location"
    echo "       Please check the path: $CLAUDE_PATH"
fi

# Source bashrc for current session
source ~/.bashrc 2>/dev/null || true
