# PR & News 指标

> ❌ **当前 Agent 不可直接查询**  
> 本文件所有指标依赖 `t_opinion_news`、`t_opinion_google_trends` 等后端服务层（MySQL）表名，**没有对应的 BigQuery 真实表路径**。  
> 待后端确认 BigQuery 路径后，请将表名替换为真实路径再添加 SQL。

---

## 指标一览

| 指标 | 统计口径说明 | 来源表（待确认 BQ 路径） |
|------|-------------|------------------------|
| Total Articles | 总新闻条数（COUNT） | `t_opinion_news` |
| Negative Articles | 负面情绪（`sentiment_rating IN (1,2)`）新闻数 | `t_opinion_news` |
| Positive Articles | 正面情绪（`sentiment_rating IN (4,5)`）新闻数 | `t_opinion_news` |
| Neutral Articles | 中性情绪（`sentiment_rating = 3`）新闻数 | `t_opinion_news` |
| News Brand Health | `(正面去重用户数 - 负面去重用户数) / (正面 + 负面) * 100`，样本 ≤10 时返回 -99999 | `t_opinion_news` |
| News Engagement | `SUM(comment_number + visit_number + like_number + unlike_number)`（仅 DataBrain 数据源） | `t_opinion_news` |
| Google Trends | `value` 字段直接取值，范围 0-100 | `t_opinion_google_trends` |
| Google Trends Ratio | 前端计算：`当前值 / 最大值 * 100` | `t_opinion_google_trends` |

---

## DoD 环比说明

Total Articles DoD、Negative Articles DoD 等环比为**前端/外部计算**：

> `dod_pct = (当日值 - 昨日值) / ABS(昨日值) * 100`  
> 待 BQ 路径确认后，可参考 `mentions_sentiment.md` 的 DoD 写法，用 `COUNTIF + DATE_SUB` 在同一 SQL 内计算。

---

## 待补充模板（BQ 路径确认后填入）

**请将以下占位符替换为真实 BigQuery 表名后，再使用这些 SQL：**

| 占位符 | 需替换内容 |
|--------|-----------|
| `<bq_news_table>` | `t_opinion_news` 对应的 BQ 完整路径（如 `tencent-databrain-prod.opinion.news`） |
| `<bq_trends_table>` | `t_opinion_google_trends` 对应的 BQ 完整路径 |

> ⚠️ 在占位符未替换前，以下 SQL **不可执行**，不要传给 `query_metrics.py`。

**Total Articles + 情绪分布**：

```sql
-- ❌ 表名待确认，不可直接执行
SELECT
  COUNT(comment_uin)                                                   AS total_articles,
  COUNT(CASE WHEN sentiment_rating IN (4,5) THEN comment_uin END)      AS positive_articles,
  COUNT(CASE WHEN sentiment_rating = 3     THEN comment_uin END)       AS neutral_articles,
  COUNT(CASE WHEN sentiment_rating IN (1,2) THEN comment_uin END)      AS negative_articles
FROM `<bq_news_table>`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```

**News Brand Health**：

```sql
-- ❌ 表名待确认，不可直接执行
SELECT
  CASE
    WHEN (
      COUNT(DISTINCT CASE WHEN sentiment_rating IN (4,5) THEN md5_uin END)
      + COUNT(DISTINCT CASE WHEN sentiment_rating IN (1,2) THEN md5_uin END)
    ) <= 10 THEN -99999
    ELSE SAFE_DIVIDE(
      COUNT(DISTINCT CASE WHEN sentiment_rating IN (4,5) THEN md5_uin END)
      - COUNT(DISTINCT CASE WHEN sentiment_rating IN (1,2) THEN md5_uin END),
      COUNT(DISTINCT CASE WHEN sentiment_rating IN (4,5) THEN md5_uin END)
      + COUNT(DISTINCT CASE WHEN sentiment_rating IN (1,2) THEN md5_uin END)
    ) * 100
  END AS news_brand_health
FROM `<bq_news_table>`
WHERE unified_edition_id = '<game_id>'
  AND comment_time >= '<start_date> 00:00:00'
  AND comment_time <= '<end_date> 23:59:59'
```
