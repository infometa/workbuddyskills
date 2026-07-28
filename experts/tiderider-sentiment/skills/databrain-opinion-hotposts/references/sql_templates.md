# SQL 模板（feeds 表 · 每日热帖）

> ⚠️ **EdgeOne 关键字黑名单**（实测整理，与 metrics 一致 + 新坑）
>
> **被拦截（HTTP 566 + HTML 拦截页）**：
> - `IF` / `IFNULL` / `COALESCE` / `CASE WHEN`
> - `OR 1=1` / `IS NULL OR ...`（任何 OR 触发 SQLi 黑名单）
> - `LOWER(channel_name)` 在长 SQL 中（短 SQL 中可能通过，不要依赖）
> - `ARRAY(SELECT ... FROM UNNEST(...) WHERE ... LIMIT)` 子查询
> - `(SELECT ... FROM UNNEST(...) WHERE ... LIMIT)` 标量子查询
>
> **通过**：`GREATEST` / `LEAST` / `COUNTIF` / `SUM` / `AVG` / `COUNT(DISTINCT)`
> / `SAFE_DIVIDE` / `arr[SAFE_OFFSET(N)]` 数组下标 / `UNNEST` 在 FROM 子句
>
> **替代方案速查**：
> - `IF(x<0,0,x)` → `GREATEST(x, 0)`
> - `IFNULL(col, 0)` → 调用方 Python 处理 None
> - `COALESCE(a, b)` → 不可避免时拆 SQL
> - `(col IS NULL OR col = 'x')` → 数据保证非 NULL 时直接 `col = 'x'`；否则拆 SQL
> - `LOWER(col) = 'x'` → 调用方传小写值 + 直接 `col = 'x'`
> - `ARRAY(SELECT s.url FROM UNNEST(arr) s WHERE s.url != '')` → 展开 `arr[SAFE_OFFSET(0..N)].url` 多列，Python 选首个非空
>
> ⚠️ **空 body 陷阱**：SQL 引用不存在的字段 / 表无权限 → API 返回 HTTP 200 + empty body（不是错误）。query_executor 会当作可重试错误抛出。

---

## feeds 表已确认字段

来自 [databrain-opinion-metrics/references/feeds_templates.md](../../databrain-opinion-metrics/references/feeds_templates.md)：

| 字段 | 类型 | 说明 |
|------|------|------|
| `unified_edition_id` | STRING | 游戏 ID（`u` 前缀手游 / `e` 前缀 PC/Console），feeds 表唯一 ID |
| `channel_name` | STRING | 渠道名（实测取值：`reddit` / `twitter` / `youtube` / `tiktok`；其他平台需现场探查） |
| `comment_time` | TIMESTAMP | 帖子发布时间 |
| `comment_parent_id` | STRING | 父帖 ID；`'-1'` 表示主帖（推荐过滤），其他值为评论 |
| `comment_uin` | STRING | 评论者 UID（去重用） |
| `reviewer` | STRING | 用户名（展示用） |
| `follower_number` | INT64 | 粉丝量（可能为负值，用 `GREATEST(x, 0)` 清洗） |
| `tweets_like` / `tweets_reply` / `tweets_retweet` / `tweets_view` | INT64 | 互动量（可能为负，需清洗） |
| `sentiment_rating` | INT64 | 情感打分（4-5 正面 / 3 中性 / 1-2 负面 / -1 未知） |
| `is_recommend` | INT64 | Steam 专用，1 推荐 / 0 不推荐 / -1 未知 |
| `language` | STRING | 语种（en/ja/zh-cn 等） |
| `country` | STRING | ISO-3166-1 alpha-2 小写（fr/de/jp 等），`global` 表示无归属 |
| `media_type` | STRING | 媒体类型（video/live/post/...） |
| `sources` | ARRAY<STRUCT<source, name, url>> | 帖子的外部数据源（含原帖 url） |
| `content` | STRING | ✅ 已实测可用：帖子正文。取数用 `SUBSTR(content, 0, 400)` 拉原料，Python 端再按显示宽度归一（中文≈200字 / 拉丁≈400字符）作 snippet（防标题党 + 喂 AI 摘要） |
| `content_url` | STRING | ✅ 已实测可用：单帖永久链接（渲染 🔗 用，优于 sources 订阅源 url） |

