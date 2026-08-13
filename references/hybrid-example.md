# hybrid 模式示例：官方六段式 × WenWu 导演深度

本示例演示同一份导演简报如何写成两段 hybrid 提示词（英文六段式外壳 +
WenWu 内容标准），可直接放入 `prompts/seg_01.txt` 与 `prompts/seg_02.txt`。
原简报为 20 秒，超出 H3 单段 15 秒上限，拆成 2×10s，段间用硬切并在文字
锚点交接（禁止引用上一段尾帧）。

## 用户导演简报（原文要点）

生成一支约 20 秒、16:9 横版、原创都市奇幻 JRPG 游戏宣传 PV。整体采用纯二维
日式赛璐珞动画与抽象 Editorial MG 平面设计风格。全片必须保持纯二维，禁止
任何 3D 效果、立体建模、真实空间纵深、三维透视渲染、CG 质感。

主题为「命运赌场空间」：由扑克、筹码、骰子和规则组成的抽象赌场世界。视觉用
红、白、黑三色高反差：深红/猩红/酒红/纯白/黑色；红色代表赌局、危险、欲望，
白色代表规则和命运，黑色代表未知与压迫。原创角色、原创赌场世界、原创游戏
标题，不出现任何现有游戏角色、Logo 或素材。

音乐为 132BPM 暗调日系 Electro Rock：电子鼓、低沉 Bass、碎拍、冷感钢琴、
机械节奏、洗牌声、筹码碰撞声、骰子滚动声与神秘女声哼唱。开场只有扑克牌划过
桌面的摩擦声、骰子滚动声和筹码落下声，搭配低频脉冲制造紧张感；8 秒后鼓点
进入，节奏逐渐加快，后半段加入快速电子切片和强烈节奏变化，结尾随最后一张牌
翻开的声音突然停止。

人物：女主银白及腰长发、冷艳神秘、黑白赌场制服（黑修身外套/白衬衫/黑长裙），
手持一张扑克牌，二维动画设计，身体由黑色剪影、白色区域和红色轮廓线构成；
反派灰长发、黑礼帽、黑西装、深红领带，以二维剪影坐在赌桌另一侧。

时间线：
- 0-3s：纯黑背景中白色筹码落下，红色圆形扩散，白色概率刻度、扑克花纹和几何
  线条展开；红色扑克牌横向划过并翻转成转场。
- 3-6s：镜头沿扑克牌边缘移动，女主银白长发出现，坐在二维赌桌前手指轻触筹码，
  轮廓在黑色剪影、白色剪影和赛璐珞角色间快速切换，背景逐层拼接。
- 6-9s：展开巨大二维赌场版面，红色筹码图案扩散，黑色斜线切割成漫画式区域，
  骰子以二维图标旋转变化。
- 9-12s：女主抬眼，眼睛特写内部是扑克/筹码/骰子二维图层，脸部被红色网点、
  扫描线、几何切片覆盖；出现 UI 文字 FINAL ROUND / RISK / REWARD /
  ONE LAST CARD；扑克牌覆盖画面完成转场。
- 12-16s：鼓点爆发，快速二维 MG 蒙太奇：翻最后一张牌、筹码快速排列、骰子切换、
  扑克牌纸片旋转飞散、黑色剪影玩家围坐圆桌；全部用二维剪切、遮罩、翻页、图形
  替换完成。
- 16-19s：赌场平面版面快速重组，女主站中央持最后一张牌，反派剪影在另一侧推
  一枚白色筹码，距离靠画面分割表现。
- 19-20s：瞬间切黑，一张扑克牌翻开，红符号出现，元素重组成标题 FINAL BET，
  下方副标题 PLAY YOUR FATE，筹码落桌声结束。

动效只能用：纸片翻转、平面遮罩、斜向切割、圆形扩散、剪影变化、红白黑反相、
几何拆解、MG 图形运动、单帧闪白、二维 Glitch。运镜只能模拟二维平移、缩放、
旋转和平面推拉，禁止任何三维镜头运动。

## seg_01.txt（0-10s）

