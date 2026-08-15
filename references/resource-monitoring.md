# 无人值守与资源监控（resource-monitoring）

## 批量前置确认（每次开始批量前必做）

**每次开始批量提交（`submit_jobs.py`）之前，必须先询问用户本次是否无人值守。**

- **是（无人值守）**：
  1. 与用户**约定关机时间**（HH:MM）：本机运行则约定 Windows 自动关机时间；
     AutoDL / 云实例则约定实例到期时间（云端关机用 API `power_off` 或控制台
     定时关机，见 [autodl-cloud.md](autodl-cloud.md)）。
  2. 把约定写入 `<项目>/jobs/run_plan.json`：
     `{"unattended": true, "shutdown_at": "23:00", "agreed_by_user": true}`。
  3. 启动资源监控（后台）：
     ```bash
     python scripts/monitor_resources.py --project <项目目录> \
       --remote-url <base_url> --interval 30 \
       --shutdown-at <HH:MM> --allow-shutdown
     ```
     本机 GPU 时去掉 `--remote-url`。`--allow-shutdown` 只在本机 + 用户已约定
     关机时间时传入。
- **否（有人值守）**：正常流程，跳过关机约定；资源监控可选（`--once` 手动
  抽查即可）。

## 监控内容与阈值

- **GPU 显存**：本机读 `nvidia-smi`；远程读 ComfyUI `/system_stats` 的
  `devices[].vram_total / vram_free`。
- **系统内存**：Windows `GlobalMemoryStatusEx`（远程时读
  `system.ram_total / ram_free` 换算）。
- 默认阈值：warn 90%、stop 95%（`--vram-warn/--vram-stop/--ram-warn/
  --ram-stop` 可调）。
- 每次采样写入 `<项目>/jobs/resource_state.json`：
  `{timestamp, gpu, ram_pct, level, thresholds, shutdown_at}`。

## 防爆联动

- `monitor_resources.py` 在 `level=stop` 时控制台告警并建议暂停/关机；
  `--once` 模式以退出码 2 表示超阈值。
- `monitor_jobs.py` 每轮循环开始前读取 `resource_state.json`；若
  `level=stop` 则暂停本轮提交/下载并等待（`--once` 直接退出码 2），防止
  显存/内存爆掉导致整批失败。
- 无人值守 + 约定时间到达：`monitor_resources.py` 打印提示；`--allow-shutdown`
  时在 Windows 执行 `shutdown /s /t 60`。远程云实例无法代操作，需用户在
  云控制台提前设置自动关机。

## 典型无人值守命令

```bash
# 后台监控（远程 ComfyUI，约定 23:00 关机）
python scripts/monitor_resources.py --project <项目目录> \
  --remote-url <base_url> --shutdown-at 23:00 --allow-shutdown

# 单次抽查（有人值守）
python scripts/monitor_resources.py --project <项目目录> --once
```

提交与监控命令照常：

```bash
python scripts/submit_jobs.py --project <项目目录> --workspace <工作区根>
python scripts/monitor_jobs.py --project <项目目录> --workspace <工作区根>
```

## 安全约定

- 只有用户明确确认「无人值守 + 约定关机时间」后才启用 `--allow-shutdown`。
- 监控阈值达到 stop 时**不静默继续**：暂停并报告，由用户决定释放资源或关机。
- run_plan.json 是断点恢复依据：重跑时先读它，若无人值守约定仍在，继续沿用
  监控与关机计划，不再重复询问。
