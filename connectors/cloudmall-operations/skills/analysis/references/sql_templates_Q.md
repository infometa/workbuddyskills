# SQL 模板 — Q 组：快速查询（Quick Query）

> **主要用途**：供 `sql_templates_A.md`（A组）复用（A-1/A-4/A-5 直接复用本组 Q-1/Q-2/Q-4），以及第三档人工排查参考。

**通用约束**：
- BITMAP 字段必须用 `BITMAP_COUNT()` 包裹
- 跨日聚合使用 `BITMAP_COUNT(BITMAP_UNION(field))`
- `app_user_stat_di` / `app_market_stat_di` 必须 `WHERE tag_type='xxx'`
- `imp_date` 格式：`yyyyMMdd`（如 `'20260315'`）
- 占位符 `{start_date}` / `{end_date}` 替换为实际日期
- ⚠️ 概览表无 `click_pv`/`click_uv`，点击指标用 `cart_pv`/`cart_uv`（加购行为）

**数据覆盖与空数据纪律**：
- 报表宽表按日（`imp_date`）批量生成，**T+1 更新**：今天能查到的最新完整数据是昨天；指定时间窗前先确认表内实际有数据的日期范围
- **各维度表覆盖进度可能不齐**：同一时间窗内，交易大盘表可能有数据而品类/商品/用户维度表尚未生成——某维度查询返回空不等于该期间无业务，需换维度表或时间窗核实
- 分析报告遇到空数据或覆盖不齐时：先查该表最近有数据的完整周期，改用该周期做对比，并在报告中**明确说明实际使用的口径与原因**；禁止用零值冒充无数据、禁止静默换口径不说明

---

### Q-1 交易域大盘概览

```sql
SELECT
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    BITMAP_COUNT(BITMAP_UNION(order_cnt)) AS 下单订单数,
    SUM(pay_item_cnt) AS 销量,
    SUM(refund_amt) AS 退款金额,
    BITMAP_COUNT(BITMAP_UNION(refund_uv)) AS 退款人数,
    BITMAP_COUNT(BITMAP_UNION(refund_order_cnt)) AS 退款订单数,
    SUM(visit_pv) AS 访问次数,
    BITMAP_COUNT(BITMAP_UNION(visit_uv)) AS 访问人数,
    SUM(browse_pv) AS 浏览次数,
    BITMAP_COUNT(BITMAP_UNION(browse_uv)) AS 浏览人数,
    SUM(cart_pv) AS 加购次数,
    BITMAP_COUNT(BITMAP_UNION(cart_uv)) AS 加购人数,
    BITMAP_COUNT(BITMAP_UNION(register_uv)) AS 注册人数,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 客单价,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 笔单价,
    SUM(pay_item_cnt) / BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 连带率,
    SUM(refund_amt) * 1.0 / NULLIF(SUM(gmv), 0) AS 退款率,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(visit_uv)), 0) AS 整体转化率,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(cart_uv)), 0) AS 加购转化率
FROM app_sales_stat_overview_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}';
```

### Q-2 商品域品类概览

```sql
SELECT
    category_name1,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    BITMAP_COUNT(BITMAP_UNION(pay_order_cnt)) AS 成交订单数,
    SUM(pay_quantity) AS 销量,
    BITMAP_COUNT(BITMAP_UNION(expose_uv)) AS 曝光人数,
    BITMAP_COUNT(BITMAP_UNION(click_uv)) AS 点击人数,
    BITMAP_COUNT(BITMAP_UNION(addcart_uv)) AS 加购人数,
    BITMAP_COUNT(BITMAP_UNION(click_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(expose_uv)), 0) AS 点击率CTR,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) * 1.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(expose_uv)), 0) AS 转化率CVR
FROM app_commodity_stat_category_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY category_name1
ORDER BY gmv DESC
LIMIT 20;
```

> 品类表已有 `refund_amt` / `refund_quantity`，可直接查询品类退款。如需更细粒度（SPU 级），用 Q-2b。

### Q-2b 品类退款分析（从 SPU 表按品类聚合）

```sql
SELECT
    category_name1,
    SUM(gmv) AS gmv,
    SUM(refund_amt) AS 退款金额,
    SUM(refund_quantity) AS 退款件数
FROM app_commodity_stat_spu_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY category_name1
ORDER BY 退款金额 DESC
LIMIT 20;
```

### Q-3 门店排行

```sql
SELECT
    store_name,
    SUM(gmv) AS gmv,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(gmv) / BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 客单价,
    SUM(pay_item_cnt) AS 销量
FROM app_sales_stat_store_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY store_name
ORDER BY gmv DESC
LIMIT 10;
```

### Q-4 用户分群快查

```sql
-- ⚠️ 替换 {tag_type} 为 'lifecycle' / 'rfm' / 'source' / 'member_level'
SELECT
    tag_value,
    BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS 支付人数,
    SUM(total_gmv) AS 成交金额,
    SUM(total_pay_quantity) AS 销量,
    SUM(total_gmv) / NULLIF(BITMAP_COUNT(BITMAP_UNION(pay_uv)), 0) AS 客单价
FROM app_user_stat_di
WHERE tag_type = '{tag_type}'
  AND imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY tag_value
ORDER BY 成交金额 DESC;
```

### Q-5 分销推广（Q-5 按推广人排行 / Q-5b 大盘汇总）

```sql
-- Q-5：按推广人排行（加 GROUP BY promoter_uid + LIMIT 20）
-- Q-5b：大盘汇总（去掉 GROUP BY，加 COUNT(DISTINCT promoter_uid) AS 推广人数）
SELECT
    promoter_uid,                  -- Q-5b 删除此行
    promoter_name,                 -- Q-5b 删除此行
    BITMAP_COUNT(BITMAP_UNION(order_cnt)) AS 订单数,
    BITMAP_COUNT(BITMAP_UNION(order_uv)) AS 支付人数,
    SUM(cps_gmv) AS 订单金额,
    SUM(total_commission) AS 佣金,
    BITMAP_COUNT(BITMAP_UNION(settle_cnt)) AS 结算单数,
    SUM(settle_commission) AS 结算佣金
    -- Q-5b 加: COUNT(DISTINCT promoter_uid) AS 推广人数
FROM app_market_stat_cps_di
WHERE imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY promoter_uid, promoter_name  -- Q-5b 删除此行
ORDER BY 订单金额 DESC                -- Q-5b 删除此行
LIMIT 20;                              -- Q-5b 删除此行
```
