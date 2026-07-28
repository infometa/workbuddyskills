# Language Policy（输出语言一致性策略）

本文件是 `databrain-game-content-trend` Skill 的**强制规则**，优先级高于其他 references。生成任何用户可见报告之前，必须先执行第 1 步确定 `target_language`，并在取数与渲染过程中严格遵循后续规则。

---

## 1. 判定 `target_language`（必须最先执行）

按以下优先级判定，命中即停：

```
target_language ←
  if 用户最新 prompt 显式要求"双语 / 中英两版 / both / bilingual"   → both
  elif 用户最新 prompt 显式要求"用英文 / in English / English version" → en
  elif 用户最新 prompt 显式要求"用中文 / 中文版 / Chinese version"     → zh
  elif 用户最新 prompt 自然语言主体为英文                             → en
  elif 用户最新 prompt 自然语言主体为中文                             → zh
  else                                                                → zh（默认）
```

判定一旦确定，整次响应内不得再变化。若用户在后续追问中切换语言，重新执行判定。

每日自动推送 cron 触发本 skill 时，从 `payload.message` 中提取期望语言；若未指定，默认 `zh`。

---

## 1.5 单语严格规则 / Monolingual Strict Rule（最高优先级硬约束）

当 `target_language ∈ {zh, en}` 时，输出中**任何**位置都不得出现另一种语言的内联翻译 —— 包括但不限于章节标题、卡片标题、字段标签、按钮文字、emoji 注释、列表项首词、HTML 中的 `<h1>` / `<h2>` / `<h3>` / `<label>` / `<th>` / `<button>` 等元素文本。

**错误样例**（任一出现即视为缺陷，均直接引自真实报告）：

- `作者Author:` / `Author:作者：`
- `📌 Module 1 · Marketing 创意速选 📌 Module 1 · Marketing Creative Shortlist`
- `压力释放剧情：地铁→办公室 Stress-Relief Drama: Commute → Office`
- `为什么入选Why it makes the cut`
- `卖点Selling:` / `玩法分类Subtype:` / `原帖Source`

**正确样例**：

- 中文报告（`target_language=zh`）：`作者：` / `📌 Module 1 · Marketing 创意速选` / `为什么入选` / `卖点：`
- 英文报告（`target_language=en`）：`Author:` / `📌 Module 1 · Marketing Creative Shortlist` / `Why it makes the cut` / `Selling:`

"贴心地补一份翻译方便对方读" 在单语模式下是**质量缺陷**，不是加分项。仅 `target_language=both` 模式允许两份共存，且必须用 `═══════════════` 分隔符切到独立两段报告，**不得**在同一段落 / 同一行 / 同一标签 / 同一 HTML 元素内并排出现。

---

## 2. 字段映射表（按 `target_language` 取字段）

`marketing_hub_video_trending` / `marketing_hub_hashtag_video` 视频表平行字段：

| 字段语义 | `zh` 取 | `en` 取 | `both` 取 |
|---|---|---|---|
| 视频标题 | `video_title_zh` | `video_title_en` | 两个都取 |
| 原文标题（兜底） | `video_title` | `video_title` | 同上 |

`opinion.memes` 热梗表平行字段：

| 字段语义 | `zh` 取 | `en` 取 | `both` 取 |
|---|---|---|---|
| 梗名称 | `title_zh` | `title` | 两个都取 |
| 梗描述（创意发散核心输入） | `content_zh` | `content` | 两个都取 |
| 梗类型 | `meme_type_zh` | `meme_type` | 两个都取 |
| 核心元素 | `meme_elements_zh` | `meme_elements` | 两个都取 |
| 地区 | `region_code_zh` | `region_code` | 两个都取 |

`marketing_hub_video_ai_tags` 表的 `summary` / `meme_trend` / `text` 是单一字段（无平行翻译版），原文语种由 `language_country` 标识。这类字段视为**叙述性内容**，输出前须由 LLM 转译到 `target_language`。

`marketing_hub_kol_info.description`（KOL 简介）同上：单一字段，原文语种不固定，输出前必须翻译到 `target_language`。

---

## 3. 取数策略

- `target_language=zh`：SQL SELECT 子句仅保留 `_zh` 列（`video_title_zh`、`title_zh`、`content_zh`、`meme_type_zh`、`meme_elements_zh`、`region_code_zh`），不取英文版列；`marketing_hub_video_trending` 中需保留 `video_title` 作为缺失兜底。
- `target_language=en`：SQL SELECT 子句仅保留英文列（`video_title_en` 或 `video_title`、`title`、`content`、`meme_type`、`meme_elements`、`region_code`），不取 `_zh` 列。
- `target_language=both`：两组列都取，渲染时切分两份独立报告。

