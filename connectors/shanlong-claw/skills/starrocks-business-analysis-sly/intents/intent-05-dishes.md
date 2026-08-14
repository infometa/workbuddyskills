# 🍽️ 分类五：菜品与套餐

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 卖什么、点什么，套餐、会员、退菜分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 20: PackageAnalysis — 套餐消费分析

**触发**：套餐分析/套餐占比/含套餐门店/套餐销售/套餐搭配

**业务说明**：分析含套餐与散单的营收差异，帮助了解套餐销售贡献和搭配偏好。

**枚举值**：`exist_package`：含有套餐 / 不含有套餐

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/管理类型/时段 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `city` | String | 城市名称 | 城市过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    SUM(bill_count) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费,
    ROUND(SUM(busi_income) / NULLIF(SUM(people_qty), 0), 2) AS 人均消费,
    CASE exist_package
        WHEN '含有套餐' THEN '含套餐'
        ELSE '散单'
    END AS 套餐类型
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
GROUP BY {{group_by:store_code}}, {{group_by:store_name}},
    CASE exist_package WHEN '含有套餐' THEN '含套餐' ELSE '散单' END
ORDER BY 实收金额 DESC
LIMIT {{top_n:20}};
```

**套餐占比分析**：
```sql
SELECT
    CASE exist_package
        WHEN '含有套餐' THEN '含套餐'
        ELSE '散单'
    END AS 套餐类型,
    COUNT(DISTINCT id) AS 账单数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) * 100.0 / SUM(SUM(busi_income)) OVER(), 2) AS 营收占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY CASE exist_package WHEN '含有套餐' THEN '含套餐' ELSE '散单' END
ORDER BY 实收金额 DESC;
```

**输出格式**：占比表格（套餐类型 / 账单数 / 实收金额 / 营收占比%）

---

## Intent 21: MemberConsumptionAnalysis — 会员消费分析

**触发**：会员消费/会员占比/会员转化/非会员分析/会员粘性

**业务说明**：区分会员与非会员消费，分析会员粘性、消费能力和转化率。

**枚举值**：`is_member_bill`：会员消费账单 / 非会员消费账单

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
    COUNT(DISTINCT id) AS 总账单,
    COUNT(DISTINCT CASE WHEN is_member_bill = '会员消费账单' THEN id END) AS 会员账单,
    COUNT(DISTINCT CASE WHEN is_member_bill != '会员消费账单' THEN id END) AS 非会员账单,
    ROUND(COUNT(DISTINCT CASE WHEN is_member_bill = '会员消费账单' THEN id END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 会员占比,
    ROUND(SUM(CASE WHEN is_member_bill = '会员消费账单' THEN busi_income ELSE 0 END), 2) AS 会员营收,
    ROUND(SUM(CASE WHEN is_member_bill != '会员消费账单' THEN busi_income ELSE 0 END), 2) AS 非会员营收,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND(SUM(CASE WHEN is_member_bill = '会员消费账单' THEN busi_income ELSE 0 END) * 100.0 / NULLIF(SUM(busi_income), 0), 2) AS 会员营收占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 会员营收 DESC
LIMIT {{top_n:20}};
```

**会员单均分析**：
```sql
SELECT
    CASE WHEN is_member_bill = '会员消费账单' THEN '会员' ELSE '非会员' END AS 客群,
    COUNT(DISTINCT id) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费,
    ROUND(SUM(busi_income) / NULLIF(SUM(people_qty), 0), 2) AS 人均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY CASE WHEN is_member_bill = '会员消费账单' THEN '会员' ELSE '非会员' END
ORDER BY 总营收 DESC;
```

**输出格式**：对比表格（维度 / 会员账单 / 会员占比% / 会员营收 / 会员营收占比%）

---

## Intent 22: ReturnDishAnalysis — 退菜分析

**触发**：退菜分析/退货率/退菜原因/退菜门店/退菜金额

**业务说明**：分析退菜高频门店和品项，识别潜在质量问题或服务问题。

**字段说明**：
- `return_real_income_negative`：退菜负金额（退款）
- `return_real_income_positive`：退菜正金额
- `return_count`：退菜数量
- `return_bills`：退货账单数

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/管理类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT id) AS 总账单数,
    SUM(return_bills) AS 退菜账单数,
    ROUND(SUM(return_bills) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 退菜账单率,
    ROUND(SUM(ABS(return_real_income_negative) + return_real_income_positive), 2) AS 退菜总金额,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND((SUM(ABS(return_real_income_negative) + return_real_income_positive)) * 100.0 / NULLIF(SUM(busi_income), 0), 2) AS 退菜金额占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
HAVING SUM(return_bills) > 0
ORDER BY 退菜总金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（维度 / 总账单 / 退菜账单 / 退菜账单率% / 退菜金额）
