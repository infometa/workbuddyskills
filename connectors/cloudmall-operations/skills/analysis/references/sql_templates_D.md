# SQL 模板 — D 组：归因诊断（Diagnosis / Attribution）

> **主要 SQL 来源**：L2 归因诊断和 L3 报告的归因分析专用。9 个模板统一使用 `CASE WHEN ... current / baseline` 模式，一条 SQL 同时拉取两个周期。
> 通用约束同 Q 组（BITMAP 包裹、tag_type WHERE、yyyyMMdd 格式）。
> 占位符：`{start_date}` / `{end_date}`（当期），`{baseline_start}` / `{baseline_end}`（基期）。

---

### D-1 规模 vs 效率拆解（交易域大盘，当期+基期）

```sql
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    BITMAP_COUNT(BITMAP_UNION(order_cnt)) AS 下单订单数,
    SUM(pay_quantity) AS 销量,
    SUM(refund_amt) AS 退款金额,
    BITMAP_COUNT(BITMAP_UNION(refund_order_cnt)) AS 退款订单数,
    SUM(visit_pv) AS 访问次数,
    BITMAP_COUNT(BITMAP_UNION(visit_uv)) AS 访问人数,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    SUM(cart_pv) AS 点击次数,
    BITMAP_COUNT(BITMAP_UNION(cart_uv)) AS 点击人数,
    BITMAP_COUNT(BITMAP_UNION(register_uv)) AS 注册人数
FROM app_sales_stat_overview_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END;
```

### D-2 品类贡献度（当期+基期品类对比）

```sql
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    category_name1,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    SUM(pay_quantity) AS 销量,
    BITMAP_COUNT(BITMAP_UNION(click_uv)) AS 点击人数,
    BITMAP_COUNT(BITMAP_UNION(expose_uv)) AS 曝光人数
FROM app_commodity_stat_category_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END,
    category_name1
ORDER BY gmv DESC;
```

### D-3 头部 SPU 异动排查

```sql
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    spu_id, spu_name, category_name1,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    SUM(pay_quantity) AS 销量,
    SUM(refund_amt) AS 退款金额
FROM app_commodity_stat_spu_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END,
    spu_id, spu_name, category_name1
ORDER BY gmv DESC
LIMIT 40;
```

### D-4 新老客贡献度拆解

```sql
-- 新老客拆解：用 is_new_customer 列替代旧版 user_order_type
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    CASE WHEN is_new_customer = '1' THEN '新客' ELSE '老客' END AS 用户类型,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(total_gmv) AS 成交金额,
    SUM(total_pay_quantity) AS 销量
FROM app_user_stat_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END,
    CASE WHEN is_new_customer = '1' THEN '新客' ELSE '老客' END;
```

### D-5 生命周期/RFM 拆解

```sql
-- ⚠️ 替换 {tag_type} 为 'lifecycle' 或 'rfm'
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    tag_value,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(total_gmv) AS 成交金额
FROM app_user_stat_di
WHERE tag_type = '{dim_type}'
  AND (imp_date BETWEEN '{start_date}' AND '{end_date}'
       OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}')
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END,
   tag_value;
```

### D-6 留存复购趋势诊断

> 直接复用 A-10 模板（见 `sql_templates_A.md`）

### D-7 渠道贡献度拆解

```sql
-- D-7: 渠道贡献度拆解
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    channel_name AS 渠道,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(total_gmv) / 100 AS 成交金额_元
FROM app_market_channel_stat_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END,
    channel_name
ORDER BY 浏览人数 DESC;
```

### D-8 活动效果诊断

```sql
-- D-8: 活动效果诊断（当期 vs 基期）
SELECT
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END AS period,
    BITMAP_COUNT(BITMAP_UNION(participate_uv)) AS 参与人数,
    SUM(promotion_gmv) AS 成交金额_元,
    SUM(promotion_discount_amt) AS 补贴金额_元,
    SUM(promotion_gmv) / NULLIF(SUM(promotion_discount_amt), 0) AS ROI
FROM app_market_stat_promotion_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
   OR imp_date BETWEEN '{baseline_start}' AND '{baseline_end}'
GROUP BY
    CASE WHEN imp_date BETWEEN '{start_date}' AND '{end_date}' THEN 'current' ELSE 'baseline' END;
```

### D-9 时间维度定位（逐日走势，扩展前7天基线）

```sql
SELECT
    imp_date,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 客单价,
    SUM(visit_pv) AS 访问次数,
    BITMAP_COUNT(BITMAP_UNION(visit_uv)) AS 访问人数,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    SUM(cart_pv) AS 点击次数,
    BITMAP_COUNT(BITMAP_UNION(cart_uv)) AS 点击人数
FROM app_sales_stat_overview_di
WHERE imp_date BETWEEN '{extended_start}' AND '{end_date}'
GROUP BY imp_date
ORDER BY imp_date;
```

---

### D-10 退款原因归因（DWD 订单明细，仅退款率归因场景使用）

> **当前 Agent 可用性门禁**：当前分析服务白名单不包含 `dwd_base_sales_order_item_df`；以下 D-10/用户明细查询是条件模板，不是已可用能力。必须先通过 table_structure 按精确表名查询且确认实际授权与字段；当前不可用时明确告知无法执行该明细归因/用户聚合，只能使用已授权汇总维度并说明限制。禁止直接执行、扩展白名单、编造字段或将汇总数据冒充用户明细。


> ⚠️ 仅在用户问"退款率为什么涨/降、退款原因、退款集中在哪"时使用，不要在其他场景使用。
> 如需按商品维度下钻，取消注释 spu_id / spu_name 并加入 GROUP BY。

```sql
SELECT
    refund_reason_desc                                            AS 退款原因,
    -- spu_id                                                     AS 商品ID,
    -- spu_name                                                   AS 商品名称,
    COUNT(DISTINCT after_sale_id)                                 AS 退款单数,
    SUM(refund_amount) / 100.0                                    AS 退款金额_元,
    SUM(refund_quantity)                                          AS 退款件数,
    ROUND(SUM(refund_amount) * 100.0 / SUM(SUM(refund_amount)) OVER (), 2) AS 占比_百分比
FROM dwd_base_sales_order_item_df
WHERE refund_amount > 0
  AND refund_time BETWEEN '{start_date} 00:00:00' AND '{end_date} 23:59:59'
GROUP BY refund_reason_desc
    -- , spu_id, spu_name
ORDER BY 退款金额_元 DESC
LIMIT 20;
```

---

## 使用说明

- **品类退款**：品类表已有 refund_amt / refund_qty 字段，可直接查询；SPU 粒度用 Q-2b
- **BITMAP 字段**：品类表和 SPU 表的 `pay_order_cnt` / `refund_order_cnt` 都是 BITMAP，查询时需 `BITMAP_COUNT(BITMAP_UNION())` 包裹
