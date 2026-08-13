# -*- coding: utf-8 -*-
"""Submit generated per-segment workflows to a ComfyUI instance.

Uploads local reference images to the remote input directory first, then POSTs
each workflow to /prompt and records prompt_id in <project>/jobs/seg_XX_job.json.
Already submitted or completed jobs are skipped unless --force is used, so the
script can resume after interruptions.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
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


def upload_image(base_url: str, local_path: Path, subfolder: str, timeout: int = 120) -> str:
    boundary = "----pipeline" + uuid.uuid4().hex
    filename = local_path.name
    parts = []
    for field_name, field_value in (
        ("type", "input"),
        ("overwrite", "true"),
        ("subfolder", subfolder),
    ):
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'
            f"{field_value}\r\n"
        )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    )
    body = ("".join(parts)).encode("utf-8") + local_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    url = base_url.rstrip("/") + "/upload/image"
    request = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    remote_subfolder = result.get("subfolder", "")
    remote_name = result.get("name", filename)
    return f"{remote_subfolder}/{remote_name}" if remote_subfolder else remote_name


def upload_workflow_assets(workflow: dict, project: Path, base_url: str) -> int:
    subfolder = f"{project.name}/refs"
    uploaded = 0
    cache: dict[str, str] = {}
    for node in workflow.values():
        if node.get("class_type") != "LoadImage":
            continue
        image = node["inputs"].get("image")
        if not isinstance(image, str):
            continue
        path = Path(image)
        if not path.is_absolute():
            path = project / path
        if not path.exists():
            continue
        key = str(path)
        if key in cache:
            remote = cache[key]
        else:
            remote = upload_image(base_url, path, subfolder)
            cache[key] = remote
            uploaded += 1
        node["inputs"]["image"] = remote
    return uploaded


def submit_segment(
    project: Path,
    segment: dict,
    workflow: dict,
    base_url: str,
    attempt: int,
) -> dict:
    seg_id = int(segment["id"])
    payload = {
        "prompt": workflow,
        "client_id": f"story-video-{project.name}-{seg_id:02d}-{attempt}-{uuid.uuid4().hex[:8]}",
    }
    response = http_json(base_url, "/prompt", method="POST", payload=payload, timeout=180)
    if response.get("node_errors"):
        raise RuntimeError(f"seg {seg_id}: 节点校验失败 {json.dumps(response['node_errors'], ensure_ascii=False)}")
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"seg {seg_id}: 服务器未返回 prompt_id: {response}")
    job = {
        "segment": seg_id,
        "prompt_id": str(prompt_id),
        "number": response.get("number"),
        "seed": segment.get("seed"),
        "attempt": attempt,
        "status": "submitted",
        "submitted_at": now_iso(),
        "workflow_path": str(project / "workflows" / f"seg_{seg_id:02d}_api.json"),
    }
    save_json(project / "jobs" / f"seg_{seg_id:02d}_job.json", job)
    return job


def resolve_base_url(workspace: Path, explicit: str | None) -> str:
    if explicit:
        return explicit.rstrip("/")
    pipeline = load_pipeline_config(workspace)
    if pipeline.get("base_url"):
        return pipeline["base_url"].rstrip("/")
    probe = subprocess.run(
        [
            sys.executable, "-X", "utf8",
            str(Path(__file__).resolve().parent / "probe_comfy.py"),
            "--workspace", str(workspace), "--write",
        ],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    if probe.returncode != 0:
        raise SystemExit(f"未找到 ComfyUI：{probe.stdout} {probe.stderr}")
    last_line = probe.stdout.strip().splitlines()[-1]
    return json.loads(last_line)["base_url"].rstrip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--base-url")
    parser.add_argument("--segments", help="逗号分隔的段号，例如 1,3,5")
    parser.add_argument("--force", action="store_true", help="重新提交已提交的段")
    parser.add_argument("--dry-run", action="store_true", help="只上传资产和校验，不提交")
    args = parser.parse_args()

    project = args.project.resolve()
    params_path = project / "jobs" / "params.json"
    if not params_path.exists():
        raise SystemExit(f"缺少 {params_path}，请先运行 build_workflows.py")
    params = load_json(params_path)
    base_url = resolve_base_url(args.workspace.resolve(), args.base_url)
    console(f"[submit] ComfyUI: {base_url}")

    selected = {int(x) for x in args.segments.split(",")} if args.segments else None
    submitted = 0
    skipped = 0
    for segment in params["segments"]:
        seg_id = int(segment["id"])
        if selected and seg_id not in selected:
            continue
        job_path = project / "jobs" / f"seg_{seg_id:02d}_job.json"
        if not args.force and job_path.exists():
            existing = load_json(job_path)
            if existing.get("status") in {"submitted", "downloaded"}:
                console(f"[submit] seg {seg_id:02d} 已存在（{existing['status']}），跳过")
                skipped += 1
                continue

        workflow_path = project / "workflows" / f"seg_{seg_id:02d}_api.json"
        if not workflow_path.exists():
            raise SystemExit(f"缺少 {workflow_path}，请先运行 build_workflows.py")
        workflow = load_json(workflow_path)
        uploaded = upload_workflow_assets(workflow, project, base_url)
        console(f"[submit] seg {seg_id:02d} 上传参考图 {uploaded} 张")

        if args.dry_run:
            console(f"[submit] dry-run: 将提交 seg {seg_id:02d}（种子 {segment.get('seed')}）")
            continue
        job = submit_segment(project, segment, workflow, base_url, attempt=1)
        console(f"[submit] seg {seg_id:02d} 已提交 prompt_id={job['prompt_id']}")
        submitted += 1

    console(json.dumps({"ok": True, "submitted": submitted, "skipped": skipped}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
