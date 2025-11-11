#!/bin/bash
# setup-claude-wsl.sh - Setup Claude CLI in WSL with proper authentication

echo "[INFO] Setting up Claude CLI in WSL..."

# Function to setup browser integration
setup_browser() {
    echo "[INFO] Setting up browser integration for WSL..."
    
    # Check if wslu is installed
    if ! command -v wslview &> /dev/null; then
        echo "[INFO] Installing wslu for browser integration..."
        sudo apt update
        sudo apt install -y wslu
    fi
    
    # Set BROWSER environment variable
    export BROWSER=wslview
    
    # Add to bashrc if not already there
    if ! grep -q "export BROWSER=wslview" ~/.bashrc; then
        echo 'export BROWSER=wslview' >> ~/.bashrc
        echo "[OK] Browser integration configured"
    fi
}

# Function to setup API key
setup_api_key() {
    echo ""
    echo "[INFO] Setting up API authentication..."
    echo "Choose authentication method:"
    echo "1. Enter API key manually"
    echo "2. Copy from Windows config"
    echo "3. Use environment variable"
    
    read -p "Select option (1-3): " choice
    
    case $choice in
        1)
            read -p "Enter your Anthropic API key: " api_key
            export ANTHROPIC_API_KEY="$api_key"
            echo "export ANTHROPIC_API_KEY=\"$api_key\"" >> ~/.bashrc
            
            # Also create config file
            mkdir -p ~/.config/claude
            cat > ~/.config/claude/config.json << EOF
{
    "api_key": "$api_key",
    "default_model": "claude-3-opus-20240229"
}
EOF
            chmod 600 ~/.config/claude/config.json
            echo "[OK] API key configured"
            ;;
            
        2)
            # Try to find Windows config
            WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
            
            # Check common locations
            if [ -f "/mnt/c/Users/$WIN_USER/.config/claude/config.json" ]; then
                mkdir -p ~/.config/claude
                cp "/mnt/c/Users/$WIN_USER/.config/claude/config.json" ~/.config/claude/
                echo "[OK] Copied config from Windows"
            elif [ -f "/mnt/c/Users/$WIN_USER/.claude/config.json" ]; then
                mkdir -p ~/.config/claude
                cp "/mnt/c/Users/$WIN_USER/.claude/config.json" ~/.config/claude/
                echo "[OK] Copied config from Windows"
            else
                echo "[FAIL] Could not find Windows config"
                echo "       Please check Windows config location"
            fi
            ;;
            
        3)
            read -p "Enter your Anthropic API key: " api_key
            export ANTHROPIC_API_KEY="$api_key"
            echo "export ANTHROPIC_API_KEY=\"$api_key\"" >> ~/.bashrc
            echo "[OK] Environment variable set"
            ;;
    esac
}

# Function to test claude
test_claude() {
    echo ""
    echo "[INFO] Testing Claude CLI..."
    
    # Check if claude command exists
    if command -v claude &> /dev/null; then
        echo "[OK] Claude command found"
        claude --version
    else
        echo "[WARN] Claude command not found"
        echo ""
        echo "Try installing with one of these methods:"
        echo "1. pip install anthropic"
        echo "2. npm install -g @anthropic/cli (if it exists)"
        echo "3. Copy from Windows: /mnt/c/path/to/claude"
    fi
}

# Main setup flow
echo "=========================================="
echo "Claude CLI WSL Setup"
echo "=========================================="

setup_browser
setup_api_key
test_claude

echo ""
echo "=========================================="
echo "Setup complete!"
echo ""
echo "If claude command is not found, you may need to:"
echo "1. Install it: pip install anthropic"
echo "2. Add to PATH if installed elsewhere"
echo "3. Restart terminal: source ~/.bashrc"
echo ""
echo "To use with our project:"
echo "cd /mnt/i/projects/thumper_counter"
echo "claude chat --context specs/"
echo "=========================================="
