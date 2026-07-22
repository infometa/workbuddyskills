# Community 指标

> **主要数据表**：`tencent-databrain-prod.opinion.feeds`  
> **分区字段**：`comment_time`（按 DAY 分区）⚠️ 查询必须带时间范围  
> **渠道**：`channel_type = 'social'`（除特殊说明外）

## 快速判断：你现在想查什么？

- 想查全网曝光量 → 见"1. Potential Impressions"
- 想查发帖量/发帖人数/观看量/互动量 → 见"3, 5, 7, 9"
- 想查环比变化 → 见各指标对应的 DoD 部分
- 想查直播相关数据（Hours Watched / CCV）→ 见"13-15"（⚠️ 表名待确认）
- 想查官号内容 / 玩家内容占比 → 见"16-17"

---

## 1. Potential Impressions | 全网潜在曝光量

**说明**：累加发帖者粉丝数，负值按 0 处理

```sql
SELECT SUM(IF(follower_number > 0, follower_number, 0)) AS potential_impressions
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 2. Impressions DoD | 曝光量日环比

```sql
SELECT
  SUM(CASE WHEN DATE(comment_time) = '<target_date>'
      THEN IF(follower_number > 0, follower_number, 0) END)            AS impressions,
  SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      THEN IF(follower_number > 0, follower_number, 0) END)            AS impressions_old,
  SAFE_DIVIDE(
    SUM(CASE WHEN DATE(comment_time) = '<target_date>'
        THEN IF(follower_number > 0, follower_number, 0) END)
    - SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
          THEN IF(follower_number > 0, follower_number, 0) END),
    SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
        THEN IF(follower_number > 0, follower_number, 0) END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 3. Publications | 发帖量

**说明**：仅统计主帖（`comment_parent_id = '-1'`），不含评论/回复

> ⚠️ 原始口径还包含直播数据（`t_opinion_streaming`），但该表的 BigQuery 路径待确认，当前 SQL 仅覆盖 `opinion.feeds` 部分。

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

## 4. Publications DoD | 发帖量日环比

```sql
SELECT
  COUNT(DISTINCT CASE
    WHEN DATE(comment_time) = '<target_date>'
      AND comment_parent_id = '-1' AND channel_type = 'social'
    THEN comment_uin END)                                              AS publications,
  COUNT(DISTINCT CASE
    WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      AND comment_parent_id = '-1' AND channel_type = 'social'
    THEN comment_uin END)                                              AS publications_old,
  SAFE_DIVIDE(
    COUNT(DISTINCT CASE WHEN DATE(comment_time) = '<target_date>'
      AND comment_parent_id = '-1' AND channel_type = 'social' THEN comment_uin END)
    - COUNT(DISTINCT CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      AND comment_parent_id = '-1' AND channel_type = 'social' THEN comment_uin END),
    COUNT(DISTINCT CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      AND comment_parent_id = '-1' AND channel_type = 'social' THEN comment_uin END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 5. Creators | 全网发帖人数

**说明**：主帖作者去重，`reviewer + channel_name` 组合为唯一标识

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

## 6. Creators DoD | 发帖人数日环比

```sql
SELECT
  COUNT(DISTINCT CASE WHEN DATE(comment_time) = '<target_date>'
    AND comment_parent_id = '-1' AND channel_type = 'social'
    THEN CONCAT(reviewer, '-', LOWER(channel_name)) END)              AS creators,
  COUNT(DISTINCT CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
    AND comment_parent_id = '-1' AND channel_type = 'social'
    THEN CONCAT(reviewer, '-', LOWER(channel_name)) END)              AS creators_old,
  SAFE_DIVIDE(
    COUNT(DISTINCT CASE WHEN DATE(comment_time) = '<target_date>'
      AND comment_parent_id = '-1' AND channel_type = 'social'
      THEN CONCAT(reviewer, '-', LOWER(channel_name)) END)
    - COUNT(DISTINCT CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      AND comment_parent_id = '-1' AND channel_type = 'social'
      THEN CONCAT(reviewer, '-', LOWER(channel_name)) END),
    COUNT(DISTINCT CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      AND comment_parent_id = '-1' AND channel_type = 'social'
      THEN CONCAT(reviewer, '-', LOWER(channel_name)) END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 7. Views | 观看量

**说明**：视频观看数，负值按 0 处理

```sql
SELECT SUM(IF(tweets_view < 0, 0, tweets_view)) AS total_views
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 8. Views DoD | 观看量日环比

```sql
SELECT
  SUM(CASE WHEN DATE(comment_time) = '<target_date>'
      THEN IF(tweets_view < 0, 0, tweets_view) END)                   AS views,
  SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
      THEN IF(tweets_view < 0, 0, tweets_view) END)                   AS views_old,
  SAFE_DIVIDE(
    SUM(CASE WHEN DATE(comment_time) = '<target_date>'
        THEN IF(tweets_view < 0, 0, tweets_view) END)
    - SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
          THEN IF(tweets_view < 0, 0, tweets_view) END),
    SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY)
        THEN IF(tweets_view < 0, 0, tweets_view) END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 9. Engagement | 互动量

