"""
Drive Pi (https://github.com/badlogic/pi-mono / pi-coding-agent) in RPC mode over stdin/stdout.
Protocol: https://cdn.jsdelivr.net/npm/@mariozechner/pi-coding-agent/docs/rpc.md
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


def _windows_npm_shim(head: str) -> Optional[Path]:
    """Find pi.cmd / npx.cmd when PATH seen by Python omits %AppData%\\npm (common on Windows)."""
    stem = Path(head).stem if head else head
    if not stem:
        return None
    names = [f"{stem}.cmd", f"{stem}.exe", stem]
    roots: List[Path] = []
    ad = os.environ.get("APPDATA")
    if ad:
        roots.append(Path(ad) / "npm")
    roots.append(Path.home() / "AppData" / "Roaming" / "npm")
    for root in roots:
        for n in names:
            p = root / n
            if p.is_file():
                return p
    return None


def resolve_pi_argv(argv: List[str]) -> List[str]:
    """Resolve the Pi CLI to a real executable path (Windows: pi.cmd vs pi)."""
    if not argv:
        raise RuntimeError("LEASH_PI_COMMAND parsed to an empty command.")
    head, *rest = argv
    p0 = Path(head)
    if p0.is_file():
        return [str(p0.resolve())] + rest

    candidates = [head]
    if sys.platform == "win32":
        low = head.lower()
        if not low.endswith((".exe", ".cmd", ".bat")):
            candidates.extend([f"{head}.cmd", f"{head}.exe", f"{head}.bat"])

    found: Optional[str] = None
    for c in candidates:
        w = shutil.which(c)
        if w:
            found = w
            break

    if not found and sys.platform == "win32":
        shim = _windows_npm_shim(head)
        if shim is not None:
            found = str(shim.resolve())

    if not found:
        raise RuntimeError(
            f"Cannot find Pi executable {head!r} on PATH (Windows needs pi.cmd from npm). "
            "Install: npm install -g @mariozechner/pi-coding-agent. "
            "Add npm global to PATH (often %AppData%\\npm), run Leash from the same environment "
            "where `pi` works in a terminal, or set LEASH_PI_COMMAND to the full path, e.g. "
            r'LEASH_PI_COMMAND="C:\Users\You\AppData\Roaming\npm\pi.cmd" --mode rpc --provider ollama --model qwen3.5:latest'
        )
    return [found] + rest


def safe_pi_subdir(root: Path, subpath: Optional[str]) -> Path:
    """Resolve a path under root only. Empty subpath → root. Rejects absolute paths and '..'."""
    root = root.resolve()
    if subpath is None or not str(subpath).strip():
        return root
    raw = str(subpath).strip().replace("\\", "/").lstrip("/")
    if not raw or raw == ".":
        return root
    for part in Path(raw).parts:
        if part == "..":
            raise ValueError("subpath must not contain '..'")
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError("subpath must stay under LEASH_PI_CWD")
    if not candidate.is_dir():
        raise ValueError(f"not a directory: {candidate}")
    return candidate


def normalize_pi_cwd(raw: Optional[str]) -> str:
    """Pi's subprocess cwd must exist. Expand ~ and resolve.

    If LEASH_PI_CWD is unset, use the user's home directory (not the shell cwd),
    so `cd server && python api.py` still lets Pi see ~/ by default.
    """
    if raw and str(raw).strip():
        p = Path(str(raw).strip()).expanduser()
        if not p.is_dir():
            rp = p.resolve()
            raise RuntimeError(
                "LEASH_PI_CWD must be an existing directory (Pi runs tools there). "
                f"Not found: {p} → {rp}. "
                "Tip: your macOS home is usually just $HOME — use export LEASH_PI_CWD=\"$HOME\" "
                "not $HOME/$(basename $HOME). For a repo, use e.g. $HOME/phone-harness."
            )
        return str(p.resolve())
    return str(Path.home().resolve())


def _json_line(obj: Dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")


def _parse_stdout_line(line: bytes) -> Optional[Dict[str, Any]]:
    line = line.rstrip(b"\r\n")
    if not line:
        return None
    try:
        return json.loads(line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _assistant_text_from_agent_end(obj: Dict[str, Any]) -> str:
    msgs: List[Any] = list(obj.get("messages") or [])
    for m in reversed(msgs):
        if not isinstance(m, dict):
            continue
        if m.get("role") != "assistant":
            continue
        content = m.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text")
                    if isinstance(t, str):
                        parts.append(t)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    return ""


class PiBridge:
    """One long-lived `pi --mode rpc` subprocess; all RPC is serialized with a lock."""

    def __init__(self) -> None:
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()
        self._root_dir = normalize_pi_cwd(os.getenv("LEASH_PI_CWD"))
        self._cwd = self._root_dir
        raw = os.getenv(
            "LEASH_PI_COMMAND",
            "pi --mode rpc --provider ollama --model qwen3.5:latest",
        )
        if sys.platform == "win32":
            self._argv = shlex.split(raw, posix=False)
        else:
            self._argv = shlex.split(raw)
        self._exec_argv = resolve_pi_argv(self._argv)
        self._stderr_task: Optional[asyncio.Task[None]] = None

    @property
    def argv(self) -> List[str]:
        return list(self._argv)

    @property
    def executable(self) -> str:
        return self._exec_argv[0]

    @property
    def cwd(self) -> str:
        return self._cwd

    @property
    def root_dir(self) -> str:
        return self._root_dir

    @property
    def subpath_relative(self) -> str:
        root = Path(self._root_dir).resolve()
        cwd = Path(self._cwd).resolve()
        try:
            rel = cwd.relative_to(root)
            if rel == Path("."):
                return ""
            return str(rel).replace("\\", "/")
        except ValueError:
            return ""

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def _stop_proc(self) -> None:
        t = self._stderr_task
        self._stderr_task = None
        if t and not t.done():
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        proc = self._proc
        self._proc = None
        if proc and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()

    async def set_effective_cwd(self, subpath: Optional[str]) -> str:
        """Move Pi's cwd to a subdirectory of LEASH_PI_CWD; restarts the Pi process."""
        new_path = safe_pi_subdir(Path(self._root_dir), subpath)
        new_s = str(new_path)
        async with self._lock:
            await self._stop_proc()
            self._cwd = new_s
        return new_s

    async def ensure_running(self) -> None:
        if self.is_running():
            return
        self._proc = await asyncio.create_subprocess_exec(
            *self._exec_argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._cwd,
            limit=50 * 1024 * 1024,
        )
        if self._stderr_task is None or self._stderr_task.done():
            self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self) -> None:
        proc = self._proc
        if not proc or not proc.stderr:
            return
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            try:
                txt = line.decode("utf-8", errors="replace").rstrip()
                if txt:
                    print(f"[pi] {txt}")
            except Exception:
                pass

    async def _read_line(self, timeout: float) -> bytes:
        if not self._proc or not self._proc.stdout:
            raise RuntimeError("Pi process not started")
        return await asyncio.wait_for(self._proc.stdout.readline(), timeout=timeout)

    async def rpc_transact(self, cmd: Dict[str, Any], timeout: float) -> Dict[str, Any]:
        """Send one command; read stdout until matching response (same id)."""
        await self.ensure_running()
        assert self._proc and self._proc.stdin
        rid = cmd.get("id") or str(uuid.uuid4())
        out_cmd = {**cmd, "id": rid}
        self._proc.stdin.write(_json_line(out_cmd))
        await self._proc.stdin.drain()

        while True:
            line = await self._read_line(timeout)
            if not line:
                raise RuntimeError("Pi closed stdout before sending a response")
            obj = _parse_stdout_line(line)
            if obj is None:
                continue
            if obj.get("type") == "response" and obj.get("id") == rid:
                return obj

    async def new_session(self, timeout: float = 60.0) -> None:
        async with self._lock:
            r = await self.rpc_transact({"type": "new_session"}, timeout=timeout)
            if not r.get("success", True):
                err = r.get("error") or r.get("message") or str(r)
                raise RuntimeError(f"new_session failed: {err}")

    async def prompt(self, message: str, timeout: float) -> str:
        """Send user text to Pi. Model comes only from `LEASH_PI_COMMAND` (`--model …`), not RPC."""
        async with self._lock:
            await self.ensure_running()
            assert self._proc and self._proc.stdin

            pid = str(uuid.uuid4())
            self._proc.stdin.write(
                _json_line({"type": "prompt", "message": message, "id": pid})
            )
            await self._proc.stdin.drain()

            accepted = False
            text_parts: List[str] = []
            tool_blocks: List[str] = []
            deadline = time.monotonic() + timeout

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Pi prompt timed out before agent_end")
                line = await self._read_line(min(remaining, 600.0))
                if not line:
                    raise RuntimeError("Pi stdout closed mid-prompt")
                obj = _parse_stdout_line(line)
                if obj is None:
                    continue

                t = obj.get("type")
                if t == "response" and obj.get("id") == pid:
                    accepted = True
                    if not obj.get("success", True):
                        err = obj.get("error") or obj.get("message") or str(obj)
                        raise RuntimeError(f"prompt rejected: {err}")
                    continue

                if not accepted:
                    continue

                if t == "message_update":
                    ev = obj.get("assistantMessageEvent") or {}
                    if ev.get("type") == "text_delta":
                        d = ev.get("delta")
                        if isinstance(d, str):
                            text_parts.append(d)
                elif t == "tool_execution_end":
                    name = obj.get("toolName") or "tool"
                    result = obj.get("result") or {}
                    content = result.get("content") or []
                    chunks: List[str] = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            tx = c.get("text")
                            if isinstance(tx, str):
                                chunks.append(tx)
                    if chunks:
                        body = "".join(chunks)
                        if len(body) > 12000:
                            body = body[:12000] + "\n… (truncated)"
                        tool_blocks.append(f"\n\n### {name}\n```\n{body}\n```")
                elif t == "agent_end":
                    body = "".join(text_parts).strip()
                    if not body:
                        body = _assistant_text_from_agent_end(obj)
                    if tool_blocks:
                        body = (body or "(Pi finished — tool output below.)") + "".join(
                            tool_blocks
                        )
                    return body or "(empty reply)"

                elif t == "extension_error":
                    err = obj.get("error") or str(obj)
                    raise RuntimeError(f"Pi extension error: {err}")

    async def shutdown(self) -> None:
        # Do not take _lock: a long prompt would block app shutdown forever.
        await self._stop_proc()


def last_user_text(messages: List[Dict[str, Any]]) -> Optional[str]:
    for m in reversed(messages):
        if not isinstance(m, dict):
            continue
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None
