# Memes 热梗查数手册

> ⚠️ **项目说明**：本文档 SQL 使用 `tencent-databrain.opinion.memes` 和 `tencent-databrain.opinion.meme_videos`（非 prod 项目）。  
> 如果 `tencent-databrain-prod` 中存在同名表，优先使用 prod 版本，请在使用前确认。

## 这份文档适合谁

这份文档适合两类人：

- 不看接口实现、但需要查数、写报告、解释榜单的业务或分析同学
- 需要快速回忆 `Memes` 相关接口大致逻辑的后端维护者

这组接口能回答的问题，本质上都围绕两张表展开：

- `tencent-databrain.opinion.memes`：热梗主档 / 元信息
- `tencent-databrain.opinion.meme_videos`：热梗对应的视频事实表

你可以用它查：当前时间窗口内哪些 meme 最热、单个 meme 的聚合详情、趋势图、语言分布、视频明细、以及当前实现下的 KOL 聚合结果。

---

## 快速判断：你现在想查什么？

- 想看当前时间范围里哪些 meme 最热 → 看“场景 1：想看热梗榜单，怎么查？”
- 想下钻某个 meme 的基础信息、聚合指标、Top4 视频 → 看“场景 2：想看单个 meme 详情，怎么查？”
- 想看某个 meme 在一段时间内的播放量 / 发帖量趋势 → 看“场景 3：想看趋势图，怎么查？”
- 想看某个 meme 在不同语言下的分布 → 看“场景 4：想看语言分布，怎么查？”
- 想看某个 meme 的具体视频明细，或者只看某个作者的视频 → 看“场景 5：想看视频明细，怎么查？”
- 想看某个 meme 涉及了哪些 KOL / 作者 → 看“场景 6：想看 KOL 聚合，怎么查？”
- 想解释为什么结果和直觉不一致 → 先看“查询前先判断”和最后的“常见误区”

---

## 你可以查什么数据

| 想回答什么问题 | 关键条件 | 表 | 备注 |
|---|---|---|---|
| 当前最热的 meme 是哪些 | `start_time/end_time` + 可选 `channels/meme_types/meme_elements/regions` | `tencent-databrain.opinion.memes` + `tencent-databrain.opinion.meme_videos` | 列表是“主档 + 视频聚合”拼出来的 |
| 某个 meme 的完整详情 | `meme_title` 精确匹配 | 同上 | 详情页会额外补 Top4 related videos |
| 某个 meme 的趋势图 | `meme_title` + 时间窗口 + 可选 `languages` | `tencent-databrain.opinion.meme_videos` | 输出是 `views + publications` 双轴 |
| 某个 meme 的语言分布 | `meme_title` + 时间窗口 + 可选 `languages` | `tencent-databrain.opinion.meme_videos` | 分别返回按 `views` / 按 `videos` 的 Top5 |
| 某个 meme 的视频列表 | `meme_title` + 时间窗口 + 可选 `languages/anchor_uid` | `tencent-databrain.opinion.meme_videos` | 明细级视频数据 |
| 某个 meme 的 KOL 列表 | `meme_title` + 时间窗口 + 可选 `search_text` | `tencent-databrain.opinion.meme_videos` | 当前是基于视频表按 `author_url` 聚合的临时实现 |

---

## 查询前先判断

- 先分清你要的是 **meme 主档信息**，还是 **视频事实数据**
  - `memes` 表放标题、内容、类型、元素、region、tags 等主档字段
  - `meme_videos` 表放 views、likes、comments、shares、language、author、release_time 等视频事实
