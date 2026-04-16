# Leash on Windows (PowerShell, Pi, env vars)

This guide is for **Windows Terminal + PowerShell**. Bash-style `export` in the main README does not apply here.

## Shells and environment variables

| Shell | Set for current session | Notes |
|-------|-------------------------|--------|
| **PowerShell** | `$env:NAME = "value"` | What most people use in Windows Terminal. |
| **cmd.exe** | `set NAME=value` | No spaces around `=`. |
| **Git Bash** | `export NAME=value` | Same as macOS/Linux README examples. |

Leash reads variables from the **process that starts Python** (your terminal, VS Code “Run”, a service, etc.). If you set `$env:…` in one window and start the server from another, it will not see them.

**After changing any Pi-related variable, restart the Leash server.** `LEASH_PI_COMMAND` and the extra prompt env vars are applied when the Pi subprocess is configured at startup.

To confirm what Leash will run, check the server log line:

`[API] Pi command: …`

It prints the resolved argv (including `--system-prompt` / `--append-system-prompt` if present).

## Pi mode in PowerShell

Minimal session (current window only):

```powershell
$env:LEASH_BACKEND = "pi"
$env:LEASH_PI_COMMAND = "pi --mode rpc --provider ollama --model qwen3.5:latest"
cd path\to\phone-harness\server
python api.py
```

Requires **Node** and a global Pi install, for example:

`npm install -g @mariozechner/pi-coding-agent`

If `pi` is not on `PATH`, point `LEASH_PI_COMMAND` at **`pi.cmd`** under your npm global folder (often `%AppData%\npm\pi.cmd`):

```powershell
$env:LEASH_PI_COMMAND = "C:\Users\YourName\AppData\Roaming\npm\pi.cmd --mode rpc --provider ollama --model qwen3.5:latest"
```

## System prompt: `LEASH_PI_COMMAND` vs dedicated env vars

Pi’s CLI supports `--system-prompt` and `--append-system-prompt` (see `pi --help`). You can put them in `LEASH_PI_COMMAND`, **or** use Leash’s optional variables so you avoid fragile quoting in one long line.

### Option A — flags inside `LEASH_PI_COMMAND`

Use **double quotes** around values that contain spaces. Example:

```powershell
$env:LEASH_PI_COMMAND = "pi --mode rpc --provider ollama --model qwen3.5:latest --system-prompt `"You are concise.`""
```

(Inside a double-quoted PowerShell string, a literal double quote is `` `" ``.)

Leash parses `LEASH_PI_COMMAND` with Windows-safe rules: quoted words are turned into argv Pi understands. If something still looks wrong, prefer Option B.

### Option B — `LEASH_PI_SYSTEM_PROMPT` / `LEASH_PI_APPEND_SYSTEM_PROMPT` (recommended for long text)

Keep `LEASH_PI_COMMAND` short; put the system text in a **separate** variable. Leash appends the matching Pi flag **only if** that flag is not already present in `LEASH_PI_COMMAND`.

```powershell
$env:LEASH_BACKEND = "pi"
$env:LEASH_PI_COMMAND = "pi --mode rpc --provider ollama --model qwen3.5:latest"
$env:LEASH_PI_SYSTEM_PROMPT = @"
You are a coding assistant.
Prefer small patches. Ask before destructive commands.
"@
```

**Append** extra rules or point at a file (Pi treats `--append-system-prompt` as text or file path, same as the CLI):

```powershell
$env:LEASH_PI_APPEND_SYSTEM_PROMPT = "C:\Users\YourName\leash-extra.md"
```

If a path has spaces, quote it in the variable value:

```powershell
$env:LEASH_PI_APPEND_SYSTEM_PROMPT = "C:\Users\Your Name\leash-extra.md"
```

### Precedence

If `LEASH_PI_COMMAND` already contains `--system-prompt` or `--append-system-prompt`, Leash **does not** add a second flag from `LEASH_PI_SYSTEM_PROMPT` / `LEASH_PI_APPEND_SYSTEM_PROMPT` for that slot.

## `LEASH_PI_CWD` on Windows

Pi’s working directory for tools should be an existing folder, for example:

```powershell
$env:LEASH_PI_CWD = "C:\Users\YourName\Projects\my-repo"
```

Use a normal Windows path; forward slashes also work (`C:/Users/...`).

## Making variables persist (optional)

Session-only `$env:…` is lost when you close the terminal. For a **user-level** variable that new shells inherit (PowerShell):

```powershell
[System.Environment]::SetEnvironmentVariable("LEASH_BACKEND", "pi", "User")
[System.Environment]::SetEnvironmentVariable("LEASH_PI_COMMAND", "pi --mode rpc --provider ollama --model qwen3.5:latest", "User")
```

Open a **new** Windows Terminal tab after that. Long system prompts are easier to keep in a `.ps1` or `.env` file you dot-source before `python api.py`, or use `LEASH_PI_APPEND_SYSTEM_PROMPT` with a file path.

## See also

- Main **[README](../README.md)** — env table, Ollama defaults, tunneling.
- Pi RPC protocol: [`pi-coding-agent` RPC docs](https://cdn.jsdelivr.net/npm/@mariozechner/pi-coding-agent/docs/rpc.md).
