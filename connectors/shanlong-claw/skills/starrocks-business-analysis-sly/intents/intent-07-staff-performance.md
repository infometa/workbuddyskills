# 👨‍🍳 分类七：员工绩效

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 谁干得好，服务员、收银员、业务员绩效分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 25: WaiterPerformance — 服务员绩效分析

**触发**：服务员绩效/服务员排名/服务员业绩/服务员创收 + 分析/排名

**业务说明**：分析服务员的服务质量和创收能力，辅助绩效考核和提成计算。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `metric` | Enum | 营收/账单数/客流量 | 排序指标 |
| `top_n` | Integer | 默认20 | 排名数量 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 管理类型过滤 |

**SQL 模板**：
```sql
SELECT
    waiter_name AS 服务员姓名,
    waiter_code AS 工号,
    SUM(busi_income) AS 实收金额,
    COUNT(DISTINCT id) AS 服务账单数,
    SUM(people_qty) AS 服务客流量,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均创收
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
    AND waiter_code IS NOT NULL
    {{#if manage_type}} AND manage_type = '{{manage_type}}'
GROUP BY waiter_code, waiter_name
HAVING SUM(busi_income) > 0
ORDER BY {{metric:实收金额}} DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（序号 / 服务员 / 工号 / 实收金额 / 账单数 / 客流量 / 单均创收）

---

## Intent 26: CashierAnalysis — 收银员绩效分析

**触发**：收银员绩效/收银排名/收银额/收银员业绩 + 分析/排名

**业务说明**：分析收银员的收银效率和差错率，辅助收银员管理和培训。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `metric` | Enum | 营收/账单数 | 排序指标 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    creator_name AS 收银员姓名,
    creator_code AS 收银员工号,
    SUM(busi_income) AS 收银金额,
    COUNT(DISTINCT id) AS 收银笔数,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均收银,
    SUM(cancel_money) AS 作废金额,
    SUM(invalid_bill_money) AS 废单金额
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
    AND creator_code IS NOT NULL
GROUP BY creator_code, creator_name
HAVING SUM(busi_income) > 0
ORDER BY {{metric:收银金额}} DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（序号 / 收银员 / 工号 / 收银金额 / 收银笔数 / 单均收银 / 作废金额）

---

## Intent 27: SalesmanPerformance — 业务员业绩分析

**触发**：业务员业绩/业务员排名/营销活动效果/业务员带来的客流

**业务说明**：分析业务员带来的客流和营收贡献，评估营销活动效果。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `metric` | Enum | 营收/账单数/客流量 | 排序指标 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    COALESCE(salesman_name, '未知') AS 业务员姓名,
    salesman_code AS 业务员工号,
    sale_marketing_type AS 营销类型,
    COUNT(DISTINCT id) AS 带来账单数,
    SUM(people_qty) AS 带来客流量,
    ROUND(SUM(busi_income), 2) AS 带来营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均创收
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND salesman_code IS NOT NULL
GROUP BY salesman_code, salesman_name, sale_marketing_type
HAVING SUM(busi_income) > 0
ORDER BY {{metric:带来营收}} DESC
LIMIT {{top_n:20}};
```

**营销类型效果分析**：
```sql
SELECT
    sale_marketing_type AS 营销类型,
    COUNT(DISTINCT id) AS 账单数,
    SUM(people_qty) AS 客流量,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费,
    ROUND(SUM(people_qty) * 100.0 / SUM(SUM(people_qty)) OVER(), 2) AS 客流贡献
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND sale_marketing_type IS NOT NULL
GROUP BY sale_marketing_type
ORDER BY 总营收 DESC;
```

**输出格式**：排名表格（业务员 / 工号 / 营销类型 / 账单数 / 客流 / 营收）
