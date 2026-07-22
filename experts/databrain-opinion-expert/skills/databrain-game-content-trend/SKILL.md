---
name: databrain-game-content-trend
description: 游戏创意灵感引擎。融合 TikTok/YouTube 热门视频和行业热梗数据，为游戏运营/市场团队提供社媒内容制作灵感和端内资源跟进建议。当用户询问"今日热门"、"游戏内容灵感"、"素材方向"、"官号整活"、"趋势情报"、"热梗"、"热点借势"、"KOL 合作方向"、"端内动作"、"做进游戏"时触发。也应在用户用模糊表达如"最近有什么好玩的"、"竞品在搞什么"、"帮我看看市场热点"、"有没有能跟的趋势"、"内容没灵感了"时触发，即使没有明确提到游戏名称或具体平台。报告语言严格跟随用户 prompt 语言（中文问→中文报告，英文问→英文报告，要求"中英两版"→切分双语），任何混排都视为缺陷。
metadata: {"openclaw": {"requires": {"env": ["TAI_IT_TOKEN"]}}}
---

# 🚨 LANGUAGE POLICY (MUST READ FIRST)

**生成任何用户可见报告之前，必须先确定 `target_language` 并严格遵循。**

判定优先级（命中即停）：

1. 用户显式指令："双语 / 中英两版 / both / bilingual" → `both`；"用英文 / in English" → `en`；"用中文 / Chinese version" → `zh`
2. 用户最新 prompt 自然语言主体：英文 → `en`；中文 → `zh`
3. 默认：`zh`（每日自动推送 cron 触发时同此默认）

硬规则：

- **取数**：`target_language=zh` 仅 SELECT `_zh` 字段（`video_title_zh`、`title_zh`、`content_zh`、`meme_type_zh`、`meme_elements_zh`、`region_code_zh`），`en` 仅 SELECT 英文版列（`video_title_en` 或 `video_title`、`title`、`content`、`meme_type`、`meme_elements`、`region_code`），`both` 两组都取（详细字段映射见 `references/language-policy.md` 第 2 节）。
- **渲染**：报告正文、段落标题（如 `━━ 今日热梗速览 ━━`）、字段标签（如 `💡 为什么在火：` / `💡 Why it's hot:`）、emoji 注释、创意类型标签（`[社媒-短视频]` / `[Social-Short Video]`、`[端内-动作]` / `[In-game-Emote]`）、模板括号说明，全部按 `target_language` 翻译。
- **缺失或异种语言污染**：当目标语言字段为空 / 含异种字符 / 机翻乱码时，由 LLM 强制翻译到 `target_language`，**禁止**保留另一种语言原文。`summary` / `meme_trend` / `text` / `description` 等单语字段必须翻译。
- **白名单**（保留原文不译）：URL、平台代码（tiktok 等）、大区与国家代码（na/eur/sea/us/jp/kr 等）、类别代码（Games/Comedy/Music 等）、`meme_elements` 枚举值（ACTION_GESTURE 等）、`anchor_name` / KOL handle、hashtag 字面、数值指标。其他叙述性内容必须翻译。
- **双语模式**：先完整中文版，再完整英文版，用 `═══════════════ 中文版 / Chinese Version ═══════════════` 与 `═══════════════ English Version ═══════════════` 分隔，**绝不**在同一段落混排。
- **生成前自检**：中文输出不得出现连续 4+ 拉丁字母英文整词（白名单除外）；英文输出不得出现任何 CJK 字符（白名单除外）。
- **【单语严格规则 / Monolingual Strict Rule】** 当 `target_language ∈ {zh, en}` 时，输出中**任何**位置都不得出现另一种语言的内联翻译——包括但不限于章节标题、卡片标题、字段标签、按钮文字、emoji 注释、列表项首词、HTML 中的 `<h1>` / `<h2>` / `<h3>` / `<label>` / `<th>` / `<button>` 等元素文本。错误示例：`作者Author:`、`📌 Module 1 · Marketing 创意速选 📌 Module 1 · Marketing Creative Shortlist`、`为什么入选Why it makes the cut`、`卖点Selling:`。"贴心地补一份翻译方便对方读"在单语模式下是**质量缺陷**，不是加分项。完整错误/正确样例与自检 pattern 见 `references/language-policy.md` 第 1 节末尾与第 8 节。

