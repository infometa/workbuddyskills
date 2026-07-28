# Mentions & Sentiment 指标

**核心表**：`tencent-databrain-prod.opinion.feeds`

**分区字段**：`comment_time`（按 DAY 分区）  
⚠️ 查询必须在 WHERE 中包含 `comment_time` 范围，否则触发全表扫描，费用极高。

**关键字段速查**：

| 字段 | 说明 |
|------|------|
| `unified_edition_id` | 游戏唯一标识（必传，`e...` = PC，`u...` = 移动） |
| `comment_time` | 内容发布时间，分区字段（必传范围） |
| `channel_type` | 渠道大类：`social`（社媒）/ `comments`（商店评论）/ `news`（新闻） |
| `sentiment_rating` | 情绪值：`5`=正面，`3`=中性，`1`=负面，`-1`=未知；实测仅出现 1/3/5 三值 |
| `comment_uin` | 发帖用户 ID，用于 `COUNT(DISTINCT comment_uin)` 统计独立用户数 |
| `md5_uin` | 用户 ID 哈希，Brand Health 中用于去重 |

**默认口径**：Mentions 类指标默认覆盖 social + comments，如需单独过滤见各指标说明

## 快速判断：你现在想查什么？

- 想查总声量 → 见"1. Mentions | 声量"
- 想查声量日环比 → 见"2. Mentions DoD"
- 想查正/中/负分布及占比 → 见"3-8. 情绪分布"
- 想查品牌健康度 → 见"9. Brand Health"
- 想查情感分 → 见"11. Sentiment"
- 想查互动/曝光/发帖/创作者/观看量 → 见"13-17"（social 渠道专用）

---

## 1. Mentions | 声量

**渠道**：social + comments（全量）  
**说明**：统计所有内容条数（含重复用户）

```sql
SELECT COUNT(comment_uin) AS mentions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 2. Mentions DoD | 声量日环比

**说明**：对比目标日期（`<target_date>`）与前一天的声量变化，`<target_date>` 格式 `YYYY-MM-DD`

```sql
SELECT
  COUNTIF(DATE(comment_time) = '<target_date>')                            AS mentions,
  COUNTIF(DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY))  AS mentions_old,
  SAFE_DIVIDE(
    COUNTIF(DATE(comment_time) = '<target_date>')
    - COUNTIF(DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)),
    COUNTIF(DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY))
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 3-8. 情绪分布（Positive / Neutral / Negative Mentions 及占比）

**说明**：
- `sentiment_rating` 4-5 = 正面，3 = 中性，1-2 = 负面，-1 = 未知（排除在占比计算之外）
- 以下 SQL 同时返回正/中/负绝对数和占比，无需分别查询

```sql
SELECT
  COUNT(comment_uin)                                                   AS total_mentions,
  COUNT(CASE WHEN sentiment_rating IN (4,5) THEN comment_uin END)      AS positive_mentions,
  COUNT(CASE WHEN sentiment_rating = 3     THEN comment_uin END)       AS neutral_mentions,
  COUNT(CASE WHEN sentiment_rating IN (1,2) THEN comment_uin END)      AS negative_mentions,
  SAFE_DIVIDE(
    COUNT(CASE WHEN sentiment_rating IN (4,5) THEN comment_uin END),
    COUNT(comment_uin)
  ) * 100                                                              AS positive_pct,
  SAFE_DIVIDE(
    COUNT(CASE WHEN sentiment_rating = 3 THEN comment_uin END),
    COUNT(comment_uin)
  ) * 100                                                              AS neutral_pct,
  SAFE_DIVIDE(
    COUNT(CASE WHEN sentiment_rating IN (1,2) THEN comment_uin END),
    COUNT(comment_uin)
  ) * 100                                                              AS negative_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 9. Brand Health | 品牌健康度

**说明**：加权综合 social 和 store 渠道的正负情绪，范围 -100 ~ 100，样本 ≤ 10 时返回 -99999  
**权重 w** = social 总声量 / store 总声量  
**公式**：`(pos_social - neg_social + w*pos_store - w*neg_store) / (pos_social + neg_social + w*pos_store + w*neg_store) * 100`

```sql
WITH base AS (
  SELECT
    COUNTIF(channel_type = 'social'   AND sentiment_rating IN (4,5)) AS pos_social,
    COUNTIF(channel_type = 'social'   AND sentiment_rating IN (1,2)) AS neg_social,
    COUNTIF(channel_type = 'comments' AND sentiment_rating IN (4,5)) AS pos_store,
    COUNTIF(channel_type = 'comments' AND sentiment_rating IN (1,2)) AS neg_store,
    COUNT(CASE WHEN channel_type = 'social'   THEN 1 END)            AS vol_social,
    COUNT(CASE WHEN channel_type = 'comments' THEN 1 END)            AS vol_store
  FROM `tencent-databrain-prod.opinion.feeds`
  WHERE unified_edition_id = '<game_id>'
    AND comment_time >= '<start_date> 00:00:00'
    AND comment_time <= '<end_date> 23:59:59'
)
SELECT
  CASE
    WHEN (pos_social + neg_social + pos_store + neg_store) <= 10 THEN -99999
    ELSE SAFE_DIVIDE(
      (pos_social - neg_social)
        + SAFE_DIVIDE(vol_social, NULLIF(vol_store, 0)) * (pos_store - neg_store),
      (pos_social + neg_social)
        + SAFE_DIVIDE(vol_social, NULLIF(vol_store, 0)) * (pos_store + neg_store)
    ) * 100
  END AS brand_health