- `memes/list` 不是只查一张表，而是 **先按视频表聚合，再跟主档表 JOIN**
- `search_text` 只搜 `title/title_zh`，**不搜 tags**
- `total_views` / `total_likes` 是 **聚合后的 meme 级范围筛选**，而且支持多区间 **OR**
- `min_release_time` / `max_release_time` 不是当前时间窗口内的最早最晚视频，而是 **去掉时间条件后重新算的全量时间范围**
- `should_include_timeline=true` 只会给 **当前页的 meme** 补趋势，不会给全量结果补
- 详情、趋势、语言分布、视频列表、KOL 列表这 5 个接口，都依赖 `meme_title` **精确匹配**
- 这组接口目前 **没有 hashtag list 那种 latest date 兜底逻辑**；查不到就是当前条件下没有结果
- 代码里 `channels` / `languages` 传空数组，或包含 `99999`，都会视为“不筛选”

---

## 按场景怎么查

### 场景 1：想看热梗榜单，怎么查？

#### 适合什么场景：
- 想看某一段时间内，哪些 meme 最热
- 想按播放量、点赞量、首次出现时间、类型、元素等维度排序
- 想做“本周最热视频梗”“某 region 最近最热 meme”这类榜单

#### 你会拿它回答什么问题：
- 最近这几天最热的 meme 是哪些？
- 指定渠道 / region / meme_type 下，最值得解释的热梗有哪些？
- 某一类热梗是靠播放量高，还是靠点赞高？

#### 查哪张表：
- 主档：`tencent-databrain.opinion.memes`
- 聚合来源：`tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- 视频层时间字段用的是 `release_time`
- `channels` 作用在 `meme_videos.channel`
- `meme_types` / `meme_elements` / `regions` / `search_text` 作用在 `memes` 主档
- `total_views` / `total_likes` 是聚合后筛选，不是视频明细筛选
- 默认 `stat_type=views`，默认 `sort_item=stat_type`，默认 `sort_model=desc`
- 可排序字段对应关系：
  - `views` → `total_views`
  - `likes` → `total_likes`
  - `first_seen` → `min_release_time`
  - `meme_type` / `meme_type_zh`
  - `meme_elements` / `meme_elements_zh`
  - `first_channel`

```sql
WITH meme_stats AS (
  SELECT
    meme_title,
    SUM(views) AS total_views,
    SUM(likes) AS total_likes,
    SUM(comments) AS total_comments,
    SUM(shares) AS total_shares,
    COUNT(DISTINCT url) AS video_count
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE release_time >= '2026-03-20 00:00:00'
    AND release_time <= '2026-03-26 23:59:59'
    AND LOWER(channel) IN ('tiktok')
  GROUP BY meme_title
),
meme_time_range AS (
  SELECT
    meme_title,
    MIN(release_time) AS min_release_time,
    MAX(release_time) AS max_release_time
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE LOWER(channel) IN ('tiktok')
  GROUP BY meme_title
),
meme_details AS (
  SELECT *
  FROM `tencent-databrain.opinion.memes`
  WHERE LOWER(region_code) IN ('global')
    AND LOWER(meme_type) IN ('pop music trends')
    AND (LOWER(title) LIKE '%sorry%' OR LOWER(title_zh) LIKE '%sorry%')
),
main_data AS (
  SELECT
    m.title AS meme_id,
    m.title,
    m.title_zh,
    m.content,
    m.content_zh,
    ARRAY_TO_STRING(m.channels, ',') AS channels,
    m.channels[SAFE_OFFSET(0)] AS first_channel,
    m.region_code,
    m.region_code_zh,
    m.meme_type,
    m.meme_type_zh,
    m.meme_elements,
    m.meme_elements_zh,
    ARRAY_TO_STRING(
      ARRAY(
        SELECT TRIM(tag)
        FROM UNNEST(SPLIT(ARRAY_TO_STRING(m.tags, '\n'), '\n')) AS tag
        WHERE TRIM(tag) != '' AND TRIM(tag) != 'NaN'
      ),
      ','
    ) AS tags,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', m.hot_time) AS hot_time,
    ms.total_views,
    ms.total_likes,
    ms.total_comments,
    ms.total_shares,
    ms.video_count,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', mtr.min_release_time) AS min_release_time,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', mtr.max_release_time) AS max_release_time
  FROM meme_details m
  LEFT JOIN meme_stats ms ON m.title = ms.meme_title
  LEFT JOIN meme_time_range mtr ON m.title = mtr.meme_title
)
SELECT *
FROM main_data
WHERE (
    (total_views >= 1000000 AND total_views <= 10000000)
    OR (total_views >= 50000000)
  )
  AND ((total_likes >= 100000))