完整规则、字段映射表、双语段落标题对照表、典型场景示例、自检 checklist → [references/language-policy.md](references/language-policy.md)。

---

# 游戏创意灵感引擎

## 快速开始

收到请求时，按以下流程执行：

1. **埋点上报** → 调用 `python scripts/report_log.py --message "用户原始问题" 2>/dev/null || true`，静默记录本次调用（失败不影响主流程）
2. **确定 `target_language`** → 根据用户显式指令 / prompt 自然语言 / 默认值判定 `zh` / `en` / `both`，详见 [references/language-policy.md](references/language-policy.md) 第 1 节
3. **解析用户意图** → 确定模式（通用 / 指定游戏 / 指定场景：社媒内容制作 or 端内资源跟进）
4. **查询数据** → 通过 BigQuery Global Query API 获取热门视频（路径A）+ 热梗数据（路径B）；**SQL SELECT 子句按 `target_language` 仅取对应语言字段**（详见 language-policy.md 第 2-3 节）
5. **执行分析流水线** → 安全过滤 → 匹配关联 → 创意发散 → 排序输出
6. **生成输出** → 热梗速览 + 热门视频精选 + 创意灵感卡；段落标题、字段标签、创意类型标签按 `target_language` 翻译（对照表见 language-policy.md 第 6 节）
7. **生成前自检** → 对照 language-policy.md 第 8 节 checklist 检查无异种语言残留，再输出
8. **首次使用引导** → 如果是用户首次触发本 Skill，在输出末尾追加「每日自动推送」引导（见下方"每日自动推送"章节）

---

## 输入参数识别

从用户 prompt 中提取以下参数（未提及则使用默认值）：

| 参数 | 默认值 | 示例 |
|------|--------|------|
| 输出语言 `target_language` | `zh`（无显式指令时按 prompt 自然语言判定） | "用英文给我"、"in English"、"中英两版"、"bilingual" |
| 游戏名称 | 无（通用模式） | "PUBGM"、"原神" |
| 使用场景 | 全场景 | "社媒内容制作"、"端内资源跟进"、"官号整活" |
| 平台 | tiktok + youtube | "只看 TikTok" |
| 地区 | 全区 | "美区"、"东南亚"、"日韩" |
| 输出数量 | 3-5 条 | "给我 5 条" |
| 视频时效 | 7天 | "最近3天发布的"、"本周发布的"、"近两周" |
| 热梗时效 | 14天 | "最近一周的热梗"、"近一个月" |
| 模式 | 主动查询 | 定时推送通过 `openclaw cron` 配置，见下方"每日自动推送"章节 |

若用户已配置多游戏追踪，读取 `{baseDir}/games-config.json`。

---

# Configuration

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `TAI_IT_TOKEN` | 是 | — | 太湖认证 token 原始值（**不含** `Bearer ` 前缀），脚本会自动拼接；不要写死在代码中 |
| `DATABRAIN_HOST` | 否 | `https://databrain.mcp.it.woa.com` | API 主机地址；不设置时使用太湖 MCP 域名，显式设置后仅允许受信任域名（`databrain.mcp.it.woa.com`） |

Token 由环境变量或已安装 plugin 根目录 `.env` 自动读取。若为空，引导用户前往 `https://tai.it.woa.com/user/pat` 获取"授权访问应用-全部应用"的 token，设置 `TAI_IT_TOKEN` 即可，不要加 `Bearer` 前缀。

---

# 数据源

