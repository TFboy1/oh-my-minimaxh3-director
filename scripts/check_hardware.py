# -*- coding: utf-8 -*-
"""Check whether a machine can realistically run MiniMax H3.

Reads NVIDIA GPU name/VRAM via nvidia-smi (or from a remote ComfyUI's
/system_stats when --remote-url is given), system RAM, and free disk space,
then prints a JSON verdict with resolution and model recommendations. This is
an advisory check only; the final call stays with the user.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import shutil
import subprocess
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_common import http_json  # noqa: E402


def system_ram_gb() -> float:
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
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return status.ullTotalPhys / (1024**3)
    return 0.0


def nvidia_info() -> dict | None:
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
                "--query-gpu=name,memory.total,memory.free,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    line = result.stdout.strip().splitlines()
    if not line:
        return None
    parts = [part.strip() for part in line[0].split(",")]
    if len(parts) < 4:
        return None
    return {
        "name": parts[0],
        "vram_total_gb": float(parts[1]),
        "vram_free_gb": float(parts[2]),
        "driver_version": parts[3],
    }


def remote_gpu_info(remote_url: str) -> dict | None:
    stats = http_json(remote_url, "/system_stats", timeout=15, attempts=2)
    for device in stats.get("devices", []):
        if device.get("type") != "cuda":
            continue
        return {
            "name": device.get("name", "remote CUDA"),
            "vram_total_gb": device.get("vram_total", 0) / (1024**3),
            "vram_free_gb": device.get("vram_free", 0) / (1024**3),
            "driver_version": "remote",
        }
    return None


def verdict(gpu: dict | None, ram_gb: float, disk_free_gb: float) -> dict:
    if gpu is None:
        return {
            "can_run_local": False,
            "level": "no-nvidia-gpu",
            "recommendation": (
                "未检测到 NVIDIA GPU。MiniMax H3 需要 NVIDIA 显卡（CUDA），"
                "建议使用云 GPU（AutoDL、Comfy Cloud）或更换显卡。"
            ),
            "recommended_resolution": None,
        }
    vram = gpu["vram_total_gb"]
    if vram < 12:
        return {
            "can_run_local": False,
            "level": "vram-too-low",
            "recommendation": (
                f"显存仅 {vram:.0f}GB，本地跑 MiniMax H3 会频繁 OOM。"
                "建议使用云 GPU（AutoDL 租 24GB+ 实例）或 Comfy Cloud，"
                "或把分辨率降到 0.2MP 以下并用 4 步 Turbo 尝试极短视频。"
            ),
            "recommended_resolution": "0.2MP 以下，仅 5s 片段，不推荐",
        }
    if vram < 16:
        return {
            "can_run_local": True,
            "level": "entry",
            "recommendation": (
                f"显存 {vram:.0f}GB 属于入门档：用 int8_convrot 量化权重 + "
                "nvfp4 文本编码器 + 4 步 Turbo，分辨率 0.4MP、5-6s 短片段可尝试，"
                "长片段容易 OOM。"
            ),
            "recommended_resolution": "0.4MP，5-6s",
        }
    if vram < 24:
        return {
            "can_run_local": True,
            "level": "recommended",
            "recommendation": (
                f"显存 {vram:.0f}GB：推荐组合 int8_convrot + nvfp4 文本编码器 "
                "+ 4 步 Turbo，可稳定跑 0.4-0.6MP、10s 片段。"
            ),
            "recommended_resolution": "0.4-0.6MP，10s",
        }
    return {
        "can_run_local": True,
        "level": "high-end",
        "recommendation": (
            f"显存 {vram:.0f}GB 属于高配：可尝试 0.6-1MP、10-15s 片段，"
            "bf16 权重也可考虑（占显存更多但画质更稳）。"
        ),
        "recommended_resolution": "0.6-1MP，10-15s",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="只输出 JSON")
    parser.add_argument(
        "--remote-url",
        help="远程 ComfyUI 地址，从 /system_stats 读取该机器 GPU 并评估",
    )
    args = parser.parse_args()

    gpu = remote_gpu_info(args.remote_url) if args.remote_url else nvidia_info()
    ram_gb = system_ram_gb()
    disk_free_gb = shutil.disk_usage(Path.cwd().anchor).free / (1024**3)
    result = verdict(gpu, ram_gb, disk_free_gb)
    result["gpu"] = gpu
    result["remote"] = bool(args.remote_url)
    result["ram_total_gb"] = round(ram_gb, 1)
    result["disk_free_gb"] = round(disk_free_gb, 1)
    result["model_download_need_gb"] = 40
    if disk_free_gb < 40:
        result["recommendation"] += (
            f" 注意：磁盘仅剩 {disk_free_gb:.0f}GB，模型下载约需 40GB，"
            "请先清理磁盘或换盘下载。"
        )
    if not args.json:
        print("硬件检测结果：")
        if gpu:
            print(
                f"  GPU: {gpu['name']} | 显存 {gpu['vram_total_gb']:.0f}GB "
                f"(空闲 {gpu['vram_free_gb']:.0f}GB) | 驱动 {gpu['driver_version']}"
            )
        else:
            print("  GPU: 未检测到 NVIDIA 显卡")
        print(f"  内存: {ram_gb:.1f}GB | 磁盘剩余: {disk_free_gb:.1f}GB")
        print(f"  结论: {result['recommendation']}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
