# -*- coding: utf-8 -*-
"""Shared helpers for oh-my-minimaxh3-director pipeline scripts."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


LOCAL_COMFY_URL = "http://127.0.0.1:8188"
DEFAULT_POLL_SECONDS = 30
DEFAULT_RETRY_LIMIT = 2
DEFAULT_TIMEOUT = 60

JIANYING_SKILL_CANDIDATES = [
    r"C:\Users\86150\.agents\skills\jianying-editor",
    r"C:\Users\86150\.codex\skills\jianying-editor",
]
JY_DRAFTS_ROOT = Path(
    r"C:\Users\86150\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
)
JY_EXE_DEFAULT = Path(r"D:\JianyingPro\5.9.0.11632\JianyingPro.exe")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> object:
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8-sig"))


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(path)


def config_paths(workspace: Path) -> dict[str, Path]:
    config_dir = workspace / ".config"
    return {
        "config_dir": config_dir,
        "pipeline": config_dir / "pipeline-config.json",
        "cloudflared": config_dir / "cloudflared-config.json",
        "comfy": config_dir / "comfy-config.json",
        "autodl": config_dir / "autodl-config.json",
        "tools": config_dir / "tools",
        "logs": config_dir / "logs",
    }


def load_pipeline_config(workspace: Path) -> dict:
    path = config_paths(workspace)["pipeline"]
    default = {
        "base_url": None,
        "tunnel_url": None,
        "project_root": str(workspace),
        "templates_dir": None,
        "poll_seconds": DEFAULT_POLL_SECONDS,
        "retry_limit": DEFAULT_RETRY_LIMIT,
    }
    if path.exists():
        data = load_json(path)
        if isinstance(data, dict):
            default.update(data)
    return default


def save_pipeline_config(workspace: Path, data: dict) -> None:
    save_json(config_paths(workspace)["pipeline"], data)


def load_cloudflared_config(workspace: Path) -> dict:
    path = config_paths(workspace)["cloudflared"]
    if path.exists():
        data = load_json(path)
        if isinstance(data, dict):
            return data
    return {}


def http_json(
    base_url: str,
    path: str,
    method: str = "GET",
    payload: object | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    attempts: int = 3,
) -> dict:
    url = base_url.rstrip("/") + path
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{method} {path} 失败: {last_error}")


def check_base_url(base_url: str, timeout: int = 3) -> dict | None:
    """Return parsed system_stats if the base URL serves a live ComfyUI."""
    try:
        return http_json(
            base_url, "/system_stats", timeout=timeout, attempts=1
        )
    except Exception:  # noqa: BLE001
        return None


def console(message: str) -> None:
    print(message, flush=True)


def find_venv_python(workspace: Path) -> str:
    candidate = workspace / ".venv" / "Scripts" / "python.exe"
    return str(candidate) if candidate.exists() else sys.executable


def find_jianying_scripts() -> str | None:
    for candidate in JIANYING_SKILL_CANDIDATES:
        path = Path(candidate) / "scripts" / "jy_wrapper.py"
        if path.exists():
            return str(path.parent)
    return None
