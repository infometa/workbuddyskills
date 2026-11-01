# 🟩 商品域 SQL 模板

> 商品域 SQL 以引用全局 `sql_templates_Q.md`（Q 组）、`sql_templates_A.md`（A 组）、`sql_templates_D.md`（D 组）中的编号为主，补充域特有模板。

---

## 引用的全局 SQL 模板

| SQL 编号 | 名称 | 服务的能力 |
|---------|------|-----------|
| Q-2 | 品类概览 | 能力 7 |
| Q-2b | 品类退款（SPU 聚合） | 能力 7（退款维度） |
| A-4 | 品类同环比 | 能力 7 |
| A-7 | 商品漏斗 | 能力 7, 10, 11 |
| A-7b | 品类/SPU CTR·CVR 逐日趋势 | 能力 7 |
| A-9 | SPU Top N（需按价格带/新品筛选时改用 CM-2/CM-1，两者均无对应物理字段） | 能力 8, 9, 11, 12 |
| D-2 | 品类贡献度 | 能力 10 |
| D-3 | 头部 SPU 异动 | 能力 10 |

---

## 域特有补充模板

### CM-1：SPU 逐日 GMV 趋势（能力 9, 12 用）

> `is_new`/`price_tier` 已在基座2.0移除，无对应物理字段，改用 `dim_base_commodity_info_df` 派生：`is_new` 按 `listing_time`（首次上架时间）与统计日期差值 ≤30 天判定。`sales_qty` 已改名 `pay_quantity`，`gmv` 已是元不再需要 `/100`。
>
> **JOIN 注意事项**：`dim_base_commodity_info_df` 粒度是 `tenant_id+spu_id+sku_id+store_id`，JOIN 前需先按 `tenant_id+spu_id` 聚合到 SPU 粒度（子查询已处理），避免 SKU×门店行数导致 `SUM(gmv)`/`SUM(pay_quantity)` 被放大；且必须同时用 `tenant_id`+`spu_id` 关联（`spu_id` 在多租户系统下不保证全局唯一）。`t.imp_date` 是 `VARCHAR(8)`，`DATEDIFF` 前需 `STR_TO_DATE` 显式转换为日期类型。

```sql
-- CM-1: 指定 SPU 逐日 GMV（新品跟踪/生命周期趋势）
SELECT
    t.imp_date,
    t.spu_id,
    t.spu_name,
    CASE WHEN DATEDIFF(STR_TO_DATE(t.imp_date, '%Y%m%d'), d.listing_time) <= 30 THEN 1 ELSE 0 END AS is_new,  -- 上架30天内视为新品
    SUM(t.gmv) AS gmv_yuan,               -- 基座2.0 gmv 已是元，不再 /100
    SUM(t.pay_quantity) AS pay_quantity,  -- sales_qty 已改名 pay_quantity
    BITMAP_COUNT(BITMAP_UNION(t.pay_uv)) AS pay_uv
FROM app_commodity_stat_spu_di t
LEFT JOIN (
    -- 先按 tenant_id+spu_id 去重聚合到 SPU 粒度，避免 SKU×门店行数导致下游 SUM 膨胀
    SELECT tenant_id, spu_id, MIN(listing_time) AS listing_time, MIN(min_price) AS min_price
    FROM dim_base_commodity_info_df
    GROUP BY tenant_id, spu_id
) d ON t.tenant_id = d.tenant_id AND t.spu_id = d.spu_id
WHERE t.imp_date BETWEEN '{start_date}' AND '{end_date}'
  AND ({spu_filter})  -- 新品用 DATEDIFF(STR_TO_DATE(t.imp_date,'%Y%m%d'), d.listing_time)<=30，或指定 spu_id 列表
GROUP BY t.imp_date, t.spu_id, t.spu_name, d.listing_time
ORDER BY t.imp_date, gmv_yuan DESC;
```

### CM-2：价格带 × 漏斗（能力 11 S3 用）

> `price_tier` 字段已在基座2.0移除，无对应物理字段，改用 `dim_base_commodity_info_df.min_price`（最低SKU价格）派生价格带分档。
>
> **JOIN 注意事项**：同 CM-1，须用 `tenant_id`+`spu_id` 关联（避免多租户串号），dim 子查询先按 `tenant_id+spu_id` 聚合去重（本模板指标均为 `BITMAP_UNION`，天然去重不受粒度膨胀影响，聚合仅为收窄 JOIN 结果集提升性能）。

```sql
-- CM-2: 各价格带全链路漏斗
SELECT
    CASE
        WHEN d.min_price < 50  THEN '¥0-50'
        WHEN d.min_price < 100 THEN '¥50-100'
        WHEN d.min_price < 200 THEN '¥100-200'
        WHEN d.min_price < 500 THEN '¥200-500'
        ELSE '¥500以上'
    END AS price_tier,
    BITMAP_COUNT(BITMAP_UNION(t.expose_uv)) AS expose_uv,
    BITMAP_COUNT(BITMAP_UNION(t.click_uv)) AS click_uv,
    BITMAP_COUNT(BITMAP_UNION(t.addcart_uv)) AS addcart_uv,
    BITMAP_COUNT(BITMAP_UNION(t.pay_uv)) AS pay_uv,
    ROUND(BITMAP_COUNT(BITMAP_UNION(t.click_uv)) * 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(t.expose_uv)), 0), 2) AS ctr_pct,
    ROUND(BITMAP_COUNT(BITMAP_UNION(t.pay_uv)) * 100.0 / NULLIF(BITMAP_COUNT(BITMAP_UNION(t.click_uv)), 0), 2) AS cvr_pct
FROM app_commodity_stat_spu_di t
LEFT JOIN (
    SELECT tenant_id, spu_id, MIN(min_price) AS min_price
    FROM dim_base_commodity_info_df
    GROUP BY tenant_id, spu_id
) d ON t.tenant_id = d.tenant_id AND t.spu_id = d.spu_id
WHERE t.imp_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY price_tier
ORDER BY price_tier;
```