ORDER BY total_views DESC
LIMIT 20 OFFSET 0;
```

#### 查数注意点：
- `search_text` **只查 `title/title_zh`**，不会命中 `tags`
- `total_views` / `total_likes` 是在 `GROUP BY meme_title` 之后再筛，所以和直接扫视频明细不是一回事
- `min_release_time` / `max_release_time` 会去掉时间过滤后重算，因此常常早于 / 晚于你的查询窗口
- `tags` 在底层做过一次清洗：不是直接 `UNNEST(m.tags)`，而是先 `ARRAY_TO_STRING -> SPLIT('\n') -> UNNEST`
- 如果 `should_include_timeline=true`，后端还会额外给当前页 meme 补 `video_stats_timelines`，并带上一段环比时间窗口 `link_time`

#### 简短后端逻辑小结：
- 入口是 `memes.List`
- 先分别构建 `meme_videos` 过滤、去时间版 `meme_videos` 过滤、`memes` 过滤、聚合后过滤
- `GetMemesTotalCount` 先查总数，`GetMemesMainData` 再查当前页主数据
- `should_include_timeline=true` 时，只拿当前页的 `meme_title` 去补当前窗口和上一窗口的趋势
- `old_total / old_timeline` 来自 `utils.GetLinkTime(...)` 算出的上一段对比时间

### 场景 2：想看单个 meme 详情，怎么查？

#### 适合什么场景：
- 已经知道具体 meme 名称，想看它的详情卡片
- 想看该 meme 的总播放、总点赞、视频数、最热视频示例

#### 你会拿它回答什么问题：
- 这个 meme 是什么梗？
- 这个梗当前累计有多少视频、多少播放？
- 当前窗口里最能代表它的几个视频是哪几个？

#### 查哪张表：
- 主档：`tencent-databrain.opinion.memes`
- 事实：`tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- `meme_title` 是精确匹配，不是模糊搜索
- 详情主体其实复用了列表那套“主档 + 聚合”逻辑，只是固定取 1 条
- `related_videos` 是同条件下按 `views DESC` 取 Top4

```sql
-- 详情主体：主档 + 聚合统计
WITH meme_stats AS (
  SELECT
    meme_title,
    SUM(views) AS total_views,
    SUM(likes) AS total_likes,
    SUM(comments) AS total_comments,
    SUM(shares) AS total_shares,
    COUNT(DISTINCT url) AS video_count
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE meme_title = 'Fastest 67 Challenge'
    AND release_time >= '2026-02-01 00:00:00'
    AND release_time <= '2026-02-15 23:59:59'
    AND LOWER(channel) IN ('tiktok')
  GROUP BY meme_title
),
meme_time_range AS (
  SELECT
    meme_title,
    MIN(release_time) AS min_release_time,
    MAX(release_time) AS max_release_time
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE meme_title = 'Fastest 67 Challenge'
    AND LOWER(channel) IN ('tiktok')
  GROUP BY meme_title
)
SELECT
  m.title,
  m.title_zh,
  m.content,
  m.content_zh,
  ms.total_views,
  ms.total_likes,
  ms.total_comments,
  ms.total_shares,
  ms.video_count,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', mtr.min_release_time) AS min_release_time,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', mtr.max_release_time) AS max_release_time
FROM `tencent-databrain.opinion.memes` m
LEFT JOIN meme_stats ms ON m.title = ms.meme_title
LEFT JOIN meme_time_range mtr ON m.title = mtr.meme_title
WHERE m.title = 'Fastest 67 Challenge'
LIMIT 1;

-- related videos Top4
SELECT
  url,
  title,
  cover,
  views,
  author_name
FROM `tencent-databrain.opinion.meme_videos`
WHERE meme_title = 'Fastest 67 Challenge'
  AND release_time >= '2026-02-01 00:00:00'
  AND release_time <= '2026-02-15 23:59:59'
  AND LOWER(channel) IN ('tiktok')
ORDER BY views DESC
LIMIT 4;
```

