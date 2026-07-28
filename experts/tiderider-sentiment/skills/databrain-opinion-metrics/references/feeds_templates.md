# SQL Templates — opinion.feeds

> ✅ 本文件所有 SQL 均可通过 `query_metrics.py` 调用 `POST /api/v1/opinion_pc/global/query` 执行。

## 数据源说明

**核心表**：`tencent-databrain-prod.opinion.feeds`

**分区字段**：`comment_time`（按 DAY 分区）  
⚠️ 查询必须在 WHERE 中包含 `comment_time` 范围，否则触发全表扫描，费用极高。

**关键过滤字段**：

| 字段 | 说明 | 常见值 |
|------|------|--------|
| `unified_edition_id` | 游戏唯一标识（必传） | `e...`（PC）/ `u...`（移动） |
| `comment_time` | 内容发布时间，分区字段（必传范围） | `YYYY-MM-DD HH:MM:SS` |
| `channel_type` | 渠道大类 | `social`（社媒）/ `comments`（商店评论）/ `news`（新闻） |
| `channel_name` | 具体渠道 | `twitter`、`youtube`、`reddit`、`tiktok`、`steam`、`googleplay`、`appstore` 等 |
| `sentiment_rating` | 情绪评分 | `5`=正面 / `3`=中性 / `1`=负面；`-1`=未知（排除在占比计算之外） |
| `comment_parent_id` | 父评论 ID；`'-1'` 表示主帖（非回复） | `-1` / 其他 |
| `language` | 语种代码 | `en`、`zh`、`ja`、`ko`、`pt`、`ru`、`de`、`fr`、`es` 等 |
| `is_recommend` | Steam 好评标记 | `1`=好评 / `0`=差评（仅 `channel_name = 'steam'` 有效） |
| `follower_number` | 发帖者粉丝数 | 整数，负值为异常值，使用时需过滤 `> 0` |
| `tweets_like` | 点赞数 | 整数，负值为异常值，使用 `IF(x < 0, 0, x)` 清洗 |
| `tweets_reply` | 回复数 | 同上 |
| `tweets_retweet` | 转发数 | 同上 |
| `tweets_unlike` | 踩数 | 同上 |
| `tweets_view` | 视频观看数 | 同上 |
| `comment_uin` | 发帖用户 ID | 用于统计独立用户数（`COUNT(DISTINCT comment_uin)`） |

---

## 模板目录

| 模板 ID | 指标 | 说明 |
|---------|------|------|
| [volume_daily](#volume_daily) | 日粒度声量 | 每日总条数、独立用户数 |
| [volume_total](#volume_total) | 周期总声量 | 时间范围内汇总 |
| [sentiment_distribution](#sentiment_distribution) | 情绪分布 | 正/中/负及正面率 |
| [volume_by_channel](#volume_by_channel) | 分渠道声量 | 按 `channel_name` 分组 |
| [volume_by_language](#volume_by_language) | 分语种声量 | 按 `language` 分组 |
| [engagement_total](#engagement_total) | 互动量汇总 | 点赞 + 回复 + 转发 |

---

## volume_daily

**指标**：日粒度声量（每天一行）

**说明**：`volume` = 总条数（含同一用户多条）；`mentions` = 独立用户数（去重 `comment_uin`）

```sql
SELECT
    DATE(comment_time)              AS date,
    COUNT(*)                        AS volume,
    COUNT(DISTINCT comment_uin)     AS mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
GROUP BY DATE(comment_time)
ORDER BY date
```

---

## volume_total

**指标**：时间范围内总声量（单行汇总）

```sql
SELECT
    COUNT(*)                    AS volume,
    COUNT(DISTINCT comment_uin) AS mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## sentiment_distribution

**指标**：情绪正/中/负分布及正面率

**说明**：`sentiment_rating` 值域：`5`=正面，`3`=中性，`1`=负面（实测仅出现 1/3/5 三值）；`-1`=未知，不计入占比

```sql
SELECT
    COUNT(*)                                        AS total,
    COUNTIF(sentiment_rating = 5)                  AS positive,
    COUNTIF(sentiment_rating = 3)                  AS neutral,
    COUNTIF(sentiment_rating = 1)                  AS negative,
    SAFE_DIVIDE(
        COUNTIF(sentiment_rating = 5),
        COUNTIF(sentiment_rating IN (1, 3, 5))
    )                                               AS positive_ratio
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## volume_by_channel

**指标**：按渠道分组的声量

```sql
SELECT
    channel_name,
    COUNT(*)                    AS volume,
    COUNT(DISTINCT comment_uin) AS mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
GROUP BY channel_name
ORDER BY volume DESC
```

---

## volume_by_language

**指标**：按语种分组的声量及占比

```sql
WITH total AS (
    SELECT COUNT(*) AS cnt
    FROM `tencent-databrain-prod.opinion.feeds`
    WHERE unified_edition_id = '<game_id>'
      AND comment_time >= '<start_date> 00:00:00'
      AND comment_time <= '<end_date> 23:59:59'
)
SELECT
    language,
    COUNT(*)                         AS volume,
    SAFE_DIVIDE(COUNT(*), total.cnt) AS volume_ratio
FROM `tencent-databrain-prod.opinion.feeds`
CROSS JOIN total
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
GROUP BY language, total.cnt
ORDER BY volume DESC
```

---

## engagement_total

**指标**：互动量汇总（点赞 + 回复 + 转发）

**说明**：负值数据为异常值，使用 `IF(x < 0, 0, x)` 清洗；适用于社媒渠道（商店评论无此指标）

```sql
SELECT
    SUM(
        IF(tweets_like     < 0, 0, tweets_like)
      + IF(tweets_reply    < 0, 0, tweets_reply)
      + IF(tweets_retweet  < 0, 0, tweets_retweet)
    )                                               AS total_engagement,
    SUM(IF(tweets_like    < 0, 0, tweets_like))    AS total_likes,
    SUM(IF(tweets_reply   < 0, 0, tweets_reply))   AS total_replies,
    SUM(IF(tweets_retweet < 0, 0, tweets_retweet)) AS total_retweets
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

<!-- 追加新模板格式：

## <template_id>

**指标**：<一句话描述>
**说明**：<字段含义、注意事项>

```sql
SELECT ...
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
...
```
-->
