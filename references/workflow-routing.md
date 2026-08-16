# H3 工作流路由与字段映射

## 用户工作流优先（铁律）

**构建前必须先扫描用户已有工作流并让用户确认选择，禁止自行创建新工作流。**

```bash
python scripts/scan_workflows.py --project <项目目录> --workspace <工作区根>
```

扫描范围：`<项目>/workflows`、`<项目>/templates`、`<工作区>/workflows`、
`<工作区>/pv1min_workflows` 与 `pipeline-config.json` 的 `templates_dir`。
每个候选会标注：格式（API / UI）、模式（ref2va / i2v / t2v / batch）、
参考图槽位数、Turbo 标记、模型文件与输出前缀。

用户选定后写入 `storyboard.json`：

```json
{
  "meta": {
    "workflow_map": {
      "ref2va": "workflows/clip02_ref_api.json",
      "3": "D:/.../pv1min_workflows/video_minimax_h3_r2v_v2.json"
    }
  }
}
```

- `workflow_map` 的键可以是**模式名**（整批统一）或**段号字符串**（按段
  指定）；段内 `segments[].template` 优先级最高。
- 值可以是绝对路径、相对项目路径，或模板名（去 `.json`）。
- UI 格式工作流必须先 `convert_ui_workflow.py` 转换；`build_workflows.py`
  遇到 UI 格式会报错提示，**不会自动改写用户文件**。
- 只有扫描结果为空或用户明确选择内置模板时，才使用
  `assets/templates/`（ref2va / t2v / i2v）。

## 内置模板（assets/templates，API 格式）

| 模板文件 | 路由条件 | 核心节点 |
|---|---|---|
| `ref2va.json` | 段有 `refs` 参考图 | `MiniMaxH3ReferenceToVideo` + 2 个 `LoadImage` |
| `t2v.json` | 纯文本、无图 | `MiniMaxH3ImageToVideo` + `MiniMaxH3TurboLoRA` + `MiniMaxH3TurboSampler` |
| `i2v.json` | 有 `first_frame`/`last_frame` | `MiniMaxH3ImageToVideo` + `LoadImage` + `ImageFromBatch` |

路由优先级：`segments[].template` > `meta.workflow_map[段号]` >
`meta.workflow_map[mode]` > 内置模式推断（refs → ref2va；首尾帧 → i2v；
否则 t2v）。

## 参数覆盖（按 class_type，不写死节点 ID）

| class_type | 字段 | 来源 |
|---|---|---|
| `PrimitiveStringMultiline` | `value` | 提示词全文 |
| `MiniMaxH3ImageToVideo` / `MiniMaxH3ReferenceToVideo` | `prompt`（仅当直接值） | 提示词全文 |
| `LoadImage` | `image` | `segments[].refs` 或 `first_frame`（本地路径，提交时上传到远程 input 目录） |
| `ComfyMathExpression` | `values.a` 上游 `PrimitiveFloat.value` | 时长（秒） |
| H3 视频节点 | `length`（仅当直接整数） | 时长 × 24 帧 |
| `BasicScheduler` | `steps` / `scheduler` | 参数表 |
| `KSamplerSelect` | `sampler_name`（可选） | 参数表 |
| `RandomNoise` | `noise_seed` | 参数表 |
| `ResolutionSelector` | `aspect_ratio` / `megapixels` / `multiple=32` | 参数表 |
| `SaveVideo` | `filename_prefix` | `<项目名>/<模式>/seg_XX` |

## 参数范围（后端校验，不做前端校验）

- `duration`: 5-15 秒
- `steps`: 4-40
- `seed`: 0 到 2^31-1
- `aspect`: 必须是 ResolutionSelector 选项之一
- 参考图：本地文件必须存在，否则拒绝
- 提示词：非空，否则拒绝

## 参考图上传

ComfyUI 的 `LoadImage.image` 是相对远程 `input/` 目录的路径。`submit_jobs.py`
在提交前会把本地参考图 `POST /upload/image`（multipart，`type=input`，
`subfolder=<项目名>/refs`），然后把节点字段改写为远程相对路径。已上传的
文件在同一批次内缓存，不重复上传；重试提交时 `overwrite=true` 幂等覆盖。

## 扩展模板

`pipeline-config.json` 的 `templates_dir` 可指向你自己的工作流目录
（例如 `pv1min_workflows/`），`build_workflows.py --templates-dir` 也可临时指定。
注意：ComfyUI UI 格式（含 `nodes`/`links`）的模板必须先转换：

```bash
python scripts/convert_ui_workflow.py <ui.json> --output <api.json> \
  --object-info-url <comfy_base_url>
```

`minimax_h3_r2v_reference.json`（多图 Ref2VA 大模板）就是 UI 格式，转换后
才能作为模板使用。转换脚本缺省内置 H3 常用节点的 widget 字段名，object_info
不可用时也能工作；自定义节点建议带上 ComfyUI 地址。

## 提交与监控

- `submit_jobs.py`：上传资产 → `POST /prompt` → 写 `jobs/seg_XX_job.json`。
  `node_errors` 非空时中止（通常是缺模型/节点包，报错里会写明）。
- `monitor_jobs.py`：轮询 `/history/{prompt_id}`，`status_str=error` 时提取
  报错并重试（默认 2 次），完成后从 `/view` 下载 MP4。
- 断点恢复：job 文件保留 `prompt_id`/`status`/`attempt`，重跑脚本跳过已完成段。