### 文本字段（已实测可用）

`content`（正文）/ `content_url`（单帖永久链接）/ `language` / `country` 均已通过
PUBG Mobile / NIKKE 等实测可平铺 SELECT，不触发网关静默拦截。

- feeds 表 **无独立 `title` 字段**：取数取 `content` 前 400 字符（Python 端按显示宽度归一到
  中文≈200字 / 拉丁≈400字符）作 snippet，「标题」由 agent 从 snippet 提炼（原文不翻译），见 SKILL.md。
- `make_daily_digest.py::_build_top_sql` 已包含这些字段，无需手工拼。
- 注意仍受 EdgeOne 黑名单约束：长 SQL + 大 LIMIT + 复杂 WHERE 组合可能触发；
  当前模板（平铺 SELECT + 单条 WHERE）实测稳定。

---

## 模板：单平台 Top N 热帖（v1 主用）

由 `make_daily_digest.py::_build_top_sql` 自动拼装，无需手工调用。Cheatsheet：

```sql
SELECT
    reviewer,
    comment_time,
    follower_number,
    sentiment_rating,
    content_url,
    language,
    country,
    SUBSTR(content, 0, 400) AS snippet,                  -- 正文原料：Python 端按显示宽度归一（中文≈200字/拉丁≈400字符），作标题来源 + 喂 AI 摘要
    GREATEST(tweets_like,    0)
      + GREATEST(tweets_reply,   0)
      + GREATEST(tweets_retweet, 0)                       AS engagement
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_name = '<channel_name>'                    -- 必须小写；不要用 LOWER() 触发拦截
  AND comment_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL <hours> HOUR)
  AND comment_parent_id = '-1'                           -- 仅主帖（不要 IS NULL OR，触发 SQLi 黑名单）
  AND (
        GREATEST(tweets_like,    0)
      + GREATEST(tweets_reply,   0)
      + GREATEST(tweets_retweet, 0)
      ) >= <min_engagement>                              -- 各平台门槛见 platforms.yaml
ORDER BY engagement DESC
LIMIT <candidate_limit>                                  -- = top_n × 3，留给 agent 去重后补位
```

✅ **已实测稳定**：上述平铺 SELECT（含 `content_url` / `content` / `language` / `country`）
不触发 EdgeOne 拦截。`make_daily_digest.py::_build_top_sql` 即用此模板，无需手工拼。
⚠️ 仍要避开黑名单组合：`ARRAY(SELECT...)` 子查询 + `sources[SAFE_OFFSET].url` + 复杂 WHERE 同时出现会触发拦截。

如调试需要看订阅源 url（非长 SQL 组合），可单独跑：

```sql
SELECT reviewer, sources[SAFE_OFFSET(0)].url AS u0
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_name = '<channel_name>'
  AND comment_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
LIMIT 5
```

### 可选 channel_name 探查

不知道某平台在 feeds 表里到底叫什么？跑：

```sql
SELECT channel_name, COUNT(*) AS cnt
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY channel_name
ORDER BY cnt DESC
```

把结果回填到 `platforms.yaml` 的 `channel_name` 字段。

---

## 模板：整体情感分布（顶部概况用）

```sql
SELECT
    COUNTIF(sentiment_rating IN (4, 5)) AS positive,
    COUNTIF(sentiment_rating = 3)        AS neutral,
    COUNTIF(sentiment_rating IN (1, 2))  AS negative
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL <hours> HOUR)
  AND (comment_parent_id IS NULL OR comment_parent_id = '-1')
```

---

## 备用：手工跑单条 SQL

```bash
python scripts/query_executor.py \
    --sql "SELECT ... FROM ..." \
    --game_id ufc454d9b1af70b40588e2a6fa4da4a8b
```

输出：`{"row_count": N, "rows": [...]}`（CSV 解析后）。
