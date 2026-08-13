# -*- coding: utf-8 -*-
"""Poll ComfyUI history and download finished clips.

Reads <project>/jobs/seg_XX_job.json, follows each prompt_id through
/history, retries failed segments up to the configured retry limit, and
downloads finished MP4s to <project>/clips/raw/<batch>/seg_XX_00001-audio.mp4.
State is persisted after every change so the monitor can resume safely.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import (  # noqa: E402
    console,
    http_json,
    load_json,
    load_pipeline_config,
    now_iso,
    save_json,
)
from submit_jobs import (  # noqa: E402
    resolve_base_url,
    submit_segment,
    upload_workflow_assets,
)


def extract_error(entry: dict) -> str:
    for message in entry.get("status", {}).get("messages", []):
        if isinstance(message, list) and message and message[0] == "execution_error":
            info = message[1] if len(message) > 1 and isinstance(message[1], dict) else {}
            return (
                f"{info.get('node_id', '?')} {info.get('node_type', '?')}: "
                f"{info.get('exception_message', '未知错误')}"
            )
    return "未知执行错误"


def find_media(entry: dict) -> list[dict]:
    media = []
    for node_output in entry.get("outputs", {}).values():
        for value in node_output.values():
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, dict) and str(item.get("filename", "")).endswith(".mp4"):
                    media.append(item)
    return media


def download_media(base_url: str, item: dict, destination: Path, timeout: int = 600) -> None:
    query = urllib.parse.urlencode(
        {
            "filename": item["filename"],
            "subfolder": item.get("subfolder", ""),
            "type": item.get("type", "output"),
        }
    )
    url = base_url.rstrip("/") + "/view?" + query
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"下载为空: {url}")
    temporary.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--base-url")
    parser.add_argument("--poll", type=int, default=None)
    parser.add_argument("--retry-limit", type=int, default=None)
    parser.add_argument("--batch", help="clips/raw 下的批目录名")
    parser.add_argument("--once", action="store_true", help="只轮询一轮后退出")
    args = parser.parse_args()

    project = args.project.resolve()
    workspace = args.workspace.resolve()
    params_path = project / "jobs" / "params.json"
    if not params_path.exists():
        raise SystemExit(f"缺少 {params_path}")
    params = load_json(params_path)
    base_url = resolve_base_url(workspace, args.base_url)
    pipeline = load_pipeline_config(workspace)
    poll_seconds = args.poll or pipeline.get("poll_seconds") or 30
    retry_limit = args.retry_limit or pipeline.get("retry_limit") or 2
    batch = args.batch or params.get("meta", {}).get("batch") or "default"
    clips_dir = project / "clips" / "raw" / batch
    state_path = project / "jobs" / "monitor_state.json"

    console(f"[monitor] ComfyUI: {base_url} | batch: {batch} | retry_limit: {retry_limit}")
    while True:
        pending = 0
        unrecoverable = 0
        state_segments: dict[str, dict] = {}
        for segment in params["segments"]:
            seg_id = int(segment["id"])
            job_path = project / "jobs" / f"seg_{seg_id:02d}_job.json"
            key = str(seg_id)
            if not job_path.exists():
                console(f"[monitor] seg {seg_id:02d} 无任务记录，请先运行 submit_jobs.py")
                unrecoverable += 1
                pending += 1
                continue
            job = load_json(job_path)
            status = job.get("status")
            state_segments[key] = job
            if status == "downloaded":
                continue
            pending += 1

            if status == "failed":
                attempts = int(job.get("attempt", 1))
                if attempts >= retry_limit:
                    console(f"[monitor] seg {seg_id:02d} 已失败 {attempts} 次，放弃: {job.get('error')}")
                    unrecoverable += 1
                    continue
                workflow = load_json(Path(job["workflow_path"]))
                upload_workflow_assets(workflow, project, base_url)
                new_job = submit_segment(project, segment, workflow, base_url, attempts + 1)
                console(f"[monitor] seg {seg_id:02d} 第 {attempts + 1} 次提交: {new_job['prompt_id']}")
                continue

            prompt_id = job.get("prompt_id")
            if not prompt_id:
                console(f"[monitor] seg {seg_id:02d} 缺少 prompt_id")
                unrecoverable += 1
                continue
            try:
                history = http_json(base_url, f"/history/{prompt_id}", timeout=30)
            except Exception as exc:  # noqa: BLE001
                console(f"[monitor] seg {seg_id:02d} history 请求失败: {exc}")
                continue
            entry = history.get(prompt_id)
            if not entry:
                console(f"[monitor] seg {seg_id:02d} 仍在队列中")
                continue
            entry_status = entry.get("status", {})
            if entry_status.get("status_str") == "error":
                job["status"] = "failed"
                job["error"] = extract_error(entry)
                job["attempt"] = int(job.get("attempt", 1)) + 1
                save_json(job_path, job)
                console(f"[monitor] seg {seg_id:02d} 执行失败: {job['error']}")
                continue
            if not entry_status.get("completed"):
                console(f"[monitor] seg {seg_id:02d} 生成中")
                continue

            media = find_media(entry)
            if not media:
                job["status"] = "failed"
                job["error"] = "任务完成但没有 mp4 输出"
                job["attempt"] = int(job.get("attempt", 1)) + 1
                save_json(job_path, job)
                console(f"[monitor] seg {seg_id:02d} {job['error']}")
                continue
            destination = clips_dir / f"seg_{seg_id:02d}_00001-audio.mp4"
            try:
                download_media(base_url, media[0], destination)
            except Exception as exc:  # noqa: BLE001
                job["status"] = "failed"
                job["error"] = str(exc)
                job["attempt"] = int(job.get("attempt", 1)) + 1
                save_json(job_path, job)
                console(f"[monitor] seg {seg_id:02d} 下载失败: {exc}")
                continue
            job["status"] = "downloaded"
            job["clip"] = str(destination)
            job["downloaded_at"] = now_iso()
            save_json(job_path, job)
            console(f"[monitor] seg {seg_id:02d} 已下载: {destination}")

        save_json(
            state_path,
            {"updated_at": now_iso(), "batch": batch, "segments": state_segments},
        )
        if pending == 0:
            console("[monitor] 全部片段已下载")
            return 0
        if unrecoverable > 0 and pending == unrecoverable:
            console(f"[monitor] {unrecoverable} 个片段不可恢复")
            return 2
        if args.once:
            console(f"[monitor] 仍有 {pending} 个片段未完成")
            return 1
        time.sleep(poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
