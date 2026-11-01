# 🟥 营促销域 SQL 模板

> 营促销域 SQL 以引用全局 `sql_templates_Q.md`（Q 组）、`sql_templates_A.md`（A 组）、`sql_templates_D.md`（D 组）中的编号为主。

---

## 引用的全局 SQL 模板

| SQL 编号 | 名称 | 数据表 | 服务的能力 |
|---------|------|--------|-----------|
| A-6a | 活动维度统计 | `app_market_stat_promotion_di` | 能力 19, 22 |
| A-6b | 优惠券概览统计 | `app_market_stat_coupon_overview_di` | 能力 19, 22 |
| A-6c | 渠道维度统计 | `app_market_channel_stat_di` | 能力 20 |
| A-11 | 优惠券漏斗/券批次列表 | `app_market_stat_coupon_di` | 能力 19 |
| D-7 | 渠道贡献度 | `app_market_channel_stat_di` | 能力 21 |
| D-8 | 活动效果诊断 | `app_market_stat_promotion_di` | 能力 19, 21 |
| D-9 | 时间维度定位 | `app_sales_stat_overview_di` | 能力 21 |
| Q-1 | 交易大盘概览（补贴额） | `app_sales_stat_overview_di` | 能力 22 |
| Q-5/Q-5b | 分销推广 | `app_market_stat_cps_di` | 能力 19 |

---

## 域特有补充模板

### MK-1：渠道逐日趋势（能力 20）

```sql
-- MK-1: 渠道维度逐日趋势
SELECT
    stat_date,
    channel_name,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(pay_amt) / 100 AS 成交金额_元,
    SUM(refund_amt) / 100 AS 退款金额_元
FROM app_market_channel_stat_di
WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY stat_date, channel_name
ORDER BY stat_date, 成交金额_元 DESC;
```

### MK-2：活动×商品明细（能力 19 S5）

```sql
-- MK-2: 活动商品明细（天×活动ID×SPU 粒度）
SELECT
    activity_id,
    activity_name,
    activity_type,
    spu_id,
    spu_name,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_cnt)) AS 成交订单数,
    SUM(sales_qty) AS 销量,
    SUM(pay_amt) AS 成交金额_元,
    SUM(subsidy_amt) AS 补贴金额_元
FROM dwm_market_activity_detail_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY activity_id, activity_name, activity_type, spu_id, spu_name
ORDER BY 成交金额_元 DESC
LIMIT 50;
```
