# 🟪 跨域综合 SQL 模板

> 跨域综合的 SQL 主要引用各域的全局模板（`sql_templates_Q.md` / `sql_templates_A.md` / `sql_templates_D.md`）联合使用。

---

## 引用的全局 SQL 模板

| SQL 编号 | 名称 | 服务的能力 |
|---------|------|-----------|
| Q-1 | 交易大盘概览 | 能力 23, 25, 26, 27 |
| Q-2 | 品类概览 | 能力 23, 25 |
| Q-3 | 门店排行 | 能力 25 |
| Q-4 | 用户分群（替换 dim_type 分别查新老客/生命周期/RFM） | 能力 23, 27 |
| A-2 | 大盘同环比 | 能力 23 |
| A-3 | 逐日趋势 | 能力 23, 26 |
| A-6 | 渠道分布（`dim_type='channel'`） | 能力 23 |
| A-7 | 商品漏斗 | 能力 23 |
| A-10 | 留存复购 | 能力 23 |
| D-1~D-9 | 全套归因模板 | 能力 24 |

---

## 域特有补充模板

### X-1：星期维度 GMV 分布（能力 26 S2）

```sql
-- X-1: 按星期几汇总 GMV（季节性分析）
SELECT
    DAYOFWEEK(STR_TO_DATE(stat_date, '%Y%m%d')) AS dow,
    CASE DAYOFWEEK(STR_TO_DATE(stat_date, '%Y%m%d'))
        WHEN 1 THEN '周日' WHEN 2 THEN '周一' WHEN 3 THEN '周二'
        WHEN 4 THEN '周三' WHEN 5 THEN '周四' WHEN 6 THEN '周五'
        WHEN 7 THEN '周六' END AS dow_label,
    AVG(daily_gmv) AS avg_gmv_yuan
FROM (
    SELECT stat_date, SUM(gmv) / 100 AS daily_gmv
    FROM app_sales_stat_overview_di
    WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY stat_date
) t
GROUP BY dow
ORDER BY dow;
```

### X-2：月度 GMV 汇总（能力 26 S3）

```sql
-- X-2: 按月汇总 GMV + 流量
SELECT
    LEFT(stat_date, 6) AS month_id,
    SUM(gmv) / 100 AS gmv_yuan,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS pay_uv,
    SUM(visit_pv) AS visit_pv,
    BITMAP_COUNT(BITMAP_UNION(visit_uv)) AS visit_uv,
    SUM(browse_pv) AS browse_pv,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS browse_uv,
    SUM(click_pv) AS click_pv,
    BITMAP_COUNT(BITMAP_UNION(click_uv)) AS click_uv,
    BITMAP_COUNT(BITMAP_UNION(register_uv)) AS register_uv
FROM app_sales_stat_overview_di
WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY LEFT(stat_date, 6)
ORDER BY month_id;
```
