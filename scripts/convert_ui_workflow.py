# -*- coding: utf-8 -*-
"""Convert a ComfyUI UI-format workflow JSON (nodes/links) to API-format JSON.

Usage:
  python convert_ui_workflow.py <ui_workflow.json> --output <api_workflow.json>
      [--object-info-url https://host:port]

The API format is what ComfyUI accepts at POST /prompt. Widget values that are
overridden by links are dropped, and unconnected widget values are mapped to
their field names via the live /object_info endpoint when available, falling
back to the built-in mapping below.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


KNOWN_WIDGET_FIELDS: dict[str, list[str]] = {
    "MiniMaxH3ImageToVideo": ["prompt", "width", "height", "length"],
    "MiniMaxH3ReferenceToVideo": [
        "prompt", "width", "height", "length", "ref_image_size",
    ],
    "BasicScheduler": ["scheduler", "steps", "denoise"],
    "SaveVideo": ["filename_prefix", "format", "codec"],
    "ResolutionSelector": ["aspect_ratio", "megapixels", "multiple"],
    "RandomNoise": ["noise_seed"],
    "PrimitiveFloat": ["value"],
    "PrimitiveStringMultiline": ["value"],
    "ComfyMathExpression": ["expression"],
    "KSamplerSelect": ["sampler_name"],
    "UNETLoader": ["unet_name", "weight_dtype"],
    "CLIPLoader": ["clip_name", "type", "device"],
    "VAELoader": ["vae_name"],
    "LoadImage": ["image"],
    "MiniMaxH3TurboLoRA": ["lora_name", "strength", "low_vram"],
    "MiniMaxH3TurboSampler": [],
    "ImageFromBatch": ["batch_index", "length"],
    "CreateVideo": ["fps", "bit_depth"],
    "PathchSageAttentionKJ": ["sage_attention", "allow_compile"],
}


def load_json(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8-sig"))


def fetch_all_object_info(base_url: str) -> dict:
    url = base_url.rstrip("/") + "/object_info"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {
        class_type: entry.get("input", {})
        for class_type, entry in data.items()
        if isinstance(entry, dict)
    }


def widget_fields_for(
    class_type: str,
    consumed: set[str],
    object_info: dict | None,
) -> list[str]:
    if object_info:
        widget_types = {
            "STRING", "INT", "FLOAT", "BOOLEAN",
            "COMBO", "COMFY_DYNAMICCOMBO_V3",
        }
        names = []
        for section in ("required", "optional"):
            for name, spec in object_info.get(section, {}).items():
                if name in consumed:
                    continue
                if not isinstance(spec, list) or not spec:
                    continue
                field_type = spec[0]
                if isinstance(field_type, list) or field_type in widget_types:
                    names.append(name)
        if names:
            return names
    return [
        name for name in KNOWN_WIDGET_FIELDS.get(class_type, [])
        if name not in consumed
    ]


def convert(ui: dict, object_info_url: str | None) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    link_map: dict[int, tuple[str, int]] = {}
    for link in ui.get("links", []):
        if not link or len(link) < 6:
            continue
        link_id, src_id, src_slot, dst_id, dst_slot = link[:5]
        link_map[int(link_id)] = (str(src_id), int(src_slot))

    object_info: dict[str, dict] = {}
    if object_info_url:
        try:
            object_info = fetch_all_object_info(object_info_url)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"object_info 不可用，使用内置映射（{exc}）")
    api: dict[str, dict] = {}
    for node in ui.get("nodes", []):
        node_id = str(node.get("id"))
        class_type = node.get("type")
        if not class_type:
            continue
        if node.get("mode") == 4:
            warnings.append(f"跳过已旁路节点 {node_id} ({class_type})")
            continue

        inputs: dict[str, object] = {}
        widget_values = list(node.get("widgets_values") or [])
        widget_index = 0
        for inp in node.get("inputs") or []:
            name = inp.get("name")
            link = inp.get("link")
            if link is not None:
                origin = link_map.get(int(link))
                if origin:
                    inputs[name] = [origin[0], origin[1]]
                continue
            if inp.get("widget") and widget_index < len(widget_values):
                inputs[name] = widget_values[widget_index]
                widget_index += 1

        remaining = widget_values[widget_index:]
        if remaining:
            fields = widget_fields_for(
                class_type, set(inputs), object_info.get(class_type)
            )
            if len(fields) < len(remaining):
                warnings.append(
                    f"{class_type}: {len(remaining)} 个 widget 值只有 "
                    f"{len(fields)} 个字段名，多余值将被丢弃"
                )
            for name, value in zip(fields, remaining):
                inputs[name] = value

        api[node_id] = {"class_type": class_type, "inputs": inputs}
    return api, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UI 格式工作流 JSON")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--object-info-url", help="ComfyUI 地址，用于解析字段名")
    args = parser.parse_args()

    ui = load_json(args.input)
    if "nodes" not in ui:
        raise SystemExit(f"{args.input} 不是 UI 格式工作流（缺少 nodes 字段）")
    api, warnings = convert(ui, args.object_info_url)
    for warning in warnings:
        print("WARN:", warning, file=sys.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(api, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(args.output)
    print(f"OK 已转换 {len(api)} 个节点 -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
