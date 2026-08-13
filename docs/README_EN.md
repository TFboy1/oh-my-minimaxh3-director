<p align="center">
  <img src="../banner.svg" alt="oh-my-minimaxh3-director Banner" width="100%"/>
</p>

[![Skills.sh](https://img.shields.io/badge/Skills.sh-Install%20Skill-00C853?style=for-the-badge&logo=hackthebox&logoColor=white)](https://skills.sh/tfboy1/oh-my-minimaxh3-director/oh-my-minimaxh3-director) [![爱发电](https://img.shields.io/badge/爱发电-Support%20Me-FF69B4?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.ifdian.net/item/1a20ed042f0711f1865a52540025c377) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.creem.io/payment/prod_1yc40mIhKwwrc7iqFOG9G2) [![GitHub Stars](https://img.shields.io/github/stars/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&logo=github&color=yellow)](https://github.com/TFboy1/oh-my-minimaxh3-director/stargazers) [![License](https://img.shields.io/github/license/tfboy1/oh-my-minimaxh3-director?style=for-the-badge&color=blue)](LICENSE)

[![简体中文](https://img.shields.io/badge/简体中文-README-blue?style=flat-square)](../README.md) [![English](https://img.shields.io/badge/English-Current-red?style=flat-square)](#) [![日本語](https://img.shields.io/badge/日本語-README-blue?style=flat-square)](README_JA.md) [![Français](https://img.shields.io/badge/Français-README-blue?style=flat-square)](README_FR.md) [![Deutsch](https://img.shields.io/badge/Deutsch-README-blue?style=flat-square)](README_DE.md)

<p align="center">
Your AI film director. Give me a script, and I'll give you the final cut —
an automated pipeline: storyboard → MiniMax H3 generation → one-click JianYing assembly.
</p>

## Features

- 🎬 **Automatic storyboarding**: Feed it a script or story text and it splits it into
  segments (10s each by default, 2-3 shots per segment), generating `storyboard.md`,
  `storyboard.json`, and H3 six-part prompts.
- 🎞️ **MiniMax H3 workflow routing**: Automatically routes to Ref2VA (reference images),
  T2V (pure text), or I2V (first/last frames), and patches prompt, duration, steps, seed,
  resolution, and output prefix by `class_type` — never hard-coded node IDs.
- ✅ **Parameter confirmation**: Summarizes all parameters into one table for your review
  before submission; invalid values (duration 5-15s, steps 4-40, etc.) are rejected by
  backend validation.
- ☁️ **Cloudflare tunnel**: Detects local 8188 / existing tunnels / AutoDL automatically,
  and starts or reuses a TryCloudflare tunnel when remote access is needed.
- 📥 **Batch submission & resumable monitoring**: Uploads reference images, submits each
  segment, polls and downloads results with automatic retries and persistent state.
- ✂️ **JianYing auto-assembly**: Uses jianying-editor to build a JianYing draft (ordered
  clips + dissolve transitions), with optional automatic MP4 export.
- 🖥️ **First-use onboarding**: Asks about auto-update, detects ComfyUI, evaluates hardware,
  guides model downloads from ModelScope, and asks — with a clear purpose for each — whether
  to install helper skills and the Comfy MCP server.

## Installation

Install from skills.sh (recommended):

```bash
npx skills add TFboy1/oh-my-minimaxh3-director --skill oh-my-minimaxh3-director
```

Or clone for local development:

```bash
git clone https://github.com/TFboy1/oh-my-minimaxh3-director.git
```

## First Use

On first invocation, the skill confirms the following with you, explaining the purpose of
each item before asking:

1. Enable **auto-update**? (recommended);
2. Is **ComfyUI** installed? (otherwise a desktop download tutorial is provided);
3. Run **hardware detection** to see whether your machine can run MiniMax H3;
4. Are the **MiniMax H3 models** downloaded? (otherwise a ModelScope tutorial is provided);
5. Optional dependencies: `h3-prompt-writing` (prompts), `jianying-editor` (assembly),
   `comfy-mcp` (ComfyUI management).

Full tutorial: [references/setup-guide.md](../references/setup-guide.md).

## Usage

In Codex, just say:

> Use $oh-my-minimaxh3-director to turn this script into a video

Then provide a script file or story text. Pipeline:

```text
script/story → storyboard → H3 workflows → parameter confirmation → submit & generate
→ download clips → JianYing draft → (optional) auto export
```

Manual step-by-step:

```bash
# 1. Probe ComfyUI (open a tunnel when remote access is needed)
python scripts/probe_comfy.py --workspace <workspace root> --write
python scripts/ensure_cloudflared.py --workspace <workspace root>

# 2. Build per-segment workflows and the parameter table
python scripts/build_workflows.py --project <project dir> --workspace <workspace root>

# 3. Submit and monitor (resumable)
python scripts/submit_jobs.py --project <project dir> --workspace <workspace root>
python scripts/monitor_jobs.py --project <project dir> --workspace <workspace root>

# 4. Generate and run the JianYing assembly script
python scripts/generate_assembly.py --project <project dir> --title <film title>
python <project dir>/assemble_jianying_<film title>.py
```

## Hardware Requirements

Run `python scripts/check_hardware.py` (or `--remote-url <URL>` to evaluate a remote GPU):

| VRAM | Verdict | Suggestion |
|---|---:|---|
| < 12GB | Not recommended locally | Cloud GPU (AutoDL 24GB+) or Comfy Cloud |
| 12-16GB | Entry-level | int8/nvfp4 quantized + 4-step Turbo, 0.4MP shorts |
| 16-24GB | Recommended | 0.4-0.6MP, 10s clips |
| 24GB+ | High-end | 0.6-1MP, 10-15s clips |

Models total ~40GB; NVIDIA GPU + CUDA required; reserve 60GB+ disk.

## Project Structure

```text
oh-my-minimaxh3-director/
├── SKILL.md                    # main skill workflow
├── README.md
├── banner.svg                  # repo banner
├── agents/openai.yaml          # UI metadata
├── assets/templates/           # H3 templates (ref2va / t2v / i2v, API format)
├── references/
│   ├── setup-guide.md          # first-use setup: ComfyUI / models / hardware / deps
│   ├── storyboard-schema.md    # storyboard JSON & prompt spec
│   ├── workflow-routing.md     # template routing & field mapping
│   └── cloudflared.md          # tunnel operations
├── scripts/                    # pipeline scripts
└── evals/evals.json            # test cases
```

## FAQ

- **`node_errors` on submit**: usually a missing custom node or wrong model filename on the
  remote ComfyUI; the error message names it — install/fix accordingly.
- **Local OOM**: lower resolution (0.4MP → 0.2MP), shorten clips, switch to 4-step Turbo,
  or move to a cloud GPU.
- **Unstable tunnel**: `ensure_cloudflared.py --stop` then restart, or fall back to the
  AutoDL direct address.
- **Custom templates**: convert UI-format workflows with `convert_ui_workflow.py` and put
  the API-format JSON into `templates_dir`.

## Credits

This project stands on the shoulders of these open-source projects:

- [MiniMax H3](https://github.com/MiniMax-AI/MiniMax-H3) (MiniMax-AI): the model and the
  `h3-prompt-writing` skill, under the MiniMax H3 community license;
- [Comfy-Org/minimax-H3](https://www.modelscope.cn/models/Comfy-Org/minimax-H3): ModelScope
  repackaged models for fast downloads in China;
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI): video generation engine, GPL-3.0;
- [jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)
  (luoluoluo22): JianYing assembly via JyWrapper, MIT;
- [comfy-mcp](https://github.com/Comfy-Org/comfy-mcp) (Comfy-Org): ComfyUI MCP server,
  AGPL-3.0-or-later OR Commercial;
- [cloudflared](https://github.com/cloudflare/cloudflared) (Cloudflare): remote tunnels,
  Apache-2.0.

Full list: [CONTRIBUTORS.md](../CONTRIBUTORS.md)

## License

The skill code is open-sourced under the **MIT** license — see [LICENSE](../LICENSE).
Model weights follow the MiniMax H3 community license; upstream components
(ComfyUI, comfy-mcp, jianying-editor-skill, cloudflared) keep their own licenses.