```text
subject_definitions:
<Subject 1> is the female protagonist: a young woman with waist-length silver-white hair and a cold, mysterious aura, wearing a black-white casino uniform (black tailored jacket, white shirt, black long skirt) and holding a single playing card. Her design is flat 2D cel: large solid color areas, black silhouette, white negative space, red line outlines; no realistic material and no complex texture.
<Subject 2> is the antagonist: a man with gray long hair, a black top hat, a black suit and a deep-red tie, the rule-maker of the casino, who appears as a 2D silhouette - elegant, dangerous, calm.
<Subject 3> is the abstract casino space: a flat graphic world built from playing cards, chips, dice, probability scales, UI frames, geometric color blocks, grids, diagonal lines and abstract symbols, layered like poster design.

summary:
The target video is the opening 10 seconds of a 20-second pure-2D game PV titled "FINAL BET". A white chip falls on black, a red ripple and probability/card graphics expand, a red card sweeps across and flips into the protagonist's introduction at a flat casino table; her eye close-up begins and the UI text "FINAL ROUND" appears at the end.

retention_analysis:
<Subject 1> (appears in [Shot 2], [Shot 3]): fully_preserved - waist-length silver-white hair, black-white uniform, flat cel design and red line outlines stay identical.
<Subject 2> (appears in [Shot 2] as background silhouette): partially_preserved - silhouette only; identity is locked for segment 2.
<Subject 3> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - the flat graphic casino vocabulary (cards, chips, dice, probability scale, UI frames, grids, diagonals) is retained as 2D layers.
No reference assets are used; identity is locked by the design spec above.

detailed_description:
The target video is pure 2D hand-drawn cel animation mixed with flat editorial motion graphics: hard edges, solid color fills, black silhouettes, white negative space, red line outlines; no 3D, no perspective, no depth, no realistic lighting, no CG. Camera moves are only 2D pans, zooms, rotations and planar pushes inside the frame. It contains three clearly separated shots with visible cuts between them. Do not render this as one continuous take.
[Shot 1] 0.0-3.5s. Pure black background; one white round chip drops from the top on a 2D arc. On landing, a red circular ripple expands and white probability-scale marks, playing-card patterns and geometric lines unfold from the center like a poster opening. A red playing card sweeps horizontally across the frame and its face flips like paper, becoming the transition into the next shot. Sound: card friction across a table, dice rolling, one chip landing.
[Shot 2] At 00:03.500, hard cut. A flat 2D pan travels along the red card's edge into <Subject 3>, the abstract casino layout: red table planes, black-white card patterns, circular chip symbols, dice icons, probability scales, UI wireframes and diagonal split lines assembled in layers. <Subject 1> appears seated at the flat table, waist-length silver-white hair built from simple flowing lines, black-white uniform, finger touching a chip; her outline switches between black silhouette, white silhouette and normal cel fill in quick 2D cuts. Background layers of cards and red-white geometry slide behind her. At 00:06.500 the composition expands into a huge flat casino board: multiple tables, chips, dice and cards as graphic symbols; red circular chip motifs spread behind her, black diagonals cut the frame into manga-like panels, and dice icons rotate as 2D symbols, each rotation triggering a new graphic combination.
[Shot 3] At 00:07.000, hard cut to an eye close-up. <Subject 1> lifts her eyes; inside the eyes are 2D animated layers of card textures, chip symbols and dice patterns, not realistic reflections. Red halftone dots, scanlines and geometric slices cover part of her face. At 00:09.000 flat UI text appears and holds: "FINAL ROUND". The camera holds with a slow planar push-in, ending on the card-pattern eye before the hard cut to segment 2.

overall_soundscape:
Card friction across a table surface, dice rolling, chips landing and stacking, one low cloth swish; a low-frequency pulse starts at 0s and builds tension; no human voices.

non_diegetic_music:
132BPM dark Japanese electro rock: from 0-8s only sparse low-frequency pulses and machine-like ticks (no drums); at 8s the drum beat enters with electronic kick, low bass and cold piano accents, accelerating toward the segment end.

constraints:
pure 2D cel + flat editorial MG only; no 3D, no volume modeling, no real-space depth, no 3D perspective, no CG render, no photorealistic casino, no filmic light/shadow, no depth of field, no realistic materials, no cyberpunk city; every element flat, graphic, illustration-like, layered and recombined like a dynamic game poster; all motion is 2D cuts, masks, page flips, diagonal slices, circular ripples, silhouette changes, red-white-black inversion, geometric dismantling, single-frame white flash and 2D glitch.
```

## seg_02.txt（10-20s）