例外：当目标语言字段为空 / 含明显异种语言字符 / 机翻乱码时，允许补取另一语言列与原文列作为翻译兜底输入，但**最终输出仍必须是 `target_language` 单一语言**。

---

## 4. 缺失或质量差时的处理（强制翻译）

当目标语言字段为空、含异种语言字符、机翻明显错乱时：

1. 由 LLM 翻译到 `target_language` 后渲染，**禁止**保留另一种语言原文。
2. 不要追加"原文：xxx"作为脚注；可追溯性靠链接保证（`raw_url`、`video_url`、`extend_urls`）。
3. 翻译时保留游戏 / 梗 / 品牌的官方译名（如有），不要逐字直译梗的字面意思——优先保留传播效果。例：「Brat Green 风格」译为英文时保留 "Brat Green Style"，不译成 "Naughty Green"。

---

## 5. 白名单（保留原文，不翻译）

下列内容在任何 `target_language` 下都保留原文：

- URL / 链接：`video_url`、`anchor_url`、`raw_url`、`extend_urls`、`video_cover`、`raw_cover`
- 平台代码：`tiktok`、`youtube`、`youtube_keyword`、`instagram`、`bilibili`
- 大区代码：`na`、`eur`、`sea`、`jpn`、`kr`、`sa`、`me`、`af`、`global`、`all`
- 国家 ISO 码：`us`、`gb`、`jp`、`kr`、`fr`、`de`、`br` 等
- 类别代码：`Games`、`Comedy`、`Entertainment`、`Music`、`Howto & Style` 等（直接来源于 `category` 字段值）
- `meme_elements` 枚举原值：`ACTION_GESTURE`、`AUDIO_SIGNATURE`、`VISUAL_IDENTITY`、`NARRATIVE_DRIVEN`、`TEXT_EXPRESSION`、`ABSTRACT_HYBRID`
- `anchor_name` / KOL handle（拉丁字符或平台原生 ID）
- Hashtag 字面文本（`#fyp`、`#dance` 等）——但讨论 hashtag 的描述性文字仍按 `target_language` 渲染
- 数值类指标：播放、点赞、增速百分比

注意：`description`（KOL 简介）、`summary`（视频 AI 摘要）、`meme_trend`（梗趋势分析）、`text`（视频文字提取）是**叙述性内容**，**不在白名单**，必须翻译。

---

## 6. 段落标题与字段标签对照表（双语模板）

| 中文（`zh` 输出） | 英文（`en` 输出） |
|---|---|
| `📊 游戏内容趋势情报` | `📊 Gaming Content Trend Intel` |
| `━━ 今日热梗速览 ━━` | `━━ Today's Meme Pulse ━━` |
| `━━ 热门视频精选 ━━` | `━━ Top Trending Videos ━━` |
| `━━ 不建议跟进 ━━` | `━━ Not Recommended ━━` |
| `🆕 新兴` / `🆕 新发现` | `🆕 New` |
| `🔥 持续热门` | `🔥 Sustained Hot` |
| `🔗 参考视频：` | `🔗 Reference video:` |
| `📍 {region} \| 类型：{type} \| 元素：{elements}` | `📍 {region} \| Type: {type} \| Elements: {elements}` |
| `💡 为什么在火：` | `💡 Why it's hot:` |
| `👥 目标受众：` | `👥 Target audience:` |
| `🎮 游戏侧机会：` | `🎮 In-game opportunities:` |
| `🔗 更多参考：` | `🔗 More references:` |
| `📈 播放 / 24h +X% / 👍 / 🔄` | `📈 Views / 24h +X% / 👍 / 🔄` |
| `🎨 创意方案：` | `🎨 Creative angles:` |
| `🎯 目标客群：` | `🎯 Target segment:` |
| `[社媒-短视频]` / `[社媒-表情包]` / `[社媒-BGM]` / `[社媒-挑战赛]` | `[Social-Short Video]` / `[Social-Memes]` / `[Social-BGM]` / `[Social-Challenge]` |
| `[端内-动作]` / `[端内-皮肤]` / `[端内-BGM]` / `[端内-活动]` / `[端内-喷漆]` | `[In-game-Emote]` / `[In-game-Skin]` / `[In-game-BGM]` / `[In-game-Event]` / `[In-game-Decal]` |
| `⚔️ 竞品已在跟` | `⚔️ Competitor Already On It` |
| `👾 游戏达人内容` | `👾 Gaming KOL Content` |
| `📊 数据库` / `🔍 网络搜索` | `📊 Database` / `🔍 Web Search` |
| `━━ 🔍 网络搜索补充（数据库未覆盖）━━` | `━━ 🔍 Web Search Supplement (Not in Database) ━━` |
| `⚠️ 增速数据不可用` | `⚠️ Growth data unavailable` |
| `→ 📹 与本期视频趋势 #N 呼应` | `→ 📹 Echoes video trend #N` |