#### 查数注意点：
- `meme_title` 必须对得上主档里的 `title`
- `why_hot` / `why_hot_zh` 目前是后端写死的占位内容，**不是底表真实字段**
- `related_videos` 的 Top4 是在当前时间窗口内取的；但 `min_release_time/max_release_time` 是去掉时间条件后重算的
- 如果 detail 主数据为空，后端会直接按“meme 不存在 / 无结果”处理

#### 简短后端逻辑小结：
- 入口是 `memes.Detail`
- 主信息直接复用 `GetMemesMainData(..., 1, 1)`
- 同时并发查 `GetMemeRelatedVideos(..., 4)`
- `memes` 表筛选不是复用 `search_text`，而是直接 `title = ?`
- `why_hot/why_hot_zh` 暂时是硬编码占位，后面等表字段补齐再替换

### 场景 3：想看趋势图，怎么查？

#### 适合什么场景：
- 想看某个 meme 在一段时间内的热度走势
- 想同时看播放量变化和发帖量变化
- 想做日报 / 周报里的趋势图说明

#### 你会拿它回答什么问题：
- 这个 meme 是哪几天突然爆发的？
- 播放量涨的时候，发布量有没有同步放大？
- 某个语言或某个渠道下，趋势有没有不同？

#### 查哪张表：
- `tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- 过滤条件来自：`meme_title + 时间窗口 + channels + languages`
- 聚合时间粒度取决于 `date_type`（`daily/weekly/monthly/...`）
- 输出两个值：
  - `views` = 该粒度下的 `SUM(views)`
  - `publications` = 该粒度下的 `COUNT(DISTINCT url)`

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d 00:00:00', release_time) AS time,
  SUM(views) AS views,
  COUNT(DISTINCT url) AS publications
FROM `tencent-databrain.opinion.meme_videos`
WHERE meme_title = 'Fastest 67 Challenge'
  AND release_time >= '2026-02-01 00:00:00'
  AND release_time <= '2026-02-15 23:59:59'
  AND LOWER(channel) IN ('tiktok')
  AND LOWER(language) IN ('en', 'es')
GROUP BY time
ORDER BY time;
```

#### 查数注意点：
- 趋势不是按 meme 主档查，而是纯视频表聚合
- `languages` 会直接参与过滤，所以你传了语言后，看到的是“指定语言子集”的趋势，不是全量趋势
- 后端会先调用 `GetTimeOfLineStartTime(...)` 对齐时间线；因此返回里的 `timeline_of_start_time` 可能早于你请求里的 `start_time`
- 这里的 `publications` 是 `COUNT(DISTINCT url)`，不是视频总行数，也不是账号数

#### 简短后端逻辑小结：
- 入口是 `memes.Trend`
- 默认 `date_type=daily`
- 先用 `GetTimeOfLineStartTime(...)` 把时间线起点对齐，再用 `GetDateSqlStr(...)` 生成时间粒度 SQL
- 最后由 `GetMemeDetailTrend` 从 `meme_videos` 聚合出 `views + publications`

### 场景 4：想看语言分布，怎么查？

#### 适合什么场景：
- 想知道一个 meme 主要在哪些语言里传播
- 想区分“哪个语言播放量高”和“哪个语言视频数多”

#### 你会拿它回答什么问题：
- 这个 meme 是英语区更火，还是多语言扩散更明显？
- 某个语言虽然视频不多，但单视频播放是否特别高？

