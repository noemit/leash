# Leash

> A mobile-friendly web UI for tunneling into your local AI stack — built around [Ollama](https://ollama.com) (e.g. Qwen 3.5) and a small FastAPI harness.

Licensed under the [MIT License](LICENSE).

## What this does

- Talks to Ollama on your machine (`/api/chat` proxy)
- Serves a phone-oriented chat UI at `/` (same origin as the API, so tunnels work without CORS pain)
- Binds on `0.0.0.0` by default so LAN access and reverse tunnels behave predictably

## Quick start

### Prerequisites

- [Ollama](https://ollama.ai) installed and running
- Python 3.10+ (or Docker)
- A model pulled, e.g. `ollama pull qwen3.5:latest`

### Run the harness

```bash
# Option A: Docker (includes an Ollama service in compose)
docker compose up -d

# Option B: Python (uses Ollama on the host)
pip install -r requirements.txt
cd server && python api.py
```

Open **http://localhost:8080** (or your tunnel URL on a phone).

### Tunnel from a phone

1. On the PC/Mac running Leash: `ngrok http 8080` (or Cloudflare Tunnel, SSH `-L`, etc.)
2. Open the HTTPS URL on your phone — the UI uses `window.location.origin`, so API calls stay on the same host.

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `qwen3.5:latest` | Default model name |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Listen port |
| `CHAT_TIMEOUT_SEC` | `300` | Upstream request timeout |

`config/tunnel.conf` documents similar values; export them in your shell or compose file as needed.

## Architecture

```
Phone / browser
      │ HTTPS (tunnel)
      ▼
┌─────────────────┐
│ FastAPI (Leash) │  port 8080 — static UI + /api/chat proxy
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ollama          │  localhost:11434 (or docker `ollama` service)
└─────────────────┘
```

## Development

```bash
cd server
uvicorn api:app --reload --host 0.0.0.0 --port 8080
```

## Troubleshooting

**Model not found** — `ollama pull <name>` and pick that exact tag in the UI.

**Port in use** — set `PORT=8081` (or free the port).

**Ollama unreachable** — ensure `ollama serve` is running and `OLLAMA_HOST` matches (e.g. `http://ollama:11434` inside Docker Compose).

## Repository

Upstream: [github.com/noemit/leash](https://github.com/noemit/leash)
