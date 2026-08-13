# -*- coding: utf-8 -*-
"""Monitor GPU VRAM and system RAM to prevent OOM during unattended batch runs.

Samples local nvidia-smi + system RAM (or a remote ComfyUI's /system_stats when
--remote-url is given), compares usage against warn/stop thresholds, writes
<project>/jobs/resource_state.json, and optionally shuts the machine down at a
user-agreed time (unattended mode only, gated by --allow-shutdown).
"""

from __future__ import annotations

import argparse
import ctypes
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import (  # noqa: E402
    console,
    http_json,
    now_iso,
    save_json,
)


def system_ram_pct() -> float:
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0.0
    return status.dwMemoryLoad


def local_gpu() -> dict | None:
    candidates = [
        shutil.which("nvidia-smi"),
        r"C:\Windows\System32\nvidia-smi.exe",
        r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
    ]
    exe = next((path for path in candidates if path and Path(path).exists()), None)
    if not exe:
        return None
    try:
        result = subprocess.run(
            [
                exe,
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    parts = [p.strip() for p in result.stdout.strip().splitlines()[0].split(",")]
    if len(parts) < 4:
        return None
    total = float(parts[1])
    used = float(parts[2])
    return {
        "name": parts[0],
        "vram_total_gb": total / 1024,
        "vram_used_gb": used / 1024,
        "vram_pct": round(used / total * 100, 1) if total else 0.0,
        "source": "local-nvidia-smi",
    }


def remote_gpu(remote_url: str) -> dict | None:
    stats = http_json(remote_url, "/system_stats", timeout=15, attempts=2)
    for device in stats.get("devices", []):
        if device.get("type") != "cuda":
            continue
        total = device.get("vram_total", 0)
        free = device.get("vram_free", 0)
        used = max(total - free, 0)
        return {
            "name": device.get("name", "remote CUDA"),
            "vram_total_gb": total / (1024**3),
            "vram_used_gb": used / (1024**3),
            "vram_pct": round(used / total * 100, 1) if total else 0.0,
            "source": "remote-system-stats",
        }
    return None


def level_for(vram_pct: float | None, ram_pct: float, warn: float, stop: float) -> str:
    values = [ram_pct]
    if vram_pct is not None:
        values.append(vram_pct)
    if any(v >= stop for v in values):
        return "stop"
    if any(v >= warn for v in values):
        return "warn"
    return "ok"


def maybe_shutdown(shutdown_at: str | None, allow_shutdown: bool) -> bool:
    if not shutdown_at:
        return False
    try:
        target = datetime.strptime(shutdown_at, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day,
        )
    except ValueError:
        return False
    if datetime.now() < target:
        return False
    if allow_shutdown and sys.platform == "win32":
        console(f"[monitor] 到达约定关机时间 {shutdown_at}，60 秒后关机")
        subprocess.Popen(
            ["shutdown", "/s", "/t", "60", "/c", "oh-my-minimaxh3-director unattended run finished"],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        console(f"[monitor] 到达约定关机时间 {shutdown_at}（未授权自动关机，仅提示）")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="项目目录（写 jobs/resource_state.json）")
    parser.add_argument("--remote-url", help="远程 ComfyUI 地址（从 /system_stats 读取 GPU）")
    parser.add_argument("--interval", type=int, default=30, help="采样间隔秒数")
    parser.add_argument("--vram-warn", type=float, default=90)
    parser.add_argument("--vram-stop", type=float, default=95)
    parser.add_argument("--ram-warn", type=float, default=90)
    parser.add_argument("--ram-stop", type=float, default=95)
    parser.add_argument("--once", action="store_true", help="采样一次后退出")
    parser.add_argument("--shutdown-at", help="约定关机时间 HH:MM（无人值守时由用户确认）")
    parser.add_argument("--allow-shutdown", action="store_true", help="到达约定时间后真正执行本机关机")
    args = parser.parse_args()

    project = args.project.resolve()
    state_path = project / "jobs" / "resource_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        gpu = remote_gpu(args.remote_url) if args.remote_url else local_gpu()
        ram_pct = system_ram_pct()
        level = level_for(
            gpu["vram_pct"] if gpu else None,
            ram_pct,
            args.vram_warn,
            args.vram_stop,
        )
        state = {
            "timestamp": now_iso(),
            "gpu": gpu,
            "ram_pct": round(ram_pct, 1),
            "level": level,
            "thresholds": {
                "vram_warn": args.vram_warn,
                "vram_stop": args.vram_stop,
                "ram_warn": args.ram_warn,
                "ram_stop": args.ram_stop,
            },
            "shutdown_at": args.shutdown_at,
        }
        save_json(state_path, state)
        gpu_text = (
            f"{gpu['vram_used_gb']:.1f}/{gpu['vram_total_gb']:.1f}GB "
            f"({gpu['vram_pct']}%)"
            if gpu
            else "N/A"
        )
        console(
            f"[monitor] {state['timestamp']} | GPU: {gpu_text} "
            f"| RAM: {ram_pct:.0f}% | level: {level}"
        )

        if level == "stop":
            console(
                "[monitor] 资源超过 stop 阈值：建议暂停新提交并释放显存/内存，"
                "或按约定时间关机"
            )
        if args.shutdown_at and maybe_shutdown(args.shutdown_at, args.allow_shutdown):
            return 0
        if args.once:
            return 0 if level != "stop" else 2
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