**说明**：点赞 + 回复 + 转发 + 踩，负值按 0 处理

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

## 10. Engagement DoD | 互动量日环比

```sql
SELECT
  SUM(CASE WHEN DATE(comment_time) = '<target_date>' THEN
    IF(tweets_retweet < 0, 0, tweets_retweet)
    + IF(tweets_reply  < 0, 0, tweets_reply)
    + IF(tweets_like   < 0, 0, tweets_like)
    + IF(tweets_unlike < 0, 0, tweets_unlike)
  END)                                                                 AS engagement,
  SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY) THEN
    IF(tweets_retweet < 0, 0, tweets_retweet)
    + IF(tweets_reply  < 0, 0, tweets_reply)
    + IF(tweets_like   < 0, 0, tweets_like)
    + IF(tweets_unlike < 0, 0, tweets_unlike)
  END)                                                                 AS engagement_old,
  SAFE_DIVIDE(
    SUM(CASE WHEN DATE(comment_time) = '<target_date>' THEN
      IF(tweets_retweet<0,0,tweets_retweet)+IF(tweets_reply<0,0,tweets_reply)
      +IF(tweets_like<0,0,tweets_like)+IF(tweets_unlike<0,0,tweets_unlike) END)
    - SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY) THEN
      IF(tweets_retweet<0,0,tweets_retweet)+IF(tweets_reply<0,0,tweets_reply)
      +IF(tweets_like<0,0,tweets_like)+IF(tweets_unlike<0,0,tweets_unlike) END),
    SUM(CASE WHEN DATE(comment_time) = DATE_SUB('<target_date>', INTERVAL 1 DAY) THEN
      IF(tweets_retweet<0,0,tweets_retweet)+IF(tweets_reply<0,0,tweets_reply)
      +IF(tweets_like<0,0,tweets_like)+IF(tweets_unlike<0,0,tweets_unlike) END)
  ) * 100 AS dod_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= TIMESTAMP(DATE_SUB('<target_date>', INTERVAL 1 DAY))
  AND comment_time <  TIMESTAMP(DATE_ADD('<target_date>', INTERVAL 1 DAY))
```

---

## 11. Engagement Rate | 互动率

**说明**：互动量 / 曝光量，前端计算。Agent 可分别查询后自行计算：

```sql
SELECT
  SUM(
    IF(tweets_retweet < 0, 0, tweets_retweet)
    + IF(tweets_reply  < 0, 0, tweets_reply)
    + IF(tweets_like   < 0, 0, tweets_like)
    + IF(tweets_unlike < 0, 0, tweets_unlike)
  )                                                       AS total_engagement,
  SUM(IF(follower_number > 0, follower_number, 0))       AS total_impressions,
  SAFE_DIVIDE(
    SUM(
      IF(tweets_retweet < 0, 0, tweets_retweet)
      + IF(tweets_reply  < 0, 0, tweets_reply)
      + IF(tweets_like   < 0, 0, tweets_like)
      + IF(tweets_unlike < 0, 0, tweets_unlike)
    ),
    SUM(IF(follower_number > 0, follower_number, 0))
  )                                                       AS engagement_rate
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'social'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## 13-15. 直播指标（Hours Watched / Peak CCV / Avg CCV）

> ❌ **Agent 不可查**：直播数据来自 `t_opinion_streaming` 表，其 BigQuery 完整路径待后端确认。  
> 如需查询，请联系后端提供 BigQuery 表路径后更新此文档。

---

## 16. Official Account | 官号内容

> ❌ **Agent 不可查（字段不存在）**：原始口径依赖 `organization = 'official'` 过滤，但经验证 `tencent-databrain-prod.opinion.feeds` 表中**不存在 `organization` 字段**，执行会报 `Unrecognized name: organization`。  
> 如需此指标，请联系后端确认官号账号的过滤方式（可能在 `sources`、`data_sources` 字段或 `opinion.dim_media_account` 维表中），更新后补充 SQL。

---

## 17. Earned | 玩家内容

> ❌ **Agent 不可查（字段不存在）**：原始口径依赖 `organization = 'player'` 过滤，同上，`organization` 字段在 feeds 表中不存在。  
> 如需此指标，请联系后端确认过滤方式后更新此文档。
