import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MODEL_NAME = os.getenv("OLLAMA_MODEL", os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3.5:latest"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT_SEC", "300"))

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    models = await get_available_models()
    if models:
        print(f"[API] Found models: {', '.join(models)}")
        print(f"[API] Default model: {MODEL_NAME}")
    else:
        print(f"[API] No models in Ollama yet. Example: ollama pull {MODEL_NAME}")
    yield


app = FastAPI(title="Phone Harness — Ollama", version="1.1", lifespan=lifespan)


class ChatBody(BaseModel):
    messages: List[Dict[str, Any]] = Field(..., min_length=1)
    model: Optional[str] = None


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


def resolve_model(requested: Optional[str]) -> str:
    return requested if requested else MODEL_NAME


async def process_message(model_name: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    models = await get_available_models()
    return {
        "status": "online",
        "models": models,
        "current_default": MODEL_NAME,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/models")
async def list_models():
    models = await get_available_models()
    return {"models": models, "current_default": MODEL_NAME}


@app.post("/api/chat")
async def chat(body: ChatBody):
    model_name = resolve_model(body.model)
    models = await get_available_models()
    if models and model_name not in models:
        available = ", ".join(models) if models else "none"
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found. Available: {available}",
        )
    return await process_message(model_name, body.messages)


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
    print(f"[API] Ollama: {OLLAMA_HOST}  default model: {MODEL_NAME}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