#### 查哪张表：
- `tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- 过滤条件同样来自：`meme_title + 时间窗口 + channels + languages`
- 后端会并发跑两套 Top5：
  - 按 `SUM(views)` 排序
  - 按 `COUNT(DISTINCT url)` 排序

```sql
-- 按 views 排的 Top5 语言
WITH lang_stats AS (
  SELECT
    language,
    SUM(views) AS total_views,
    COUNT(DISTINCT url) AS video_count
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE meme_title = 'Fastest 67 Challenge'
    AND release_time >= '2026-02-01 00:00:00'
    AND release_time <= '2026-02-15 23:59:59'
    AND LOWER(channel) IN ('tiktok')
  GROUP BY language
)
SELECT language, total_views, video_count
FROM lang_stats
WHERE language IS NOT NULL AND language != ''
ORDER BY total_views DESC
LIMIT 5;

-- 按 videos 排的 Top5 语言
WITH lang_stats AS (
  SELECT
    language,
    SUM(views) AS total_views,
    COUNT(DISTINCT url) AS video_count
  FROM `tencent-databrain.opinion.meme_videos`
  WHERE meme_title = 'Fastest 67 Challenge'
    AND release_time >= '2026-02-01 00:00:00'
    AND release_time <= '2026-02-15 23:59:59'
    AND LOWER(channel) IN ('tiktok')
  GROUP BY language
)
SELECT language, total_views, video_count
FROM lang_stats
WHERE language IS NOT NULL AND language != ''
ORDER BY video_count DESC
LIMIT 5;
```

#### 查数注意点：
- 返回的 `percentage` 分母不是全量语言总和，而是 **当前 Top5 结果本身的合计**
- 也就是说，如果长尾语言很多，前端看到的占比加起来会是 100%，但那是 Top5 内部的 100%
- 如果你传了 `languages` 过滤，返回的是“过滤后的语言集合里再做 Top5”，不是全量语言盘子

#### 简短后端逻辑小结：
- 入口是 `memes.LanguageDistribution`
- 复用 detail 场景那套 `meme_videos` filter
- 并发调用 `GetMemeLanguageDist(..., "views", 5)` 和 `GetMemeLanguageDist(..., "videos", 5)`
- `percentage` 在 Go 层用查询结果再计算，所以分母就是返回结果里的 Top5 合计

### 场景 5：想看视频明细，怎么查？

#### 适合什么场景：
- 想拉出某个 meme 的所有视频明细
- 想只看某种语言、某个渠道、某个作者的相关视频
- 想检查“这个梗到底是哪条视频带起来的”

#### 你会拿它回答什么问题：
- 这个 meme 在当前窗口里有哪些具体视频？
- 哪些视频播放最高 / 点赞最高 / 发布时间最新？
- 某个 KOL 在这个 meme 下发过哪些视频？

#### 查哪张表：
- `tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- 基础过滤：`meme_title + 时间窗口 + channels + languages`
- 额外过滤：`anchor_uid` 实际落到 `author_url = ?`
- 可排序字段白名单：`views / likes / comments / shares / release_time`
- 默认 `page=1`、`page_size=20`，最大 `100`

```sql
SELECT
  url,
  title,
  title_zh,
  cover,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', release_time) AS release_time,
  language,
  channel,
  author_name,
  author_url,
  author_avatar,
  views,
  likes,
  comments,
  shares
FROM `tencent-databrain.opinion.meme_videos`
WHERE meme_title = 'Fastest 67 Challenge'
  AND release_time >= '2026-02-01 00:00:00'
  AND release_time <= '2026-02-15 23:59:59'
  AND LOWER(channel) IN ('tiktok')
  AND LOWER(language) IN ('en')
  AND author_url = 'https://www.tiktok.com/@example_author'
ORDER BY views DESC
LIMIT 20 OFFSET 0;
```

