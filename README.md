<p align="center">
  <img src="banner.svg" alt="oh-my-minimaxh3-director Banner" width="100%"/>
</p>

[![Skills.sh](https://img.shields.io/badge/Skills.sh-Install%20Skill-00C853?style=for-the-badge&logo=hackthebox&logoColor=white)](https://skills.sh/tfboy1/oh-my-minimaxh3-director/oh-my-minimaxh3-director) [![爱发电](https://img.shields.io/badge/爱发电-Support%20Me-FF69B4?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.ifdian.net/) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/) [![GitHub Stars](https://img.shields.io/github/stars/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&logo=github&color=yellow)](https://github.com/TFboy1/oh-my-minimaxh3-director/stargazers) [![License](https://img.shields.io/github/license/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&color=blue)](LICENSE)

[![MiniMax H3](https://img.shields.io/badge/MiniMax-H3-c084fc?style=flat-square)](https://www.modelscope.cn/models/Comfy-Org/minimax-H3) [![ComfyUI](https://img.shields.io/badge/ComfyUI-0.32%2B-22d3ee?style=flat-square)](https://www.comfy.org/) [![JianYing](https://img.shields.io/badge/JianYing-auto-f472b6?style=flat-square)](#) [![Cloudflare Tunnel](https://img.shields.io/badge/Cloudflare-Tunnel-f97316?style=flat-square)](#)

[![简体中文](https://img.shields.io/badge/简体中文-当前语言-red?style=flat-square)](#) [![English](https://img.shields.io/badge/English-README-blue?style=flat-square)](docs/README_EN.md) [![日本語](https://img.shields.io/badge/日本語-README-blue?style=flat-square)](docs/README_JA.md) [![Français](https://img.shields.io/badge/Français-README-blue?style=flat-square)](docs/README_FR.md) [![Deutsch](https://img.shields.io/badge/Deutsch-README-blue?style=flat-square)](docs/README_DE.md)

<p align="center">
你的 AI 视频导演。把剧本交给我，把成片还给你——剧本自动分镜 →
MiniMax H3 生成 → 剪映一键拼合的全自动流水线。
</p>

## 功能特性

- 🎬 **剧本自动分镜**：输入剧本/故事文本，自动切成段（默认每段 10 秒），
  每段 2-3 个分镜，生成 `storyboard.md` + `storyboard.json` 和 H3 六段式提示词。
- 🎞️ **MiniMax H3 工作流分配**：按内容自动路由 Ref2VA（有参考图）/ T2V
  （纯文本）/ I2V（首尾帧），按 class_type 覆盖提示词、时长、步数、种子、
  分辨率与输出前缀，不写死节点 ID。
- ✅ **参数确认**：提交前把参数汇总成一张表给你确认，后端校验非法值
  （时长 5-15s、步数 4-40 等），不做前端表单。
- ☁️ **Cloudflare 隧道**：自动探测本机 8188 / 已有隧道 / AutoDL，需要远程
  访问时自动复用或启动 trycloudflare 临时隧道。
- 📥 **批量提交与断点监控**：上传参考图 → 逐段提交 → 轮询下载，失败自动
  重试，状态落盘可续跑。
- ✂️ **剪映自动拼合**：调用 jianying-editor 生成剪映草稿（顺序导入 + 叠化
  转场），可选自动导出 MP4。
- 🖥️ **首次使用引导**：询问自动更新、检测 ComfyUI、评估硬件、指导下载
  MiniMax H3 模型，逐个说明用途后询问是否安装辅助 skill 与 MCP。

## 安装

从 skills.sh 安装（推荐）：

```bash
npx skills add TFboy1/oh-my-minimaxh3-director --skill oh-my-minimaxh3-director
```

或直接使用仓库（本地开发）：

```bash
git clone https://github.com/TFboy1/oh-my-minimaxh3-director.git
```

## 首次使用

第一次调用时，skill 会按顺序与你确认，每项都会先说明用途：

1. 是否启用**自动更新**（推荐启用）；
2. 是否已安装 **ComfyUI**（未安装会给官网桌面版下载教程）；
3. 运行**硬件检测**，判断本机能不能带动 MiniMax H3；
4. 是否已下载 **MiniMax H3 模型**（未下载给 ModelScope 教程）；
5. 是否安装可选依赖：`h3-prompt-writing`（提示词）、`jianying-editor`
   （剪映拼合）、`comfy-mcp`（ComfyUI 管理）。

完整教程见 [references/setup-guide.md](references/setup-guide.md)。

## 使用方法

在 Codex 中直接说：

> 使用 $oh-my-minimaxh3-director 把剧本做成视频

然后给出剧本文件或故事文本。流程：

```text
剧本/故事 → 自动分镜 → 构建 H3 工作流 → 参数确认 → 提交生成 → 下载片段
→ 剪映拼合草稿 →（可选）自动导出
```

也可以分步手动执行：

```bash
# 1. 探测 ComfyUI（可选开隧道）
python scripts/probe_comfy.py --workspace <工作区根> --write
python scripts/ensure_cloudflared.py --workspace <工作区根>   # 需要远程时

# 2. 从 storyboard.json + prompts/ 构建每段工作流与参数表
python scripts/build_workflows.py --project <项目目录> --workspace <工作区根>

# 3. 提交并监控（断点可续跑）
python scripts/submit_jobs.py --project <项目目录> --workspace <工作区根>
python scripts/monitor_jobs.py --project <项目目录> --workspace <工作区根>

# 4. 生成并运行剪映拼合脚本
python scripts/generate_assembly.py --project <项目目录> --title <片名>
python <项目目录>/assemble_jianying_<片名>.py
```

## 硬件要求

运行 `python scripts/check_hardware.py` 自动检测本机配置：

| 显存 | 结论 | 建议 |
|---|---:|---|
| < 12GB | 不建议本地跑 | 云 GPU（AutoDL 24GB+）或 Comfy Cloud |
| 12-16GB | 入门可试 | int8/nvfp4 量化 + 4 步 Turbo，0.4MP 短片 |
| 16-24GB | 推荐档 | 0.4-0.6MP、10s 稳定 |
| 24GB+ | 高配 | 0.6-1MP、10-15s |

模型总计约 40GB，需要 NVIDIA GPU + CUDA；磁盘建议预留 60GB+。

## 目录结构

```text
oh-my-minimaxh3-director/
├── SKILL.md                    # skill 主流程
├── README.md
├── agents/openai.yaml          # UI 元数据
├── assets/templates/           # H3 模板（ref2va / t2v / i2v，API 格式）
├── references/
│   ├── setup-guide.md          # 首次安装：ComfyUI / 模型 / 硬件 / 可选依赖
│   ├── storyboard-schema.md    # 分镜 JSON 与提示词规范
│   ├── workflow-routing.md     # 模板路由与字段映射
│   └── cloudflared.md          # 隧道操作细节
├── scripts/                    # 7+1 个流水线脚本
└── evals/evals.json            # 测试用例
```

## 常见问题

- **提交报 `node_errors`**：通常是远程 ComfyUI 缺少节点包或模型文件名不对，
  报错信息会指明，按提示补装/改名。
- **本地 OOM**：降低分辨率（0.4MP → 0.2MP）、缩短时长、改用 4 步 Turbo，
  或直接切到云 GPU。
- **隧道不稳定**：`ensure_cloudflared.py --stop` 停掉后重开，或回退 AutoDL
  直连地址。
- **想加自定义模板**：用 `convert_ui_workflow.py` 把 UI 格式工作流转成 API
  格式，放进 `templates_dir` 即可。

## License

模型权重遵循 MiniMax H3 社区许可；本 skill 代码按 MIT 提供。