通过 BigQuery Global Query API 查询，返回 CSV。使用 6 张表：

| 表 | 用途 |
|----|------|
| `marketing_hub.marketing_hub_video_trending` | 每日热门视频快照，覆盖 TikTok/YouTube（主表） |
| `marketing_hub.marketing_hub_kol_info` | KOL 简介，用于竞品/官号判断 |
| `marketing_hub.marketing_hub_hashtag_trending_tiktok_gaming` | Gaming Hashtag 趋势 |
| `marketing_hub.marketing_hub_hashtag_video` | 特定 Hashtag 下的热门视频 |
| `marketing_hub.marketing_hub_video_ai_tags` | 视频 AI 标签（摘要/梗趋势/文字提取），按需关联 |
| `opinion.memes` | 行业热梗/文化趋势，覆盖 TikTok 全球热梗 |

详细字段说明、地区代码对照与 SQL 查询模板 → [references/data-sources.md](references/data-sources.md)

---

## 分析流水线

双路径获取数据，统一过滤后进行匹配关联和创意发散。

### Step 0：数据获取

并行获取两路数据：

- **路径 A：热门视频** — 查询 `marketing_hub_video_trending`，默认只保留近 7 天发布的视频，按 `tweets_view DESC`
- **路径 B：热梗数据** — 查询 `opinion.memes`，默认近 14 天，按 `hot_time DESC`

#### 查询选择策略

`scripts/query_trending.py` 里的固定函数是常用查询模板，不是唯一查询方式。先判断用户需求能不能被模板参数自然表达：

| 场景 | 查询方式 |
|------|----------|
| 标准热门视频、热梗、hashtag、作者简介、视频 AI 标签补充 | 优先调用固定函数/CLI，不要直接写 SQL |
| 用户要求自定义筛选、排序、分组、时间窗口、排除条件、多表 join、按国家/地区拆 Top N、粉丝量阈值、互动率计算等 | 根据 [references/data-sources.md](references/data-sources.md) 直接写 BigQuery SQL，并调用 `run_sql_query(sql)` |
| 数据库结果不足，或用户明确问"网上有没有/帮我搜一下" | 再启用 Web Search Fallback |

不要为了使用固定函数而改写用户问题。固定函数不合适时，直接写清晰 SQL 更可靠。

**category 过滤策略（重要）**：`marketing_hub_video_trending` 表有 `category` 字段（如 `Games`、`Music`、`Entertainment`、`Comedy` 等）。**不要默认限定 `category = 'Games'`**，应根据用户意图决定：

| 用户意图 | category 处理 |
|---------|--------------|
| 明确说"游戏视频"、"游戏相关" | 加 `--category Games` 过滤 |
| 搜索跨类别内容（"舞蹈动作"、"音乐"、"流行趋势"、"搞笑"等） | **不加** category 过滤，搜索全类别 |
| 通用热门趋势（"今日热门"、"有什么热点"） | **不加** category 过滤 |
| 指定游戏模式但需要借鉴非游戏内容 | **不加** category 过滤，在分析时做关联 |

指定游戏模式下：根据 `games-config.json` 中的 `focus_meme_types` 和 `focus_meme_elements` 过滤热梗数据。

#### Step 0.5：补充视频 AI 标签（按需）

从 Step 0 结果中挑选精选视频（如 Top 5-10），用它们的 `video_url` 批量查询 `marketing_hub_video_ai_tags`，补充 `summary`/`meme_trend`/`text`。若无匹配，回退到基于标题推理。

**当用户按内容主题搜索时**（如"枪战"、"舞蹈"、"跑酷"等），应同时执行两路搜索并合并去重：
1. 标题关键词搜索：`query_trending_videos(keyword="关键词")`
2. AI 标签内容搜索：`query_videos_by_ai_tags(keyword="关键词")`

