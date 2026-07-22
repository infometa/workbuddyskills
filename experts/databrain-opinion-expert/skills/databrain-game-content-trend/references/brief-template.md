# 输出格式与创意灵感卡规范

> **本文件中的所有模板与示例默认使用 `target_language=zh`（中文）渲染。当 `target_language=en` 时，所有段落标题、字段标签、emoji 注释、创意类型标签（`[社媒-XX]` → `[Social-XX]`、`[端内-XX]` → `[In-game-XX]`）必须按 [language-policy.md](language-policy.md) 第 6 节"段落标题与字段标签对照表"翻译为英文；`both` 模式先输出完整中文版，再用 `═══════════════ English Version ═══════════════` 分隔后输出完整英文版，绝不混排。**
> **示例输入字段（如 `content_zh` / `title_zh`）按 `target_language` 替换为对应语种的字段（`content` / `title`）。**
> **🚨 单语严格规则**：单语模式（`target_language ∈ {zh, en}`）下，任何标签 / 标题 / 字段名 / HTML 元素旁**不得**附加另一种语言的内联翻译（如 `作者Author:`、`📌 Module 1 · Marketing 创意速选 📌 Module 1 · Marketing Creative Shortlist`、`卖点Selling:` 等并排形态均视为缺陷），完整规则与错误/正确样例见 [language-policy.md](language-policy.md) 第 1.5 节。

## 整体报告结构

```
📊 游戏内容趋势情报 · {日期} · {平台} · {地区}
{若指定游戏：🎮 {游戏名称}}

━━ 今日热梗速览（{N}条）━━
{按时效性分区：🆕 新兴 / 🔥 持续热门}
{逐条输出热梗卡片}

━━ 热门视频精选（{N}条）━━
{按时效性分区}
{逐条输出视频卡片}

━━ 不建议跟进 ━━
• {话题/类型}：{原因}（如无则省略此栏）
```

## 单条热梗卡片格式

```
{序号}. {时效标签} 🔥 {梗名称（按 target_language 选 title_zh / title）}
🔗 参考视频：{raw_url}
📍 {region 显示值（按 target_language 选 region_code_zh / region_code）} | 类型：{meme_type 显示值（按 target_language 选 meme_type_zh / meme_type）} | 元素：{meme_elements_zh / meme_elements，按 target_language 选；`meme_elements` 枚举原值如 ACTION_GESTURE 始终保留作为映射键}
💡 为什么在火：{基于梗描述字段（按 target_language 选 content_zh / content）提炼 1-2 句核心传播原因，用 target_language 渲染}
👥 目标受众：{基于 region + meme_type 推断，用 target_language 渲染}

🎮 游戏侧机会：
[社媒-{类型}] {具体创意，直接说怎么和游戏结合}
[社媒-{类型}] {具体创意}
[端内-{类型}] {具体创意}（{风险提示，如有}）
{若有视频交叉} → 📹 与本期视频趋势 #{N} 呼应

🔗 更多参考：{extend_urls 前 2 个链接（如有）}
```

## 单条视频推荐格式

```
{序号}. 【{视频标题}】
🔗 {url}
📍 {platform}-{region} | 📅 {published_at} | {时效标签} | {竞品标注（如有）}
📈 播放 {views} | 24h +{growth_24h}% | 👍 {likes} | 🔄 {shares}
{关联热梗：🔥 #{关联梗名}（如有）}

💡 为什么火：{一句话}
🎯 目标客群：{画像}

🎨 创意方案：
[社媒-{类型}] {具体创意}
[端内-{类型}] {具体创意}
```

## 创意灵感卡格式要求

每条创意建议遵循"先类型，后创意"的格式：

```
[社媒-{子类型}] {具体创意方案，1-2句话}
[端内-{子类型}] {具体创意方案，1-2句话}（⚠️ {风险提示，如有}）
```

**子类型**（社媒）：短视频、表情包、BGM、挑战赛
**子类型**（端内）：动作、皮肤、BGM、活动

**关键原则**：
- **先说适用类型 `[社媒-XX]` / `[端内-XX]`，再说具体创意方案**
- 创意方案用 1-2 句话，只给灵感火花，不给实操细节（不要写"难度：低"、"周期：3天"、"优先级：⭐⭐⭐"）
- 必须和游戏的**具体角色/玩法/世界观**结合，禁止泛泛而谈
- 端内建议必须带风险标注
- 每条热梗提供 `raw_url` 作为原贴参考链接
- 热门核心原因精炼为一句话

---

## 创意灵感卡质量自检

生成创意方案前，逐条检查：

