# Model switching + agent-controlled models

Rough idea to revisit later.

## Goals

- Let the user **switch models directly in the Leash UI** without changing env vars or restarting.
- Optionally let the **agent itself request a model switch** via a constrained tool call (opt‑in).

## UI model switching

- `/models` already returns the available models and a current default.
- Treat the `model` field in `ChatTurnBody` as the **source of truth** for each turn, with the env default used only as a fallback.
- Add a compact selector in the status bar:
  - Shows something like: `qwen3.5:latest · Pi (RPC)` or `glm-4.7-flash · Ollama`.
  - On change, updates a per‑browser setting (e.g. `localStorage.leash_model`).
  - Every chat/stream call sends that model name.

Benefits:

- User can compare models on the same convo.
- No server restarts to change models.
- Model choice is explicit in each request.

## Agent-driven model switch (tool idea)

Expose a tool to the agent, something like:

- `set_model(name: string)`

Behavior:

- Session‑scoped: updates only the current Leash session’s model, not global state.
- Writes a visible system note: e.g. `Switched model: qwen3.5:latest → glm-4.7-flash`.

Guardrails:

- Allowlist of models the agent can switch to, maybe annotated by role:
  - `"fast"` (cheap, for exploration)
  - `"deep"` (slow, for final answers)
- Optional limits:
  - Max switches per N turns.
  - Tool only available when the user enables an **“Allow agent to switch models”** toggle in Settings.
- UI override:
  - If the user picks a model explicitly, that selection should either:
    - lock the model, or
    - clearly show that the agent later overrode it.

Why this might be useful:

- Let the agent:
  - use a fast model for broad exploration / file scans,
  - then switch to a stronger model for final summary or code edits.

Risks:

- Harder to debug conversations if the model changes mid‑way without clear visibility.
- Possible cost / latency explosions if the agent thrashes between models.

Implementation note:

- Start with **UI model switching only** (simple, user‑controlled).
- Add the `set_model` tool later as an experiment once UX + logging are good.

