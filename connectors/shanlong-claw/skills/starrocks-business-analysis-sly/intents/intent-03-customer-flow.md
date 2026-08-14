# 👥 分类三：客流与客群

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 人从哪来、多少人，客流来源、用餐场景、翻台率、续单率分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 10: SaleTypeAnalysis — 销售渠道分析

**触发**：外卖/堂食/外带/自提 + 分析/占比/对比

> ⚠️ **与 Intent 12 的区分**：
> - **Intent 10（sale_type）**：用户在**哪里吃**？→ 堂食 / 外卖 / 外带 / 自提
> - **Intent 12（order_source）**：用户**从哪里来**？→ 微信 / 自来客 / 支付宝 / 美团外卖

**输出格式**：占比表格 + 饼图描述（渠道名 / 账单数 / 实收金额 / 营收占比%）；按金额降序；突出最大渠道

**枚举值**：`sale_type_name`：堂食 / 外卖 / 外带 / 自提

**SQL 模板**：
```sql
SELECT
    sale_type_name AS 销售渠道,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) * 100.0 / SUM(SUM(busi_income)) OVER(), 2) AS 营收占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY sale_type_name
ORDER BY 实收金额 DESC
LIMIT 100;
```

---

## Intent 11: DiningTypeAnalysis — 用餐场景分析

**触发**：亲友聚餐/商务宴请/婚宴/家庭就餐 + 分析

**输出格式**：占比表格 + 饼图描述（场景名 / 账单数 / 实收金额 / 平均人数 / 单均消费）；按实收金额降序；突出高消费场景

**枚举值**：`dining_type_name`：普通就餐 / 亲友聚餐 / 商务宴请 / 婚宴 / 家庭就餐 / 情侣就餐 / 休闲聚餐

**SQL 模板**：
```sql
SELECT
    dining_type_name AS 用餐场景,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(people_qty) / NULLIF(SUM(bill_count), 0), 2) AS 平均人数,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if dining_type}} AND dining_type_name = :dining_type
GROUP BY dining_type_name
ORDER BY 实收金额 DESC
LIMIT 15;
```

---

## Intent 12: OrderSourceAnalysis — 订单来源分析

**触发**：订单来源/自来客/微信/支付宝/美团外卖 + 占比

> ⚠️ **与 Intent 10 的区分**：
> - "美团外卖" → Intent 12（order_source）
> - "点外卖" → Intent 10（sale_type = 外卖）
> - "扫码点餐"（微信来源）→ Intent 12

**枚举值**：`order_source_name`：自来客 / 微信 / 支付宝 / 美团外卖 / 天财线下Pos

**SQL 模板**：
```sql
SELECT
    order_source_name AS 订单来源,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(real_income), 2) AS 实收金额,
    ROUND(SUM(bill_count) * 100.0 / SUM(SUM(bill_count)) OVER(), 2) AS 占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY order_source_name
ORDER BY 账单数 DESC
LIMIT 100;
```

---

## Intent 13: CustomerAnalysis — 客群与人数分析

**触发**：客单价/人均消费/用餐人数/翻台率/桌均消费

> ⚠️ **与 Intent 24 的区分**：
> - **Intent 13**：用户**明确问了某个指标** → 深入分析该维度
> - **Intent 24**：用户**没有明确指标**，"看看经营情况" → 一次性展示所有 17 个指标

**SQL 模板**：
```sql
SELECT
    {{granularity:store_name}} AS 维度,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费,
    ROUND(AVG(people_qty), 2) AS 平均用餐人数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if manage_type}} AND manage_type = :manage_type
GROUP BY {{granularity:store_name}}
HAVING SUM(bill_count) >= 100
ORDER BY 单均消费 DESC
LIMIT 20;
```

---

## Intent 14: RenewalAnalysis — 续单率分析

**触发**：续单率/回头客/翻台分析/续单分析/二次消费

**业务说明**：分析同一顾客的续单情况，评估门店顾客留存能力和翻台效率。

**枚举值**：`is_renew`：续单 / 非续单

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/时段/场景 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT id) AS 总账单数,
    COUNT(DISTINCT CASE WHEN is_renew = '续单' THEN id END) AS 续单账单,
    COUNT(DISTINCT CASE WHEN is_renew != '续单' THEN id END) AS 首单账单,
    ROUND(COUNT(DISTINCT CASE WHEN is_renew = '续单' THEN id END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 续单率,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND(SUM(CASE WHEN is_renew = '续单' THEN busi_income ELSE 0 END), 2) AS 续单营收,
    ROUND(SUM(CASE WHEN is_renew != '续单' THEN busi_income ELSE 0 END), 2) AS 首单营收
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
HAVING COUNT(DISTINCT id) >= 50
ORDER BY 续单率 DESC
LIMIT {{top_n:20}};
```

**时段续单分析**：
```sql
SELECT
    table_settle_shift_name AS 时段,
    COUNT(DISTINCT id) AS 总账单数,
    COUNT(DISTINCT CASE WHEN is_renew = '续单' THEN id END) AS 续单账单,
    ROUND(COUNT(DISTINCT CASE WHEN is_renew = '续单' THEN id END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 续单率,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY table_settle_shift_name
ORDER BY 续单率 DESC;
```

**输出格式**：排名表格（维度 / 总账单 / 续单率% / 续单营收 / 首单营收）
