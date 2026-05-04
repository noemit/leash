# Leash

**Your AI agent. One browser tab. No drama.**

Leash is a small **FastAPI** app with a **mobile-first** web UI that talks to your machine’s brain—**[Ollama](https://ollama.com)** out of the box, or **[Pi](https://shittycodingagent.ai/)** in RPC mode when you want tools and disk access. Same origin, tunnel-friendly: point **ngrok** or Cloudflare Tunnel at it and your phone becomes a remote cockpit for whatever runs at home on the super minimal and extensible Pi agent.

Not a platform, not a new product, not a tool— just a leash. Keep the agent running, reachable, and under your rules.

[MIT License](LICENSE)

---

## What it’s about

- **Tell your local agent what to do - no matter where you are** — browser UI tuned for easy mobile use.
- **Local models by default** — Ollama on localhost; no accounts required. Use cloud agents if you want. But why would you do that when Local AI is here?
- **Power when you want it** — Give the agent a working directory (`LEASH_PI_CWD`) without reinventing orchestration.

---

## Who it’s for

- **Builders** who already run Ollama (or Pi) and want access to your agents while they step outside to get more coffee. 
- **Anyone who wants to go all in on Local AI** — Access a local model wherever you are - full privacy and control even on mobile.

---

## Why it feels good to use

You’re not opening yet another SaaS chat where your data will definitely not be kept private (even if they don't use it to train). You’re opening **your** stack: the model you pulled, using tools on disk, optional continuous mode so the agent can chain **`continue.`** without you paste‑spamming. Stop mid‑stream, collapse Pi’s “Thinking” clutter, type your next message while the model still talks—it’s built for **real work**.

---

## Modes

| | **Ollama** (default) | **Pi** (`LEASH_BACKEND=pi`) |
|--|----------------------|-----------------------------|
| **What** | Proxies chat to local Ollama | Spawns [`pi --mode rpc`](https://cdn.jsdelivr.net/npm/@mariozechner/pi-coding-agent/docs/rpc.md) |
| **Disk / shell** | No | Yes (within `LEASH_PI_CWD`) |

Listens on **`0.0.0.0:8080`** by default.

---

## Quick start

From the **repo root** (folder with `server/`, `web/`, `requirements.txt`):

1. **Ollama** running (`ollama list`). Pull a model, e.g. `ollama pull qwen3.5:latest`.
2. **Python 3.10–3.12** (3.14: use pinned `requirements.txt`). Prefer a **venv**.
3. Run **either**:
   - **Docker:** `docker compose up -d` ([Docker](https://docs.docker.com/get-docker/) required)
   - **Python:**
     ```bash
     python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
     python3 -m pip install -r requirements.txt
     cd server && python3 api.py
     ```
     Use `python` on Windows if `python3` is missing.

4. Open **http://localhost:8080** (or your tunnel URL on a phone).

**Tunnel:** e.g. `ngrok http 8080` on the machine running Leash, then open the HTTPS URL on your phone.

**Windows (PowerShell, Pi, quoting):** see **[docs/windows.md](docs/windows.md)**.

---

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL |
| `OLLAMA_MODEL` | `qwen3.5:latest` | Default model (Ollama / UI) |
| `HOST` / `PORT` | `0.0.0.0` / `8080` | Bind |
| `CHAT_TIMEOUT_SEC` | `1200` | Upstream timeout (seconds) |
| `LEASH_SESSION_MAX_AGE_SEC` | `604800` | `leash_session` cookie max-age |
| `LEASH_BACKEND` | `ollama` | Set `pi` for Pi |
| `LEASH_PI_COMMAND` | `pi --mode rpc --provider ollama --model qwen3.5:latest` | Pi launch line (must include `--mode rpc`) |
| `LEASH_PI_SYSTEM_PROMPT` | _(unset)_ | Optional full system prompt text. If command/env flags are missing, Leash falls back to `systemprompt.txt` in repo root, then `server/systemprompt.txt`, then `"You are a helpful assistant."` |
| `LEASH_PI_APPEND_SYSTEM_PROMPT` | _(unset)_ | Optional extra system text or file path; appended as `--append-system-prompt` if not already in the command (same Windows temp-file behavior when the value is not an existing file path) |
| `LEASH_PI_CWD` | `$HOME` | Pi sandbox root (not `server/` unless you set it) |

**Chat:** The UI keeps the transcript **in memory on the server** (lost when Leash restarts). Each turn sends only **`{ "content", "model" }`** over the wire; the server builds the full message list for Ollama on localhost. Clear with the **trash** button, **`/clear`** / **`/reset`**, or **`POST /api/session/reset`**. **`/help`** opens command help.

### Streaming UX

- **Stop button**: While a reply is streaming, a **Stop** button appears next to **Send**. Hitting Stop aborts the stream and keeps whatever has already been generated as the final assistant message, so you can cut off rambly answers.
- **Thinking collapsed by default**: Pi’s internal “Thinking” stream is shown as a **Thinking (tap to expand)** segment above the answer. It’s collapsed by default so the main chat stays readable; click/tap the segment to toggle the detailed thinking body.
- **Type while streaming**: The message box stays editable while the model is streaming, so you can draft or edit your next turn in parallel. The **Send** button itself is disabled until the current stream finishes or is stopped.

### Continuous mode

In the status bar, next to the Pi folder icon, there’s a **Settings** gear that opens a small settings drawer.

- **Toggle**: The drawer has a **Continuous mode** checkbox, persisted in `localStorage` so it sticks across reloads on the same browser.
- **Summarizer subagent**: The drawer also has **Enable summarizer subagent**. When enabled, each completed assistant turn appends one brief line to `log.md` at the repo root.
- **Normal continuous behavior**: When Continuous mode is **enabled**, after each successful assistant turn the app automatically sends:

  > `continue.`

  as a new user message. This lets your agent keep working without you manually spamming “continue”.

Automatic continuous follow‑ups are only triggered for successful, non‑aborted turns (if you hit **Stop**, that turn will not auto‑chain).

**Pi:** Model comes only from **`LEASH_PI_COMMAND`** (`--model …`). In the UI, **folder** sets a subpath under `LEASH_PI_CWD` (`GET/POST /api/pi/cwd`). Clearing chat also starts a **new Pi RPC session** when possible.

---

## Pi mode (shell)

```bash
export LEASH_BACKEND=pi
export LEASH_PI_COMMAND="pi --mode rpc --provider ollama --model qwen3.5:latest"
# optional: long system text via env (same as pi's prompt flags)
# export LEASH_PI_SYSTEM_PROMPT="You are …"
# export LEASH_PI_APPEND_SYSTEM_PROMPT="$HOME/leash-system-extra.md"
# optional: export LEASH_PI_CWD="$HOME/your-repo"
cd server && python3 api.py
```

### Local `systemprompt.txt` (recommended)

For stable prompt behavior without shell quoting, create a local file (kept out of git):

- `./systemprompt.txt` (repo root), or
- `./server/systemprompt.txt`

Leash will use that text as the system prompt when `LEASH_PI_COMMAND` does not explicitly set prompt flags and `LEASH_PI_SYSTEM_PROMPT` is unset.

Requires **Node** + `npm install -g @mariozechner/pi-coding-agent`. **Windows:** PowerShell examples, `pi.cmd`, `LEASH_PI_SYSTEM_PROMPT`, and quoting notes are in **[docs/windows.md](docs/windows.md)**.

---

## Dev

```bash
cd server && uvicorn api:app --reload --host 0.0.0.0 --port 8080
```

---

## Troubleshooting

- **Model not found** — `ollama pull <exact-tag>`; Pi `--model` must match `ollama list`.
- **Port in use** — `PORT=8081` or free the port.
- **Ollama unreachable** — Ollama must be listening on **11434**; “address already in use” often means it’s **already** running. Align **`OLLAMA_HOST`** if non-default.
- **No files / tools** — Use **Pi** mode and set **`LEASH_PI_CWD`**.
- **Pi `FileNotFoundError` on Windows** — See **[docs/windows.md](docs/windows.md)** (`pi.cmd` / PATH).
- **Traceback in `h11_impl.py`** — Scroll up for the real frame in `api.py` / deps. Python **3.14:** reinstall from `requirements.txt` (`uvicorn>=0.38`) or use **Docker** (Python 3.11 image).

Optional sample keys: **`config/tunnel.conf`**.

---

## Repo

https://github.com/noemit/leash
