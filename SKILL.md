---
name: oh-my-minimaxh3-director
description: AI 视频导演流水线：剧本自动分镜 → MiniMax H3 工作流分配与参数确认 → 批量生成监控 → 剪映自动拼合成片，可选 Cloudflare 隧道远程访问。用户提到剧本出片、自动分镜、H3 生成、工作流分配、剪映拼合、AI 导演或给出剧本/故事文本要求生成视频时使用。
---

# ComfyUI 剧本视频流水线

## Overview

本 skill 把一条完整链路自动化：探测/打通 ComfyUI（可选 Cloudflare 隧道）→
剧本自动分镜（每段一个 H3 视频，段内 2-3 个分镜）→ 按段分配 H3 模板并覆盖
参数 → 参数确认 → 批量提交/监控/下载 → 生成剪映拼合脚本并建草稿。

v1 只服务 MiniMax H3 的 Ref2VA / T2V / I2V 三种模板，段级生成，默认无字幕无
BGM。所有文件 UTF-8，Python 使用项目 `.venv`（存在时），Windows 下运行。

## 输入与项目结构

输入：剧本文件（`.md` / `.txt`，或对话中的故事文本），可选参考图目录
（`refs/`）与角色设定。输出项目放在 `outputs/<项目名>/`（或用户指定目录）：

```text
<项目>/
  storyboard.md          # 人读分镜
  storyboard.json        # 机器可读分镜（build_workflows 输入）
  prompts/seg_01.txt …   # H3 六段式提示词
  workflows/seg_01_api.json …
  jobs/params.json       # 参数清单（确认对象）
  jobs/seg_01_job.json … # 提交/下载状态（断点恢复）
  clips/raw/<batch>/seg_01_00001-audio.mp4 …
  assemble_jianying_<标题>.py   # 生成的拼合业务脚本（放项目根）
  edit/jianying-draft-report.json
```

分镜 JSON 结构与提示词格式见
[storyboard-schema.md](references/storyboard-schema.md)；模板路由与字段映射见
[workflow-routing.md](references/workflow-routing.md)；隧道操作见
[cloudflared.md](references/cloudflared.md)。

## 阶段 0：探测 ComfyUI 与可选隧道

1. 运行 `scripts/probe_comfy.py --workspace <工作区根> --write` 探测地址。
   探测顺序：本机 8188 → 已记录隧道 URL → AutoDL 配置；全部失败时用
   `--interactive` 询问用户。
2. **询问用户是否需要远程访问**（这是唯一必须问的选项）。需要时运行
   `scripts/ensure_cloudflared.py --workspace <工作区根>`：复用可达的已有
   隧道，否则自动下载 cloudflared 并启动 trycloudflare 临时隧道。
3. 把可用 `base_url` 写入 `.config/pipeline-config.json`，后续脚本自动读取。
   隧道失败不阻塞：回退原地址并继续。

## 阶段 1：剧本 → 分镜

1. 读剧本，必要时提取角色/单位/场景设定，创建 `outputs/<项目名>/`。
2. 按 storyboard-schema.md 生成 `storyboard.md` 与 `storyboard.json`：把剧本
   切段（默认每段 10 秒，5-15 秒可调），每段包含 2-3 个分镜、台词、节拍、
   参考图映射与生成模式。
3. 为每段写 `prompts/seg_XX.txt`：严格使用 H3 六段式
   （subject_definitions / summary / retention_analysis /
   detailed_description / overall_soundscape / non_diegetic_music），
   包含“three clearly separated shots with visible cuts between them”约束，
   原生中文对白写在 `<d>[Chinese] ...</d>`，无 BGM 时音乐层写 N/A。
4. 参考图放 `refs/`，并在提示词中用 `<Picture N>` 标签与
   `storyboard.json` 的 `refs` 数组对应。

## 阶段 2：工作流构建

运行：

```bash
python scripts/build_workflows.py --project <项目目录> --workspace <工作区根>
```