`both` 模式下两份各按对照表渲染；不要混用。

---

## 7. 三个典型场景完整示例

### 场景 A：中文 prompt → 全中文输出

用户：「今天 TikTok 全球热门和热梗给我，看看有没有能跟的趋势」

- `target_language=zh`
- 视频查询 SELECT：`video_title_zh`（含 `video_title` 兜底），不取 `video_title_en`
- 热梗查询 SELECT：`title_zh`、`content_zh`、`meme_type_zh`、`meme_elements_zh`、`region_code_zh`，不取英文版列
- 输出段落标题用中文（`━━ 今日热梗速览 ━━` 等）
- KOL 简介、视频 AI 摘要若英文，由 LLM 翻译为中文后渲染
- `meme_elements` 枚举值（`ACTION_GESTURE` 等）保留原值，但旁边的"动作/手势类"用中文描述

### 场景 B：英文 prompt → 全英文输出

用户：「What's trending on TikTok and YouTube today? Any memes worth jumping on for our game?」

- `target_language=en`
- 视频查询 SELECT：`video_title_en`（含 `video_title` 兜底），不取 `video_title_zh`
- 热梗查询 SELECT：`title`、`content`、`meme_type`、`meme_elements`、`region_code`，不取 `_zh` 列
- 输出段落标题用英文（`━━ Today's Meme Pulse ━━` 等）
- KOL 简介、视频 AI 摘要若中文，由 LLM 翻译为英文后渲染
- 不允许出现任何 CJK 字符（白名单除外，本场景白名单不含 CJK）
- 创意建议中类型标签用 `[Social-Short Video]` / `[In-game-Emote]` 等

### 场景 C：双语 prompt → 切分两份

用户：「今天的视频和热梗趋势，给我中英文两个版本」

- `target_language=both`
- 视频查询 SELECT：同时取 `video_title_zh` 和 `video_title_en`
- 热梗查询 SELECT：同时取 `title` / `title_zh`、`content` / `content_zh` 等所有平行列
- 输出顺序：先完整中文版，再完整英文版，用以下分隔符切分：

```
═══════════════ 中文版 / Chinese Version ═══════════════
（完整中文报告，遵循场景 A 规则）

═══════════════ English Version ═══════════════
（完整英文报告，遵循场景 B 规则）
```

- 两份各自内部都通过单语自检，**绝不**在同一段落混排。

---

## 8. 生成前自检 checklist（最后一道防线）

输出之前，LLM 必须自答以下问题；任意一条不通过则回到取数 / 翻译步骤再处理：

- [ ] `target_language` 是否在第 1 步明确确定，且与用户最新 prompt 一致？
- [ ] 段落标题、字段标签、emoji 注释、创意类型标签（`[社媒-XX]` / `[Social-XX]`）是否全部按对照表翻译？
- [ ] `target_language=zh` 输出中：除白名单外，是否避免出现连续 4 个以上拉丁字母构成的英文整词 / 句子？
- [ ] `target_language=en` 输出中：除白名单外，是否完全没有 CJK 字符（`[\u4e00-\u9fff]`）？
- [ ] KOL 简介、视频 AI 摘要（`summary`/`meme_trend`/`text`）等"叙述性内容"是否已转译到 `target_language`，没有保留原文残留？
- [ ] 链接 / `meme_elements` 枚举值 / 平台代码 / 大区代码 / 数值是否未被错误翻译？
- [ ] `target_language=both` 时，两份是否被分隔符明显切分，且各自内部都通过上述自检？
- [ ] `target_language ∈ {zh, en}` 时：通读全文是否还有"中文标签紧跟英文翻译"或"英文标签紧跟中文翻译"形态？典型识别 pattern：
  - 同行内同时出现 `XX：` 与 `YY:` 两个冒号标签
  - 同行内 CJK 词紧贴拉丁词（中间无标点 / 无明显语义切分）
  - HTML 元素文本同时含 CJK + 连续拉丁单词

  发现任一处即视为不合格，必须删除非目标语言部分后重新输出，**不得**以"双语友好"为由保留。

注：自检由 LLM 自行执行，不依赖外部工具。
