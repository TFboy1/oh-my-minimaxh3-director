# 分镜规范（storyboard-schema）

## 分镜主流程（每个项目按此顺序执行）

1. **询问故事要求**：向用户了解故事/剧本内容、片长、风格、目标平台，以及
   是否有指定角色或参考图；用户意图足够明确时直接创作，不连续追问。
2. **生成分镜剧本**：按叙事温度把故事切成段（段 = 一个 H3 视频单元，默认
   10s，5-15s 可调），段内写 2-3 个分镜；**上下镜头之间必须有衔接**——每个
   镜头至少传递一个锚点（同一动作方向、同一视线目标、同一道光、同一个道具、
   同一种轮廓、同一段声音或同一股受力），禁止无理由跳切；完整规则见
   [wenwu-director.md](wenwu-director.md) 的「八条生命通道 · 续」与镜头脉冲。
3. **生成人物参考图（四视图）**：
   - 若用户的模型/环境支持图片生成：直接为每个主要角色生成**四视图**——三张
     不同视角的全身（正面 / 侧面 / 背面或 3/4 视角）+ 一张脸部特写；四视图必须
     锁定同一人物身份（脸、年龄、体型、发型、服装、饰品、惯用手）。
   - 若角色是**网上已有的角色**：先搜索并下载参考图（设定图/立绘等），放入
     `refs/` 作为身份锚点，再基于它生成同一角色的四视图，保证身份不漂移。
   - 输出约定：`refs/<角色名>_front.png`、`refs/<角色名>_side.png`、
     `refs/<角色名>_back.png`、`refs/<角色名>_face.png`；在 `storyboard.json`
     的 `characters` 与段落 `refs` 中登记。
4. **写每个分镜的 H3 规范提示词**：按 `meta.prompt_mode` 选择官方 H3 六段式
   （英文）或 WenWu 导演模式（中文分镜提示词），格式见下文。

提示词模式选择与 WenWu 引擎完整规则见
[wenwu-director.md](wenwu-director.md)。

## 产物文件

分镜产物是三层文件，全部放在用户项目目录下：

1. `storyboard.md` —— 人读版本：文档元数据、人物/单位设定、角色四视图清单、
   段表、镜头表、声音设计。
2. `storyboard.json` —— 机器可读版本：`build_workflows.py` 的直接输入。
3. `prompts/seg_XX.txt` —— 每段一条 H3 提示词（`seg_01.txt`、`seg_02.txt` …）。

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
    "batch": "sc2-5min-dawn",
    "prompt_mode": "wenwu"
  },
  "characters": [
    {
      "name": "泽兰",
      "role": "指挥官",
      "refs": {
        "front": "refs/zelan_front.png",
        "side": "refs/zelan_side.png",
        "back": "refs/zelan_back.png",
        "face": "refs/zelan_face.png"
      }
    }
  ],
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

- `meta.aspect` 必须是 ComfyUI ResolutionSelector 的选项之一（如
  `16:9 (Widescreen)`、`9:16 (Portrait Widescreen)`）。
- `meta.prompt_mode`：`official`（默认）或 `wenwu`，决定提示词写法。
- `characters[]`：每个主要角色的四视图文件（front / side / back / face），
  四视图锁定的身份信息必须写进提示词的 subject_definitions 或 WenWu 生命核。
- `segments[].id` 从 1 开始连续编号，文件名用两位数（`seg_01`）。
- `segments[].mode` 可省略，`build_workflows.py` 按规则自动推断
  （见 workflow-routing.md）。
- `segments[].template` 可省略；省略时等于 mode。内置模板名：`ref2va`、
  `t2v`、`i2v`。
- `segments[].refs` 是参考图路径（相对项目目录），有图时路由到 Ref2VA。
- `segments[].first_frame` / `last_frame` 是首尾帧图片路径，有值且无 refs 时
  路由到 I2V。
- `segments[].duration` 5-15 秒；`segments[].steps` 4-40；`segments[].seed`
  0 到 2^31-1。
- `segments[].prompt_file` 可省略，默认 `prompts/seg_XX.txt`。

## storyboard.md 模板

保持以下固定小节，和现有剧本包一致：

```markdown
# 《片名》 分镜

## 文档元数据
（表格：片名 / 类型 / 全片时长 / 段数 / 规格 / 提示词模式 / 参考图 / 声音 / 工作流）

## 人物
（表格：角色 / 身份 / 声音与气质 / 四视图文件）

## 单位与设定（可选，科幻/奇幻需要）
（表格：单位 / 标准尺度 / 镜头识别规则；尺度一致性约束）

## 段表
（表格：# / 标题 / 节拍 / 戏剧任务 / 承接钩子）

## 镜头表
（表格：段 / 时间 / 开画机位 / 镜头 1 / 镜头 2 / 衔接锚点 / 对白）

## 声音设计
（环境层 / 人声层 / 音乐层；无字幕无 BGM 时明确写出）
```

## prompts/seg_XX.txt 格式

### 模式 A：官方 H3 六段式（`prompt_mode: official`）

每段一条提示词，用英文书写（H3 节点对英文提示词最稳定），包含六个部分，
顺序固定：

```text
subject_definitions:
<角色/场景/单位定义，编号 <Subject 1>、<Subject 2>…>

summary:
<10 秒内的剧情概要，包含 2-3 个分镜的时间线>

retention_analysis:
<为什么观众记住本段，画面吸引力>

detailed_description:
<逐镜头画面描述，明确 "three clearly separated shots with visible cuts between them. Do not render this as one continuous take."，并在镜头间写明衔接锚点>

overall_soundscape:
<环境音 + 原生对白，说话人编号统一，中文对白放在 <d>[Chinese] ...</d> 内>

non_diegetic_music:
<无 BGM 时写 N/A，避免模型自动加音乐>
```

### 模式 B：WenWu 导演模式（`prompt_mode: wenwu`）

每段一条**中文分镜提示词**，按
[wenwu-director.md](wenwu-director.md) 的成片书写法组织：开篇完成时长与比例、
影片类型、生命核、素材职责和最终发展线；时间线写成连续的编号镜头脉冲（每镜
标注起止时间、景别机位、唯一事件、主体变化、摄影机回应、交镜锚点）；人物片
追加「表演肌理」（心理目的、保护层、呼吸、台词触发、面部微调 AU），无人产品
片改为「状态肌理」。

## 段级生成原则（v1 固定）

- 每段 = 一个 H3 视频，默认 10 秒，段内 2-3 个分镜由提示词驱动，段间用硬切
  接续、换新机位。
- **段内上下镜头之间必须有衔接锚点**（动作方向 / 视线 / 光线 / 道具 / 轮廓 /
  声桥 / 受力）；段间换新机位但同样保留一个跨段锚点，禁止无理由跳切。
- 提示词内禁止「参考上一段尾帧/续拍」，每段独立生成（衔接靠文字锚点，不靠
  画面引用）。
- WenWu 模式下段内镜头数与单镜时长按「任意秒数密度公式」计算：高动态
  0.4-1.5s/镜、细腻文戏 2-4s/镜、混合片 1.5-3s/镜；用户指定镜头结构时精确
  遵守。
- 默认无字幕、无 BGM，原生对白直出；如用户要求字幕/BGM，在拼合阶段另行处理。
- 参考图清单与提示词标签的映射必须写进提示词（如 `<Picture 1>` →
  refs/ref_zelan.png）。
