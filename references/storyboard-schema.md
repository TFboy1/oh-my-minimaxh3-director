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
4. **先做提示词模式决策，再写提示词**：按 `meta.prompt_mode` 选择
   `official` / `wenwu` / `hybrid`，并把决策理由写入 `meta.prompt_mode_reason`。
   - `hybrid`：官方 H3 六段式英文外壳 + WenWu 导演级内容（推荐用于 PV /
     宣传片 / 广告 / 短片 / 强风格简报），格式见下文「模式 C」；
   - `wenwu`：中文 WenWu 成片书写法（用户点名导演/分镜/表演/WenWu 时）；
   - `official`：快速批量、无强风格要求时使用。

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
    "prompt_mode": "wenwu",
    "prompt_mode_reason": "用户点名导演级分镜衔接，使用 WenWu 成片书写法",
    "strict_prompt_validation": false
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
- `meta.prompt_mode`：`official`（默认）/ `wenwu` / `hybrid`，决定提示词写法。
- `meta.prompt_mode_reason`：模式决策理由（hybrid / wenwu 建议必填），随
  params.json 输出，便于复核。
- `meta.strict_prompt_validation`：可选布尔；为 true 时 build_workflows 对
  提示词深度校验不合格直接拒绝（默认只警告）。
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

## 视听签名（hybrid 强烈建议，可选字段）

`meta.audiovisual_signature` 锁定全片 8 字段，来自工业分镜模板：

```json
"audiovisual_signature": {
  "medium": "数字 + 模拟 35mm 颗粒 LUT",
  "aspect": "16:9 (Widescreen)",
  "color_ids": { "少女": "珍珠白+幻彩青", "深海墨影": "紫黑+金箔", "深海": "墨蓝黑+珊瑚粉" },
  "texture": ["粒子透光", "墨色流动", "金箔闪光", "留白"],
  "core_theme": "少女把梦之珠投入最后一道潮汐",
  "master_dna": ["宫崎骏", "田晓鹏(粒子水墨)"],
  "genre_formula": { "opening": "月光与珍珠", "turn": "墨影推潮", "climax": "珍珠投入漩涡", "ending": "潮汐退去" }
}
```

规则：

- `color_ids` ≤ 6 个（每个角色/势力一个色相，不允许漏色或重色）；
- `master_dna` ≤ 3 位（超过会互相打架）；
- `core_theme` 必须能拍成画面（主语 + 比喻动词 + 宾语），不能是抽象概念；
- 这些字段会写进 hybrid 提示词：`color_ids` → `subject_definitions`，
  `texture` → `detailed_description` 开头风格句，`genre_formula` 与
  `core_theme` → `summary`。

## 单元结构（段表增强，可选字段）

段表可选字段：

- `unit`：所属戏剧单元编号（按全片时长适配，30-90 秒 2-3 单元，
  1-3 分钟 3-5 单元）；
- `dramatic_task`：单元结束时观众应知/感受到什么（25-60 字）；
- `visual_motif`：3-6 字视觉母题，必须来自 `audiovisual_signature`；
- `hook`：承接钩子（视觉/声音/物件悬念）。

单元规则：相邻单元至少 1 种对比（情绪/视觉/节奏）；高潮单元位于全片
60-80%；首末单元意象 echo（开场意象在结尾闭环）。`meta.climax_segment`
可声明高潮段号，build_workflows 校验其起始位置。

## 声音设计 12-slot（hybrid 建议）

`meta.sound_events` 为固定顺序的 12 个关键声音事件（剧本无对应写 N/A，
不允许跳号）：

1 开场基底 / 2 第一个高频锚点（头 30 秒）/ 3 仪式启动音 / 4 第一次撞击 /
5 战斗中频群 / 6 关键 V.O. / 7 第一次静默 / 8 静默回归 / 9 主题动作音 /
10 高潮余震 / 11 全片唯一（最长静默 / 最响一击 / 最远尾音，三选一）/
12 结尾尾音。

`overall_soundscape` 按低频/中频/高频/人声四层写；`non_diegetic_music`
写 BPM、乐器、进入/变化/停止时间点。示例见
[hybrid-example.md](hybrid-example.md)。

## 7 列镜头卡与工业镜头语言库

每段可带 `shots` 数组（工业镜头卡，7 列严格）：

