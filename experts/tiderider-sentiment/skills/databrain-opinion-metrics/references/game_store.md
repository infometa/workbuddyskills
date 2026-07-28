# Game Store 指标

**核心表**：`tencent-databrain-prod.opinion.feeds`（Steam 评论数据）

**分区字段**：`comment_time`（按 DAY 分区）  
⚠️ 查询必须在 WHERE 中包含 `comment_time` 范围，否则触发全表扫描，费用极高。

**关键过滤字段**：

| 字段 | 说明 |
|------|------|
| `channel_type` | 固定为 `'comments'`（商店评论渠道） |
| `channel_name` | 指定商店：`'steam'`（Steam）/ `'googleplay'`（Google Play）/ `'appstore'`（App Store） |
| `is_recommend` | Steam 好评标记：`1` = 好评，`0` = 差评（**仅 Steam 有效**，其他平台为空） |
| `comment_score` | 评分值，部分平台（如 Google Play、App Store）使用此字段存储星级评分 |

## 可查 vs 不可查一览

| 指标 | 数据来源 | 可查性 |
|------|---------|-------|
| Steam 评论数 / 好评率 | `opinion.feeds`（channel_name = 'steam'） | ✅ 可查 |
| Xbox / PlayStation / Metacritic / OpenCritic 评分 | `t_opinion_game_data`（BQ 路径待确认） | ❌ 暂不可查 |
| Mobile 终身评分（Google Play / App Store） | `t_opinion_game_data_google_play/app_store`（BQ 路径待确认） | ❌ 暂不可查 |
| All Reviews Positive% / Positive Count / Negative Count | 前端计算 | ⚠️ 由 SQL 结果派生 |

---

## ✅ 可查：Steam 评论数（All Reviews Count）

**说明**：Steam 终身总评论数。  
⚠️ 由于表按 `comment_time` 分区，**必须传时间范围**。统计终身评论时，请将 `<start_date>` 设为游戏上线日期（或尽量早的日期）。

```sql
SELECT COUNT(*) AS steam_review_count
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'comments'
  AND channel_name = 'steam'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## ✅ 可查：Steam 好评率（All Reviews Score）

**说明**：Steam 好评率 = 好评数 / 总评论数；`is_recommend = 1` 表示好评

```sql
SELECT
  COUNT(comment_uin)                                                   AS total_reviews,
  COUNT(CASE WHEN is_recommend = 1 THEN comment_uin END)               AS positive_reviews,
  SAFE_DIVIDE(
    COUNT(CASE WHEN is_recommend = 1 THEN comment_uin END),
    COUNT(comment_uin)
  )                                                                    AS steam_score
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'comments'
  AND channel_name = 'steam'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## ✅ 可查：Steam 近 30 天评论数（Recent Reviews Count）

**说明**：`<recent_start>` 为最近 30 天的起始日期，格式 `YYYY-MM-DD`

```sql
SELECT COUNT(CASE WHEN channel_name = 'steam' THEN comment_uin END) AS recent_review_count
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'comments'
  AND channel_name = 'steam'
  AND comment_time >= '<recent_start> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## ✅ 可查：Steam 近 30 天好评率（Recent Reviews Score）

```sql
SELECT
  SAFE_DIVIDE(
    COUNT(CASE WHEN is_recommend = 1 THEN comment_uin END),
    COUNT(comment_uin)
  ) AS recent_steam_score
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'comments'
  AND channel_name = 'steam'
  AND comment_time >= '<recent_start> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## ⚠️ 派生指标（前端计算，Agent 直接在 SQL 中计算）

**All Reviews Positive%**（正面评论占比）：

```sql
SELECT
  SAFE_DIVIDE(
    COUNT(CASE WHEN is_recommend = 1 THEN comment_uin END),
    COUNT(comment_uin)
  ) * 100 AS positive_pct
FROM `tencent-databrain-prod.opinion.feeds`
WHERE unified_edition_id = '<game_id>'
  AND channel_type = 'comments'
  AND channel_name = 'steam'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

---

## ❌ 暂不可查：Xbox / PlayStation / Metacritic / OpenCritic / Mobile 评分

> **原因**：这些数据来自 `t_opinion_game_data`、`t_opinion_game_data_google_play`、`t_opinion_game_data_app_store` 等表，均为后端服务层（MySQL）表名，BigQuery 对应路径待确认。
>
> **待确认后补充**：若后端提供 BigQuery 路径，请按以下格式补充 SQL：
>
> **Xbox Score（`tencent-databrain-prod.<待确认 dataset>.<待确认 table>`）**：
>
> `SAFE_DIVIDE(SUM(comment_score), COUNT(comment_uin))` — 评分 1-5，正面 ≥4，中性 =3，负面 ≤2
>
> **Metacritic Score**：媒体评分 0-100（正面 ≥71，中性 40-70，负面 ≤39）；用户评分（正面 ≥8，中性 5-7，负面 ≤4）
>
> **Mobile Lifetime Score**：`SAFE_DIVIDE(SUM(comment_score * rating_count), SUM(rating_count))` — 加权平均
