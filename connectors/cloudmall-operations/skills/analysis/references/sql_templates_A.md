# SQL 模板 — A 组：分析用（Scene Analysis）

> **主要 SQL 来源**：L2 场景分析和 L3 报告的分析数据获取。11 个模板中 3 个复用 Q 组。
> 通用约束同 Q 组（BITMAP 包裹、tag_type WHERE、yyyyMMdd 格式）。

---

### A-1 交易域大盘汇总

> 直接复用 Q-1 模板（见 `sql_templates_Q.md`）

### A-2 交易域同环比（当期 + 基期分别查）

```sql
SELECT
    imp_date,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    BITMAP_COUNT(BITMAP_UNION(order_cnt)) AS 下单订单数,
    SUM(pay_quantity) AS 销量,
    SUM(refund_amt) AS 退款金额,
    BITMAP_COUNT(BITMAP_UNION(refund_uv)) AS 退款人数,
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
GROUP BY imp_date
ORDER BY imp_date;
```

### A-3 交易域逐日趋势

```sql
SELECT
    imp_date,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 客单价,
    SUM(pay_quantity) AS 销量,
    SUM(visit_pv) AS 访问次数,
    BITMAP_COUNT(BITMAP_UNION(visit_uv)) AS 访问人数,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    SUM(cart_pv) AS 点击次数,
    BITMAP_COUNT(BITMAP_UNION(cart_uv)) AS 点击人数,
    BITMAP_COUNT(BITMAP_UNION(register_uv)) AS 注册人数
FROM app_sales_stat_overview_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY imp_date
ORDER BY imp_date;
```

### A-4 品类分布与排行

> 直接复用 Q-2 模板（见 `sql_templates_Q.md`）

### A-5 用户分群分布

> 直接复用 Q-4 模板（见 `sql_templates_Q.md`，分别查 lifecycle / rfm / source / member_level）

### A-6a 活动维度统计

```sql
-- A-6a: 活动维度统计
SELECT
    promotion_id,
    SUM(coupon_issue_cnt) AS 发券量,
    BITMAP_COUNT(BITMAP_UNION(coupon_use_cnt)) AS 用券数,
    BITMAP_COUNT(BITMAP_UNION(participate_uv)) AS 参与人数,
    SUM(promotion_gmv) AS 成交金额_元,
    SUM(promotion_discount_amt) AS 补贴金额_元,
    ROUND(SUM(promotion_gmv) / NULLIF(BITMAP_COUNT(BITMAP_UNION(participate_uv)), 0), 2) AS 人均消费
FROM app_market_stat_promotion_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY promotion_id
ORDER BY 成交金额_元 DESC;
```

### A-6b 优惠券概览统计

```sql
-- A-6b: 优惠券概览统计（按券类型）
WITH cost_dedup AS (
    SELECT
        coupon_type,
        SUM(daily_coupon_cost_amt) AS coupon_cost_amt
    FROM (
        SELECT
            imp_date,
            coupon_type,
            MAX(coupon_cost_amt) / 100.0 AS daily_coupon_cost_amt
        FROM app_market_stat_coupon_overview_di
        WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY imp_date, coupon_type
    ) t
    GROUP BY coupon_type
)
SELECT
    o.coupon_type AS 券类型,
    BITMAP_COUNT(BITMAP_UNION(o.acquire_cnt)) AS 领取量,
    BITMAP_COUNT(BITMAP_UNION(o.acquire_uv)) AS 领取人数,
    BITMAP_COUNT(BITMAP_UNION(o.use_cnt)) AS 核销量,
    BITMAP_COUNT(BITMAP_UNION(o.use_uv)) AS 核销人数,
    SUM(o.pay_amt) / 100.0 AS 用券成交金额_元,
    MAX(cost_dedup.coupon_cost_amt) AS 券优惠成本_元,
    BITMAP_COUNT(BITMAP_UNION(o.pay_order_cnt)) AS 用券成交订单数,
    BITMAP_COUNT(BITMAP_UNION(o.pay_uv)) AS 用券成交人数,
    BITMAP_COUNT(BITMAP_UNION(o.use_cnt)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(o.acquire_cnt)), 0) AS 核销率,
    SUM(o.pay_amt) / 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(o.pay_uv)), 0) AS 用券客单价
FROM app_market_stat_coupon_overview_di o
LEFT JOIN cost_dedup ON o.coupon_type = cost_dedup.coupon_type
WHERE o.imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY o.coupon_type
ORDER BY 用券成交金额_元 DESC;
```

### A-6c 渠道维度统计

```sql
-- A-6c: 渠道维度统计
SELECT
    channel_id, channel_name,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(total_gmv) / 100 AS 成交金额_元,
    SUM(refund_amt) / 100 AS 退款金额_元,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(browse_uv)), 0) AS 转化率
FROM app_market_channel_stat_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY channel_id, channel_name
ORDER BY 成交金额_元 DESC;
```

### A-7 商品域漏斗

