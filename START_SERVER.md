# Starting the Ollama Browser Wrapper
# ==== ===========================

## Quick Start

```bash
# 1. Make sure Qwen is running
ollama list
# You should see qwen3.5:latest

# 2. Export model to env (if not using config file)
export OLLAMA_MODEL=qwen3.5:latest

# 3. Start Python server
cd phone-harness/server
python api.py

# OR with Docker
cd phone-harness
docker-compose up -d
```

## Verify Setup

```bash
# Check if Python server is running
ps aux | grep python

# Check model in Ollama
ollama list

# Test API endpoint
curl http://localhost:8080/health
```

## Expected Response

```json
{
  "status": "online",
  "models": ["qwen3.5:latest"],
  "current_default": "qwen3.5:latest"
}
```

## Common Issues

### Issue: Model not showing up in UI
```bash
# Verify Ollama is running
ollama serve &

# Verify model exists
ollama list

# Restart Python server
pkill -f "python api.py"
python api.py
```

### Issue: Port 8080 already in use
```bash
# Find what's using port 8080
lsof -i :8080

# Kill it or use different port
export PORT=8081
python api.py
```

### Issue: Cannot connect to Ollama
```bash
# Make sure Ollama is running
ollama serve

# Check Ollama is listening
lsof -i :11434

# Verify Ollama URL is correct
echo $OLLAMA_HOST  # Should be http://localhost:11434
```

## Environment Variables

Set these before starting:

```bash
OLLAMA_MODEL=qwen3.5:latest  # Your model
OLLAMA_HOST=http://localhost:11434  # Ollama host
PORT=8080  # Wrapper port
HOST=0.0.0.0  # External access allowed
```

## Using Docker Alternative

```bash
cd phone-harness
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Model Selection from UI

After starting, open browser and click:
1. **📦 Model** button in top-right
2. Select **qwen3.5** from dropdown
3. Start chatting!

The UI will auto-detect all models running in Ollama.