脚本按段路由模板（有参考图 → `ref2va`；首尾帧 → `i2v`；纯文本 → `t2v`；
`template` 显式指定时优先），按 class_type 覆盖提示词、参考图、时长、步数、
scheduler、种子、分辨率与输出前缀，做后端校验（时长 5-15s、步数 4-40、
种子范围、参考图存在、提示词非空），写出 `workflows/seg_XX_api.json` 和
`jobs/params.json`，并打印参数汇总表。

## 阶段 3：参数确认

1. 把 `params.json` 汇总成表格展示给用户：段号 / 时长 / 模式 / 模板 / steps /
   scheduler / seed / 比例 / 参考图 / 输出前缀。
2. 用户可修改 `storyboard.json` 中的参数（时长、步数、种子、模板、参考图等）
   后重跑阶段 2；不要做前端表单，脚本后端校验非法值并拒绝。
3. 用户确认后锁定参数，进入提交（`params.json` 保持为提交依据）。

## 阶段 4：提交、监控与下载

```bash
python scripts/submit_jobs.py --project <项目目录> --workspace <工作区根>
python scripts/monitor_jobs.py --project <项目目录> --workspace <工作区根>
```

- `submit_jobs.py` 先上传本地参考图到远程 input 目录（同批次缓存去重），再
  POST `/prompt`；`node_errors` 非空时中止并报告缺什么。已提交/已下载的段
  自动跳过（`--force` 可重提），支持 `--segments 1,3` 部分提交。
- `monitor_jobs.py` 轮询 `/history/{prompt_id}`：错误提取报错并按重试上限
  （默认 2 次）重新提交，完成后把 MP4 下载到
  `clips/raw/<batch>/seg_XX_00001-audio.mp4`；状态落盘，可断点续跑。
  监控长任务时放后台运行并定期查看 `jobs/monitor_state.json`。
- 单段重试后仍失败：**不要静默跳过**，向用户报告失败段与原因，由用户决定
  重跑、改参数或换模板。

## 阶段 5：剪映拼合

1. 确认片段齐全后生成业务脚本（遵守 jianying-editor“业务脚本放项目目录”规则）：

```bash
python scripts/generate_assembly.py --project <项目目录> --title <片名> \
  --width <宽> --height <高>
```

2. 运行生成的 `assemble_jianying_<标题>.py`（内部 bootstrap jy_wrapper，
   按段序 `add_media_safe`，相邻段加“叠化 0.3s”转场，`save()` 后写
   `edit/jianying-draft-report.json`）。无字幕无 BGM。
3. 告知用户草稿名称与路径，让用户在剪映中打开微调；**仅当用户显式要求**
   自动导出时，调用 jianying-editor 的 `auto_exporter.py`（Windows + 剪映
   5.9 及以下）。导出前可先检查报告 JSON 的 `draft_name`/`drafts_root`。

## 失败恢复与边界

- 断点：`jobs/` 下所有状态为 JSON，重跑任意阶段都幂等跳过已完成段。
- 隧道抖动：探测失败自动回退；`ensure_cloudflared.py --stop` 可停隧道。
- 模板：内置三套 H3 紧凑模板；大模板（如 270KB 多图 Ref2VA）先经
  `convert_ui_workflow.py` 转 API 格式再放入 `templates_dir`。
- 本 skill 不做前端验证；所有合法性检查由脚本后端完成。
- 不在 skill 目录内创建任何业务脚本/项目文件；业务产物一律放用户项目目录。

## 脚本速查

| 脚本 | 用途 |
|---|---|
| `probe_comfy.py` | 探测可用 ComfyUI 地址并写入配置 |
| `ensure_cloudflared.py` | 复用/启动/停止 trycloudflare 隧道 |
| `convert_ui_workflow.py` | UI 格式模板转 API 格式 |
| `build_workflows.py` | 分镜 → 每段 API 工作流 + 参数表 |
| `submit_jobs.py` | 上传资产并批量提交 |
| `monitor_jobs.py` | 轮询下载、失败重试、断点续跑 |
| `generate_assembly.py` | 生成剪映拼合业务脚本 |
