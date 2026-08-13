# -*- coding: utf-8 -*-
"""Probe for a reachable ComfyUI instance and record it in pipeline-config.

Probe order: explicit --url > local 127.0.0.1:8188 > existing cloudflared tunnel
URL > AutoDL address from comfy-config.json. Every candidate is verified with
GET /system_stats before being accepted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import (  # noqa: E402
    LOCAL_COMFY_URL,
    check_base_url,
    config_paths,
    console,
    load_cloudflared_config,
    load_json,
    load_pipeline_config,
    save_pipeline_config,
)


def candidates(workspace: Path, explicit: str | None) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if explicit:
        result.append((explicit, "explicit"))
    result.append((LOCAL_COMFY_URL, "local"))

    cloudflared = load_cloudflared_config(workspace)
    tunnel_url = cloudflared.get("tunnel_url")
    if tunnel_url:
        result.append((tunnel_url, "cloudflared-config"))

    pipeline = load_pipeline_config(workspace)
    if pipeline.get("tunnel_url"):
        result.append((pipeline["tunnel_url"], "pipeline-config"))

    comfy_path = config_paths(workspace)["comfy"]
    if comfy_path.exists():
        comfy = load_json(comfy_path)
        if isinstance(comfy, dict):
            address = comfy.get("connection", {}).get("address")
            if address:
                result.append((address, "comfy-config"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--url", help="显式 ComfyUI 地址，优先级最高")
    parser.add_argument("--timeout", type=int, default=3)
    parser.add_argument("--write", action="store_true", help="写入 pipeline-config.json")
    parser.add_argument("--interactive", action="store_true", help="未找到时询问用户")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    found: tuple[str, str] | None = None
    for url, source in candidates(workspace, args.url):
        stats = check_base_url(url, timeout=args.timeout)
        if stats:
            found = (url, source)
            break
        console(f"[probe] 不可达: {url} ({source})")

    if not found and args.interactive:
        user_url = input("未找到可用的 ComfyUI，请输入地址（例如 https://xxx.trycloudflare.com 或 http://127.0.0.1:8188）: ").strip()
        if user_url and check_base_url(user_url, timeout=args.timeout):
            found = (user_url, "user-input")

    if not found:
        console(json.dumps({"found": False}, ensure_ascii=False))
        return 2

    url, source = found
    result = {
        "found": True,
        "base_url": url,
        "source": source,
        "comfyui_version": None,
    }
    stats = check_base_url(url, timeout=args.timeout)
    if stats:
        result["comfyui_version"] = stats.get("system", {}).get("comfyui_version")

    if args.write:
        pipeline = load_pipeline_config(workspace)
        pipeline["base_url"] = url
        pipeline["source"] = source
        save_pipeline_config(workspace, pipeline)
    console(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