- [ ] 创意是否和游戏的**具体角色/玩法/世界观**结合了，而不是通用套话
- [ ] 是否**先标明了适用类型**（`[社媒-XX]` / `[端内-XX]`）再给方案
- [ ] 社媒创意能不能让内容团队看完**直接上手**，不需要再追问
- [ ] 端内创意是否标注了**风险**（版权/文化/时效）
- [ ] 热梗推荐是否包含了**原帖链接**（`raw_url`）
- [ ] 热梗是否标注了**时效标签**（🆕 新发现 / 🔥 持续热门）
- [ ] 没有出现"借鉴XX风格"这类模糊描述
- [ ] 没有泛泛而谈的模板文案（如"可以结合游戏元素做内容"）

---

## "热梗→游戏创意" 思考链示例

> 示例 1-4 展示 `target_language=zh` 场景，输入字段使用 `_zh` 列，输出全中文。
> 示例 5 展示 `target_language=en` 场景，输入字段使用英文列（`title` / `content` / `meme_type` / `meme_elements` / `region_code`），输出全英文，演示段落标题与创意类型标签如何按对照表翻译。

以下 4 个示例展示从 `meme_elements` 出发，如何推理出具体的落地方向。每个示例包含完整的思考过程，而不只是结论。

### 示例 1：ACTION_GESTURE — 热舞梗

**输入**：
- title_zh: "Tok Tok 舞"
- meme_elements: ACTION_GESTURE
- content_zh: "一段源自韩国的简单舞蹈，特点是双手交替敲击动作配合左右摇摆。动作简单、节奏感强，适合各年龄段参与。配合特定BGM在TikTok上迅速传播。"
- hot_time: 3天前
- region_code_zh: 全球

**思考链**：
1. `ACTION_GESTURE` → 优先看端内 emote 可行性
2. 动作复杂度评估：双手交替敲击 + 左右摇摆 → 动作简单，游戏骨骼可执行，不需要复杂的手指动画
3. 版权风险：源自韩国 → 检查是否有明确编舞师；描述中未提及特定编舞师，属于民间自发传播的简单动作 → 版权风险低
4. 文化风险：无宗教/政治关联，纯娱乐性质 → 安全
5. 时效：3天前爆发，全球传播 → 热度上升期，端内开发周期若2周可赶上
6. 同时评估社媒方向：配合特定BGM → 社媒可以出游戏角色跳舞版本

**输出**：
> [端内-动作] PUBGM 角色跳"Tok Tok 舞" emote，保留双手交替敲击核心动作，配合游戏大厅可触发
> [社媒-短视频] 用游戏角色在不同地图场景（沙漠/雪地/城市）跳 Tok Tok 舞，配原版BGM，结尾弹出"解锁新动作"引导

---

### 示例 2：AUDIO_SIGNATURE — 音频梗

**输入**：
- title_zh: "TINGI LINGI LING"
- meme_elements: AUDIO_SIGNATURE
- content_zh: "一段洗脑电子音效循环，用户在视频中配合这段音效做各种出其不意的转场或反差展示。核心是音效的节奏踩点和视觉反差。"
- hot_time: 5天前
- region_code_zh: 全球

**思考链**：
1. `AUDIO_SIGNATURE` → 优先看端内 BGM/音效 + 社媒 BGM
2. 音频类型：洗脑电子音效循环 → 适合做游戏内击杀音效或大厅等待BGM片段
3. 版权来源：需确认音效原始来源 → 标记版权风险
4. 游戏适配：节奏踩点 + 视觉反差 → 适合做击杀/淘汰时的音效反馈
5. 社媒方向：核心是转场反差 → 做"普通开局 vs 超神操作"转场视频

**输出**：
> [端内-BGM] 将 TINGI LINGI LING 音效片段做成击杀/淘汰提示音效，增强游戏反馈爽感（⚠️ 版权：需确认音效原始版权方及游戏内使用授权范围）
> [社媒-BGM] 做一组"落地捡到平底锅 vs 决赛圈吃鸡"的反差转场视频，配合 TINGI LINGI LING 节奏踩点

---

### 示例 3：VISUAL_IDENTITY — 视觉梗

**输入**：
- title_zh: "Brat Green 风格"
- meme_elements: VISUAL_IDENTITY
- content_zh: "源自Charli XCX专辑封面的荧光绿配黑色像素字体视觉风格。用户将这种配色方案应用到各种场景——自拍滤镜、穿搭、房间装饰。核心是特定的荧光绿色值(#8ACE00)和粗糙字体美学。"
- hot_time: 10天前
- region_code_zh: 欧美

