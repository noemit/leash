# Leash

> A mobile-friendly web UI for tunneling into your local AI stack — built around [Ollama](https://ollama.com) (e.g. Qwen 3.5) and a small FastAPI harness.

Licensed under the [MIT License](LICENSE).

## What this does

- **Ollama mode (default):** proxies chat to `POST /api/chat` on your local Ollama. **No disk access** — the model cannot read or create files on your machine.
- **Pi mode:** spawns [**pi**](https://shittycodingagent.ai/) in [`--mode rpc`](https://cdn.jsdelivr.net/npm/@mariozechner/pi-coding-agent/docs/rpc.md), sends your message as a `prompt`, and returns the agent reply (including summarized tool output). Pi’s working directory is **`LEASH_PI_CWD`** (default: your **home** folder). **Files and shell tools** only work in this mode (subject to Pi + OS permissions).
- Serves a phone-friendly UI at `/` (same origin as the API, tunnel-safe).
- Binds on `0.0.0.0` by default for LAN and reverse tunnels.

## Quick start

Work from a **clone of this repo** (repository root = folder that contains `server/`, `web/`, and `requirements.txt`).

### Prerequisites

1. [Ollama](https://ollama.ai) installed — **start it** (menu bar app on Mac, or `ollama serve`). Confirm: `ollama list` works in a terminal.
2. Python **3.10–3.12** recommended (3.12 is a good default). Use a **venv** and this repo’s `requirements.txt`. (**Python 3.14:** `requirements.txt` already pins **`uvicorn>=0.38`**.)
3. At least one model pulled, e.g. `ollama pull qwen3.5:latest` (name must **exactly** match `OLLAMA_MODEL` / what you pick in the UI).

### Run the harness (pick one)

**A — Docker** (compose includes an Ollama service; needs [Docker](https://docs.docker.com/get-docker/) installed):

```bash
docker compose up -d
```

**B — Python** (Leash uses Ollama already running on the host):

1. `cd` to the **repository root**.
2. Create and activate a venv, install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Windows cmd: .venv\Scripts\activate.bat
                                      # Windows PowerShell: .venv\Scripts\Activate.ps1
   python3 -m pip install -r requirements.txt
   ```
3. Start the API from **`server/`**:
   ```bash
   cd server && python3 api.py
   ```
   On Windows, if `python3` is missing, use `python api.py` after `cd server`.

Use a **venv** so `pip` can upgrade uvicorn/FastAPI cleanly (avoids “externally managed” errors on macOS/Homebrew Python). On many Macs the command is `python3`, not `python`. If you want `python` to work: `brew install python` then ensure your PATH includes Homebrew’s prefix, or add `alias python=python3` to `~/.zshrc`.

4. Open **http://localhost:8080** in a browser (or your tunnel URL on a phone).

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
| `LEASH_SESSION_MAX_AGE_SEC` | `604800` (7d) | Browser **`leash_session`** cookie lifetime |
| `LEASH_BACKEND` | `ollama` | Set to `pi` to drive Pi instead of raw Ollama |
| `LEASH_PI_COMMAND` | `pi --mode rpc --provider ollama --model qwen3.5:latest` | How to start Pi (must include `--mode rpc`) |
| `LEASH_PI_CWD` | **`$HOME`** (your user folder) | **Root sandbox** for Pi’s tools / files. Unset = home, not the `server/` cwd. |

Model is **only** whatever you pass to Pi on the command line (`--model …` in `LEASH_PI_COMMAND`); the UI does not call Pi `set_model`.

**Pi subfolder in the UI:** With **`LEASH_BACKEND=pi`**, the page shows **Pi folder** — a path **relative to `LEASH_PI_CWD`** (no `..`, must already exist). Changing it **restarts** the Pi process with that `cwd`. You can also use **`GET/POST /api/pi/cwd`** (`subpath` in JSON).

**Chat session:** The web UI uses **`GET /api/session`** and a **`leash_session`** cookie. Each **`POST /api/chat`** sends only **`{ "content": "…", "model": "…" }`**; the server keeps the full transcript **in memory** (lost on Leash restart) and sends the complete history to Ollama over localhost. That keeps tunnel requests small.

### Pi mode example

Requires Node and Pi on your PATH (`npm install -g @mariozechner/pi-coding-agent`), plus whatever Pi needs for your provider (e.g. Ollama running for `--provider ollama`).

```bash
export LEASH_BACKEND=pi
# Optional: omit LEASH_PI_CWD to use $HOME, or set a repo:
# export LEASH_PI_CWD="$HOME/phone-harness"
export LEASH_PI_COMMAND="pi --mode rpc --provider ollama --model qwen3.5:latest"
cd server && python3 api.py
```

**Windows (cmd.exe)** — use `set`, not PowerShell’s `$env:`:

```bat
set LEASH_BACKEND=pi
set LEASH_PI_CWD=C:\Users\You\your-repo
set LEASH_PI_COMMAND=pi --mode rpc --provider ollama --model qwen3.5:latest
cd C:\path\to\leash\server
python api.py
```

**Windows (PowerShell)** — same idea:

```powershell
$env:LEASH_BACKEND = "pi"
$env:LEASH_PI_CWD = "C:\Users\You\your-repo"
$env:LEASH_PI_COMMAND = "pi --mode rpc --provider ollama --model qwen3.5:latest"
cd C:\path\to\leash\server
python api.py
```

On startup, Leash logs **`cwd=...`** for Pi. That path is what matters; if the model sounds vague about directories, ask it to run a real command to print the working directory / list files (tool output), or fix **`LEASH_PI_CWD`** and restart.

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

**Model not found** — Run `ollama pull <name>` and use the **exact** tag everywhere (e.g. `qwen3.5:latest`, not `qwen3.:latest`). In Pi mode, the name in **`LEASH_PI_COMMAND`** (`--model …`) must match `ollama list`.

**Pi on Windows: `FileNotFoundError` / “cannot find the file”** — Python often does not see `pi` on PATH. Install `npm install -g @mariozechner/pi-coding-agent`, ensure `%AppData%\npm` is on PATH, or set **`LEASH_PI_COMMAND`** to the full path to **`pi.cmd`**, e.g. `C:\Users\You\AppData\Roaming\npm\pi.cmd --mode rpc --provider ollama --model qwen3.5:latest`. (Recent `pi_bridge.py` also probes `%AppData%\npm` automatically.)

**Port in use** — set `PORT=8081` (or free the port).

**Ollama unreachable** — the Ollama **app or service** must be running (listening on **11434**). If `ollama list` works, you do not need a second `ollama serve`. A “socket address already in use” / “address already in use” error usually means Ollama is **already** running. Match **`OLLAMA_HOST`** if you use a non-default port.

**“Connected” but no files / no mkdir** — you are probably in **Ollama** mode. Switch to **`LEASH_BACKEND=pi`** and set **`LEASH_PI_CWD`** to the repo you want Pi to work in (see Windows example above).

**Pi new session** — restart Leash or call `POST /api/pi/new-session` if you need a fresh Pi session (the web UI no longer has a Clear control).

**Traceback mentions `h11_impl.py` line ~415 (`await app(...)`)** — that line is **uvicorn** calling your app; scroll up for the **first** frame in `api.py` or a dependency. On **Python 3.14**, install deps from this repo (**`uvicorn>=0.38`**): `python -m pip install -r requirements.txt` from the project root. **Alternative without touching Python:** run Leash with **Docker** (`docker compose`) — the image uses Python 3.11.

## Repository

Upstream: [github.com/noemit/leash](https://github.com/noemit/leash)