AI 标签搜索匹配 `marketing_hub_video_ai_tags` 表的 `summary`/`meme_trend`/`text` 字段，能找到标题中未提及关键词但视频内容实际相关的结果。两路结果按 `video_url` 去重后合并排序。

### Step 1：安全过滤

两路数据统一过滤，详细规则见 [references/safety-filter.md](references/safety-filter.md)：
- 争议性事件 / 敏感话题（政治、宗教、种族歧视）
- `growth_24h < 0` 且 `video_release_time` 超过 5 天（热度下降，仅视频）
- 与游戏行业关联度极低且无迁移价值 — **注意**：当用户主动搜索非游戏类别内容（如舞蹈、音乐、流行趋势）时，不应以"游戏关联度低"为由过滤，因为用户的意图就是从非游戏内容中寻找灵感
- 端内资源建议需额外检查端内落地风险（硬过滤 + 软过滤），见 references/safety-filter.md "端内落地风险评估"章节

### Step 2：匹配与关联

- **热梗 × 游戏契合度评估**：基于 `meme_elements` + 梗描述字段（按 `target_language` 选 `content_zh` 或 `content`，`both` 两个都参考），评估热梗与游戏的落地可能性
- **热门视频 × 热梗交叉关联**：通过 `tags`/`title` 关键词匹配，发现视频趋势与热梗的呼应关系
- **竞品标注**（保留原逻辑）：基于 `anchor_name`、`video_title` 判断发帖主体，需额外查询 `marketing_hub_kol_info` 补充 `description`（即作者简介）
  - 若判断为游戏官方账号 → 标注 `⚔️ 竞品已在跟`
  - 若判断为游戏类 KOL → 标注 `👾 游戏达人内容`

### Step 3：创意发散

基于梗描述字段（按 `target_language` 选 `content_zh` 或 `content`） + `hot_extension`，为每条热梗/视频生成创意建议；最终创意文本必须用 `target_language` 渲染：

- **社媒内容方向**：先判断适用子类型（短视频/表情包/BGM/挑战赛），再给 1-2 句创意方案
- **端内资源方向**：先根据 `meme_elements` 映射适用子类型（动作/皮肤/BGM/活动），再给创意方案 + 风险评估

指定游戏模式下：结合游戏的具体角色/玩法/世界观 + `in_game_capabilities` 生成定制创意。

创意发散的详细格式和思考链示例见 [references/brief-template.md](references/brief-template.md)。
场景分析维度见 [references/role-scenarios.md](references/role-scenarios.md)。

### Step 4：排序与输出

- 按时效性分区：`🆕 新兴`（create_time 近 3 天） / `🔥 持续热门`
- 热梗和视频分开输出
- 格式化输出，报告结构、卡片模板与创意规范见 [references/brief-template.md](references/brief-template.md)

---

## Web Search Fallback（数据库无结果时的补充搜索）

当数据库查询返回结果不足时，启用 web search 作为补充数据源：

**触发条件**（满足任一即触发）：
- 数据库查询（标题搜索 + AI 标签搜索）返回结果合计 < 3 条
- 用户的查询关键词非常具体（如特定游戏模式名称"GTA导演模式"、特定功能"枪械改装"等）
- 用户明确要求"帮我搜一下"或"网上有没有"

**搜索策略**：
1. 构造搜索 query，优先搜 TikTok / YouTube 上的相关内容：`site:tiktok.com OR site:youtube.com "{用户关键词}"`
2. 如果限定平台结果不足，扩大搜索范围去掉 `site:` 限制
3. 使用 web search 工具执行搜索

**结果处理**：
- 对搜索结果进行同样的安全过滤流程（Step 1）
- 在输出中明确标注数据来源，区分 `📊 数据库` 和 `🔍 网络搜索`
- 网络搜索结果没有 `growth_24h` 等量化指标，输出时注明"增速数据不可用"
- 创意发散和 Brief 生成流程不变

**输出示例**：