**思考链**：
1. `VISUAL_IDENTITY` → 优先看社媒表情包 + 端内皮肤/喷漆
2. 视觉元素：荧光绿 #8ACE00 + 黑色像素字体 → 高度标志性，易于复制
3. 端内可行性：做成武器皮肤配色方案？→ 但这涉及 Charli XCX 专辑视觉 IP → 侵权风险较高
4. 降级方案：不做皮肤，做成游戏内喷漆/涂鸦 → 用户自定义空间更大，IP 风险更低
5. 社媒方向：做游戏角色的 Brat Green 风格表情包/头像 → 传播力强
6. 时效：已热10天，属于持续热门期 → 社媒可追，端内需谨慎

**输出**：
> [社媒-表情包] 做一组 PUBGM 角色的 Brat Green 风格头像和表情包，荧光绿底 + 游戏梗文案，供玩家做社交头像
> [端内-喷漆] 出一个限时 Brat Green 配色喷漆/涂鸦，玩家可在游戏内喷涂（⚠️ 版权：灵感来源为 Charli XCX 专辑视觉，建议做风格致敬而非直接复制，避免字体和精确色值完全一致）

---

### 示例 4：ABSTRACT_HYBRID — 通用文化热点

**输入**：
- title_zh: "很好但是能再加点吗"
- meme_elements: ABSTRACT_HYBRID
- content_zh: "源自一段综艺片段的'很好但是能再加点吗'口头禅。用户用这个句式展示各种'过度添加'的搞笑场景——给食物不断加料、给照片不断加滤镜、给简历不断加技能。核心是'不断叠加到荒谬'的幽默结构。"
- hot_time: 2天前
- region_code_zh: 中文圈

**思考链**：
1. `ABSTRACT_HYBRID` → 综合评估，不直接映射到单一端内资源
2. 核心结构："不断叠加到荒谬" → 这是叙事结构型梗，更适合社媒内容
3. 端内可行性：做成 emote 或皮肤？→ 这个梗的核心是叙事过程而非单一动作/视觉，端内很难承载 → 放弃端内
4. 社媒方向：用游戏内装备系统做"很好但是能再加点吗"→ 给角色不断叠加装备/配件直到荒谬
5. 时效：2天前爆发 → 新兴热点，立刻做社媒

**输出**：
> [社媒-短视频] 做一个"PUBGM 装备很好但是能再加点吗"视频——角色从裸装开始不断叠加头盔/背包/枪械配件，每加一件喊一句"很好但是能再加点吗"，直到角色被装备淹没

---

### 示例 5（`target_language=en`）：ACTION_GESTURE — Tok Tok Dance

**Demonstrates how `target_language=en` changes the entire output: input fields switch to English columns (`title`/`content`/`meme_type`/`meme_elements`/`region_code`), section headers and creative type tags (`[Social-XX]` / `[In-game-XX]`) follow the bilingual mapping table in [language-policy.md](language-policy.md) Section 6, and there must be no CJK characters in the output (whitelist exceptions only).**

**Input**：
- title: "Tok Tok Dance"
- meme_elements: ACTION_GESTURE
- content: "A simple dance originating from Korea, characterized by alternating hand-tapping movements paired with side-to-side swaying. Simple and rhythmic, suitable for all ages. Spread rapidly on TikTok with a specific BGM."
- hot_time: 3 days ago
- region_code: GLOBAL

**Reasoning chain**：
1. `ACTION_GESTURE` → prioritize in-game emote feasibility
2. Motion complexity: alternating hand-tapping + side-to-side sway → simple enough for game skeleton, no complex finger animation needed
3. IP risk: Korean origin, no specific choreographer mentioned → low IP risk
4. Cultural risk: no religious/political ties, purely entertainment → safe
5. Timing: hot for 3 days, global spread → on the rise; 2-week dev cycle can still ride the wave
6. Social angle: paired with specific BGM → social can release character-dancing version

**Output**：
> [In-game-Emote] PUBGM character performs the Tok Tok Dance emote — preserve the alternating hand-tap as the core motion, triggerable in the lobby
> [Social-Short Video] Use game characters dancing the Tok Tok Dance across different map scenes (desert / snow / city) with the original BGM, ending with a "New emote unlocked" CTA

---

**渲染该示例时的语言一致性自检对照（参考）**：
- [x] `target_language=en` 已在第 1 步确定
- [x] 段落标题（`Output:` / `Reasoning chain:` / `Input:`）、字段标签（`In-game-Emote` / `Social-Short Video`）已按对照表翻译
- [x] 输出中无 CJK 字符
- [x] `meme_elements` 枚举值 `ACTION_GESTURE`、产品名 `PUBGM`、链接（如有）保留原文
- [x] KOL 名 / 编舞师名（如有）保留原文，但描述性内容（如来源说明）翻译为英文

