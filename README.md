# Leash

> A mobile-friendly web UI for tunneling into your local AI stack — built around [Ollama](https://ollama.com) (e.g. Qwen 3.5) and a small FastAPI harness.

Licensed under the [MIT License](LICENSE).

## What this does

- **Ollama mode (default):** proxies chat to `POST /api/chat` on your local Ollama.
- **Pi mode:** spawns [**pi**](https://shittycodingagent.ai/) in [`--mode rpc`](https://cdn.jsdelivr.net/npm/@mariozechner/pi-coding-agent/docs/rpc.md), sends your message as a `prompt`, and returns the agent reply (including summarized tool output). Pi’s working directory is **`LEASH_PI_CWD`** (default: your **`$HOME`** folder).
- Serves a phone-friendly UI at `/` (same origin as the API, tunnel-safe).
- Binds on `0.0.0.0` by default for LAN and reverse tunnels.

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
python3 -m pip install -r requirements.txt
cd server && python3 api.py
```

On many Macs the command is `python3`, not `python`. If you want `python` to work: `brew install python` then ensure your PATH includes Homebrew’s prefix, or add `alias python=python3` to `~/.zshrc`.

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
| `LEASH_BACKEND` | `ollama` | Set to `pi` to drive Pi instead of raw Ollama |
| `LEASH_PI_COMMAND` | `pi --mode rpc --provider ollama --model qwen3.5:latest` | How to start Pi (must include `--mode rpc`) |
| `LEASH_PI_CWD` | **`$HOME`** (your user folder) | Directory Pi uses for tools / files. Unset = home, not the `server/` cwd. |

Model is **only** whatever you pass to Pi on the command line (`--model …` in `LEASH_PI_COMMAND`); the UI does not call Pi `set_model`.

### Pi mode example

Requires Node and Pi on your PATH (`npm install -g @mariozechner/pi-coding-agent`), plus whatever Pi needs for your provider (e.g. Ollama running for `--provider ollama`).

```bash
export LEASH_BACKEND=pi
# Optional: omit LEASH_PI_CWD to use $HOME, or set a repo:
# export LEASH_PI_CWD="$HOME/phone-harness"
export LEASH_PI_COMMAND="pi --mode rpc --provider ollama --model qwen3.5:latest"
cd server && python3 api.py
```

**Clear** in the UI calls Pi’s `new_session` over RPC so you start a fresh agent session.

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
│ Ollama or Pi    │  Ollama: HTTP API · Pi: subprocess RPC (`pi --mode rpc`)
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
