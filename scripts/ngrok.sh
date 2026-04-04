#!/bin/bash
# ngrok tunnel script - local machine usage
# ========== ==============================
# Use for remote access to your local Ollama setup

NGROK_TOKEN="${NGROK_AUTH_TOKEN:-}"
PORT="${PORT:-8080}"

echo "=============================="
echo "  Starting ngrok tunnel..."
echo "=============================="
echo

# Get ngrok auth (if not set)
if [ -z "$NGROK_TOKEN" ]; then
    echo "No auth token. Using free (unauthenticated) tunnel."
    echo "Free tunnels expire in 2 hours. Use auth token for longer sessions."
    
    # Start unauthenticated tunnel
    ngrok http -address 0.0.0.0:$PORT
else
    # Start authenticated tunnel
    export NGROK_AUTHTOKEN=$NGROK_TOKEN
    ngrok http -address 0.0.0.0:$PORT
fi
