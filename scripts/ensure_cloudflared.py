# -*- coding: utf-8 -*-
"""Ensure a Cloudflare TryCloudflare quick tunnel points at the target ComfyUI.

Reuses an already-recorded tunnel URL when it is still reachable, otherwise
downloads cloudflared (if missing) and starts a new quick tunnel:

  cloudflared tunnel --url <target> --no-autoupdate --logfile <log>

The resulting https://*.trycloudflare.com URL is stored in
<workspace>/.config/cloudflared-config.json and pipeline-config.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import (  # noqa: E402
    check_base_url,
    config_paths,
    console,
    load_cloudflared_config,
    load_pipeline_config,
    now_iso,
    save_json,
    save_pipeline_config,
)


CLOUDFLARED_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.zip"
)
TRYCLOUDFLARE_PATTERN = re.compile(r"https://[\w-]+\.trycloudflare\.com")


def find_cloudflared(workspace: Path) -> str | None:
    on_path = shutil.which("cloudflared")
    if on_path:
        return on_path
    local = config_paths(workspace)["tools"] / "cloudflared.exe"
    return str(local) if local.exists() else None


def download_cloudflared(workspace: Path) -> str:
    tools_dir = config_paths(workspace)["tools"]
    tools_dir.mkdir(parents=True, exist_ok=True)
    archive = tools_dir / "cloudflared-windows-amd64.zip"
    target = tools_dir / "cloudflared.exe"
    console(f"[cloudflared] 下载 {CLOUDFLARED_DOWNLOAD_URL}")
    urllib.request.urlretrieve(CLOUDFLARED_DOWNLOAD_URL, archive)  # noqa: S310
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            if member.filename.endswith("cloudflared.exe"):
                with zf.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                break
        else:
            raise RuntimeError("zip 中未找到 cloudflared.exe")
    archive.unlink(missing_ok=True)
    target.chmod(0o755)
    return str(target)


def wait_for_tunnel_url(log_file: Path, timeout_seconds: int) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if log_file.exists():
            text = log_file.read_text(encoding="utf-8", errors="replace")
            match = TRYCLOUDFLARE_PATTERN.search(text)
            if match:
                return match.group(0)
        time.sleep(1)
    raise RuntimeError(
        f"{timeout_seconds} 秒内未从日志解析到 trycloudflare 地址：{log_file}"
    )


def stop_tunnel(workspace: Path) -> dict:
    config = load_cloudflared_config(workspace)
    pid = config.get("pid")
    stopped = False
    if pid:
        try:
            os.kill(int(pid), 9)
            stopped = True
        except OSError as exc:
            console(f"[cloudflared] 停止 PID {pid} 失败: {exc}")
    config["pid"] = None
    config["stopped_at"] = now_iso()
    save_json(config_paths(workspace)["cloudflared"], config)
    return {"stopped": stopped, "tunnel_url": config.get("tunnel_url")}


def ensure_tunnel(
    workspace: Path,
    target_url: str | None,
    dry_run: bool,
    timeout_seconds: int,
) -> dict:
    config = load_cloudflared_config(workspace)
    existing = config.get("tunnel_url")
    if existing:
        console(f"[cloudflared] 检测已有隧道 {existing}")
        if check_base_url(existing, timeout=5):
            pipeline = load_pipeline_config(workspace)
            pipeline["tunnel_url"] = existing
            pipeline["base_url"] = existing
            save_pipeline_config(workspace, pipeline)
            return {
                "tunnel_url": existing,
                "base_url": existing,
                "reused": True,
                "started": False,
            }
        console("[cloudflared] 已有隧道不可达，将重新创建")

    target = target_url or load_pipeline_config(workspace).get("base_url")
    if not target:
        raise SystemExit("未找到目标 ComfyUI 地址，请先运行 probe_comfy.py 或传 --url")
    console(f"[cloudflared] 目标地址: {target}")

    if dry_run:
        exe = find_cloudflared(workspace) or f"<将下载到 {config_paths(workspace)['tools'] / 'cloudflared.exe'}>"
        return {
            "dry_run": True,
            "cloudflared": exe,
            "command": ["cloudflared", "tunnel", "--url", target, "--no-autoupdate"],
            "tunnel_url": None,
        }

    exe = find_cloudflared(workspace)
    if not exe:
        exe = download_cloudflared(workspace)

    log_file = config_paths(workspace)["logs"] / "cloudflared.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        [
            exe, "tunnel", "--url", target,
            "--no-autoupdate", "--logfile", str(log_file), "--loglevel", "info",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
    )
    try:
        tunnel_url = wait_for_tunnel_url(log_file, timeout_seconds)
    except Exception:
        process.terminate()
        raise

    config.update(
        {
            "tunnel_url": tunnel_url,
            "base_url": target,
            "pid": process.pid,
            "log_file": str(log_file),
            "started_at": now_iso(),
            "source": "auto",
        }
    )
    save_json(config_paths(workspace)["cloudflared"], config)
    pipeline = load_pipeline_config(workspace)
    pipeline["tunnel_url"] = tunnel_url
    pipeline["base_url"] = tunnel_url
    save_pipeline_config(workspace, pipeline)
    console(f"[cloudflared] 隧道已启动: {tunnel_url}")
    return {
        "tunnel_url": tunnel_url,
        "base_url": tunnel_url,
        "reused": False,
        "started": True,
        "pid": process.pid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--url", help="隧道目标地址（默认为 pipeline-config.base_url）")
    parser.add_argument("--dry-run", action="store_true", help="只报告将执行的操作")
    parser.add_argument("--stop", action="store_true", help="停止已记录的隧道进程")
    parser.add_argument("--timeout", type=int, default=90, help="等待隧道地址的秒数")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if args.stop:
        console(json.dumps(stop_tunnel(workspace), ensure_ascii=False))
        return 0
    result = ensure_tunnel(workspace, args.url, args.dry_run, args.timeout)
    console(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