#### 查数注意点：
- `anchor_uid` 名字看起来像 UID，但实现里实际比对的是 `author_url`
- 如果你是从 KOL 列表点进来查视频，最好直接复用 KOL 返回的 `author_url`
- `title/title_zh` 是视频标题，不是 meme 标题
- 分页上限是 100，想一次全拉要自己翻页

#### 简短后端逻辑小结：
- 入口是 `memes.VideoList`
- 先用通用 filter 拼出 `meme_videos` 条件，再额外补 `author_url = ?`
- 并发跑 `GetMemeVideoTotal` 和 `GetMemeVideoList`
- 排序字段有白名单保护，非法值会回退到默认 `views`

### 场景 6：想看 KOL 聚合，怎么查？

#### 适合什么场景：
- 想看某个 meme 主要是哪些作者在发
- 想快速枚举参与这个梗的账号，并按发文数排序

#### 你会拿它回答什么问题：
- 当前时间窗口里，哪些作者发这个 meme 最多？
- 我想从作者维度往下钻视频，应该先拿什么字段？

#### 查哪张表：
- 当前实现只查：`tencent-databrain.opinion.meme_videos`

#### 查的时候抓住：
- 过滤条件来自：`meme_title + 时间窗口 + channels`
- 额外搜索：`search_text` 会模糊匹配 `author_name` 或 `author_url`
- 只统计 `author_url` 非空的记录
- 当前唯一有效排序字段：`video_count`

```sql
SELECT
  author_url,
  MAX(author_name) AS author_name,
  MAX(author_avatar) AS author_avatar,
  COUNT(DISTINCT url) AS video_count
FROM `tencent-databrain.opinion.meme_videos`
WHERE meme_title = 'Fastest 67 Challenge'
  AND release_time >= '2026-02-01 00:00:00'
  AND release_time <= '2026-02-15 23:59:59'
  AND LOWER(channel) IN ('tiktok')
  AND author_url IS NOT NULL
  AND author_url != ''
  AND (
    LOWER(author_name) LIKE '%example%'
    OR LOWER(author_url) LIKE '%example%'
  )
GROUP BY author_url
ORDER BY video_count DESC
LIMIT 20 OFFSET 0;
```

#### 查数注意点：
- 这不是独立的 KOL 主档表结果，而是 **基于视频表临时聚合** 的结果
- `followers_count` 当前固定返回 `0`，不能拿来做分析
- `author_name` / `author_avatar` 也是从视频表里 `MAX(...)` 取的，不是权威 KOL 档案
- 如果后续接入 `meme_kol` 表，这个口径会变

#### 简短后端逻辑小结：
- 入口是 `memes.KolList`
- 复用 detail 场景下的视频过滤条件，再额外拼 KOL 搜索条件
- 并发跑 `GetMemeKolTotal` 和 `GetMemeKolList`
- 当前底层是 `GROUP BY author_url`，`FollowersCount` 在 Go 层直接写成 `0`
- 代码里已经留了 TODO：后续改成 JOIN 真正的 KOL 表

---

## 常见误区：这些地方最容易查错

- `search_text` 不是“全字段搜索”，它只搜 `memes.title` 和 `memes.title_zh`
- 列表页的 `total_views` / `total_likes` 不是视频级字段，而是 `meme_videos` 聚合到 `meme_title` 后的结果
- `min_release_time` / `max_release_time` 不是当前查询窗口内的时间边界，而是去掉时间条件后重算出的全量范围
- `should_include_timeline=true` 不是给全量结果补趋势，而是只给当前页的 meme 补趋势
- 详情页的 `why_hot` / `why_hot_zh` 目前是占位文本，不能当成真实数据字段解释
- 语言分布里的 `percentage` 分母是 Top5 结果内部合计，不是全量语言盘子
- `video_list.anchor_uid` 实际匹配的是 `author_url`
- `kol_list` 当前不是正式 KOL 模型，只是视频表聚合，所以 `followers_count=0`
- 这组接口没有“查空后返回最近有数据日期”的兜底逻辑；如果要解释空结果，只能回到你的筛选条件逐项排查
