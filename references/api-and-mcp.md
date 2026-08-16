# ComfyUI API 调用指南与 comfy-mcp（api-and-mcp）

本文件解决两类问题：调用 ComfyUI HTTP API 时的正确姿势与常见报错排查
（减少无效重试浪费 token），以及可选安装的 comfy-mcp 服务用法。

## 一、HTTP API 端点速查

| 端点 | 方法 | 用途 |
|---|---|---|
| `/system_stats` | GET | 探测可用性与 GPU/内存状态 |
| `/object_info` | GET | 节点定义与字段名（模板转换/校验用） |
| `/object_info/<class>` | GET | 单个节点定义 |
| `/upload/image` | POST multipart | 上传参考图到 `input/` |
| `/prompt` | POST | 提交工作流，返回 `prompt_id` |
| `/queue` | GET | 当前运行/等待队列 |
| `/history/{prompt_id}` | GET | 任务状态与输出记录 |
| `/view?filename=&subfolder=&type=` | GET | 下载输出文件 |
| `/free` | POST | 释放模型/显存（大任务间隔用） |

本 skill 的 `submit_jobs.py` / `monitor_jobs.py` 已封装上述流程（上传 → 提交
→ 轮询 → 下载，断点续跑）。不要用对话直接逐条 curl 重试，重复提交只会
浪费 token 和算力。

## 二、正确调用顺序（避免踩坑）

1. **先探测**：`probe_comfy.py` 确认 `/system_stats` 可达（隧道/直连均验证
   通过后再继续）。
2. **先校验再提交**：UI 格式工作流先 `convert_ui_workflow.py` 转 API 格式；
   提交前可 `POST /prompt` 返回的 `node_errors` 是唯一权威校验——出错先读
   `node_errors`，不要盲目重试。
3. **一次提交、轮询完成**：记录 `prompt_id` 后只轮询
   `/history/{prompt_id}`，不重复 POST 同一段。
4. **下载只看输出记录**：任务 `completed` 后从 history 的 outputs 提取
   `.mp4` 记录，再 `/view` 下载。
5. **长批量间隔释放显存**：每段之间可 `POST /free`（`unload_models=true`）。

## 三、常见报错与排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `/prompt` 返回 `node_errors` | 缺自定义节点 / 缺模型文件 / 字段名或链接错误 | 读 node_errors 里的 `class_type` 与消息；缺模型按 setup-guide 下载到正确目录；缺节点按名字安装 |
| `node_errors` 提到 `UNETLoader/CLIPLoader` | 模型文件名与远程 ComfyUI 实际文件不一致 | 用 `/object_info/UNETLoader` 看可选模型列表，改模板字段 |
| 连接超时 / `Could not resolve host` | 隧道失效或 DNS 抖动 | 重跑 `probe_comfy.py`；隧道失效重新 `ensure_cloudflared.py` 或回退直连 |
| `SSL: UNEXPECTED_EOF_WHILE_READING` | TryCloudflare 免费隧道不稳定 | 脚本内已有重试；连续失败则换隧道或直连 AutoDL |
| HTTP 404/405 | 端点拼错或远程 ComfyUI 版本旧 | 对照上表端点；确认 base_url 无多余路径 |
| 任务 `status_str=error` | 执行期错误（显存不足/节点内部异常） | 读 `messages` 里的 `exception_message`；OOM 就降分辨率/缩短/换 Turbo，或按无人值守监控处理 |
| 上传图片失败 | 网络抖动或文件名冲突 | 重试（overwrite=true 幂等）；确认路径含中文时编码正确 |
| `/free` 报错 | 某些版本该端点行为不同 | 忽略并继续（脚本已容错） |

**原则**：任何 API 报错先读响应体与日志，定位原因后再动作；同一条命令连续
重试超过 3 次仍未变，停止并报告用户，而不是继续烧 token。

## 四、comfy-mcp（可选增强）

`comfy-mcp` 是 Comfy-Org 官方 MCP 服务，让 Codex 直接管理/运行 ComfyUI
（搜索节点与模型、校验与运行工作流、监控任务、启停服务）。它与本 skill 的
HTTP 脚本并存：脚本是主通道，MCP 是可选交互增强。

### 安装（装进 venv，遵守项目约定）

```bash
<项目>/.venv/Scripts/pip install comfy-mcp "comfy-cli>=1.14.0"
```

### 配置到 Codex（`~/.codex/config.toml`）

```toml
[mcp_servers.comfy]
command = "D:\\Documents\\ChatGPT\\comfyui\\.venv\\Scripts\\comfy-mcp.exe"
```

远程实例（AutoDL/隧道）时，给 MCP 进程设置环境变量：

```toml
[mcp_servers.comfy]
command = "D:\\Documents\\ChatGPT\\comfyui\\.venv\\Scripts\\comfy-mcp.exe"
env = { COMFYUI_URL = "https://<隧道或AutoDL地址>" }
```

### 常用能力

- 探测：`server_info`、`get_system_stats`；
- 工作流：`run_workflow`（API 或 UI JSON）、`validate_workflow`、模板槽位编辑；
- 监控：提交异步任务后 `wait_job` / `watch_job` / `cancel_job`，读取失败原因；
- 管理：`start_comfyui` / `stop_comfyui`、日志查看、资产上传。

注意：MCP 工具面向交互式探索；批量确定性流程仍走本 skill 脚本，避免每次
对话把工作流与状态重新加载一遍（省 token）。

## 五、与无人值守/资源监控配合

- API 层错误（`status_str=error`）与资源层错误（VRAM/RAM 超阈值）分开处理：
  API 错误由 `monitor_jobs.py` 提取报错并重试；资源错误由
  `monitor_resources.py` 暂停提交，防止 OOM 连锁失败。
- 详见 [resource-monitoring.md](resource-monitoring.md)。
