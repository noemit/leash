# ✅ Server is Ready!

## Configuration Applied

**Qwen3.5:27B is now hardcoded as the default model**

## Current Setup

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen3.5:27B
PORT=8080
HOST=0.0.0.0  # Allow external access
```

## Quick Start (from phone-harness folder)

1. **Navigate to wrapper folder:**
   ```bash
   cd /Users/noemititarenco/phone-harness
   ```

2. **Install dependencies (once only):**
   ```bash
   pip3 install aiohttp fastapi uvicorn python-multipart --user --break-system-packages
   export PATH=$PATH:/Library/Python/3.14/bin
   ```

3. **Ensure Ollama is running:**
   ```bash
   ollama serve &
   ollama run qwen3.5:latest
   ```

4. **Start wrapper (from phone-harness folder):**
   ```bash
   export PATH=$PATH:/Library/Python/3.14/bin
   cd server
   python3 api.py
   ```

5. **Open in browser:**
   ```
   http://localhost:8080
   ```

## What Changed

- ✅ **Qwen3.5:27B hardcoded** as default
- ✅ **No model selection prompt** - uses Qwen by default
- ✅ **Dependencies installed** via user pip
- ✅ **Error handling** for missing models

## Available Commands

```bash
# Check server health
curl http://localhost:8080/health

# List models (shows Qwen3.5 only)
curl http://localhost:8080/models

# List installed Ollama models
ollama list

# Stop server
pkill -f "python3 api.py"
```

## Server Logs

```bash
tail -f /var/log/system.log  # Check server logs
# Or:
ps aux | grep api.py
```

---

**Server is running!** Open http://localhost:8080 in your browser.
