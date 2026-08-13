# Cloudflare 隧道（Windows）

## 探测顺序

`probe_comfy.py` 依次验证候选地址（每个都要 `GET /system_stats` 成功才算数）：

1. `--url` 显式指定（最高优先级）
2. 本机 `http://127.0.0.1:8188`
3. `.config/cloudflared-config.json` 中已记录的 `tunnel_url`（用户参考隧道或上次自动启动的）
4. `.config/pipeline-config.json` 中记录的 `tunnel_url`
5. `.config/comfy-config.json` 的 `connection.address`（AutoDL 直连地址）

`--interactive` 时全部失败会询问用户输入地址。探测结果用 `--write` 写入
`.config/pipeline-config.json`。

## 何时开隧道

只在用户确认"需要远程访问"时启动。如果已有隧道 URL 且可达，直接复用，不再
启动新进程。`ensure_cloudflared.py` 的执行流程：

1. 检查已有隧道（可达则返回）。
2. 找 `cloudflared`（PATH → `.config/tools/cloudflared.exe`）。
3. 都没有则从 GitHub latest 下载 `cloudflared-windows-amd64.zip` 并解压到
   `.config/tools/`。
4. 后台启动：`cloudflared tunnel --url <目标地址> --no-autoupdate
   --logfile .config/logs/cloudflared.log --loglevel info`。
5. 轮询日志（默认 90 秒）匹配 `https://[\w-]+\.trycloudflare\.com`。
6. 把 `tunnel_url` / `base_url` / PID 写入 `.config/cloudflared-config.json`
   和 `pipeline-config.json`。

## 常用命令

```bash
# 探测并写入配置
python scripts/probe_comfy.py --workspace D:\Documents\ChatGPT\comfyui --write --interactive

# 只报告将要做什么
python scripts/ensure_cloudflared.py --workspace D:\Documents\ChatGPT\comfyui --dry-run

# 启动/复用隧道
python scripts/ensure_cloudflared.py --workspace D:\Documents\ChatGPT\comfyui

# 停止隧道（按记录的 PID）
python scripts/ensure_cloudflared.py --workspace D:\Documents\ChatGPT\comfyui --stop
```

## 故障处理

- **隧道 URL 失效**：提交/监控时 `/system_stats` 失败 → 重新探测：本机 8188
  或 AutoDL 直连地址可能仍然可用；需要远程时重新 `ensure_cloudflared.py`。
- **SSL UNEXPECTED_EOF / 偶发超时**：TryCloudflare 免费隧道不稳定，脚本内部
  有重试；`convert_ui_workflow.py` 拉不到 object_info 时会回退内置字段映射。
- **AutoDL 直连 vs 隧道**：AutoDL 的 seetacloud 地址可直接提交 API；隧道只是
  在直连不可达或需要固定入口时使用。skill 默认优先复用可用地址，不重复开隧道。
- **清理**：`--stop` 按 PID 结束进程并清空记录；隧道日志在
  `.config/logs/cloudflared.log`。
