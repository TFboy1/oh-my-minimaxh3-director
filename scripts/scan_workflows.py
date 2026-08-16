# -*- coding: utf-8 -*-
"""Scan the user's existing ComfyUI workflows and list reusable candidates.

Usage:
  python scripts/scan_workflows.py [--project <项目目录>] [--workspace <工作区根>]
      [--dirs dir1,dir2] [--json]

Default scan roots: <project>/workflows, <project>/templates,
<workspace>/workflows, <workspace>/pv1min_workflows, plus
pipeline-config.json's templates_dir. Every JSON is classified as API / UI /
data (non-workflow) and annotated with core H3 nodes, model files, ref-image
slots, Turbo LoRA, and the inferred generation mode. Use the output to ask the
user which workflow to reuse — never invent a new workflow on your own.
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
    console,
    load_json,
    load_pipeline_config,
)


VIDEO_NODES = {
    "MiniMaxH3ReferenceToVideo": "ref2va",
    "MiniMaxH3ImageToVideo": "i2v",
    "MiniMaxH3TextToVideo": "t2v",
    "MiniMaxH3ImageToVideoWithKeyframes": "fl2va",
}
LOADER_FIELDS = {
    "UNETLoader": "unet_name",
    "CLIPLoader": "clip_name",
    "VAELoader": "vae_name",
    "LoraLoaderBypassModelOnly": "lora_name",
    "MiniMaxH3TurboLoRA": "lora_name",
}


def default_roots(project: Path, workspace: Path) -> list[Path]:
    roots: list[Path] = []
    for candidate in (
        project / "workflows",
        project / "templates",
        workspace / "workflows",
        workspace / "pv1min_workflows",
    ):
        if candidate.is_dir():
            roots.append(candidate)
    pipeline = load_pipeline_config(workspace)
    if pipeline.get("templates_dir"):
        extra = Path(pipeline["templates_dir"])
        if extra.is_dir() and extra not in roots:
            roots.append(extra)
    return roots


def classify(path: Path) -> dict:
    try:
        data = load_json(path)
    except Exception as exc:  # noqa: BLE001
        return {"path": str(path), "format": "error", "error": str(exc)}
    if not isinstance(data, dict):
        return {"path": str(path), "format": "error", "error": "顶层不是 JSON 对象"}
    if "nodes" in data and "links" in data:
        fmt = "UI"
        nodes = data.get("nodes", [])
        get_type = lambda node: node.get("type", "") if isinstance(node, dict) else ""
        inputs_of = lambda node: node.get("inputs", []) if isinstance(node, dict) else []
        widgets_of = lambda node: node.get("widgets_values", []) if isinstance(node, dict) else []
    else:
        fmt = "API"
        nodes = list(data.values())
        get_type = lambda node: node.get("class_type", "") if isinstance(node, dict) else ""
        inputs_of = lambda node: node.get("inputs", {}) if isinstance(node, dict) else {}
        widgets_of = lambda node: {}

    types = [get_type(node) for node in nodes]
    core = [t for t in types if t in VIDEO_NODES]
    if not core and not any(t in LOADER_FIELDS for t in types):
        return {"path": str(path), "format": fmt, "kind": "data", "core_nodes": []}

    modes: list[str] = []
    for t in core:
        mode = VIDEO_NODES[t]
        if mode not in modes:
            modes.append(mode)
    load_images = sum(1 for t in types if t == "LoadImage")
    def node_value(node: dict, field: str) -> str:
        if fmt == "UI":
            values = widgets_of(node)
            return str(values[0]) if values else ""
        inputs = inputs_of(node)
        value = inputs.get(field) if isinstance(inputs, dict) else None
        return str(value) if value else ""

    save_video = ""
    for node in nodes:
        if get_type(node) == "SaveVideo":
            save_video = node_value(node, "filename_prefix")
            break
    models: list[str] = []
    turbo = False
    for node in nodes:
        t = get_type(node)
        if t not in LOADER_FIELDS:
            continue
        field = LOADER_FIELDS[t]
        value = node_value(node, field)
        if value:
            models.append(value)
            if "turbo" in value.lower():
                turbo = True
    mode = "|".join(modes) if modes else "other"
    if len(core) > 1 and mode in ("i2v", "ref2va"):
        mode += "-batch"
    scene = "参考图槽位 " + str(load_images) if load_images else "无参考图（纯文本）"
    if turbo:
        scene += " · Turbo"
    return {
        "path": str(path),
        "format": fmt,
        "kind": "workflow",
        "mode": mode,
        "core_nodes": sorted(set(core)),
        "load_image_count": load_images,
        "models": models,
        "turbo": turbo,
        "save_prefix": save_video,
        "scene": scene,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=None)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--dirs", help="逗号分隔的额外扫描目录")
    parser.add_argument("--json", action="store_true", help="只输出 JSON")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    project = args.project.resolve() if args.project else workspace
    roots = default_roots(project, workspace)
    if args.dirs:
        roots = [Path(d).resolve() for d in args.dirs.split(",") if d.strip()] + roots

    seen: set[Path] = set()
    results: list[dict] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            if path in seen or path.stat().st_size > 3_000_000:
                continue
            seen.add(path)
            item = classify(path)
            if item.get("kind") == "workflow":
                results.append(item)

    if args.json:
        console(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    header = f"{'格式':<5} {'模式':<14} {'参考图':<6} {'Turbo':<6} 文件"
    console(header)
    for item in results:
        console(
            f"{item['format']:<5} {item['mode']:<14} "
            f"{item['load_image_count']:<6} {str(item['turbo']):<6} "
            f"{Path(item['path'])}"
        )
    console(json.dumps({"found": len(results), "workflows": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
