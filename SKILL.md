---
name: oh-my-minimaxh3-director
description: AI 视频导演流水线：剧本自动分镜（含 WenWu 导演级镜头衔接与人物四视图参考图）→ MiniMax H3 工作流分配与参数确认 → 批量生成监控 → 剪映自动拼合成片，可选 Cloudflare 隧道远程访问。提示词支持官方 H3 六段式（official）、WenWu 中文导演模式（wenwu），以及两者兼顾的 hybrid 模式（官方六段式外壳 + WenWu 导演级内容）。用户提到剧本出片、自动分镜、分镜衔接、WenWu、人物四视图、H3 生成、工作流分配、剪映拼合、AI 导演、游戏 PV/宣传片/广告短片/风格与音乐简报，或给出剧本/故事文本要求生成视频时使用。
---

# ComfyUI 剧本视频流水线

## Overview

本 skill 把一条完整链路自动化：探测/打通 ComfyUI（可选 Cloudflare 隧道）→
剧本自动分镜（每段一个 H3 视频，段内 2-3 个分镜）→ 按段分配 H3 模板并覆盖
参数 → 参数确认 → 批量提交/监控/下载 → 生成剪映拼合脚本并建草稿。

v1 只服务 MiniMax H3 的 Ref2VA / T2V / I2V 三种模板，段级生成，默认无字幕无
BGM。所有文件 UTF-8，Python 使用项目 `.venv`（存在时），Windows 下运行。

## 首次使用引导（Onboarding）

第一次使用（以用户目录下的 `~/.oh-my-minimaxh3-director.json` 是否存在判断）
时，按下面顺序逐项与用户确认，**每一项先说明用途再询问**，不替用户做决定；
完成后把选择写入该配置文件。非首次且用户启用自动更新时，每次使用前先
`npx skills update oh-my-minimaxh3-director -g -y`（失败不阻塞流程）。

1. **自动更新**：说明用途（每次使用前自动拉取本 skill 的最新脚本、模板与
   教程），询问是否启用。推荐启用；选项：启用 / 不启用 / 每次询问。
2. **ComfyUI 位置确认**：询问用户“ComfyUI 是本地运行还是云端？”——
   - **本地**：运行 `scripts/probe_comfy.py --workspace <工作区根> --write`
     探测本机 8188；未安装时按 [setup-guide.md](references/setup-guide.md)
     第 1 节给出官网桌面版下载教程（https://www.comfy.org/download）。
   - **云端**：请用户提供网址链接（trycloudflare 隧道地址或 AutoDL 的
     seetacloud 地址），用
     `scripts/probe_comfy.py --workspace <工作区根> --url <链接> --write`
     验证并把该地址写入 `.config/pipeline-config.json` 的 `base_url`；
     链接失效时回退到自动探测。
   把 `comfyui_location: local | cloud` 与地址记入
   `~/.oh-my-minimaxh3-director.json`，后续运行不再重复询问。
3. **硬件评估**：运行 `scripts/check_hardware.py` 检测 NVIDIA 显存、内存与
   磁盘；本机无独显但已有远程 ComfyUI（隧道/AutoDL）时改用
   `--remote-url <地址>` 直接评估远程 GPU。若判定不适合（显存 < 12GB 或
   没有 NVIDIA GPU），明确告知用户，并询问是改用云 GPU（AutoDL / Comfy
   Cloud）还是仍想尝试；远程可用时流水线不受影响。
4. **MiniMax H3 模型**：本地 ComfyUI 且未确认过模型时，询问“是否已下载
   MiniMax H3 模型”；未下载则按 [setup-guide.md](references/setup-guide.md)
   第 2 节给 ModelScope 教程（仓库 `Comfy-Org/minimax-H3`，含文件清单、
   放置目录与约 40GB 空间提示）。
5. **可选依赖**：逐个说明用途后询问是否安装——
   - `h3-prompt-writing`：专业改写 H3 六段式提示词（仅服务 official 与
     hybrid 的六段式外壳；wenwu 纯中文模式不依赖它）；
   - `jianying-editor`：剪映草稿自动拼合（本 skill 拼合阶段依赖）；
   - `comfy-mcp`：让 Codex 直接管理/运行 ComfyUI，可选增强。
   需要安装时按 [setup-guide.md](references/setup-guide.md) 第 4 节执行；
   明确拒绝的记录下来，之后不再反复询问。

## 输入与项目结构

输入：剧本文件（`.md` / `.txt`，或对话中的故事文本），可选参考图目录
（`refs/`）与角色设定。输出项目放在 `outputs/<项目名>/`（或用户指定目录）：

