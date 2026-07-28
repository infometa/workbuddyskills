# SQL 模板：舆情告警取数

所有查询通过 `POST /api/v1/opinion_pc/global/query` 执行，返回 CSV。
表：`tencent-databrain-prod.opinion.feeds`（分区字段 `comment_time`，查询时必须带日期范围）。

---

## 1. 评分告警（Rating Alert）

### 1.1 计算区间好评率

```sql
SELECT
  COUNT(CASE WHEN is_recommend = 1 THEN 1 END) AS positive_count,
  COUNT(CASE WHEN is_recommend = 0 THEN 1 END) AS negative_count,
  COUNT(*) AS total_count,
  ROUND(
    COUNT(CASE WHEN is_recommend = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) AS positive_rate
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_name = 'steam'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

**字段说明**：
- `sentiment_rating`：4-5 = 正面，3 = 中性，1-2 = 负面
- `positive_rate`：好评率 %，与 `--threshold` 比较

### 1.2 按日趋势（用于阈值计算及告警详情）

```sql
SELECT
  DATE(comment_time) AS date,
  COUNT(CASE WHEN is_recommend = 1 THEN 1 END) AS positive_count,
  COUNT(*) AS total_count,
  ROUND(
    COUNT(CASE WHEN is_recommend = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
    2
  ) AS positive_rate
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_name = 'steam'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
GROUP BY date
ORDER BY date
```

---

## 2. KOL 热帖告警（KOL Alert）

### 2.1 查询高互动帖子

```sql
SELECT
  content,
  author,
  channel_name,
  source_url,
  IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet) AS engagement,
  IF(tweets_like<0,0,tweets_like) AS likes,
  sentiment_rating,
  DATE(comment_time) AS date
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND (IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet)) >= <min_engagement>
ORDER BY engagement DESC
LIMIT 20
```

**负面过滤版（`--kol_sentiment_filter` 开启时使用）**：

```sql
SELECT
  content,
  author,
  channel_name,
  source_url,
  IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet) AS engagement,
  IF(tweets_like<0,0,tweets_like) AS likes,
  sentiment_rating,
  DATE(comment_time) AS date
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND (IF(tweets_like<0,0,tweets_like)+IF(tweets_reply<0,0,tweets_reply)+IF(tweets_retweet<0,0,tweets_retweet)) >= <min_engagement>
  AND sentiment_rating IN (1, 2)
ORDER BY engagement DESC
LIMIT 20
```

### 2.2 近 N 天 engagement 分布（阈值计算用）

```sql
SELECT
  DATE(comment_time) AS date,
  APPROX_QUANTILES(engagement, 100)[OFFSET(90)] AS p90_engagement,
  APPROX_QUANTILES(engagement, 100)[OFFSET(95)] AS p95_engagement,
  MAX(engagement) AS max_engagement,
  AVG(engagement) AS avg_engagement
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<lookback_start> 00:00:00'
  AND comment_time <= '<lookback_end> 23:59:59'
GROUP BY date
ORDER BY date
```

---

## 3. 关键词告警（Keyword Alert）

### 3.1 当前窗口关键词匹配

```sql
SELECT
  COUNT(*) AS mentions,
  COUNT(CASE WHEN CAST(sentiment_rating AS STRING) IN ('1', '2') THEN 1 END) AS negative_mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP('<window_end>') - INTERVAL <window_hours> HOUR
  AND comment_time <= TIMESTAMP('<window_end>')
  AND (
    EXISTS (
      SELECT 1 FROM UNNEST(<keyword_array>) kw
      WHERE EXISTS (SELECT 1 FROM UNNEST(keywords) k WHERE LOWER(k.value) = kw)
         OR STRPOS(LOWER(CONCAT(IFNULL(content_to_zh, ''), ' ', IFNULL(content, ''))), kw) > 0
    )
  )
```

> `<keyword_array>` 示例：`['az3', 'p2w']`（脚本自动拼接）。关键词告警 v2 同时使用 NLP `keywords` 字段和正文模糊匹配，避免版本热词未入库时漏检。

### 3.2 代表高互动帖

```sql
SELECT
  channel_name,
  language,
  sentiment_rating,
  SUBSTR(COALESCE(NULLIF(content_to_zh, ''), NULLIF(content, ''), ''), 1, 240) AS snippet,
  GREATEST(IFNULL(tweets_like, 0), 0)
    + GREATEST(IFNULL(tweets_reply, 0), 0)
    + GREATEST(IFNULL(tweets_retweet, 0), 0) AS engagement
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP('<window_end>') - INTERVAL <window_hours> HOUR
  AND comment_time <= TIMESTAMP('<window_end>')
  AND (<same keyword OR content condition>)
ORDER BY engagement DESC, comment_time DESC
LIMIT 20
```

Python 侧基于当前窗口和前 7 天基准计算三类触发维度：提及量激增、负面占比、单帖爆款。

---

## 字段快查

| 字段 | 类型 | 说明 |
|------|------|------|
| `unified_edition_id` | STRING | 游戏 ID（e/u 开头） |
| `comment_time` | TIMESTAMP | 评论时间（分区字段，必须带范围） |
| `channel_type` | STRING | 渠道大类（`social` / `comments` / `news`） |
| `channel_name` | STRING | 具体渠道（`steam` / `twitter` / `reddit` / `youtube` 等） |
| `sentiment_rating` | INT64 | 1-2=负面，3=中性，4-5=正面（全渠道情绪字段） |
| `is_recommend` | INT64 | Steam 专用好评标记：`1`=好评 / `0`=差评（仅 `channel_name='steam'` 有效） |
| `tweets_like` | INT64 | 点赞数（负值为异常，计算时用 `IF(tweets_like<0,0,tweets_like)`） |
| `tweets_reply` | INT64 | 回复数 |
| `tweets_retweet` | INT64 | 转发数 |
| `engagement`（计算字段） | — | `tweets_like + tweets_reply + tweets_retweet`（无直接字段，需手动计算） |
| `keywords` | REPEATED STRUCT | 关键词列表；子字段 `value`（词）、`type`、`en`、`cn` |
| `content` | STRING | 评论正文 |
| `content_to_zh` | STRING | 翻译到中文的正文，关键词模糊匹配优先使用 |
| `author` | STRING | 作者 |
| `source_url` | STRING | 原文链接 |