FROM base
```

---

## 10. Brand Health DoD | 品牌健康度日环比

**说明**：对比两天的 Brand Health，需执行两次上方 SQL（分别传 `<target_date>` 和前一天）后在外部计算环比

> ⚠️ Brand Health 计算复杂，Agent 建议分两次查询，然后前端/外部计算：  
> `dod_pct = (brand_health - brand_health_old) / ABS(brand_health_old) * 100`

---

## 11. Sentiment | 情感分

**说明**：情感分均值，范围 0 ~ 5，仅统计有效情绪（排除 -1）

```sql
SELECT AVG(sentiment_rating) AS avg_sentiment
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
  AND sentiment_rating BETWEEN 1 AND 5
```

---

## 12. Sentiment DoD | 情感分日环比

```sql
SELECT
  AVG(CASE WHEN DATE(comment_time) = '<target_date>'
           AND sentiment_rating BETWEEN 1 AND 5
      THEN CAST(sentiment_rating AS FLOAT64) END)                     AS avg_sentiment,
  AVG(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
           AND sentiment_rating BETWEEN 1 AND 5
      THEN CAST(sentiment_rating AS FLOAT64) END)                     AS avg_sentiment_old,
  SAFE_DIVIDE(
    AVG(CASE WHEN DATE(comment_time) = '<target_date>'
             AND sentiment_rating BETWEEN 1 AND 5
        THEN CAST(sentiment_rating AS FLOAT64) END)
    - AVG(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
               AND sentiment_rating BETWEEN 1 AND 5
           THEN CAST(sentiment_rating AS FLOAT64) END),
    AVG(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
             AND sentiment_rating BETWEEN 1 AND 5
        THEN CAST(sentiment_rating AS FLOAT64) END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 13. Engagement | 互动量

**渠道**：social（`channel_type = 'social'`）  
**说明**：点赞 + 回复 + 转发 + 踩；负值按 0 处理

```sql
SELECT
  SUM(
    IF(tweets_retweet < 0, 0, tweets_retweet)
    + IF(tweets_reply  < 0, 0, tweets_reply)
    + IF(tweets_like   < 0, 0, tweets_like)
    + IF(tweets_unlike < 0, 0, tweets_unlike)
  ) AS total_engagement
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 14. Impressions | 潜在曝光量

**渠道**：social  
**说明**：累加发帖者粉丝数，仅统计粉丝数 > 0 的记录

```sql
SELECT SUM(IF(follower_number > 0, follower_number, 0)) AS total_impressions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 15. Publications | 发帖量

**渠道**：social  
**说明**：仅统计主帖（`comment_parent_id = '-1'`），不含回复

```sql
SELECT
  COUNT(DISTINCT CASE
    WHEN comment_parent_id = '-1' AND channel_type = 'social'
    THEN comment_uin
  END) AS publications
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 16. Creators | 发帖人数

**渠道**：social  
**说明**：主帖作者去重，以 `reviewer + channel_name` 组合作为唯一标识（同一人在不同渠道视为不同创作者）

```sql
SELECT
  COUNT(DISTINCT CASE
    WHEN comment_parent_id = '-1' AND channel_type = 'social'
    THEN CONCAT(reviewer, '-', LOWER(channel_name))
  END) AS creators
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 17. Views | 观看量

**渠道**：social  
**说明**：视频观看数累加，负值按 0 处理

```sql
SELECT SUM(IF(tweets_view < 0, 0, tweets_view)) AS total_views
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```