```json
"shots": [
  {
    "no": 1,
    "time": "0:00",
    "duration": 2.0,
    "shot_size": "极端特写",
    "camera": "水下 · 慢推",
    "content": "珍珠粒子坠落，光透粒子缝隙",
    "sound": "深海低频 + 气泡",
    "transition": "硬切",
    "technique": "插入镜头",
    "tags": ["海报帧"]
  }
]
```

- 内容 ≤30 字（主体 + 动作 + 关键细节）；声音列必填（静默也要写）；
- 标签：`[海报帧]` `[伏笔]` `[关键]` `[重特效]` `[长镜]` `[音锚]`
  `[特设备]`，单镜头最多 2 个；
- 镜号连续不跳号；时长累加 = 段长；时间格式统一 `mm:ss`，半秒精度
  写 `1.5"`，闪剪写 `0.3"`/`0.5"` 并标 Flash Cut；
- 镜头卡是 `detailed_description` 镜头脉冲的“前身”：卡片内容 + 声音
  直接翻译进英文六段，保证官方格式与 WenWu 内容都落地；
- 可选列：`transition`（转场，默认硬切）、`technique`（高级技法）。

### 景别 7 档（中文强制，禁止 ECU/CU 等英文缩写）

| 景别 | 范围 | 主要用途 | 经典片例 |
|---|---|---|---|
| 极端特写 | 眼睛/嘴唇/指尖/一颗钉 | 情感顶点/关键细节/抽象符号 | 《镖客三部曲》眼睛对决；《黑天鹅》羽毛长出皮肤 |
| 近景 | 头部（下巴到发际） | 表情/内心独白/情绪 | 《沉默的羔羊》；《公民凯恩》“玫瑰花蕾” |
| 中近景 | 胸部以上 | 对白主力/半身肢体+表情 | 《老无所依》对峙长镜 |
| 中景 | 腰部以上 | 动作+表情/双人对话 | 《教父》会议桌 |
| 中远景 | 大腿以上 | 动作+环境关系/武打编排 | 《神奇女侠》战场 |
| 全景 | 全身+部分环境 | 空间关系/群体调度 | 《阿拉伯的劳伦斯》；《辛德勒的名单》红衣女孩 |
| 远景 | 全身渺小+大量环境 | 建立/史诗感/终幕渺小 | 《疯狂麦克斯》；《2001》猿人遥望 |

速查：情感顶点→极端特写/近景；对白→中近景/中景；动作→中远景+中景交替；
建立空间→全景/远景；黑屏/闪剪/纯字幕→`—`。

### 机位库（11）

机位 = 摄影机相对主体的空间位置和角度；写法 `<机位修饰>·<运动>`。

平视（默认对白）/ 俯拍（失败/上帝暗示）/ 仰拍（反派登场/英雄定格）/
荷兰角·倾斜（惊悚/反派内心）/ 主观视角 POV（第一人称）/ 过肩 OTS（双人
对白）/ 上帝视角（建立/终幕/调度）/ 虫视角（巨物/仰望英雄）/ 侧面剖视
（武打对峙）/ 双人构图 / 三人构图。

复合写法：`低角度 OTS·过肩`、`俯拍 POV·主观`、`荷兰角 极端特写·倾斜`。

### 运镜库（15）

运动 = 摄影机怎么移动；写法 `<机位>·<运动>(·<速度修饰>)`。

摇（横向跟随）/ 仰俯（上下扫描）/ 推（情绪逼近）/ 拉（情绪释放/揭示）/
横移（跟拍行走）/ 升降（站起坐下跟随）/ 摇臂（开场/终幕）/ 斯坦尼康
（长镜跟随/伪一镜到底）/ 手持（纪录片风/心理失控）/ 跟拍（行走/追逐）/
推拉变焦（风格化推进）/ 急摇（转场利器）/ 无人机（建立/史诗）/
高速摄影（爆炸/子弹时间）/ 静止（冷峻凝视/留白）。

速度修饰：`慢推`/`急推`、`丝滑横移`、`急摇接切`（Whip Pan + Cut）、
`Flash Cut`（≤1 秒）。

### 转场库（14）

默认 `硬切`，不写默认即可；特殊转场写在镜末或镜首注释。

硬切（默认）/ 匹配剪辑（形/动/声匹配）/ 撞切（强烈反差：静→噪）/
J 切（下镜声音先入）/ L 切（上镜声音后留）/ 交叉剪辑（双线并行）/
跳切（同景别时间跳跃）/ 叠化（时间流逝/梦境）/ 淡入 / 淡出 /
圈入圈出（复古/锁焦）/ 划像（条状/星形/对角）/ 急摇接切 /
闪白闪黑（撞击/闪回触发）。

