# Ollama Browser Wrapper - Setup Guide
# ======================================

## Overview

This wrapper runs **Ollama's local AI models** in a browser-accessible format.
Perfect for running **Llama, Qwen, Mistral** models locally and talking to them via browser or phone.

## System Requirements

- **Ollama installed** on your machine (Mac/Linux/Windows)
- **At least 8GB RAM** (free)
- **Model loaded** before use (e.g., llama3.2, qwen2.5)
- **Port 11434** available for Ollama
- **Port 8080** available for wrapper

## Quick Start (3 Minutes)

### 1. Install Ollama

```bash
# Download for your platform
# Mac: https://ollama.ai/download
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Windows: https://ollama.ai/download-windows

# Verify Ollama is running
ollama --version

# 2. Pull a model (choose one)
ollama pull llama3.2          # 4GB, fast, smart
ollama pull qwen2.5:7b        # 5GB, multilingual
ollama pull mistral           # 3.5GB, fast
ollama pull phi4              # 3.5GB, reasoning

# 3. Verify model is loaded
ollama show llama3.2
```

### 2. Start the Wrapper

```bash
cd phone-harness

# Option A: Docker (cleanest)
docker-compose up -d

# Option B: Pure Python
pip install -r requirements.txt
cd server
python api.py
```

### 3. Get Your URL

```bash
# For local access
curl http://localhost:8080

# For external access, use tunnels:
# ngnrok:
ngrok http 8080

# SSH tunnel (to cloud VPS):
ssh -L 8080:localhost:8080 user@your-vps.com
```

### 4. Open from Phone

Open browser with:
```
http://localhost:8080
```

Or your tunnel URL.

**Start chatting with your local AI!**

---

## Configuration

### Edit `/config/tunnel.conf`:

```bash
# Ollama backend
OLLAMA_HOST=http://127.0.0.1:11434      # Local default
OLLAMA_MODEL=llama3.2                    # Your model

# Network binding
HOST=0.0.0.0                             # Allow external
PORT=8080

# Optional: API key for security
# SECRET_TOKEN=your-api-key
```

### Common Models to Try

```bash
# Lightweight & Fast
ollama pull llama3.2              # 4GB, great for general tasks
ollama pull phi4                  # 3.5GB, reasoning focus
ollama pull mistral              # 3.5GB, fast

# Mid-size
ollama pull qwen2.5:14b           # 9GB, multilingual

# Large-capable
ollama pull llama3.1:8b           # 6GB, powerful
ollama pull llama3.1:405b         # 380GB (80G context)
```

---

## Architecture

```
┌──────────────────────────────┐
│   Your Phone Browser         │
│   (Chrome, Safari, Firefox)  │
└───────────┬──────────────────┘
            │ HTTPS/WSS
            │
┌───────────▼──────────────────┐
│   FastAPI Wrapper API        │
│   Port: 8080                 │
│   - Proxies to Ollama        │
│   - Returns streaming text   │
└───────────┬──────────────────┘
            │
            │ HTTP/JSON
            │
┌───────────▼──────────────────┐
│   Ollama Server              │
│   Port: 11434                │
│   - Loads models locally     │
│   - Generates responses      │
└───────────┬──────────────────┘
            │
            │ RAM Disk
            │
┌───────────▼──────────────────┐
│   Model Files (GGUF)         │
│   - ~/.ollama/models/        │
└──────────────────────────────┘
```

---

## How It Works

1. **You type** in browser (phone)
2. **Request** sent to wrapper API (port 8080)
3. **Wrapper** proxies to Ollama (11434)
4. **Ollama** loads model from RAM/GPU
5. **Response** streams back to you
6. **Model stays loaded** in memory for fast replies

---

## Development Mode

```bash
cd server
python api.py --reload
```

Runs with auto-reload for development.

---

## Production Mode

```bash
# Docker production
docker-compose up -d

# Or run with gunicorn
pip install gunicorn
gunicorn server.api:app -b 127.0.0.1:8080
```

---

## Security

### Local Only (Default)
```bash
OLLAMA_HOST=http://127.0.0.1:11434
HOST=127.0.0.1
```

### External Access Needed
```bash
OLLAMA_HOST=http://0.0.0.0:11434
HOST=0.0.0.0
```

### Optional Security
- Add `SECRET_TOKEN` for API key checks
- Rate limiting already included
- CORS configuration available

---

## Troubleshooting

### Problem: `Ollama connection refused`
```bash
# Fix: Start Ollama
ollama serve &

# Or use system service (Linux/Mac)
ollama serve
```

### Problem: `Model not found`
```bash
# Pull model first
ollama pull llama3.2

# Then restart
python api.py
```

### Problem: `Port 8080 in use`
```bash
# Find what's using it
lsof -i :8080

# Kill or change port
PORT=8081
```

### Problem: `Out of Memory`
```bash
# Unload other models
ollama rm other-model-name

# Or use lighter model
ollama pull phi4
```

---

## Next Steps

1. Try different models (llama3.2, qwen2.5, mistral)
2. Add custom instructions in prompt
3. Build custom web interface
4. Deploy with ngrok for remote access
5. Add authentication if needed

---

## FAQ

**Q: Why use this wrapper?**
A: Direct Ollama API works, but this adds:
- Streaming responses
- Better error handling
- Rate limiting
- Conversation memory layer
- Easy tunnel support

**Q: Can I use system prompts?**
A: Edit wrapper code, or use `/api/system/prompt` endpoint

**Q: How much RAM?**
A: Model file + 2-4x in RAM. E.g., 4GB model needs ~8GB free.

**Q: GPU acceleration?**
A: Uses system GPU automatically (Mac MPS, Linux CUDA)
