# 首次使用环境搭建教程（setup-guide）

本文件用于第一次使用 `oh-my-minimaxh3-director` 时，按用户情况引导安装
ComfyUI、下载 MiniMax H3 模型、评估硬件，以及安装可选依赖。所有安装都
**先说明用途，再询问用户是否执行**，不替用户做决定。

## 1. 安装 ComfyUI 桌面版

用途：本地运行 MiniMax H3 推理的引擎（也可以只用远程 AutoDL，本步可跳过）。

- 官网：https://www.comfy.org/
- 下载页：https://www.comfy.org/download
- Windows 直链（NVIDIA x64）：https://download.comfy.org/windows/nsis/x64

安装步骤：

1. 下载安装包并安装，首次启动选择「本地安装（Local）」。
2. 启动后 ComfyUI 会监听 `http://127.0.0.1:8188`（可在设置中确认端口）。
3. Comfy Desktop 会在设置里显示模型目录（默认 Windows 为
   `%USERPROFILE%\Documents\ComfyUI\models`，也可自定义，例如
   `E:\Comfy-Desktop\ComfyUI-Shared`）。

验证：访问 `http://127.0.0.1:8188/system_stats`，返回 JSON 即成功。也可运行
`scripts/probe_comfy.py --workspace <项目根> --write` 自动探测。

## 2. 从 ModelScope 下载 MiniMax H3 模型

用途：MiniMax H3 的推理权重（Unet / 文本编码器 / 双 VAE）。ModelScope
（魔搭）国内直连、支持断点续传，比 HuggingFace 更适合国内网络。

模型仓库（官方重打包）：https://www.modelscope.cn/models/Comfy-Org/minimax-H3

社区量化版（nvfp4/INT4/INT8 合并包）：
https://www.modelscope.cn/models/Abiray/MiniMax-H3-nvfp4-INT4-INT8-Convrot

文件放对位置（对照 ComfyUI/models 目录）：

| ComfyUI 目录 | 文件（按需选择） | 说明 |
|---|---|---|
| `models/diffusion_models/` | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | Ref2VA 主模型（推荐 int8） |
| `models/diffusion_models/` | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | FL2VA/首尾帧模式 |
| `models/text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` 或 `..._nvfp4_awq.safetensors` | 32B 文本编码器（nvfp4 更省显存） |
| `models/vae/` | `minimax_h3_video_vae_fp16.safetensors` | 视频 VAE |
| `models/vae/` | `minimax_h3_audio_vae_fp32.safetensors` | 音频 VAE |
| `models/loras/`（可选） | `minimax_h3_turbo_4step_ema_ckpt500.safetensors` | 4 步 Turbo LoRA（T2V 模板需要） |

下载方式（ModelScope 网页或 CLI）：

```bash
# 用 pip 安装 modelscope 后命令行下载（推荐放项目 venv）
<venv>/Scripts/pip install modelscope
<venv>/Scripts/modelscope download --model Comfy-Org/minimax-H3 --local_dir <模型目录>
```

也可以直接在 ModelScope 网页点「下载模型」，逐个文件放入上面的目录。
全部文件约 40GB，请确认磁盘剩余空间足够（`check_hardware.py` 会提示）。

验证：模型就位后，用 skill 内置模板（`assets/templates/`）跑一次
`build_workflows.py` + `submit_jobs.py`，若返回 `node_errors` 且提到
`UNETLoader/CLIPLoader`，说明对应文件名或路径不对，按报错修正。

## 3. 硬件评估

用途：判断本机能不能带得动 MiniMax H3，避免装完跑不动或频繁 OOM。

运行：

```bash
python scripts/check_hardware.py
```

本机没有 NVIDIA GPU、但 ComfyUI 跑在远程机器上时，直接评估远程机器：

```bash
python scripts/check_hardware.py --remote-url https://<隧道或AutoDL地址>
```

脚本会从远程 `/system_stats` 读取 GPU 型号与显存并给出同样的分档建议。

参考分档（NVIDIA 显存）：

| 显存 | 结论 | 建议 |
|---|---:|---|
| < 12GB | 不建议本地跑 | 用云 GPU（AutoDL 24GB+ 实例）或 Comfy Cloud |
| 12-16GB | 入门可试 | int8/nvfp4 量化 + 4 步 Turbo，0.4MP、5-6s 短片 |
| 16-24GB | 推荐档 | int8 + Turbo，0.4-0.6MP、10s 稳定 |
| 24GB+ | 高配 | 0.6-1MP、10-15s，可尝试 bf16 |

其他注意：

- 需要 NVIDIA GPU + CUDA 驱动；int8_convrot 权重需要 PyTorch cu130（ComfyUI
  0.30+ / Comfy Desktop 自带）。
- 系统内存建议 32GB+；模型下载约 40GB，生成视频也占磁盘。
- 显存不足时的替代：AutoDL 租卡（`run_b35_*` 脚本就是远程用法）、Comfy Cloud。

## 4. 可选依赖（逐个询问，说明用途后再装）

### MiniMax H3 提示词 skill（h3-prompt-writing）

用途：专门把分镜需求改写成 H3 六段式提示词（subject_definitions /
summary / retention_analysis / detailed_description / overall_soundscape /
non_diegetic_music），提升提示词质量和一致性。本 skill 自带提示词规范，
装上它后分镜质量更好。

安装：若本地已有 `h3-prompt-writing` skill 则跳过；否则按 skill 发布/安装
流程从 skills.sh 或 GitHub 安装。

### 剪映自动化 skill（jianying-editor）

用途：用 `JyProject` 封装自动生成剪映草稿（导入片段、转场、字幕、导出），
本 skill 的拼合阶段依赖它。未安装时拼合阶段会失败。

安装：本地路径通常为 `C:\Users\<用户名>\.agents\skills\jianying-editor`；
不存在时从 skills.sh / GitHub 安装。安装后确认
`scripts/jy_wrapper.py` 存在。

### ComfyUI MCP 服务（comfy-mcp）

用途：让 Codex 直接管理本地/远程 ComfyUI——搜索节点与模型、校验和运行
工作流、监控任务、启动/停止服务。可选；不装也能用本 skill 的 HTTP API
脚本，装上后交互更顺。

安装（装进项目 venv，遵守「Python 环境装到 venv」约定）：

```bash
<项目>/.venv/Scripts/pip install comfy-mcp "comfy-cli>=1.14.0"
```

配置到 Codex（`~/.codex/config.toml` 的 `[mcp_servers.comfy]`）：

```toml
[mcp_servers.comfy]
command = "D:\\Documents\\ChatGPT\\comfyui\\.venv\\Scripts\\comfy-mcp.exe"
```

说明：`comfy-mcp` 是 stdio 服务，默认驱动 `127.0.0.1:8188`；远程实例可设
环境变量 `COMFYUI_URL=https://<隧道或 AutoDL 地址>` 指向。