### 高级镜头技法（8）

一镜到底（8 秒+）/ 变焦对焦切换（前景↔背景焦点）/ 动作匹配剪 /
镜面反射（镜中倒影）/ 插入镜头（道具/手部/细节）/ 闪剪（心理/联想）/
反应镜头（对白后必有）/ 子弹时间（多机位环绕+冻结）。

### 单元内景别分配模板与单元间衔接 5 法

单元内：首镜 = 远景/全景（建立）或极端特写（冷开场钩子）；中段 = 中景/
中近景主体 + 极端特写/近景情感顶点 + 全景/中远景调度；末镜 = 钩子镜
（Match Cut / 急摇 / 撞切 / 黑屏闪剪）。

单元间 5 法：Match Cut（物件/形状/动作匹配）、J-Cut（下单元声音先入）、
L-Cut（上单元声音延留）、物件回扣（伏笔物再现）、撞切 Smash Cut。

### 参考片样本（`meta.reference_films`）

视听签名、景别、节奏、声音都需要可查的参考片。`meta.reference_films`
为数组，每项含 `title` / `director` / `year` / `usage`（用途：色彩/运镜/
转场/节奏/声音/粒子技法）/ `source`（出处，可选）：

```json
"reference_films": [
  { "title": "深海", "director": "田晓鹏", "year": 2023, "usage": "粒子水墨色彩与质感、深海梦幻光效", "source": "用户指定" },
  { "title": "蜘蛛侠：平行宇宙", "director": "Bob Persichetti", "year": 2018, "usage": "Editorial MG 平面动效、漫画分屏", "source": "用户指定" }
]
```

建议 ≤6 部；build_workflows 校验每项含 title/usage。
## 剪辑节奏统计（可选）

storyboard.md 增加节奏表；可计算项由 build_workflows 校验：

- 全片 ASL = 全片时长 / 总镜数；段 ASL 同理；
- 类型对标基准：短剧 (9:16) 1-2" / 现代商业 2-4" / 迈克尔·贝 1.5-2.5" /
  诺兰 3-4" / 文艺长镜 15-60"；
- 红线：段 ASL 偏离全片均值 >50% 必须诊断；全片 σ <0.3 过平、>1.5 过抖；
- 高潮前应有呼吸段（ASL 拉到全片均值 2× 以上）。

storyboard.md 节奏表模板：

| 段 | 镜头数 | 时长 | ASL | σ | 节奏特征 |
|---|---|---|---|---|---|
| 1 | [N] | [X"] | [X.X"] | [X.X] | [一句话特征] |

## 世界锚点与角色模板（可选）

`meta.world_anchors` 5 个固定 slot（每条带出处，不允许现编）：

- `origin`（起源·时空背景）/ `equipment`（装备·防御机制）/
  `energy`（能源·时间约束）/ `rule`（关键协议·规则）/
  `support`（支援·后援距离）

`characters[]` 模板字段（可选）：

- `function`（功能：工具的灵魂 / 见证者 / 推动者…）
- `visible_shots`（可视镜头清单，引用段号或镜号）
- `dialogue_count`（台词字数；0 字需注明服务什么主题）
- `gender_age`（性别/年龄；剧本未指明时说明服务什么主题）
- 反派额外：`size` / `color_id`（对齐视听签名）/ `sound_signature` /
  `drive`（情绪驱动）/ `appearances`（出场次数）

这些字段写进 `subject_definitions`（身份/色彩/功能）与
`retention_analysis`（出场位置核对）。

## 后端校验项（build_workflows.py）

- 段时长累加与 `meta.total_duration` 偏差 ≤5%；
- `climax_segment` 起始位置位于全片 60-80%；
- `audiovisual_signature`：color_ids ≤6、master_dna ≤3、8 字段齐全；
- `sound_events` ≤12 且每项含 time/event；
- 镜头卡 `shots`：7 列齐全、镜号连续、时长累加 = 段长；
- 节奏统计：段 ASL 偏离全片均值 >50% 诊断、全片 σ 健康区间；
- `world_anchors`：5 slot 齐全且带出处；
- `characters[].visible_shots` 引用存在的段号；
- `reference_films` 每项含 title/usage，且 ≤6 部。
默认只警告；`meta.strict_prompt_validation: true` 时不合格直接拒绝。

