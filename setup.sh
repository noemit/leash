#!/bin/bash
# Interactive setup for local Ollama AI browser wrapper
# ========== ==============================
# For local machine (Mac/Linux/Windows)

set -e

echo "=========================================="
echo "  Ollama Local AI Browser Setup"
echo "=========================================="
echo

# Step 1: Check prerequisites
echo "Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python3 not found. Install Python3 first:"
    echo "  Mac: brew install python"
    echo "  Linux: sudo apt install python3"
    echo "  Windows: https://www.python.org/downloads/"
    exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
    echo "Error: Ollama not found. Install from: https://ollama.ai"
    echo "After installing, run: ollama pull llama3.2"
    read -p "Do you want to exit anyway? [y/N]: " choice
    [[ $choice =~ ^[Yy]$ ]] && exit 1
fi

echo "✓ Prerequisites met"
echo

# Step 2: Pull model
echo "=========================================="
echo "  Ollama Model Selection"
echo "=========================================="
echo

echo "Select a model by entering the number:"
echo ""
echo "  A) llama3.2       → 4GB, general purpose (RECOMMENDED)"
echo "  B) qwen2.5:7b     → 9GB, multilingual"
echo "  C) mistral        → 3.5GB, fast reasoning"
echo "  D) phi4           → 3.5GB, compact smart"
echo "  E) llama3.1:8b    → 6GB, large context"
echo "  F) phi3.5         → 2GB, very lightweight"
echo "  G) gemma2:9b      → 9GB, google-based"
echo ""
echo "  Enter your choice (A-G):"
read -p "Selection: " choice

case $choice in
    A|a) model="llama3.2"       ;;
    B|b) model="qwen2.5:7b"     ;;
    C|c) model="mistral"        ;;
    D|d) model="phi4"           ;;
    E|e) model="llama3.1:8b"    ;;
    F|f) model="phi3.5"         ;;
    G|g) model="gemma2:9b"      ;;
    *)
        echo "Invalid selection. Defaulting to: llama3.2"
        model="llama3.2"
        ;;
esac

echo "Pulling model: $model (this may take a few minutes)..."
ollama pull "$model"

echo
echo "Model loaded! ✓"
echo

# Step 3: Setup options
echo "=========================================="
echo "  Binding Configuration"
echo "=========================================="
echo

echo "1) Run wrapper on this computer (localhost only)"
echo "2) Run on cloud VPS (SSH tunnel needed)"
echo "3) Run via Docker"
echo

read -p "Select option [1]: " option
option=${option:-1}

case $option in
    1)
        echo "Binding to localhost only."
        echo "Access via local IP or SSH tunnel."
        echo

        ip=$(hostname -I | awk '{print $1}')
        echo "Local IP: $ip"
        echo "Open in browser: http://$ip:8080"
        ;;
    2)
        echo "Binding to cloud VPS. Access via ngrok or SSH tunnel."
        echo
        echo "You'll need to:"
        echo "  1. Run 'ngrok http 8080' on your cloud server, or"
        echo "  2. Use SSH tunnel: ssh -L 8080:localhost:8080 user@vps"
        echo
        ;;
    3)
        echo "Starting Docker containers..."
        echo
        if [ -f docker-compose.yml ]; then
            docker-compose up -d
        else
            echo "No docker-compose.yml found. Create it first."
        fi
        echo
        ;;
esac

# Step 4: Start server
echo
echo "=========================================="
echo "  Starting Web Server"
echo "=========================================="
echo

cd server
echo "Server starting on http://localhost:8080"
echo "Model: $model"
echo

if [ "$option" = "3" ]; then
    # Docker - don't start python process
    echo "Docker running. Access URL shown above."
else
    # Local/SSH
    python api.py &
    SERVER_PID=$!
    
    echo
    echo "PID: $SERVER_PID"
    echo
    echo "Access your AI from phone/browser at:"
    echo "  → http://localhost:8080"
    echo
    echo "Or use your tunnel/ngrok URL:"
    echo "  → (if using cloud/server setup)"
    echo
    echo "Press Ctrl+C to stop the server."
    wait $SERVER_PID
fi