```text
<项目>/
  storyboard.md          # 人读分镜
  storyboard.json        # 机器可读分镜（build_workflows 输入）
  prompts/seg_01.txt …   # H3 提示词（official / wenwu / hybrid）
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
[cloudflared.md](references/cloudflared.md)；首次安装与硬件评估见
[setup-guide.md](references/setup-guide.md)；导演级分镜与 WenWu 引擎见
[wenwu-director.md](references/wenwu-director.md)；hybrid 完整示例见
[hybrid-example.md](references/hybrid-example.md)；无人值守与资源监控见
[resource-monitoring.md](references/resource-monitoring.md)。

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

1. **询问故事要求**：片长、风格、目标平台、角色/参考图、是否指定镜头结构；
   用户意图足够明确时直接创作，不连续追问。
2. 创建 `outputs/<项目名>/`，按 storyboard-schema.md 生成衔接分镜：
   把剧本切段（默认每段 10 秒，5-15 秒可调），每段 2-3 个分镜，上下镜头之间
   写清衔接锚点（动作方向 / 视线 / 光线 / 道具 / 轮廓 / 声桥 / 受力），禁止
   无理由跳切。
3. **生成人物参考图四视图**：模型支持生成图片时直接生成；角色是网上已有角色
   时先搜索下载参考图再生成——每角色三张不同视角全身 + 一张脸部特写，存到
   `refs/` 并在 `storyboard.json` 的 `characters` 登记。
4. **先做提示词模式决策，再写提示词**：写提示词前必须判断简报复杂度，并把
   `meta.prompt_mode` 与 `meta.prompt_mode_reason` 写入 storyboard.json，
   禁止静默走默认。三种模式：
   - `hybrid`（推荐）：创意简报 / 游戏 PV / 宣传片 / 广告 / 短片默认。保持
     官方 H3 六段式英文外壳（subject_definitions / summary /
     retention_analysis / detailed_description / overall_soundscape /
     non_diegetic_music），内容按 WenWu 导演标准写（逐秒镜头脉冲、生命核、
     八条生命通道、表演/状态肌理、音轨编排、结尾 `constraints:` 风格与
     负向约束块），规范见
     [wenwu-director.md](references/wenwu-director.md) 的「hybrid：官方
     六段式 × WenWu 导演深度」，完整示例见
     [hybrid-example.md](references/hybrid-example.md)。项目还可附带
     视听签名 `audiovisual_signature`、声音事件表 `sound_events`、
     7 列镜头卡 `shots`（含机位库/运镜库/转场库/高级技法）、节奏统计、
     世界锚点 `world_anchors`、参考片样本 `reference_films`、
     `climax_segment` 与 `total_duration`，规范见
     [storyboard-schema.md](references/storyboard-schema.md)。
   - `wenwu`：用户明确提到导演 / 分镜衔接 / 镜头设计 / 表演 / WenWu，或
     要求纯中文导演分镜提示词时使用（WenWu 成片书写法）。
   - `official`：仅用于快速批量、无强风格要求的段级生成。
   判断规则：简报含风格系统、色彩系统、音乐编排、逐秒分镜或负向约束，
   或任务属性是 PV / 宣传片 / 广告 / 短片 → 必须 `hybrid`。
   `h3-prompt-writing` 只用于 `official` 与 `hybrid` 的六段式外壳；
   `wenwu` 纯中文模式不依赖它。
   参考图在提示词中用 `<Picture N>` 标签与 `refs` 数组对应。

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
提示词深度也做后端校验：六段齐全、镜头标记与时间码、hybrid 的
`constraints:` 块；`meta.strict_prompt_validation: true` 时不达标直接拒绝。
hybrid meta 另做后端校验：视听签名字段、段时长累加、高潮位置与声音事件表。

## 阶段 3：参数确认

1. 把 `params.json` 汇总成表格展示给用户：段号 / 时长 / 模式 / 模板 / steps /
   scheduler / seed / 比例 / 参考图 / 输出前缀。
2. 用户可修改 `storyboard.json` 中的参数（时长、步数、种子、模板、参考图等）
   后重跑阶段 2；不要做前端表单，脚本后端校验非法值并拒绝。
3. 用户确认后锁定参数，进入提交（`params.json` 保持为提交依据）。

## 阶段 3.5：无人值守确认（每次批量开始前必做）

每次开始批量提交前，**询问用户本次是否无人值守**：

- **是**：与用户约定关机时间（本机 Windows 自动关机，或 AutoDL/云实例的到期
  时间并提醒在云控制台设置）；把约定写入 `jobs/run_plan.json`；按
  [resource-monitoring.md](references/resource-monitoring.md) 启动
  `scripts/monitor_resources.py` 后台监控 GPU 显存与系统内存（默认 warn 90% /
  stop 95%），到达约定时间且用户已授权时执行本机关机。
- **否**：正常人工值守流程，跳过关机约定；资源监控可选。

`monitor_jobs.py` 每轮会读取 `jobs/resource_state.json`，达到 stop 阈值时暂停
本轮并报告，防止显存/内存爆掉。

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
| `build_workflows.py` | 分镜 → 每段 API 工作流 + 参数表（含提示词深度校验） |
| `submit_jobs.py` | 上传资产并批量提交 |
| `monitor_jobs.py` | 轮询下载、失败重试、断点续跑 |
| `generate_assembly.py` | 生成剪映拼合业务脚本 |
| `check_hardware.py` | 检测 GPU/内存/磁盘并给出本地运行建议 |
| `monitor_resources.py` | 无人值守时监控 GPU 显存/内存，支持约定时间关机 |
