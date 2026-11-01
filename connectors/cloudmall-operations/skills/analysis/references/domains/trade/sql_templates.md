# 🟦 交易域 SQL 模板

> 交易域 SQL 模板以引用全局 `references/sql_templates_Q.md`（Q 组）、`sql_templates_A.md`（A 组）、`sql_templates_D.md`（D 组）中的编号为主，补充域特有模板。
>
> **引用语法**：`→ 引用 {SQL编号}` 表示该 SQL 完整定义在对应全局模板文件中，此处不重复。

---

## 引用的全局 SQL 模板

| SQL 编号 | 名称 | 服务的能力 | 全局文件位置 |
|---------|------|-----------|------------|
| Q-1 | 交易大盘概览 | 能力 1, 3, 6 | → 引用 Q-1 |
| Q-3 | 门店排行 | 能力 2, 5 | → 引用 Q-3 |
| A-2 | 大盘同环比 | 能力 1 | → 引用 A-2 |
| A-3 | 逐日趋势 | 能力 1, 3, 6 | → 引用 A-3 |
| A-8 | 门店多维度对比 | 能力 2, 5 | → 引用 A-8 |
| Q-2b | 品类退款 | 能力 6 | → 引用 Q-2b |
| A-9 | SPU Top N | 能力 6 | → 引用 A-9 |
| D-1 | 规模 vs 效率拆解 | 能力 4 | → 引用 D-1 |
| D-2 | 品类贡献度 | 能力 4 | → 引用 D-2 |
| D-3 | 头部 SPU 异动 | 能力 4 | → 引用 D-3 |
| D-4 | 新老客贡献度 | 能力 4 | → 引用 D-4 |
| D-5 | 生命周期/RFM 拆解 | 能力 4 | → 引用 D-5 |
| D-7 | 渠道贡献度 | 能力 4 | → 引用 D-7 |
| D-9 | 时间维度定位 | 能力 4 | → 引用 D-9 |

---

## 域特有补充模板

### T-1：门店逐日 GMV 趋势（能力 2 S5）

```sql
-- T-1: 各门店逐日 GMV 趋势（用于能力 2 多门店折线图）
SELECT
    stat_date,
    store_id,
    store_name,
    SUM(gmv) / 100 AS gmv_yuan,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS pay_uv
FROM app_sales_stat_store_di
WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY stat_date, store_id, store_name
ORDER BY stat_date, gmv_yuan DESC;
```

### T-2：门店退款率汇总（能力 6 S5）

```sql
-- T-2: 各门店退款率对比（用于能力 6 门店品控对比）
SELECT
    store_id,
    store_name,
    SUM(gmv) / 100 AS gmv_yuan,
    SUM(refund_amt) / 100 AS refund_amt_yuan,
    ROUND(SUM(refund_amt) * 100.0 / NULLIF(SUM(gmv), 0), 2) AS refund_rate_pct
FROM app_sales_stat_store_di
WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY store_id, store_name
ORDER BY refund_rate_pct DESC;
```
