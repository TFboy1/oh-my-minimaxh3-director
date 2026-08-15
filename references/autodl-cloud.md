# AutoDL 云端算力使用教程（autodl-cloud）

本地显卡跑不动 MiniMax H3 时，用 AutoDL 租一张云 GPU 来跑 ComfyUI。本文件
独立说明：注册与 Token、启动云端服务（网页控制台 / API 两种方式）、费用说明、
与无人值守关机约定如何衔接。

## 什么时候用 AutoDL

- `check_hardware.py` 判定本地不适合（无 NVIDIA GPU 或显存 < 12GB）；
- 本地能跑但排队任务太多，想并发加速；
- 需要临时大显存（PRO6000-96G / H800-80G）跑高分辨率或长片段。

启动后把 ComfyUI 的服务地址（`https://<主机>.seetacloud.com:8443` 或
Jupyter 域名）交给 skill 初始化流程，用
`scripts/probe_comfy.py --workspace <项目根> --url <地址> --write` 验证并写入
`.config/pipeline-config.json`。

## 一、注册与获取 Token

1. 注册/登录：https://www.autodl.com
2. 获取 Token：
   https://www.autodl.com/console/center/settings/token
   （控制台 → 账户 → 设置 → 开发者 Token）
3. API 服务端 HOST：`https://www.autodl.art`
4. 请求头：`Authorization: <你的Token>`

**安全提醒**：Token 是敏感凭据，只写入 `.config/autodl-config.json`（该文件已
被 .gitignore 排除）或环境变量，绝不提交到 git、绝不写进提示词或日志。

## 二、启动云端服务

### 方式 A：网页控制台（推荐给第一次使用）

1. 进入「算力市场 / 租用实例」，应用镜像选择 **ComfyUI**（如
   「ComfyUI-纯净版」）。
2. 选择 GPU 规格与数量（起步建议 `5090-32G` 或 `4080(S)-32G`；预算充足再上
   `PRO6000-96G` / `H800-80G`）。
3. 计费方式选**按量计费（PAYG）**；系统盘按需扩容（H3 模型约 40GB，建议
   系统盘 ≥ 80GB）。
4. 开机后，在实例详情里复制 **JupyterLab 地址**或 **服务端口 6006 地址**
   （形如 `https://u1-xxxx.seetacloud.com:8443`，即 ComfyUI API 入口），
   交给 skill。

### 方式 B：API 自动创建（进阶）

创建应用实例：

```http
POST https://www.autodl.art/api/v1/adl_dev/dev/instance/pro/create
Authorization: <你的Token>
Content-Type: application/json
```

请求体：

```json
{
  "data_center_list": ["westDC3", "beijingDC2"],
  "req_gpu_amount": 1,
  "expand_system_disk_by_gb": 80,
  "gpu_spec_uuid": "5090-p",
  "application_uuid": "vbxoJpZdGD",
  "application_version": "latest",
  "instance_name": "oh-my-minimaxh3-director",
  "start_command": "sleep 1"
}
```

说明：

- `gpu_spec_uuid` 见下方规格表；`application_uuid="vbxoJpZdGD"` 是
  ComfyUI-纯净版 应用（来自官方 API 响应示例，实际以网页应用详情页为准）。
- `data_center_list` 可选，不传则系统自动选择地区。
- API 创建目前**只支持按量计费**。
- 返回 `data` 为实例 ID，例如 `pro-76419909953e`。

已有实例开机（有卡模式）：

```json
POST /api/v1/adl_dev/dev/instance/pro/power_on
{"instance_uuid": "pro-xxxx", "payload": "gpu", "start_command": "sleep 1"}
```

实例列表 / 详情 / 状态：

```text
POST /api/v1/adl_dev/dev/instance/pro/list       # 分页列表
GET  /api/v1/adl_dev/dev/instance/pro/snapshot   # 详情（SSH/Jupyter/服务地址/价格）
GET  /api/v1/adl_dev/dev/instance/pro/status     # 状态（running / stopped 等）
```

`snapshot` 响应里会返回：

- `ssh_command` / `ssh_port` / `root_password`：SSH 登录信息；
- `jupyter_domain`：JupyterLab 地址；
- `service_6006_domain`：6006 端口服务（ComfyUI API 入口）；
- `payg_price` / `origin_pay_price`：按量计费的折扣价与原始价（数值单位以
  官方文档为准，示例中 `PRO6000-96G` 为 1970 / 3030，按分/小时换算约为
  19.7 元 / 30.3 元每小时，最终以控制台实时价格为准）。

### GPU 规格 ID 对照表（API 使用）

| 前台显示 GPU | 规格名称 | API 规格 ID |
|---|---|---|
| H800-80G | 通用型 | `h800` |
| 4090-48G | 通用型 | `v-48g` |
| PRO6000-96G | 性能型 | `pro6000-p` |
| 4080(S)-32G | 性能型 | `v-32g-p` |
| 3090-48G | 通用型 | `v-48g-350w` |
| 5090-32G | 性能型 | `5090-p` |

## 三、费用说明

- **按量计费（PAYG）**：只有实例**开机（有卡）**时才按小时计费；关机后停止
  按量计费，但实例与磁盘仍保留（数据盘/系统盘费用以控制台账单为准）。
- 建议：先用小规格（`5090-p` 或 `v-32g-p`）验证 ComfyUI + MiniMax H3 能跑通，
  再按需升级到 `pro6000-p` / `h800`，避免白烧大卡费用。
- 模型下载约 40GB，注意系统盘扩容与存储计费。

## 四、无人值守关机衔接

本 skill 的「无人值守 + 约定关机时间」与 AutoDL 对接方式：

- 云端实例：约定时间到达时，调用
  `POST /api/v1/adl_dev/dev/instance/pro/power_off`
  （`{"instance_uuid": "pro-xxxx"}`）关机；或提前在 AutoDL 控制台设置
  **定时关机**。skill 的 `monitor_resources.py --shutdown-at` 只负责本机
  Windows 关机，云实例需用 API/控制台。
- **释放前必须先关机**，否则可能无法释放；释放接口：
  `POST /api/v1/adl_dev/dev/instance/pro/release`。
- 建议把 `instance_uuid` 写进 `.config/autodl-config.json`，方便无人值守脚本
  读取后调用 `power_off`。
