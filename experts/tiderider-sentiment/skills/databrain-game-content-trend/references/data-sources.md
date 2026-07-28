# 数据源

> **取数前必须先确定 `target_language`**（见 [language-policy.md](language-policy.md) 第 1 节）。下方所有涉及标题/描述等翻译列的 SQL 模板都按 `zh` / `en` / `both` 给出 SELECT 列选取规则；`target_language` 决定取哪一组，**不要在单语模式下把 `_zh` 与 `_en` 都列进 SELECT 子句**，避免渲染时混排。

## 目录

- [Endpoint](#endpoint) — API 地址与认证
- [marketing_hub_video_trending](#主表marketing_hub_video_trending) — 每日热门视频快照（主表）
- [marketing_hub_kol_info](#辅助表marketing_hub_kol_info) — KOL 简介
- [marketing_hub_hashtag_trending_tiktok_gaming](#辅助表marketing_hub_hashtag_trending_tiktok_gaming) — Gaming Hashtag 趋势
- [marketing_hub_hashtag_video](#辅助表marketing_hub_hashtag_video) — Hashtag 下热门视频
- [marketing_hub_video_ai_tags](#辅助表marketing_hub_video_ai_tags) — 视频 AI 标签
- [opinion.memes](#热梗数据源opinionmemes) — 行业热梗/文化趋势

---

## Endpoint

POST `{DATABRAIN_HOST}/api/v1/opinion_pc/global/query`

默认 `DATABRAIN_HOST` 为 `https://databrain.mcp.it.woa.com`。

**Headers:**

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | 是 | `Bearer <DATABRAIN_TOKEN>` |
| `Content-Type` | 是 | `application/json` |

**Request Body:**

```json
{
  "sql": "<BigQuery SQL>"
}
```

**Response:** `Content-Type: text/csv; charset=utf-8`，返回 CSV 格式数据。

**自定义 SQL 兜底：** 当 `scripts/query_trending.py` 的固定函数无法表达用户需求时，根据本文件的表结构和字段说明直接写 BigQuery SQL，并调用 `run_sql_query(sql)` 执行。常见触发场景包括自定义筛选/排序、分组聚合、多表 JOIN、排除账号、粉丝量阈值、互动率计算、按国家或地区拆 Top N。

## API 兼容性

DataBrain Global Query API 对多行 SQL、`WITH`、多表 `JOIN`、窗口函数等复杂 SQL 支持不稳定，常见表现是 HTTP 200 但 body 为空。推荐策略：

- 优先使用单表 `SELECT`。
- 需要关联数据时，分两次查询并在 Python 端合并。
- 通过 `run_sql_query(sql)` 发送 SQL；脚本会在 API 边界把 SQL 压缩为单行。
- 视频查询同时使用 `date_time` 和 `video_release_time`：`date_time` 限制最近快照范围，`video_release_time` 限制视频发布时间。
- 始终显式列字段并加 `LIMIT`，不要使用 `SELECT *`。

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 0 | 成功（返回 CSV） |
| 400 | 参数错误（sql 为空） |
| 500 | 系统异常（数据库连接失败、SQL 执行错误等） |

---

## 主表：`marketing_hub_video_trending`

BigQuery 全路径：`tencent-databrain-prod.marketing_hub.marketing_hub_video_trending`

每日热门视频快照，每天更新，覆盖 TikTok 和 YouTube 双平台。

### 字段与映射

| BigQuery 字段 | 类型 | 映射到 SKILL 字段 | 说明 |
|---------------|------|-------------------|------|
| `date_time` | DATE | — | 数据抓取日期（用于计算 growth_24h） |
| `video_url` | STRING | `url` | 视频链接 |
| `channel_name` | STRING | `platform` | 平台：`tiktok` / `youtube` |
| `video_title` | STRING | `caption` | 原文标题 |
| `video_title_zh` | STRING | `title`（中文） | 中文翻译标题 |
| `video_title_en` | STRING | `title`（英文） | 英文翻译标题 |
| `video_release_time` | STRING | `published_at` | 视频发布时间 |
| `video_duration` | INT64 | — | 视频时长（秒） |
| `anchor_name` | STRING | `author_name` | 作者名称 |
| `anchors_followers` | INT64 | — | 作者粉丝数 |
| `video_cover` | STRING | — | 封面图 URL |
| `tweets_view` | INT64 | `views` | 播放量 |
| `tweets_like` | INT64 | `likes` | 点赞数 |
| `tweets_comment` | INT64 | `comments` | 评论数 |
| `tweets_retweet` | INT64 | `shares` | 转发/分享数 |
| `region` | STRING | `region` | 大区代码（`na`/`eur`/`sea`/`jpn`/`kr`等） |
| `country` | STRING | — | 国家 ISO 码（`us`/`gb`/`jp`等） |
| `category` | STRING | — | 内容类别（`Games`/`Comedy`/`Entertainment`等） |

### 地区代码对照

| 用户说 | region 值 | 典型 country |
|--------|-----------|-------------|
| 美区 / US | `na` | `us` |
| 欧洲 | `eur` | `gb`, `de`, `fr` |
| 东南亚 / SEA | `sea` | `id`, `th`, `ph`, `vn` |
| 日本 / JP | `jpn` | `jp` |
| 韩国 / KR | `kr` | `kr` |
| 南美 | `sa` | `br`, `mx`, `ar` |
| 中东 | `me` | `sa`, `ae` |
| 非洲 | `af` | `ng`, `za` |

### 核心查询：近期热门视频

先按当前筛选条件获取最新可用快照日，避免运行环境时区与数据快照日期不一致：

```sql
SELECT MAX(date_time) AS snapshot_date
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_video_trending`
WHERE 1 = 1
  -- 可按需追加 platform / region / country / category / keyword 过滤
```

再使用该快照日查询近期发布的视频：

```sql
SELECT
  date_time, video_url, channel_name,
  -- ============================================================
  -- 标题字段：按 target_language 三选一，调用时只保留对应那一套
  -- ============================================================
  -- [A] target_language=zh：  video_title_zh,
  --     （video_title 可保留作翻译兜底，不直接渲染）
  -- [B] target_language=en：  video_title_en,
  --     （video_title 可保留作翻译兜底，不直接渲染）
  -- [C] target_language=both: video_title_zh, video_title_en,
  --     （渲染时切分两份；video_title 仅在两个翻译列都缺失时兜底）
  -- ============================================================
  video_title_zh,   -- ← 替换为 [A] / [B] / [C] 对应行
  video_release_time,
  video_duration, anchor_name, anchors_followers, video_cover,
  tweets_view, tweets_like, tweets_comment, tweets_retweet,
  region, country, category
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_video_trending`
WHERE date_time = DATE '<snapshot_date>'
  AND video_release_time >= '<cutoff_date>'
  -- category 过滤：按需添加，不要默认写死
  -- 用户明确要求游戏视频时加：AND category = 'Games'
  -- 搜索舞蹈/音乐/流行趋势等跨类别内容时不加
ORDER BY tweets_view DESC
LIMIT 50
```

> 时间过滤默认 7 天，用户可指定（"最近3天"→ `INTERVAL 3 DAY`，"近两周"→ `INTERVAL 14 DAY`）。`date_time` 使用表内最新可用快照日，不依赖 `CURRENT_DATE()`；`<cutoff_date>` 由该快照日向前计算 N 天，用于过滤 `video_release_time`，确保结果是近 N 天发布的视频，而不是快照里仍在榜的老视频。
> 可按需追加 `AND channel_name = 'tiktok'`（平台过滤）、`AND region = 'na'`（地区过滤）。
> **category 可选值**：`Games`、`Comedy`、`Entertainment`、`Film & Animation`、`Howto & Style`、`Music`、`Nonprofits & Activism`、`Now`、`Other`、`People & Blogs`、`Sports & Outdoor`。不传则搜索全类别。
> 24h 增速由调用方先确定当前候选视频，再查询上一张可用快照中相同 `video_url` 的播放量，在 Python 端计算，不在 SQL 中 self-join。

## 辅助表：`marketing_hub_kol_info`

BigQuery 全路径：`tencent-databrain-prod.marketing_hub.marketing_hub_kol_info`

KOL/作者信息表，用于 Step 2 竞品标注时补充作者简介。

### 字段

| BigQuery 字段 | 类型 | 说明 |
|---------------|------|------|
| `channel_name` | STRING | 平台：`tiktok` / `youtube` |
| `anchor_uid` | INT64 | 作者平台 UID |
| `anchor_sec_uid` | STRING | 作者加密 UID（TikTok） |
| `anchor_url` | STRING | 作者主页链接 |
| `anchor_name` | STRING | 作者名称 |
| `anchor_image` | STRING | 作者头像 URL |
| `description` | STRING | 作者简介，**用于判断是否为游戏官号/KOL** |
| `followers_number` | INT64 | 粉丝数 |
| `posts_number` | INT64 | 发帖数 |
| `likes_number` | INT64 | 总获赞数 |
| `country` | STRING | 国家（可能为 null） |
| `region` | STRING | 大区（可能为 null） |

### 查询 KOL 简介

```sql
SELECT anchor_name, description, followers_number, posts_number, likes_number, country, region, anchor_url, channel_name
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_kol_info`
WHERE anchor_name IN ('name1', 'name2', ...)
```

---

## 辅助表：`marketing_hub_hashtag_trending_tiktok_gaming`

BigQuery 全路径：`tencent-databrain-prod.marketing_hub.marketing_hub_hashtag_trending_tiktok_gaming`

TikTok Gaming 类 Hashtag 趋势，用于 Step 2 匹配与关联。

### 字段

| BigQuery 字段 | 类型 | 说明 |
|---------------|------|------|
| `date` | DATE | 数据日期 |
| `country` | STRING | 国家（`all` 表示全球） |
| `region` | STRING | 大区（`all` 表示全球） |
| `time_range` | STRING | 时间窗口：`last_7_days` / `last_30_days` 等 |
| `hashtag` | STRING | Hashtag 名称（含 `#`） |
| `tweets_views` | INT64 | 窗口内总播放量 |
| `tweets_views_trend` | STRING | 每日播放量趋势（逗号分隔，如 `"1187,405390,924485,..."` ） |
| `order_by_list` | STRING | 排序方式：`by_growth` / `by_views` |

### 查询 Gaming Hashtag 趋势

```sql
SELECT date, country, region, time_range, hashtag, tweets_views, tweets_views_trend
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_hashtag_trending_tiktok_gaming`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
  AND time_range = 'last_7_days'
ORDER BY tweets_views DESC
LIMIT 20
```

---

## 辅助表：`marketing_hub_hashtag_video`

BigQuery 全路径：`tencent-databrain-prod.marketing_hub.marketing_hub_hashtag_video`

特定 Hashtag 下的热门视频明细。

### 字段

| BigQuery 字段 | 类型 | 说明 |
|---------------|------|------|
| `channel_name` | STRING | 平台：`tiktok` |
| `hashtag` | STRING | Hashtag 名称（含 `#`） |
| `video_id` | INT64 | 视频 ID |
| `video_url` | STRING | 视频链接 |
| `video_title` | STRING | 原文标题 |
| `video_title_zh` | STRING | 中文翻译标题 |
| `video_title_en` | STRING | 英文翻译标题 |
| `video_release_time` | STRING | 视频发布时间 |
| `video_image` | STRING | 视频封面 URL |
| `video_duration` | INT64 | 视频时长（秒） |
| `anchor_name` | STRING | 作者名称 |
| `anchor_uid` | INT64 | 作者 UID |
| `anchor_url` | STRING | 作者主页链接 |
| `tweets_view` | INT64 | 播放量 |
| `tweets_like` | INT64 | 点赞数 |
| `tweets_comment` | INT64 | 评论数 |
| `tweets_retweet` | INT64 | 转发/分享数 |

### 查询 Hashtag 下的视频

当需要查看某个特定 hashtag 下的热门视频时：

```sql
-- ============================================================
-- 标题字段：按 target_language 三选一，调用时只保留对应那一套
-- ============================================================
-- [A] target_language=zh：  video_title_zh,
-- [B] target_language=en：  video_title_en,
-- [C] target_language=both: video_title_zh, video_title_en,
-- ============================================================
SELECT hashtag, video_url,
       video_title_zh,   -- ← 替换为 [A] / [B] / [C] 对应行
       anchor_name, anchor_url,
       tweets_view, tweets_like, tweets_comment, tweets_retweet, video_release_time, country, region
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_hashtag_video`
WHERE hashtag = '#gaming'
ORDER BY tweets_view DESC
LIMIT 20
```

---

## 辅助表：`marketing_hub_video_ai_tags`

BigQuery 全路径：`tencent-databrain-prod.marketing_hub.marketing_hub_video_ai_tags`

视频 AI 理解标签表，通过 `video_url` 关联 `marketing_hub_video_trending`，提供视频内容摘要、梗趋势分析和文字提取。在 Step 0 获取热门视频后按需查询，补充视频内容理解（主表只有标题，无内容描述）。

### 字段

| BigQuery 字段 | 类型 | 说明 |
|---------------|------|------|
| `video_url` | STRING | 视频链接（**关联键**，JOIN `marketing_hub_video_trending` 用） |
| `summary` | STRING | AI 生成的视频内容摘要 |
| `meme_trend` | STRING | 梗/趋势分析 |
| `text` | STRING | 视频文字/字幕提取 |
| `language_country` | STRING | 视频语言/地区 |
| `create_time` | DATETIME | 记录创建时间 |
| `insert_time` | TIMESTAMP | 入库时间 |

### 按需查询视频 AI 标签

先从 `video_trending` 拿到精选视频的 `video_url` 列表，再批量查询：

```sql
SELECT video_url, summary, meme_trend, text, language_country
FROM `tencent-databrain-prod.marketing_hub.marketing_hub_video_ai_tags`
WHERE video_url IN ('url1', 'url2', ...)
```

### 通过 AI 标签关键词搜索视频

当用户按内容主题搜索（如"枪战"、"舞蹈"、"跑酷"）时，标题搜索可能遗漏大量相关视频。此查询通过 AI 理解的视频内容（summary/meme_trend/text）匹配关键词，再 JOIN 回 `video_trending` 获取完整数据：

```sql
WITH tag_matches AS (
  SELECT DISTINCT video_url
  FROM `tencent-databrain-prod.marketing_hub.marketing_hub_video_ai_tags`
  WHERE LOWER(summary) LIKE '%关键词%'
     OR LOWER(meme_trend) LIKE '%关键词%'
     OR LOWER(text) LIKE '%关键词%'
),
snapshots AS (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY video_url, country ORDER BY date_time DESC) AS rn
  FROM `tencent-databrain-prod.marketing_hub.marketing_hub_video_trending`
  WHERE date_time >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
)
SELECT
  -- ============================================================
  -- 标题字段：按 target_language 三选一，调用时只保留对应那一套
  -- ============================================================
  -- [A] target_language=zh：  t.video_title_zh,
  -- [B] target_language=en：  t.video_title_en,
  -- [C] target_language=both: t.video_title_zh, t.video_title_en,
  --     （t.video_title 仅在两个翻译列都缺失时作兜底，不直接渲染）
  -- ============================================================
  t.date_time, t.video_url, t.channel_name,
  t.video_title_zh,   -- ← 替换为 [A] / [B] / [C] 对应行
  t.video_release_time, t.video_duration, t.anchor_name,
  t.anchors_followers, t.video_cover, t.tweets_view, t.tweets_like,
  t.tweets_comment, t.tweets_retweet, t.region, t.country, t.category,
  a.summary AS ai_summary, a.meme_trend AS ai_meme_trend
FROM snapshots t
INNER JOIN tag_matches m ON t.video_url = m.video_url
LEFT JOIN `tencent-databrain-prod.marketing_hub.marketing_hub_video_ai_tags` a ON t.video_url = a.video_url
WHERE t.rn = 1
  -- 可按需加 category/platform/region 过滤
  AND SAFE.PARSE_DATE('%Y-%m-%d', LEFT(t.video_release_time, 10))
      >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY t.tweets_view DESC
LIMIT 20
```

> 建议与标题关键词搜索并行执行，两路结果按 `video_url` 去重后合并。AI 标签搜索能发现标题中未提及关键词但视频内容实际相关的结果。

---

## 热梗数据源：`opinion.memes`

BigQuery 全路径：`tencent-databrain-prod.opinion.memes`

行业热梗/文化趋势数据表，持续更新，覆盖 TikTok 平台的全球热梗。用于提供超越视频格式的文化话题灵感，支撑社媒内容创意和端内资源跟进建议。

### 字段与映射

| BigQuery 字段 | 类型 | 说明 |
|---------------|------|------|
| `channels` | STRING | 来源平台（如 `tiktok`） |
| `title` / `title_zh` | STRING | 梗名称（英文/中文） |
| `content` | STRING | 梗的完整英文描述（含参与方式）。`target_language=en` 时作为 AI 创意发散的核心输入 |
| `content_zh` | STRING | 梗的完整中文描述。`target_language=zh` 时作为 AI 创意发散的核心输入；`both` 模式下两个都取 |
| `meme_type` / `meme_type_zh` | STRING | 分类（15种），用于匹配适用场景 |
| `meme_elements` / `meme_elements_zh` | STRING | 核心元素类型，**直接映射端内资源方向** |
| `tags` | STRING | 相关 hashtag |
| `raw_url` | STRING | 示例视频链接（**原贴参考链接**） |
| `raw_title` | STRING | 原帖标题 |
| `raw_cover` | STRING | 原帖封面图 URL |
| `hot_extension` | STRING | 延伸玩法/变体描述 |
| `extend_urls` | STRING | 更多参考链接（逗号分隔多个 URL） |
| `hot_time` | TIMESTAMP | 热度时间（用于时效性判断） |
| `create_time` | TIMESTAMP | 记录创建时间 |
| `region_code` / `region_code_zh` | STRING | 地区（如 `EN`/`英语区`、`GLOBAL`/`全球`） |

### `meme_elements` 到落地方向的映射规则

| meme_elements | 映射到 | 说明 |
|---------------|--------|------|
| ACTION_GESTURE | 端内-动作/表情 | 舞蹈、手势等可做进游戏 emote |
| AUDIO_SIGNATURE | 端内-BGM/音效 + 社媒-BGM | 热门音频 |
| VISUAL_IDENTITY | 端内-皮肤/装扮 + 社媒-表情包 | 视觉梗 |
| NARRATIVE_DRIVEN | 社媒-短视频/剧情 | 叙事结构可改编 |
| TEXT_EXPRESSION | 社媒-表情包/贴纸 | 文字梗 |
| ABSTRACT_HYBRID | 综合评估 | 复合型梗需 case-by-case |

### 时效标签判断逻辑

- `create_time` 近 3 天 → `🆕 新发现`
- `create_time` 超 3 天但 `hot_time` 近 3 天 → `🔥 持续热门`

### 核心查询：近期热梗

```sql
-- ============================================================
-- 多语字段：按 target_language 三选一，调用时只保留对应那一套
-- ============================================================
-- [A] target_language=zh：
--   SELECT channels,
--          title_zh, content_zh, meme_type_zh, meme_elements_zh, region_code_zh,
--          meme_elements,        -- 英文枚举原值（如 ACTION_GESTURE）始终保留作映射键
--          tags, raw_url, raw_title, raw_cover,
--          hot_extension, extend_urls, hot_time, create_time
--
-- [B] target_language=en：
--   SELECT channels,
--          title, content, meme_type, meme_elements, region_code,
--          tags, raw_url, raw_title, raw_cover,
--          hot_extension, extend_urls, hot_time, create_time
--
-- [C] target_language=both（渲染时切分两份）：
--   SELECT channels,
--          title, title_zh, content, content_zh,
--          meme_type, meme_type_zh, meme_elements, meme_elements_zh,
--          region_code, region_code_zh,
--          tags, raw_url, raw_title, raw_cover,
--          hot_extension, extend_urls, hot_time, create_time
-- ============================================================
-- 下方为 [A] zh 版本完整 SQL，调用时替换 SELECT 子句即可：
SELECT channels, title_zh, content_zh, meme_type_zh,
       meme_elements, meme_elements_zh, tags, raw_url, raw_title, raw_cover,
       hot_extension, extend_urls, hot_time, create_time,
       region_code_zh
FROM `tencent-databrain-prod.opinion.memes`
WHERE hot_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
ORDER BY hot_time DESC
LIMIT 30
```

> 可追加过滤：`AND region_code = 'GLOBAL'`（地区）、`AND meme_type = 'Dance & Movement Trends'`（类型）、`AND meme_elements = 'ACTION_GESTURE'`（元素类型）。
> 默认 14 天，用户可通过 `热梗时效` 参数调整。

### 关键词搜索热梗

```sql
-- ============================================================
-- 多语字段：按 target_language 三选一，参考上方"核心查询"模板的注释
-- [A] zh：  title_zh, content_zh, meme_type_zh, meme_elements_zh, region_code_zh, meme_elements
-- [B] en：  title, content, meme_type, meme_elements, region_code
-- [C] both: 两组都取
-- ============================================================
-- 下方为 [A] zh 版本完整 SQL，调用时替换 SELECT 子句即可：
SELECT channels, title_zh, content_zh, meme_type_zh,
       meme_elements, meme_elements_zh, tags, raw_url, raw_title, raw_cover,
       hot_extension, extend_urls, hot_time, create_time,
       region_code_zh
FROM `tencent-databrain-prod.opinion.memes`
WHERE LOWER(title) LIKE '%关键词%'
   OR LOWER(title_zh) LIKE '%关键词%'
   OR LOWER(content_zh) LIKE '%关键词%'
ORDER BY hot_time DESC
LIMIT 10
```

> WHERE 子句中的 `LIKE` 关键词搜索可同时匹配 `title` / `title_zh` / `content_zh`（多语命中），不影响 SELECT 列的语种选择——SELECT 仍按 `target_language` 单语取列。
