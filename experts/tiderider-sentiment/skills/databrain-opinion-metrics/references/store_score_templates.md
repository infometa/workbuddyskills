# SQL Templates — store_score 商店评分

> **API 可用性**：❌ 本文件模板**不能**通过 `POST /api/v1/opinion_pc/global/query` 执行。  
> `store_score_*` 系列表的服务账号权限不开放给该 API（返回 403 Access Denied）。  
> **如需查询商店评分，请改用直连 BigQuery 的方案（参见 `databrain-bigquery/SKILL.md`）。**  
> 本文件保留作为 SQL 口径参考文档。

---

**数据表**：`store_score_google_play_daily`、`store_score_app_store_daily`、`store_score_steam`  
**查询方式**：需直连 BigQuery（`bigquery_pro.json` 服务账号）

**占位符**（仅供参考）：
- `<game_id>` → 游戏 ID（`u...` 移动 / `e...` PC），通过 `game_search.py` 获取
- `<start_date>` / `<end_date>` → 日期范围（格式 `YYYY-MM-DD`）

**如需通过 BigQuery 执行**，请使用 `databrain-bigquery/SKILL.md` 中的直连 BigQuery 方案（`bigquery_pro.json` 服务账号），本 skill 的 `query_metrics.py` **不支持**查询 `store_score_*` 系列表。

> ⚠️ **安全要求**：
> - 必须原样使用模板 SQL，**不得改写聚合逻辑**（避免口径偏差）
> - 占位符只做简单字符串替换，不得拼接用户输入的任意文本到 SQL 中
> - `query_metrics.py` 会对 `game_id` 和日期格式做二次校验

---

## 平台说明

| `game_id` 前缀 | 平台 | 适用模板 |
|---------------|------|---------|
| `u...` | 移动游戏 | `gp_store_score`、`as_store_score` |
| `e...` | PC 游戏 | `steam_store_score` |
| Console 平台 | **不支持** | — |

---

## 模板目录

| 模板 ID | 指标 | 适用平台 |
|---------|------|---------|
| [gp_store_score](#gp_store_score) | Google Play 历史累计评分 | 移动（`u...`） |
| [as_store_score](#as_store_score) | App Store 历史累计评分 | 移动（`u...`） |
| [steam_store_score](#steam_store_score) | Steam 历史评分快照 | PC（`e...`） |

---

## gp_store_score

**指标**：Google Play 历史累计评分（按评论量加权平均，每日一条）

**适用**：`game_id` 以 `u` 开头的移动游戏

**输出字段**：
| 字段 | 说明 |
|------|------|
| `score_date` | 日期 |
| `store_score` | 加权平均评分（4 位小数，0~5） |
| `comments_number` | 当日总评论数 |

```sql
SELECT
    DATE(date) AS score_date,
    ROUND(
        SAFE_DIVIDE(
            SUM(CAST(comments_number AS FLOAT64) * store_score),
            SUM(CAST(comments_number AS FLOAT64))
        ),
        4
    ) AS store_score,
    MAX(CAST(comments_number AS INT64)) AS comments_number
FROM `tencent-databrain-prod.opinion.store_score_google_play_daily`
WHERE unified_id = '<game_id>'
  AND DATE(date) BETWEEN '<start_date>' AND '<end_date>'
GROUP BY DATE(date)
ORDER BY score_date
```

---

## as_store_score

**指标**：App Store 历史累计评分（按评论量加权平均，每日一条）

**适用**：`game_id` 以 `u` 开头的移动游戏

**输出字段**：
| 字段 | 说明 |
|------|------|
| `score_date` | 日期 |
| `store_score` | 加权平均评分（4 位小数，0~5） |
| `comments_number` | 当日总评论数 |

```sql
SELECT
    DATE(date) AS score_date,
    ROUND(
        SAFE_DIVIDE(
            SUM(CAST(comments_number AS FLOAT64) * store_score),
            SUM(CAST(comments_number AS FLOAT64))
        ),
        4
    ) AS store_score,
    MAX(CAST(comments_number AS INT64)) AS comments_number
FROM `tencent-databrain-prod.opinion.store_score_app_store_daily`
WHERE unified_id = '<game_id>'
  AND DATE(date) BETWEEN '<start_date>' AND '<end_date>'
GROUP BY DATE(date)
ORDER BY score_date
```

---

## steam_store_score

**指标**：Steam 历史评分快照（每日取最新一条，去重）

**适用**：`game_id` 以 `e` 开头的 PC 游戏

**输出字段**：
| 字段 | 说明 |
|------|------|
| `score_date` | 日期 |
| `store_score` | 综合评分 |
| `all_reviews_name` | 历史评价标签（如 "Very Positive"） |
| `all_reviews_count` | 历史总评价数 |
| `all_reviews_score` | 历史好评率（0~1） |
| `recent_reviews_name` | 近期评价标签 |
| `recent_reviews_count` | 近期评价数 |
| `recent_reviews_score` | 近期好评率（0~1） |

```sql
WITH ranked AS (
    SELECT
        DATE(create_time)     AS score_date,
        store_score,
        all_reviews_name,
        all_reviews_count,
        all_reviews_score,
        recent_reviews_name,
        recent_reviews_count,
        recent_reviews_score,
        ROW_NUMBER() OVER (
            PARTITION BY DATE(create_time)
            ORDER BY create_time DESC
        ) AS rn
    FROM `tencent-databrain-prod.opinion.store_score_steam`
    WHERE edition_id = '<game_id>'
      AND DATE(create_time) BETWEEN '<start_date>' AND '<end_date>'
)
SELECT
    score_date,
    store_score,
    all_reviews_name,
    all_reviews_count,
    all_reviews_score,
    recent_reviews_name,
    recent_reviews_count,
    recent_reviews_score
FROM ranked
WHERE rn = 1
ORDER BY score_date
```

---

<!-- ============================================================
  后续指标在此追加，无需修改任何 .py 文件
  格式示例：

## <template_id>

**指标**：<描述>
**适用**：<platform>
**输出字段**：<table>

```sql
SELECT ...
FROM `tencent-databrain-prod.opinion.<table>`
WHERE <id_field> = '<game_id>'
  AND DATE(<date_field>) BETWEEN '<start_date>' AND '<end_date>'
...
```
============================================================ -->