```
━━ 🔍 网络搜索补充（数据库未覆盖）━━
⚠️ 以下结果来自网络搜索，无法提供播放量增速等量化数据

1. 【{视频标题}】
🔗 {url}
📍 来源：{平台}
💡 内容概要：{搜索结果摘要}
🎨 创意方案：{同标准格式}
```

---

## 多游戏追踪模式

若存在 `games-config.json`，为每个游戏独立输出一段分析，格式：

```
═══════════════════════════
🎮 {游戏名称} · {genre}
目标平台：{platforms} | 地区：{regions}
═══════════════════════════
{推荐视频 + Brief，聚焦该游戏的 focus_scenarios}
```

---

## 每日自动推送

当用户首次触发本 Skill 或提到"自动推送"、"定时推送"时，读取 [references/daily-push.md](references/daily-push.md) 获取完整的 cron 配置、渠道投递规则和企业微信注意事项。

---

## 重要原则

- **语言一致性优先级最高**：所有输出（段落标题、字段标签、创意类型标签、叙述性内容）必须严格匹配 `target_language`。详见 [references/language-policy.md](references/language-policy.md)。混排（中文报告夹英文段、英文报告夹中文）视为质量缺陷
- **克制**：宁可少推荐，不输出低相关内容。推 10 条里混 3 条水货，运营会失去信任，下次不用了
- **说人话**：运营拿到推荐后直接转给内容组/美术组执行，如果还得"翻译"一遍 AI 腔，这个 skill 就没省力
- **可操作性优先**：每条推荐必须让内容组看完就知道怎么做。"可以结合游戏元素"这种话等于没说，要给到具体角色/玩法/素材方向
- **安全第一**：有风险疑虑宁可不推。一条翻车内容造成的公关损失远大于错过一个热点的机会成本
- **时效判断**：优先推当日新增且仍在增长的内容。已经满大街的热点，官号再跟只会显得迟钝

---

# Script Usage

## 埋点上报脚本: `scripts/report_log.py`

每次 Skill 被触发时，先调用此脚本记录调用情况。仅依赖标准库，无额外依赖。

```bash
python scripts/report_log.py --message "用户原始问题" 2>/dev/null || true
```

> `query_trending.py` 的 CLI 入口已内置埋点（非阻塞线程），通过 CLI 调用查询时无需额外调用 `report_log.py`。
> 仅当 Skill 未通过 `query_trending.py` CLI 执行查询时（如纯 async 接口调用），需手动调用 `report_log.py`。

## 查询脚本: `scripts/query_trending.py`

依赖：`httpx`

**命令行：**

```bash
# 热门视频（默认只看近7天发布的视频，不限类别）
python scripts/query_trending.py
python scripts/query_trending.py --platform tiktok --region na --limit 20
python scripts/query_trending.py --max-age 3  # 只看近3天发布的视频

# 仅游戏类别视频
python scripts/query_trending.py --category Games

# 跨类别搜索（舞蹈、音乐等非游戏内容）
python scripts/query_trending.py --keyword dance
python scripts/query_trending.py --keyword 舞蹈 --limit 10

# 通过 AI 标签搜索视频（匹配视频内容摘要，而非仅标题）
python scripts/query_trending.py --ai-tag-keyword 枪战
python scripts/query_trending.py --ai-tag-keyword shooting --limit 10

# 热梗查询
python scripts/query_trending.py --memes --limit 10
python scripts/query_trending.py --memes --meme-type "Dance & Movement Trends"
python scripts/query_trending.py --memes --meme-elements ACTION_GESTURE
python scripts/query_trending.py --meme-keyword 舞

# 按增速排序
python scripts/query_trending.py --sort-by growth --limit 10

# 按关键词搜索 Hashtag 趋势
python scripts/query_trending.py --hashtag-trends --hashtag-keyword dance

# 输出 JSON
python scripts/query_trending.py --memes --json
```

**函数使用指南：**

