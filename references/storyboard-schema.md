# 分镜规范（storyboard-schema）

分镜产物是三层文件，全部放在用户项目目录下：

1. `storyboard.md` —— 人读版本：文档元数据、人物/单位设定、段表、镜头表、声音设计。
2. `storyboard.json` —— 机器可读版本：`build_workflows.py` 的直接输入。
3. `prompts/seg_XX.txt` —— 每段一条 H3 六段式提示词（`seg_01.txt`、`seg_02.txt` …）。

## storyboard.json 结构

```json
{
  "meta": {
    "title": "星海圣战",
    "aspect": "16:9 (Widescreen)",
    "megapixels": 0.4,
    "duration_default": 10,
    "default_steps": 8,
    "default_seed": 123456789,
    "batch": "sc2-5min-dawn"
  },
  "segments": [
    {
      "id": 1,
      "title": "星海·舰队",
      "duration": 10,
      "mode": "ref2va",
      "template": "ref2va",
      "refs": ["refs/ref_mothership.png"],
      "first_frame": null,
      "last_frame": null,
      "shot_notes": ["广角全舰", "侧后方平拍"],
      "dialogue": ["泽兰：太安静了。"],
      "prompt_file": "prompts/seg_01.txt"
    }
  ]
}
```

字段规则：

- `meta.aspect` 必须是 ComfyUI ResolutionSelector 的选项之一（如 `16:9 (Widescreen)`、`9:16 (Portrait Widescreen)`）。
- `segments[].id` 从 1 开始连续编号，文件名用两位数（`seg_01`）。
- `segments[].mode` 可省略，`build_workflows.py` 按规则自动推断（见 workflow-routing.md）。
- `segments[].template` 可省略；省略时等于 mode。内置模板名：`ref2va`、`t2v`、`i2v`。
- `segments[].refs` 是参考图路径（相对项目目录），有图时路由到 Ref2VA。
- `segments[].first_frame` / `last_frame` 是首尾帧图片路径，有值且无 refs 时路由到 I2V。
- `segments[].duration` 5-15 秒；`segments[].steps` 4-40；`segments[].seed` 0 到 2^31-1。
- `segments[].prompt_file` 可省略，默认 `prompts/seg_XX.txt`。

## storyboard.md 模板

保持以下固定小节，和现有剧本包一致：

```markdown
# 《片名》 分镜

## 文档元数据
（表格：片名 / 类型 / 全片时长 / 段数 / 规格 / 参考图 / 声音 / 工作流）

## 人物
（表格：角色 / 身份 / 声音与气质）

## 单位与设定（可选，科幻/奇幻需要）
（表格：单位 / 标准尺度 / 镜头识别规则；尺度一致性约束）

## 段表
（表格：# / 标题 / 节拍 / 戏剧任务 / 承接钩子）

## 镜头表
（表格：段 / 时间 / 开画机位 / 镜头 1 / 镜头 2 / 对白）

## 声音设计
（环境层 / 人声层 / 音乐层；无字幕无 BGM 时明确写出）
```

## prompts/seg_XX.txt 格式（H3 六段式）

每段一条提示词，用英文书写（H3 节点对英文提示词最稳定），包含以下六个部分，顺序固定：

```text
subject_definitions:
<角色/场景/单位定义，编号 <Subject 1>、<Subject 2>…>

summary:
<10 秒内的剧情概要，包含 2-3 个分镜的时间线>

retention_analysis:
<为什么观众记住本段，画面吸引力>

detailed_description:
<逐镜头画面描述，明确 "three clearly separated shots with visible cuts between them. Do not render this as one continuous take.">

overall_soundscape:
<环境音 + 原生对白，说话人编号统一，中文对白放在 <d>[Chinese] ...</d> 内>

non_diegetic_music:
<无 BGM 时写 N/A，避免模型自动加音乐>
```

段级生成原则（v1 固定）：

- 每段 = 一个 H3 视频，默认 10 秒，段内 2-3 个分镜由提示词驱动，段间用硬切接续、换新机位。
- 提示词内禁止"参考上一段尾帧/续拍"，每段独立生成。
- 默认无字幕、无 BGM，原生对白直出；如用户要求字幕/BGM，在拼合阶段另行处理。
- 参考图清单与提示词标签的映射必须写进提示词（如 `<Picture 1>` → refs/ref_zelan.png）。