```text
subject_definitions:
<Subject 1> is the female protagonist: a young woman with waist-length silver-white hair and a cold, mysterious aura, wearing a black-white casino uniform (black tailored jacket, white shirt, black long skirt) and holding a single playing card. Her design is flat 2D cel: large solid color areas, black silhouette, white negative space, red line outlines; no realistic material and no complex texture.
<Subject 2> is the antagonist: a man with gray long hair, a black top hat, a black suit and a deep-red tie, the rule-maker of the casino, who appears as a 2D silhouette - elegant, dangerous, calm.
<Subject 3> is the abstract casino space: a flat graphic world built from playing cards, chips, dice, probability scales, UI frames, geometric color blocks, grids, diagonal lines and abstract symbols, layered like poster design.

summary:
The target video is the final 10 seconds (10-20s) of the same pure-2D PV. The eye close-up continues with UI texts "RISK / REWARD" and "ONE LAST CARD"; cards cover the screen, then a fast 2D montage: the protagonist flips the last card, chips and dice rearrange, silhouette players sit around a round table; the casino layout rebuilds, the antagonist pushes one white chip, and the end card forms the title "FINAL BET" with subtitle "PLAY YOUR FATE", ending in a hard stop.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - waist-length silver-white hair, black-white uniform, flat cel design and red line outlines stay identical.
<Subject 2> (appears in [Shot 3]): fully_preserved - gray long hair, black top hat, black suit, deep-red tie and silhouette treatment stay identical.
<Subject 3> (appears in [Shot 2], [Shot 3]): fully_preserved - the flat graphic casino vocabulary is retained as 2D layers.
No reference assets are used; identity is locked by the design spec above.

detailed_description:
The target video keeps the same pure 2D cel + editorial MG style: hard edges, solid colors, black silhouettes, white negative space, red line outlines; no 3D, no perspective, no depth, no realistic lighting, no CG. It contains three clearly separated shots with visible cuts between them. Do not render this as one continuous take.
[Shot 1] 10.0-12.5s. Continue the eye close-up: red halftone dots, scanlines and geometric slices over the face; at 10.5s UI text "RISK / REWARD" appears, then at 11.5s it is replaced by "ONE LAST CARD"; at 12.0s playing cards fly up like paper and cover the whole frame, flipping into the next shot.
[Shot 2] At 00:12.500, hard cut into a fast 2D MG montage: <Subject 1> flips the last card with a page-flip motion; chip symbols snap into rows, dice icons switch rapidly, cards scatter and spin flat like paper; black silhouette players sit around a flat round table. All changes happen through 2D cuts, masks, page flips and graphic substitution - no 3D rotation and no real motion blur. The drum beat bursts in.
[Shot 3] At 00:16.500, hard cut: the whole flat casino layout re-assembles quickly, red-white-black geometric blocks sliding and rotating in-plane; <Subject 1> stands at the center, silver-white hair as simple flowing lines, holding the final card; <Subject 2>, the gray-haired antagonist in a black top hat and deep-red tie, appears as a black silhouette on the opposite side and pushes one white chip across the table; distance is conveyed by screen split, not spatial depth. At 00:19.000 the frame cuts to pure black instantly; a playing card flips open with a red symbol; card, chip, dice and UI elements re-arrange like paper into the title "FINAL BET" with the subtitle "PLAY YOUR FATE" below; a chip lands and the music stops hard on the flip.

overall_soundscape:
Card flips, paper flutter, chips clacking and landing, one sharp table knock; a final chip lands at 19.8s and everything stops.

non_diegetic_music:
132BPM dark Japanese electro rock continuing: drums and low bass from the start, fast electronic slicing and rhythm changes intensify in the montage, cold piano stabs and mechanical patterns; at the final card flip at 19s the music cuts abruptly to silence.

constraints:
pure 2D cel + flat editorial MG only; no 3D, no volume modeling, no real-space depth, no 3D perspective, no CG render, no photorealistic casino, no filmic light/shadow, no depth of field, no realistic materials, no cyberpunk city; every element flat, graphic, illustration-like, layered and recombined like a dynamic game poster; all motion is 2D cuts, masks, page flips, diagonal slices, circular ripples, silhouette changes, red-white-black inversion, geometric dismantling, single-frame white flash and 2D glitch.
```

## 写作检查

- 六段齐全，字段名与顺序固定，英文书写；
- `detailed_description` 逐镜有起止时间、机位、唯一事件、主体变化、摄影机
  回应、交镜锚点，镜头时间首尾相接且总和精确等于段长；
- 每段结尾有 `constraints:` 风格与负向约束块；
- 中文画面文字（UI / 标题）原样保留在引号内，对白（如有）放在 `<d>` 内；
- 20 秒简报拆成 2×10s，段间硬切并在文字锚点交接，不引用上一段尾帧。
