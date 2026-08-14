# 📱 分类六：渠道与来源

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 线上还是线下，小程序、订单类型、预点单分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 23: AppletChannelAnalysis — 小程序渠道分析

**触发**：小程序订单/扫码点餐/小程序营收占比/线上渠道/小程序分析

**业务说明**：区分POS下单与小程序下单，分析线上渠道对营收的贡献占比。

**枚举值**：`is_applet_bill`：小程序账单 / 非小程序账单

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/管理类型/日期 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT CASE WHEN is_applet_bill = '小程序账单' THEN id END) AS 小程序账单,
    COUNT(DISTINCT CASE WHEN is_applet_bill != '小程序账单' THEN id END) AS POS账单,
    COUNT(DISTINCT id) AS 总账单数,
    ROUND(SUM(CASE WHEN is_applet_bill = '小程序账单' THEN busi_income ELSE 0 END), 2) AS 小程序营收,
    ROUND(SUM(CASE WHEN is_applet_bill != '小程序账单' THEN busi_income ELSE 0 END), 2) AS POS营收,
    ROUND(SUM(busi_income), 2) AS 总营收,
    ROUND(SUM(CASE WHEN is_applet_bill = '小程序账单' THEN busi_income ELSE 0 END) * 100.0 / NULLIF(SUM(busi_income), 0), 2) AS 小程序占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 总营收 DESC
LIMIT {{top_n:20}};
```

**渠道对比趋势**：
```sql
SELECT
    DATE_FORMAT(settle_biz_date, '%Y-%m-%d') AS 日期,
    COUNT(DISTINCT CASE WHEN is_applet_bill = '小程序账单' THEN id END) AS 小程序账单,
    COUNT(DISTINCT CASE WHEN is_applet_bill != '小程序账单' THEN id END) AS POS账单,
    ROUND(SUM(CASE WHEN is_applet_bill = '小程序账单' THEN busi_income ELSE 0 END), 2) AS 小程序营收,
    ROUND(SUM(CASE WHEN is_applet_bill != '小程序账单' THEN busi_income ELSE 0 END), 2) AS POS营收
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
GROUP BY DATE_FORMAT(settle_biz_date, '%Y-%m-%d')
ORDER BY 日期
LIMIT 30;
```

**输出格式**：对比表格（维度 / 小程序账单 / POS账单 / 小程序营收 / 占比%）

---

## Intent 24: OrderTypeAnalysis — 订单类型分析

**触发**：订单类型/外卖配送费/堂食vs外卖/订单类型占比/外送分析

**业务说明**：分析不同订单类型（线上/线下/外送等）的营收和成本结构。

**枚举值**：`order_type_name`：线上 / 线下 / 外送 / 自提 / 其他（实际值需查询）

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/订单类型 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:order_type_name}} AS 订单类型,
    COUNT(DISTINCT id) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(deliver_fee), 2) AS 配送费总额,
    ROUND(SUM(deliver_fee) * 100.0 / NULLIF(SUM(busi_income), 0), 2) AS 配送费占比,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND order_type_name IS NOT NULL
    {{#if region}} AND region = :region
GROUP BY {{group_by:order_type_name}}
ORDER BY 实收金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：占比表格（订单类型 / 账单数 / 实收金额 / 配送费 / 配送费占比%）
