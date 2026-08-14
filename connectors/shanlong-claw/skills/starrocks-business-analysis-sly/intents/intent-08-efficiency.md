# ⏱️ 分类八：运营效率

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 快不快、好不好，时段分析、天气影响、出品速度、用餐时长、评分分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 28: TimeSlotAnalysis — 用餐时段分析

**触发**：早市/午市/晚市/宵夜 + 营收/分析

**枚举值**：`table_settle_shift_name`：早市 / 午市 / 晚市 / 宵夜

**SQL 模板**：
```sql
SELECT
    table_settle_shift_name AS 时段,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if time_slot}} AND table_settle_shift_name = :time_slot
GROUP BY table_settle_shift_name
ORDER BY 实收金额 DESC
LIMIT 100;
```

---

## Intent 29: WeatherRevenueAnalysis — 天气营收关联分析

**触发**：天气影响/气温/天气/雨天晴天 + 营收 + 分析

**业务说明**：分析天气状况和气温与营收的关联关系，指导门店运营决策（如备货、人员排班）。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 天气/气温/门店/日期 | 聚合维度 |
| `city` | String | 城市名称 | 城市过滤 |
| `top_n` | Integer | 默认10 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:dayweather}} AS 天气,
    COUNT(DISTINCT settle_biz_date) AS 营业天数,
    SUM(busi_income) AS 总营收,
    COUNT(DISTINCT id) AS 总账单数,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT settle_biz_date), 0), 2) AS 日均营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
    {{#if city}} AND city = '{{city}}'
GROUP BY {{group_by:dayweather}}
ORDER BY 总营收 DESC;
```

**气温分段分析**：
```sql
SELECT
    CASE
        WHEN daytemperature < '10' THEN '低温(<10°C)'
        WHEN daytemperature BETWEEN '10' AND '20' THEN '凉爽(10-20°C)'
        WHEN daytemperature BETWEEN '20' AND '30' THEN '温暖(20-30°C)'
        ELSE '高温(>30°C)'
    END AS 气温区间,
    COUNT(DISTINCT settle_biz_date) AS 营业天数,
    SUM(busi_income) AS 总营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT settle_biz_date), 0), 2) AS 日均营收
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
    AND daytemperature IS NOT NULL
GROUP BY 气温区间
ORDER BY 总营收 DESC;
```

**输出格式**：对比表格 + 柱状图描述（维度 / 营收 / 账单数 / 日均营收）

---

## Intent 30: DishesProductionAnalysis — 出品效率分析

**触发**：出品效率/等待时间/出餐速度/做菜时间 + 分析

**业务说明**：分析后厨出品效率，包括准备时长，制作时长、等待时长，优化流程减少顾客等待。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `metric` | Enum | 平均制作时长/平均等待时长/超时率 | 分析指标 |
| `group_by` | Enum | 门店/品牌/管理类型 | 聚合维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：

*出品时长分析*：
```sql
SELECT
    {{group_by:store_name}} AS 门店,
    COUNT(DISTINCT id) AS 订单数,
    ROUND(AVG(prepare_duration), 2) AS 平均备餐时长,
    ROUND(AVG(make_duration), 2) AS 平均制作时长,
    ROUND(AVG(products_duration), 2) AS 平均出品时长,
    ROUND(AVG(overtime_duration), 2) AS 平均超时时长,
    ROUND(SUM(CASE WHEN overtime_duration > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS 超时订单率
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
    AND make_duration IS NOT NULL
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
HAVING COUNT(DISTINCT id) >= 10
ORDER BY {{metric:平均制作时长}} DESC
LIMIT {{top_n:20}};
```

*效率排名（制作时长越短越好）*：
```sql
SELECT
    {{group_by:store_name}} AS 门店,
    COUNT(DISTINCT id) AS 订单数,
    ROUND(AVG(make_duration), 2) AS 平均制作时长分钟,
    ROUND(AVG(ready_duration), 2) AS 平均等待时长分钟
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date AND settle_biz_date < :end_date_plus_1
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
ORDER BY 平均制作时长分钟 ASC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（门店 / 订单数 / 备餐时长 / 制作时长 / 出品时长 / 超时率%）

---

## Intent 31: DiningDurationAnalysis — 用餐时长分析

**触发**：用餐时长/等位时间/翻台时间/平均用餐时间/用餐效率

**业务说明**：分析不同场景/时段/门店的用餐时长，为翻台优化和人员排班提供数据支持。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/时段/场景/日期 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT id) AS 账单数,
    ROUND(AVG(dinner_time), 0) AS 平均用餐时长分钟,
    ROUND(MIN(dinner_time), 0) AS 最快用餐分钟,
    ROUND(MAX(dinner_time), 0) AS 最长用餐分钟,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费,
    ROUND(SUM(people_qty) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 平均人数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND dinner_time IS NOT NULL
    AND dinner_time > 0
    AND dinner_time < 10000  -- 过滤异常值（最大合理值约166小时）
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
HAVING COUNT(DISTINCT id) >= 50
ORDER BY 平均用餐时长分钟 DESC
LIMIT {{top_n:20}};
```

> ⚠️ **数据异常说明**：`dinner_time` 字段存在异常大值（最大超1000万），SQL 中需添加 `dinner_time < 10000` 过滤条件，确保分析准确性。

**输出格式**：排名表格（维度 / 账单数 / 平均时长 / 最快 / 最慢）

---

## Intent 32: CustomerRatingAnalysis — 顾客评分分析

**触发**：顾客评分/好评率/评分分析/星级分析/顾客满意度

**业务说明**：分析门店顾客评分趋势，识别服务质量变化（需确认评分数据来源）。

**枚举值**：`star`：实际评分值（需查询实际分布）

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/时段/日期 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    COUNT(DISTINCT id) AS 评价数,
    ROUND(AVG(star), 2) AS 平均评分,
    ROUND(SUM(CASE WHEN star >= 16 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 好评率,
    ROUND(SUM(CASE WHEN star >= 18 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 高分率,
    ROUND(SUM(CASE WHEN star < 10 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(DISTINCT id), 0), 2) AS 低分率,
    SUM(star) AS 总评分
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND star IS NOT NULL
    {{#if region}} AND region = :region
GROUP BY {{group_by:store_code}}, {{group_by:store_name}}
HAVING COUNT(DISTINCT id) >= 10
ORDER BY 平均评分 DESC
LIMIT {{top_n:20}};
```

> ⚠️ **评分体系说明**：该集团评分范围为 0-35 分（非标准5分制），阈值需相应调整：
> - 好评：star >= 16（对应约80%）
> - 高分：star >= 18（对应约90%）
> - 低分：star < 10（对应约30%以下）

**输出格式**：排名表格（维度 / 评价数 / 平均评分 / 好评率% / 高分率%）
