# -*- coding: utf-8 -*-
"""Build per-segment ComfyUI API workflows from a storyboard.json.

Reads <project>/storyboard.json and <project>/prompts/seg_XX.txt, routes each
segment to an H3 template (ref2va / t2v / i2v), overwrites the parameter nodes
by class_type, validates the parameters and prompt depth, and writes:

  <project>/workflows/seg_XX_api.json
  <project>/jobs/params.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import (  # noqa: E402
    console,
    load_json,
    load_pipeline_config,
    now_iso,
    save_json,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"
H3_VIDEO_NODES = {"MiniMaxH3ReferenceToVideo", "MiniMaxH3ImageToVideo"}
PROMPT_MODES = {"official", "wenwu", "hybrid"}
OFFICIAL_SECTIONS = [
    "subject_definitions:",
    "summary:",
    "retention_analysis:",
    "detailed_description:",
    "overall_soundscape:",
    "non_diegetic_music:",
]
VALID_ASPECTS = {
    "1:1 (Square)", "2:3 (Portrait Photo)", "3:2 (Photo)",
    "3:4 (Portrait Standard)", "4:3 (Standard)", "9:16 (Portrait Widescreen)",
    "16:9 (Widescreen)", "21:9 (Ultrawide)",
}


def load_template(templates_dir: Path, name: str, project: Path) -> dict:
    candidate = Path(name)
    if not candidate.suffix:
        candidate = Path(name + ".json")
    search_paths = [
        candidate if candidate.is_absolute() else templates_dir / candidate,
        project / "templates" / candidate,
    ]
    for path in search_paths:
        if path.exists():
            data = load_json(path)
            if isinstance(data, dict):
                return data
            raise RuntimeError(f"模板不是 JSON 对象: {path}")
    raise RuntimeError(
        f"模板 {name} 未找到（查找: " + "、".join(str(p) for p in search_paths) + "）"
    )


def apply_prompt(workflow: dict, prompt: str) -> None:
    changed = False
    for node in workflow.values():
        class_type = node.get("class_type", "")
        if class_type == "PrimitiveStringMultiline":
            node["inputs"]["value"] = prompt
            changed = True
        elif class_type in H3_VIDEO_NODES:
            current = node["inputs"].get("prompt")
            if not isinstance(current, list):
                node["inputs"]["prompt"] = prompt
                changed = True
    if not changed:
        raise RuntimeError("模板中没有可写入提示词的节点（PrimitiveStringMultiline 或 H3 节点 prompt 字段）")


def apply_refs(workflow: dict, refs: list[str], project: Path) -> None:
    loaders = [
        node for node in workflow.values()
        if node.get("class_type") == "LoadImage"
    ]
    if not refs:
        return
    if not loaders:
        raise RuntimeError("该模板没有 LoadImage 节点，无法使用参考图")
    resolved: list[str] = []
    for ref in refs:
        path = Path(ref)
        if not path.is_absolute():
            path = project / path
        if not path.exists():
            raise RuntimeError(f"参考图不存在: {path}")
        resolved.append(str(path))
    if len(resolved) < len(loaders):
        console(f"[build] 警告: 参考图 {len(resolved)} 张少于 LoadImage 节点 "
                f"{len(loaders)} 个，多余节点将重复使用最后一张")
    for index, loader in enumerate(loaders):
        loader["inputs"]["image"] = resolved[min(index, len(resolved) - 1)]


def apply_duration(workflow: dict, duration: float) -> None:
    frames = int(round(duration * 24))
    for node in workflow.values():
        if node.get("class_type") == "ComfyMathExpression":
            source = node["inputs"].get("values.a")
            if isinstance(source, list) and len(source) == 2:
                origin = workflow.get(str(source[0]))
                if origin and origin.get("class_type") == "PrimitiveFloat":
                    origin["inputs"]["value"] = duration
    for node in workflow.values():
        if node.get("class_type") in H3_VIDEO_NODES:
            length = node["inputs"].get("length")
            if isinstance(length, (int, float)):
                node["inputs"]["length"] = frames


def set_widget(workflow: dict, class_type: str, field: str, value: object, required: bool = True) -> None:
    hits = [node for node in workflow.values() if node.get("class_type") == class_type]
    for node in hits:
        if field in node["inputs"]:
            node["inputs"][field] = value
    if required and not hits:
        raise RuntimeError(f"模板缺少节点 {class_type}，无法设置 {field}")


def apply_common_params(
    workflow: dict,
    segment: dict,
    meta: dict,
    project: Path,
    prompt: str,
) -> None:
    seg_id = int(segment["id"])
    duration = float(segment.get("duration", meta.get("duration_default", 10)))
    steps = int(segment.get("steps", meta.get("default_steps", 8)))
    seed = int(segment.get("seed", meta.get("default_seed", 123456789) + seg_id))
    scheduler = segment.get("scheduler", meta.get("default_scheduler", "simple"))
    sampler = segment.get("sampler", meta.get("default_sampler"))

    apply_prompt(workflow, prompt)
    image_inputs = list(segment.get("refs") or [])
    if segment.get("first_frame"):
        image_inputs.append(segment["first_frame"])
    if segment.get("last_frame"):
        image_inputs.append(segment["last_frame"])
    apply_refs(workflow, image_inputs, project)
    apply_duration(workflow, duration)
    set_widget(workflow, "BasicScheduler", "steps", steps)
    set_widget(workflow, "BasicScheduler", "scheduler", scheduler)
    if sampler:
        set_widget(workflow, "KSamplerSelect", "sampler_name", sampler, required=False)
    set_widget(workflow, "RandomNoise", "noise_seed", seed)

    aspect = segment.get("aspect", meta.get("aspect", "16:9 (Widescreen)"))
    megapixels = float(segment.get("megapixels", meta.get("megapixels", 0.4)))
    for node in workflow.values():
        if node.get("class_type") == "ResolutionSelector":
            node["inputs"]["aspect_ratio"] = aspect
            node["inputs"]["megapixels"] = megapixels
            node["inputs"]["multiple"] = 32

    prefix = f"{project.name}/{segment.get('mode', 'h3')}/seg_{seg_id:02d}"
    set_widget(workflow, "SaveVideo", "filename_prefix", prefix)

    segment["steps"] = steps
    segment["seed"] = seed
    segment["scheduler"] = scheduler
    segment["sampler"] = sampler
    segment["duration"] = duration
    segment["aspect"] = aspect
    segment["megapixels"] = megapixels
    segment["filename_prefix"] = prefix


def validate_hybrid_meta(
    meta: dict,
    segments: list[dict],
    characters: list[dict],
    strict: bool,
) -> None:
    """Backend checks for hybrid meta (signature / units / shots / rhythm / sound / anchors)."""
    problems: list[str] = []
    total = sum(
        float(s.get("duration", meta.get("duration_default", 10)))
        for s in segments
    )
    declared = meta.get("total_duration")
    if declared is not None:
        declared_f = float(declared)
        if abs(total - declared_f) > declared_f * 0.05:
            problems.append(
                f"段时长累加 {total:.1f}s 与 meta.total_duration {declared_f:g}s 偏差 >5%"
            )
    sig = meta.get("audiovisual_signature")
    if isinstance(sig, dict):
        color_ids = sig.get("color_ids") or []
        if isinstance(color_ids, (list, dict)) and len(color_ids) > 6:
            problems.append("视听签名 color_ids 超过 6 个")
        master = sig.get("master_dna") or []
        if isinstance(master, (list, tuple)) and len(master) > 3:
            problems.append("视听签名 master_dna 超过 3 位")
        if not str(sig.get("core_theme", "")).strip():
            problems.append("视听签名缺少 core_theme（必须可拍成画面）")
        for field in ("medium", "aspect", "texture", "genre_formula"):
            if not sig.get(field):
                problems.append(f"视听签名缺少 {field}")
    climax = meta.get("climax_segment")
    if climax is not None:
        try:
            target = int(climax)
            starts = 0.0
            found = False
            for segment in segments:
                duration = float(segment.get("duration", meta.get("duration_default", 10)))
                if int(segment["id"]) == target:
                    found = True
                    break
                starts += duration
            if found and total > 0:
                position = starts / total
                if not 0.60 <= position <= 0.80:
                    problems.append(
                        f"高潮段 {target} 起始位置 {position:.0%} 不在全片 60-80%"
                    )
            elif not found:
                problems.append(f"meta.climax_segment={target} 不存在")
        except (TypeError, ValueError, KeyError):
            problems.append("meta.climax_segment 格式错误")
    events = meta.get("sound_events")
    if isinstance(events, list):
        if len(events) > 12:
            problems.append("sound_events 超过 12 个")
        for index, event in enumerate(events, 1):
            if not isinstance(event, dict) or not str(event.get("time", "")).strip() or not str(event.get("event", "")).strip():
                problems.append(f"sound_events 第 {index} 项缺少 time/event")
    shot_segments: list[tuple[int, list[dict]]] = []
    for segment in segments:
        seg_id = int(segment["id"])
        shots = segment.get("shots")
        if not isinstance(shots, list) or not shots:
            continue
        shot_segments.append((seg_id, shots))
        expected_no = 1
        shot_total = 0.0
        for index, shot in enumerate(shots, 1):
            if not isinstance(shot, dict):
                problems.append(f"seg {seg_id} shots 第 {index} 项不是对象")
                continue
            missing = [
                key for key in ("no", "time", "duration", "shot_size", "camera", "content", "sound")
                if not str(shot.get(key, "")).strip()
            ]
            if missing:
                problems.append(f"seg {seg_id} 镜头卡缺字段: {missing}")
            if shot.get("no") != expected_no:
                problems.append(f"seg {seg_id} 镜号不连续: 期望 {expected_no} 实际 {shot.get('no')}")
            expected_no += 1
            try:
                shot_total += float(shot["duration"])
            except (TypeError, ValueError, KeyError):
                problems.append(f"seg {seg_id} 镜头卡 duration 非数字")
        seg_dur = float(segment.get("duration", meta.get("duration_default", 10)))
        if abs(shot_total - seg_dur) > seg_dur * 0.05:
            problems.append(
                f"seg {seg_id} 镜头时长累加 {shot_total:.1f}s 与段长 {seg_dur:g}s 偏差 >5%"
            )
    if shot_segments:
        try:
            import statistics
            per_seg_asl: dict[int, float] = {}
            for seg_id, shots in shot_segments:
                durations = [float(shot["duration"]) for shot in shots]
                per_seg_asl[seg_id] = sum(durations) / len(durations)
            shot_count = sum(len(shots) for _, shots in shot_segments)
            total_sec = sum(
                float(shot["duration"])
                for _, shots in shot_segments
                for shot in shots
            )
            whole_asl = total_sec / shot_count if shot_count else 0.0
            if whole_asl:
                for seg_id, asl in per_seg_asl.items():
                    if asl > whole_asl * 1.5 or asl < whole_asl * 0.5:
                        problems.append(
                            f"seg {seg_id} ASL {asl:.1f}s 偏离全片均值 {whole_asl:.1f}s >50%（需诊断）"
                        )
                if len(per_seg_asl) >= 2:
                    sigma = statistics.pstdev(list(per_seg_asl.values()))
                    if sigma < 0.3:
                        problems.append(f"全片 σ={sigma:.2f} 过平（<0.3）")
                    elif sigma > 1.5:
                        problems.append(f"全片 σ={sigma:.2f} 过抖（>1.5）")
        except (TypeError, ValueError, ZeroDivisionError):
            problems.append("节奏统计失败：镜头卡 duration 异常")
    anchors = meta.get("world_anchors")
    if isinstance(anchors, dict):
        required_anchor_keys = ("origin", "equipment", "energy", "rule", "support")
        for key in required_anchor_keys:
            if not str(anchors.get(key, "")).strip():
                problems.append(f"world_anchors 缺少 {key}")
        for key in anchors:
            if key not in required_anchor_keys:
                problems.append(f"world_anchors 存在未知 slot: {key}")
            elif "出处" not in str(anchors.get(key, "")):
                problems.append(f"world_anchors.{key} 缺少出处标注")
    ref_films = meta.get("reference_films")
    if isinstance(ref_films, list):
        if len(ref_films) > 6:
            problems.append("reference_films 超过 6 部（建议精简）")
        for index, item in enumerate(ref_films, 1):
            if not isinstance(item, dict) or not str(item.get("title", "")).strip() or not str(item.get("usage", "")).strip():
                problems.append(f"reference_films 第 {index} 项缺少 title/usage")
    for character in characters:
        if not isinstance(character, dict):
            continue
        name = character.get("name", "?")
        visible = character.get("visible_shots")
        if isinstance(visible, (list, tuple)):
            valid_ids = {int(segment["id"]) for segment in segments}
            for ref in visible:
                num = ref if isinstance(ref, int) else None
                if isinstance(ref, str) and ref.strip().isdigit():
                    num = int(ref.strip())
                if num is not None and num not in valid_ids:
                    problems.append(f"角色 {name} visible_shots 引用不存在段号: {ref}")
        dialogue_count = character.get("dialogue_count")
        if dialogue_count is not None:
            try:
                float(dialogue_count)
            except (TypeError, ValueError):
                problems.append(f"角色 {name} dialogue_count 非数字")
    for problem in problems:
        console(f"[build] hybrid meta 警告: {problem}")
    if strict and problems:
        raise RuntimeError(
            "hybrid meta 校验失败（strict_prompt_validation）: " + "; ".join(problems)
        )

def validate_prompt_depth(prompt: str, mode: str, seg_id: int, strict: bool) -> None:
    """Backend check for prompt depth per mode (warnings; hard-fail when strict)."""
    problems: list[str] = []
    if mode in ("official", "hybrid"):
        missing = [s for s in OFFICIAL_SECTIONS if s not in prompt]
        if missing:
            problems.append("缺少官方六段式小节: " + ", ".join(missing))
        if "[Shot" not in prompt:
            problems.append("缺少 [Shot N] 镜头标记")
        if "At 00:" not in prompt and "00:" not in prompt:
            problems.append("缺少时间码（At 00:… / 00:…）")
        if mode == "hybrid":
            if "constraints:" not in prompt.lower():
                problems.append("hybrid 模式缺少结尾 constraints: 风格/负向约束块")
    elif mode == "wenwu":
        for keyword in ("镜头", "秒", "声音"):
            if keyword not in prompt:
                problems.append(f"wenwu 模式缺少关键字「{keyword}」")
    else:
        problems.append(f"未知 prompt_mode: {mode}（应为 official / wenwu / hybrid）")
    for problem in problems:
        console(f"[build] seg {seg_id:02d} 提示词深度警告: {problem}")
    if strict and problems:
        raise RuntimeError(
            f"seg {seg_id:02d} 提示词深度校验失败（strict_prompt_validation）: "
            + "; ".join(problems)
        )


def validate_segment(segment: dict, meta: dict) -> None:
    duration = float(segment.get("duration", meta.get("duration_default", 10)))
    steps = int(segment.get("steps", meta.get("default_steps", 8)))
    seed = int(segment.get("seed", meta.get("default_seed", 123456789)))
    aspect = segment.get("aspect", meta.get("aspect", "16:9 (Widescreen)"))
    if not 5 <= duration <= 15:
        raise RuntimeError(f"seg {segment['id']}: 时长 {duration}s 超出 5-15s 范围")
    if not 4 <= steps <= 40:
        raise RuntimeError(f"seg {segment['id']}: 步数 {steps} 超出 4-40 范围")
    if not 0 <= seed <= 2**31 - 1:
        raise RuntimeError(f"seg {segment['id']}: 种子 {seed} 超出 0..2^31-1 范围")
    if aspect not in VALID_ASPECTS:
        raise RuntimeError(f"seg {segment['id']}: 未知比例 {aspect}")


def resolve_mode_and_template(segment: dict, templates_dir: Path, project: Path) -> tuple[str, dict]:
    refs = segment.get("refs") or []
    explicit = segment.get("template")
    mode = segment.get("mode")
    if explicit and not mode:
        mode = Path(explicit).stem
    if not mode:
        if refs:
            mode = "ref2va"
        elif segment.get("first_frame") or segment.get("last_frame"):
            mode = "i2v"
        else:
            mode = "t2v"
    segment["mode"] = mode
    template_name = explicit or mode
    workflow = load_template(templates_dir, template_name, project)
    return mode, workflow


def build(project: Path, templates_dir: Path, selected: set[int] | None) -> dict:
    storyboard_path = project / "storyboard.json"
    if not storyboard_path.exists():
        raise SystemExit(f"缺少 {storyboard_path}")
    storyboard = load_json(storyboard_path)
    if not isinstance(storyboard, dict):
        raise SystemExit("storyboard.json 顶层必须是对象")
    meta = storyboard.get("meta", {})
    segments = storyboard.get("segments", [])
    if not segments:
        raise SystemExit("storyboard.json 没有 segments")
    validate_hybrid_meta(
        meta,
        segments,
        storyboard.get("characters") or [],
        bool(meta.get("strict_prompt_validation", False)),
    )

    workflow_dir = project / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    jobs_dir = project / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    params_segments: list[dict] = []
    for segment in segments:
        seg_id = int(segment["id"])
        if selected and seg_id not in selected:
            continue
        validate_segment(segment, meta)
        prompt_path = Path(segment.get("prompt_file") or f"prompts/seg_{seg_id:02d}.txt")
        if not prompt_path.is_absolute():
            prompt_path = project / prompt_path
        if not prompt_path.exists():
            raise RuntimeError(f"seg {seg_id}: 提示词文件不存在 {prompt_path}")
        prompt = prompt_path.read_text(encoding="utf-8").rstrip()
        if not prompt:
            raise RuntimeError(f"seg {seg_id}: 提示词为空")
        validate_prompt_depth(
            prompt,
            str(meta.get("prompt_mode", "official")),
            seg_id,
            bool(meta.get("strict_prompt_validation", False)),
        )

        mode, workflow = resolve_mode_and_template(segment, templates_dir, project)
        workflow = copy.deepcopy(workflow)
        apply_common_params(workflow, segment, meta, project, prompt)

        output_path = workflow_dir / f"seg_{seg_id:02d}_api.json"
        save_json(output_path, workflow)
        params_segments.append(dict(segment))

    params = {
        "meta": {
            **meta,
            "project": project.name,
            "built_at": now_iso(),
        },
        "segments": params_segments,
    }
    save_json(jobs_dir / "params.json", params)
    return params


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--templates-dir", type=Path, default=None)
    parser.add_argument("--segments", help="逗号分隔的段号，例如 1,3,5")
    args = parser.parse_args()

    project = args.project.resolve()
    pipeline = load_pipeline_config(args.workspace.resolve())
    templates_dir = (
        args.templates_dir
        or (Path(pipeline["templates_dir"]) if pipeline.get("templates_dir") else None)
        or DEFAULT_TEMPLATES_DIR
    ).resolve()
    selected = {int(x) for x in args.segments.split(",")} if args.segments else None
    params = build(project, templates_dir, selected)

    header = (f"{'seg':<4} {'时长':<5} {'模式':<8} {'模板':<10} {'steps':<6} "
              f"{'seed':<12} {'参考图':<4} 输出前缀")
    console(header)
    for segment in params["segments"]:
        console(
            f"{segment['id']:<4} {segment['duration']:<5} {segment['mode']:<8} "
            f"{segment.get('template', segment['mode']):<10} {segment['steps']:<6} "
            f"{segment['seed']:<12} {len(segment.get('refs') or []):<4} "
            f"{segment['filename_prefix']}"
        )
    console(json.dumps({"ok": True, "segments": len(params["segments"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