可用函数均为 async，均支持 `token`/`host` 可选参数。它们是常用模板，复杂需求用 `run_sql_query(sql)` 兜底。

- `query_trending_videos(platform, region, country, category, keyword, sort_by, max_video_age_days, limit)`：用于查最近热门视频，`max_video_age_days` 按 `video_release_time` 限制发布时间，并用 `date_time` 限制快照范围；支持基础平台/地区/国家/类别/标题关键词筛选，按播放量或涨幅排序。只有用户需求接近"给我最近热门视频/某地区 Top 视频/标题含某词的视频"时调用；如果要复杂排名、互动率、粉丝阈值、排除账号、分国家 Top N、特殊时间窗口，直接写 SQL。
- `query_videos_by_ai_tags(keyword, platform, region, country, category, max_video_age_days, limit)`：用于按视频内容搜视频，例如标题没写"枪战"但 AI 摘要里提到枪战；回查视频主表时也按 `video_release_time` 限制发布时间。适合主题搜索；如果需要和热梗、作者、互动指标一起复杂分析，直接写 SQL。
- `query_kol_info(anchor_names)`：用于已有作者名后补作者简介，帮助判断官号/游戏 KOL。不要用它做 KOL 排行、模糊找作者、按粉丝量筛选作者；这些需求直接写 SQL 查 `marketing_hub_kol_info`。
- `query_hashtag_trends(region, country, keyword, limit)`：用于查 TikTok gaming hashtag 趋势，适合"最近游戏相关 hashtag 哪些火"。如果用户要非 gaming hashtag、自定义时间段、按国家分组、增长率对比，直接写 SQL。
- `query_hashtag_videos(hashtag, limit)`：用于已知具体 hashtag 时查该 hashtag 下热门视频。多个 hashtag 批量对比、加地区/时间/作者过滤时，直接写 SQL。
- `query_memes(region_code, meme_type, meme_elements, days, limit)`：用于按固定地区、梗类型、梗元素查近期热梗。用户只是要"最近一周热梗/某类热梗"时调用；复杂语义筛选、多字段组合、按热梗元素聚合统计时直接写 SQL。
- `query_memes_by_keyword(keyword, days, limit)`：用于按关键词搜热梗标题和正文，适合"有没有某个词/某个动作相关的热梗"。如果要更细的字段、排序或聚合，直接写 SQL。
- `query_video_ai_tags(video_urls)`：用于已经拿到 `video_url` 后补 AI 摘要、梗趋势、画面文字。它不是搜索入口；想按内容找视频时用 `query_videos_by_ai_tags` 或 raw SQL。
- `run_sql_query(sql)`：raw SQL 兜底入口。只要固定函数表达不了用户需求，就根据 `references/data-sources.md` 写 BigQuery SQL 后调用它。

---

## 补充资源

- 输出语言一致性策略 → [references/language-policy.md](references/language-policy.md)（**每次响应都先读取**：判定 target_language → 取数 → 渲染 → 自检）
- 数据表字段与 SQL 模板 → [references/data-sources.md](references/data-sources.md)（Step 0 构造查询时读取）
- 安全过滤规则 → [references/safety-filter.md](references/safety-filter.md)（Step 1 过滤时读取）
- 场景分析体系 → [references/role-scenarios.md](references/role-scenarios.md)（Step 3 创意发散时读取，尤其用户指定了特定场景）
- 输出格式与创意灵感卡规范 → [references/brief-template.md](references/brief-template.md)（Step 4 格式化输出时读取）
- 每日自动推送 → [references/daily-push.md](references/daily-push.md)（用户提到"自动推送/定时推送"时读取）
- 埋点上报脚本 → [scripts/report_log.py](scripts/report_log.py)（每次 Skill 调用时执行，静默上报）
- 查询脚本 → [scripts/query_trending.py](scripts/query_trending.py)（CLI 入口已内置埋点，无需额外调用）
- 多游戏配置 → [games-config.json](games-config.json)