## 分镜汇报格式（向用户呈现分镜时强制使用）

汇报剧本时，每个镜头/段落必须包含：**起止时间（几秒到几秒）、画面内容、
对白内容**。禁止“前面是开场、中间打斗、结尾反转”这类宽泛概括。

推荐用时间轴表格：

| 时间 | 画面 | 对白 |
|---|---|---|
| 00:00–00:04 | 金色舰队穿过蓝紫星云，母舰领航，广角缓慢推近 | 无（引擎低鸣 + 星云电磁声） |
| 00:04–00:10 | 切至舰队侧后方平拍，星尘掠过舰体，镜头横移 | 泽兰：「太安静了。」 |

或行式：

```text
00:00–00:04  画面：金色舰队穿过蓝紫星云，母舰领航，广角缓慢推近
             对白：无（引擎低鸣 + 星云电磁声）
00:04–00:10  画面：切至舰队侧后方平拍，星尘掠过舰体，镜头横移
             对白：泽兰：「太安静了。」
```

要求：

- 时间必须连续且精确到秒：首镜头从 00:00 开始，末镜头结束于全片总时长，
  相邻镜头无空洞、无重叠（与镜头卡 `time`/`duration` 一致）。
- hybrid / wenwu 模式直接引用 7 列镜头卡的 `time`、`duration`、`content`、
  `sound` 与台词字段；official 模式按提示词里的 `[Shot N]` 时间码展开。
- 汇报后由用户确认或点名要改的镜头；用户只改个别镜头时，只重新汇报
  被改镜头及其前后衔接，不整片重述。

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

### 模式 C：hybrid（官方六段式 × WenWu 导演深度）（`prompt_mode: hybrid`）

六段顺序、字段名、语言和标签与模式 A 完全一致（英文书写），但每段内容按
WenWu 导演标准写：

- `subject_definitions` = 生命核：锁定角色/场景/道具的身份、色彩系统、平面
  设计语言与素材职责（`<Subject N>` / `<Picture N>`）；
- `summary` = 最终发展线：段内 2-3 镜的完整时间线概要；
- `retention_analysis` = 八条生命通道核对：逐条写每个主体的保留关系
  （fully_preserved / partially_preserved / attribute_transfer / weak_reference）；
- `detailed_description` = 编号镜头脉冲：每个镜头写起止时间、景别机位、
  唯一事件、主体变化、摄影机回应、交镜锚点；人物片加表演肌理（心理目的、
  保护层、呼吸、台词触发、FACS AU），无人片加状态肌理；镜头时间首尾相接，
  总时长精确等于段长；
- `overall_soundscape` = 环境层 + 动作音 + 声桥；
- `non_diegetic_music` = 音乐编排：BPM、乐器、进入/变化/停止时间点；无音乐
  写 N/A；
- 末尾必须追加一行 `constraints:` 风格与负向约束块（例如 pure 2D、no 3D、
  no depth、no realistic lighting、no real casino…）。

完整示例见 [hybrid-example.md](hybrid-example.md)。build_workflows.py 会校验
六段齐全、`[Shot` 时间码与 `constraints:` 块；`meta.strict_prompt_validation:
true` 时不达标直接拒绝。

## 段级生成原则（v1 固定）

- 每段 = 一个 H3 视频，默认 10 秒，段内 2-3 个分镜由提示词驱动，段间用硬切
  接续、换新机位。
- **段内上下镜头之间必须有衔接锚点**（动作方向 / 视线 / 光线 / 道具 / 轮廓 /
  声桥 / 受力）；段间换新机位但同样保留一个跨段锚点，禁止无理由跳切。
- 提示词内禁止「参考上一段尾帧/续拍」，每段独立生成（衔接靠文字锚点，不靠
  画面引用）。
- WenWu 与 hybrid 模式下段内镜头数与单镜时长按「任意秒数密度公式」计算：
  高动态 0.4-1.5s/镜、细腻文戏 2-4s/镜、混合片 1.5-3s/镜；用户指定镜头结构
  时精确遵守。
- 默认无字幕、无 BGM，原生对白直出；如用户要求字幕/BGM，在拼合阶段另行处理。
- 参考图清单与提示词标签的映射必须写进提示词（如 `<Picture 1>` →
  refs/ref_zelan.png）。
