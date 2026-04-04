# Quick Reference
# ================

## Common Commands

### Start Server (Docker)
```bash
cd phone-harness
docker-compose up -d
```

### Start Server (CLI)
```bash
cd phone-harness/setup.sh
```

### Setup NGROK
```bash
cd phone-harness/scripts
bash ngrok.sh
```

### Check Ollama Status
```bash
curl http://localhost:11434/api/tags
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Server
```bash
docker-compose down
```

## Ports

| Service     | Port   | Purpose                  |
|-------------|--------|---------------------------|
| Ollama      | 11434  | Model serving             |
| Wrapper API | 8080   | Web/Chat interface        |
| Web Frontend| 8080   | HTML/JS interface         |

## Environment Variables

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=pi
PORT=8080
TUNNEL_URL=http://your-ngrok-link
MODEL_NAME=pi
```

## Troubleshooting

### Ollama Not Responding
```bash
ollama run pi
curl http://localhost:11434/api/tags
```

### Port in Use
```bash
sudo lsof -i :8080
# Kill process or change PORT
```

### Tunnel Not Working
```bash
# Check ngrok status
ngrok status
# Restart with new token
```