> 次数口径（默认用于转化漏斗）和人数口径同时返回，按 scene_5 规则选用。

```sql
SELECT
    BITMAP_COUNT(BITMAP_UNION(expose_pv)) AS 曝光次数,
    BITMAP_COUNT(BITMAP_UNION(click_pv)) AS 点击次数,
    BITMAP_COUNT(BITMAP_UNION(addcart_pv)) AS 加购次数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    SUM(gmv) AS gmv
FROM app_commodity_stat_category_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}';
```

### A-7b 品类/SPU CTR·CVR 逐日趋势

```sql
SELECT
    imp_date,
    category_name1,
    BITMAP_COUNT(BITMAP_UNION(expose_uv)) AS 曝光人数,
    BITMAP_COUNT(BITMAP_UNION(click_uv)) AS 点击人数,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 成交人数,
    ROUND(BITMAP_COUNT(BITMAP_UNION(click_uv)) * 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(expose_uv)), 0), 2) AS ctr_pct,
    ROUND(BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(expose_uv)), 0), 2) AS cvr_pct
FROM app_commodity_stat_category_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY imp_date, category_name1
ORDER BY imp_date, category_name1;
```

> SPU 粒度：`FROM` 换 `app_commodity_stat_spu_di`，`category_name1` 换 `spu_id, spu_name`。

### A-8 门店对比

```sql
SELECT
    store_name,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 客单价,
    SUM(pay_quantity) / BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 连带率,
    SUM(refund_amt) / NULLIF(SUM(gmv), 0) AS 退款率
FROM app_sales_stat_store_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
  AND store_name IN ('{store_a}', '{store_b}')
GROUP BY store_name;
```

### A-9 SPU Top N 排行

```sql
SELECT
    spu_id, spu_name, category_name1,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    SUM(pay_quantity) AS 销量,
    SUM(refund_amt) AS 退款金额,
    SUM(refund_quantity) AS 退款件数,
    BITMAP_COUNT(BITMAP_UNION(click_pv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(expose_pv)), 0) AS 点击率,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(click_uv)), 0) AS 转化率
FROM app_commodity_stat_spu_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY spu_id, spu_name, category_name1
ORDER BY gmv DESC
LIMIT 20;
```

### A-10 留存复购趋势

```sql
SELECT
    cohort_date, user_type,
    cohort_uv,
    ROUND(visit_retain_d7 / NULLIF(cohort_uv, 0), 4) AS 7日留存率,
    ROUND(visit_retain_d30 / NULLIF(cohort_uv, 0), 4) AS 30日留存率,
    ROUND(repurchase_d7 / NULLIF(cohort_uv, 0), 4) AS 7日复购率,
    ROUND(repurchase_d30 / NULLIF(cohort_uv, 0), 4) AS 30日复购率,
    ROUND(multi_buy_uv * 1.0 / NULLIF(period_buyers, 0), 4) AS 周期复购率
FROM dws_user_cohort_metrics_di
WHERE cohort_date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY cohort_date, user_type;
```

### A-11 优惠券漏斗

```sql
-- A-11: 优惠券漏斗（券批次列表）
WITH cost_dedup AS (
    SELECT
        template_id,
        SUM(daily_coupon_cost_amt) AS coupon_cost_amt
    FROM (
        SELECT
            imp_date,
            template_id,
            MAX(coupon_cost_amt) / 100.0 AS daily_coupon_cost_amt
        FROM app_market_stat_coupon_di
        WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY imp_date, template_id
    ) t
    GROUP BY template_id
)
SELECT
    c.template_id AS 券批次ID,
    MAX(c.template_name) AS 券名称,
    MAX(c.coupon_type) AS 券类型,
    MAX(c.issue_cnt) AS 发行总量,
    BITMAP_COUNT(BITMAP_UNION(c.acquire_cnt)) AS 领取量,
    BITMAP_COUNT(BITMAP_UNION(c.acquire_uv)) AS 领取人数,
    BITMAP_COUNT(BITMAP_UNION(c.use_cnt)) AS 核销量,
    BITMAP_COUNT(BITMAP_UNION(c.use_uv)) AS 核销人数,
    SUM(c.pay_amt) / 100.0 AS 用券成交金额_元,
    MAX(cost_dedup.coupon_cost_amt) AS 券优惠成本_元,
    BITMAP_COUNT(BITMAP_UNION(c.pay_order_cnt)) AS 用券成交订单数,
    BITMAP_COUNT(BITMAP_UNION(c.pay_uv)) AS 用券成交人数,
    BITMAP_COUNT(BITMAP_UNION(c.use_cnt)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(c.acquire_cnt)), 0) AS 核销率,
    SUM(c.pay_amt) / 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(c.pay_uv)), 0) AS 用券客单价
FROM app_market_stat_coupon_di c
LEFT JOIN cost_dedup ON c.template_id = cost_dedup.template_id
WHERE c.imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY c.template_id
ORDER BY 用券成交金额_元 DESC;
```
