import copy
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from pi_bridge import PiBridge

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL_NAME = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3.5:latest"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT_SEC", "300"))
BACKEND = os.getenv("LEASH_BACKEND", "ollama").strip().lower()

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

SESSION_COOKIE = "leash_session"
SESSION_MAX_AGE = int(os.getenv("LEASH_SESSION_MAX_AGE_SEC", str(7 * 24 * 3600)))
SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."
# In-memory chat per browser session (cleared on server restart).
SESSION_MESSAGES: Dict[str, List[Dict[str, Any]]] = {}

pi_bridge: Optional[PiBridge] = None
if BACKEND == "pi":
    pi_bridge = PiBridge()


def _pi_workspace_dict() -> Dict[str, str]:
    if not pi_bridge:
        return {}
    return {
        "root": pi_bridge.root_dir,
        "effective": pi_bridge.cwd,
        "subpath": pi_bridge.subpath_relative,
    }


def _pi_model_label() -> str:
    """Label for JSON/UI: prefer `--model` from LEASH_PI_COMMAND, else OLLAMA_MODEL."""
    if not pi_bridge:
        return MODEL_NAME
    argv = pi_bridge.argv
    for i, a in enumerate(argv):
        if a == "--model" and i + 1 < len(argv):
            return argv[i + 1]
    return MODEL_NAME


@asynccontextmanager
async def lifespan(app: FastAPI):
    if BACKEND == "pi" and pi_bridge:
        print(
            f"[API] Backend: Pi (RPC)  root={pi_bridge.root_dir}  cwd={pi_bridge.cwd}"
        )
        print(f"[API] Pi command: {' '.join(pi_bridge.argv)}")
        print(f"[API] Pi model (from --model / OLLAMA_MODEL): {_pi_model_label()}")
    else:
        models = await get_available_models()
        if models:
            print(f"[API] Backend: Ollama  models: {', '.join(models)}")
        else:
            print(f"[API] Backend: Ollama  (no models yet; try: ollama pull {MODEL_NAME})")
        print(f"[API] Default model: {MODEL_NAME}")
    yield
    if pi_bridge:
        await pi_bridge.shutdown()


app = FastAPI(title="Leash", version="1.2", lifespan=lifespan)


def _set_session_cookie(resp: JSONResponse, sid: str) -> None:
    resp.set_cookie(
        SESSION_COOKIE,
        sid,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )


def _ensure_session(sid: Optional[str]) -> str:
    if not sid:
        sid = uuid.uuid4().hex
    if sid not in SESSION_MESSAGES:
        SESSION_MESSAGES[sid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return sid


class ChatTurnBody(BaseModel):
    """Single user turn; full history stays on the server (in-memory)."""

    content: str = Field(..., min_length=1)
    model: Optional[str] = None


class PiCwdBody(BaseModel):
    """Relative path under LEASH_PI_CWD (empty string = use root)."""

    subpath: str = ""


async def get_available_models() -> List[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags") as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [m["name"] for m in data.get("models", [])]
    except aiohttp.ClientError:
        return []
    except Exception:
        return []


async def ollama_tags_reachable() -> bool:
    """True if Ollama answers GET /api/tags (daemon up)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{OLLAMA_HOST}/api/tags",
                timeout=aiohttp.ClientTimeout(total=3),
            ) as resp:
                return resp.status == 200
    except Exception:
        return False


def resolve_model(requested: Optional[str]) -> str:
    return requested if requested else MODEL_NAME


async def process_message_ollama(model_name: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9},
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=CHAT_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=err or "Ollama error")
                data = await resp.json()
        msg = data.get("message") or {}
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        return {
            "response": content,
            "model": data.get("model", model_name),
            "timestamp": datetime.now().isoformat(),
        }
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Ollama connection error: {e!s}")


@app.get("/health")
async def health_check():
    ollama_ok = await ollama_tags_reachable()
    if BACKEND == "pi" and pi_bridge:
        label = _pi_model_label()
        return {
            "status": "online",
            "backend": BACKEND,
            "models": [label],
            "current_default": label,
            "timestamp": datetime.now().isoformat(),
            "ollama_reachable": ollama_ok,
            "pi": {
                "running": pi_bridge.is_running(),
                "cwd": pi_bridge.cwd,
                "root": pi_bridge.root_dir,
                "subpath": pi_bridge.subpath_relative,
                "command": pi_bridge.argv,
            },
            "pi_workspace": _pi_workspace_dict(),
        }
    models = await get_available_models()
    return {
        "status": "online",
        "backend": BACKEND,
        "models": models,
        "current_default": MODEL_NAME,
        "timestamp": datetime.now().isoformat(),
        "ollama_reachable": ollama_ok,
    }


@app.get("/models")
async def list_models():
    ollama_ok = await ollama_tags_reachable()
    if BACKEND == "pi" and pi_bridge:
        label = _pi_model_label()
        return {
            "models": [label],
            "current_default": label,
            "backend": BACKEND,
            "ollama_reachable": ollama_ok,
            "pi_workspace": _pi_workspace_dict(),
        }
    models = await get_available_models()
    return {
        "models": models,
        "current_default": MODEL_NAME,
        "backend": BACKEND,
        "ollama_reachable": ollama_ok,
    }


@app.get("/api/pi/cwd")
async def pi_get_cwd():
    if BACKEND != "pi" or not pi_bridge:
        raise HTTPException(
            status_code=400,
            detail="Pi backend not enabled (set LEASH_BACKEND=pi).",
        )
    return _pi_workspace_dict()


@app.post("/api/pi/cwd")
async def pi_set_cwd(body: PiCwdBody):
    if BACKEND != "pi" or not pi_bridge:
        raise HTTPException(
            status_code=400,
            detail="Pi backend not enabled (set LEASH_BACKEND=pi).",
        )
    try:
        await pi_bridge.set_effective_cwd(body.subpath)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, **_pi_workspace_dict()}


@app.post("/api/pi/new-session")
async def pi_new_session():
    if BACKEND != "pi" or not pi_bridge:
        raise HTTPException(
            status_code=400,
            detail="Pi backend not enabled (set LEASH_BACKEND=pi).",
        )
    try:
        await pi_bridge.new_session()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"ok": True}


@app.get("/api/session")
async def get_session(request: Request):
    """Return chat messages for this browser session (sets session cookie)."""
    raw_sid = request.cookies.get(SESSION_COOKIE)
    sid = _ensure_session(raw_sid)
    resp = JSONResponse({"messages": copy.deepcopy(SESSION_MESSAGES[sid])})
    _set_session_cookie(resp, sid)
    return resp


@app.post("/api/session/reset")
async def reset_session(request: Request):
    """Clear in-memory transcript for this session; Pi mode also starts a new Pi RPC session (best effort)."""
    raw_sid = request.cookies.get(SESSION_COOKIE)
    sid = _ensure_session(raw_sid)
    SESSION_MESSAGES[sid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    pi_session_note: Optional[str] = None
    if BACKEND == "pi" and pi_bridge:
        try:
            await pi_bridge.new_session()
        except RuntimeError as e:
            pi_session_note = str(e)
    body: Dict[str, Any] = {
        "ok": True,
        "messages": copy.deepcopy(SESSION_MESSAGES[sid]),
    }
    if pi_session_note:
        body["pi_new_session_warning"] = pi_session_note
    resp = JSONResponse(body)
    _set_session_cookie(resp, sid)
    return resp


@app.post("/api/chat")
async def chat(request: Request, body: ChatTurnBody):
    raw_sid = request.cookies.get(SESSION_COOKIE)
    sid = _ensure_session(raw_sid)
    msgs = SESSION_MESSAGES[sid]
    user_txt = str(body.content).strip()
    if not user_txt:
        raise HTTPException(status_code=400, detail="Empty message")

    msgs.append({"role": "user", "content": user_txt})

    try:
        if BACKEND == "pi":
            if not pi_bridge:
                raise HTTPException(status_code=500, detail="Pi bridge not initialized")
            text = await pi_bridge.prompt(user_txt, float(CHAT_TIMEOUT))
            resp_body: Dict[str, Any] = {
                "response": text,
                "model": _pi_model_label(),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            model_name = resolve_model(body.model)
            models = await get_available_models()
            if models and model_name not in models:
                available = ", ".join(models) if models else "none"
                raise HTTPException(
                    status_code=404,
                    detail=f"Model '{model_name}' not found. Available: {available}",
                )
            out = await process_message_ollama(model_name, msgs)
            text = out["response"]
            resp_body = {
                "response": text,
                "model": out.get("model", model_name),
                "timestamp": out.get("timestamp", datetime.now().isoformat()),
            }
    except HTTPException:
        msgs.pop()
        raise
    except TimeoutError:
        msgs.pop()
        raise HTTPException(
            status_code=504, detail="Pi timed out before finishing the turn"
        )
    except RuntimeError as e:
        msgs.pop()
        raise HTTPException(status_code=503, detail=str(e))

    msgs.append({"role": "assistant", "content": text})
    resp_body["messages"] = copy.deepcopy(msgs)

    resp = JSONResponse(resp_body)
    _set_session_cookie(resp, sid)
    return resp


@app.get("/")
async def serve_index():
    index = WEB_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="web/index.html missing")
    return FileResponse(index)


if WEB_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR)), name="assets")


if __name__ == "__main__":
    print(f"[API] Listening on http://{HOST}:{PORT}")
    print(f"[API] LEASH_BACKEND={BACKEND}")
    if BACKEND != "pi":
        print(f"[API] Ollama: {OLLAMA_HOST}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
