# 📊 分类九：多维对比

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 交叉、趋势、对比，环比同比、跨维度、直营加盟、区域品牌、桌区分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 33: MoMAnalysis — 环比分析

**触发**：环比/上月对比/本月vs上月

**输出格式**：双列对比表格（维度 / 本期实收 / 上期实收 / 增减金额 / 环比增长率%）；增长用 🔴+X%，下降用 🟢-X%（中国惯例：红涨绿跌）

**SQL 模板**：
```sql
WITH current_period AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 本期实收,
        SUM(bill_count) AS 本期账单
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = '{{current_month}}'
    GROUP BY {{granularity:store_name}}
),
previous_period AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 上期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = DATE_FORMAT(DATE_SUB('{{current_month}}-01', INTERVAL 1 MONTH), '%Y-%m')
    GROUP BY {{granularity:store_name}}
)
SELECT
    COALESCE(c.维度, p.维度) AS 维度,
    c.本期实收,
    p.上期实收,
    ROUND((c.本期实收 - p.上期实收) / NULLIF(p.上期实收, 0) * 100, 2) AS 环比增长率
FROM current_period c
FULL OUTER JOIN previous_period p ON c.维度 = p.维度
ORDER BY c.本期实收 DESC
LIMIT 20;
```

---

## Intent 34: YoYAnalysis — 同比分析

**触发**：同比/去年同期/今年vs去年

**输出格式**：双列对比表格（维度 / 本期实收 / 去年同期实收 / 增减金额 / 同比增长率%）；增长用 🔴+X%，下降用 🟢-X%

**SQL 模板**：
```sql
WITH current_year AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 本期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = '{{current_month}}'
    GROUP BY {{granularity:store_name}}
),
previous_year AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 去年同期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = DATE_FORMAT(DATE_SUB('{{current_month}}-01', INTERVAL 1 YEAR), '%Y-%m')
    GROUP BY {{granularity:store_name}}
)
SELECT
    COALESCE(c.维度, p.维度) AS 维度,
    c.本期实收,
    p.去年同期实收,
    ROUND((c.本期实收 - p.去年同期实收) / NULLIF(p.去年同期实收, 0) * 100, 2) AS 同比增长率
FROM current_year c
FULL OUTER JOIN previous_year p ON c.维度 = p.维度
ORDER BY c.本期实收 DESC
LIMIT 20;
```

---

## Intent 35: ComprehensiveAnalysis — 综合对比

**触发**：本月vs上月vs去年同期/综合对比

**输出格式**：三列对比表格（维度 / 本期 / 上月[环比%] / 去年同期[同比%]）；三期并排

**SQL 模板**：
```sql
WITH current_period AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 本期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = '{{current_month}}'
    GROUP BY {{granularity:store_name}}
),
previous_month AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 上期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = DATE_FORMAT(DATE_SUB('{{current_month}}-01', INTERVAL 1 MONTH), '%Y-%m')
    GROUP BY {{granularity:store_name}}
),
same_month_last_year AS (
    SELECT
        {{granularity:store_name}} AS 维度,
        SUM(real_income) AS 去年同期实收
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND DATE_FORMAT(settle_biz_date, '%Y-%m') = DATE_FORMAT(DATE_SUB('{{current_month}}-01', INTERVAL 1 YEAR), '%Y-%m')
    GROUP BY {{granularity:store_name}}
)
SELECT
    COALESCE(c.维度, p.维度, s.维度) AS 维度,
    c.本期实收,
    p.上期实收,
    s.去年同期实收,
    ROUND((c.本期实收 - p.上期实收) / NULLIF(p.上期实收, 0) * 100, 2) AS 环比,
    ROUND((c.本期实收 - s.去年同期实收) / NULLIF(s.去年同期实收, 0) * 100, 2) AS 同比
FROM current_period c
FULL OUTER JOIN previous_month p ON c.维度 = p.维度
FULL OUTER JOIN same_month_last_year s ON c.维度 = s.维度
ORDER BY c.本期实收 DESC
LIMIT 20;
```

---

## Intent 36: MultiDimensionAnalysis — 多维度汇总分析

**触发**：按区域+品牌/按省份+城市 + 汇总

**输出格式**：交叉二维表格（维度1 / 维度2 / 营业额 / 实收金额 / 账单量 / 单均消费）

**SQL 模板**：
```sql
SELECT
    {{dim1:region}} AS 维度1,
    {{dim2:brand_name}} AS 维度2,
    SUM(recv_money) AS 营业应收,
    SUM(busi_income) AS 实收金额,
    SUM(bill_count) AS 账单量,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY {{dim1:region}}, {{dim2:brand_name}}
ORDER BY {{metric:实收金额}} DESC
LIMIT {{top_n:20}};
```

---

## Intent 37: ManageTypeRevenueComparison — 管理类型营收对比

**触发**：直营vs加盟/直营店vs加盟店 + 营收对比/单均消费对比

**输出格式**：管理类型对比表格（管理类型 / 门店数 / 实收金额 / 账单量 / 单均消费 / 单店平均营收）；直营 vs 加盟高亮对比

**SQL 模板**：
```sql
SELECT
    t.manage_type AS 管理类型,
    COUNT(DISTINCT t.store_code) AS 门店数,
    SUM(t.busi_income) AS 实收金额,
    SUM(t.bill_count) AS 账单量,
    ROUND(SUM(t.busi_income) / NULLIF(SUM(t.bill_count), 0), 2) AS 单均消费,
    ROUND(SUM(t.busi_income) / NULLIF(COUNT(DISTINCT t.store_code), 0), 2) AS 单店平均营收
FROM dm.v_pos_corp_sale_analysis_with_sly t
WHERE t.group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND t.settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND t.settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND t.region = :region
{{#if brand_name}} AND t.brand_name = :brand_name
GROUP BY t.manage_type
ORDER BY {{metric:实收金额}} DESC
LIMIT 100;
```

---

## Intent 38: RegionBrandCrossAnalysis — 区域品牌交叉分析

**触发**：按区域+品牌 + 含小计/汇总

**输出格式**：层级树形表格（区域为父级 / 品牌为子级 / 小计 / 合计）；小计/合计行加粗

> ⚠️ **注意**：`GROUP BY ... WITH ROLLUP` 是 MySQL 语法，StarRocks 不支持。使用三个 UNION ALL 段落实现。

**SQL 模板**：
```sql
-- 区域×品牌 明细
SELECT
    region AS 区域,
    brand_name AS 品牌,
    SUM(busi_income) AS 营业额,
    SUM(real_income) AS 实收金额,
    SUM(bill_count) AS 账单量
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY region, brand_name

UNION ALL

-- 区域小计
SELECT
    region AS 区域,
    '小计' AS 品牌,
    SUM(busi_income) AS 营业额,
    SUM(real_income) AS 实收金额,
    SUM(bill_count) AS 账单量
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY region

UNION ALL

-- 合计
SELECT
    '合计' AS 区域,
    '' AS 品牌,
    SUM(busi_income) AS 营业额,
    SUM(real_income) AS 实收金额,
    SUM(bill_count) AS 账单量
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）

ORDER BY 区域, 品牌, 实收金额 DESC
LIMIT 100;
```

---

## Intent 39: ProvinceRankingWithRatio — 省份排名含占比

**触发**：省份营收排名/省份占比/各省排名

**输出格式**：排名表格（排名 / 省份 / 实收金额 / 占比%）；Top3高亮；占比用进度条式描述

**SQL 模板**：
```sql
WITH total AS (
    SELECT SUM(real_income) AS 总计
    FROM dm.v_pos_corp_sale_analysis_with_sly
    WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
      AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
)
SELECT
    province AS 省份,
    SUM(real_income) AS 实收金额,
    ROUND(SUM(real_income) / NULLIF(t.总计, 0) * 100, 2) AS 占比,
    RANK() OVER (ORDER BY SUM(real_income) DESC) AS 排名
FROM dm.v_pos_corp_sale_analysis_with_sly
CROSS JOIN total t
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
GROUP BY province, t.总计
ORDER BY 排名
LIMIT {{top_n:10}};
```

---

## Intent 40: StoreMetricsSummary — 门店经营指标汇总

**触发**：经营指标/营业情况/门店指标/今天营业怎么样/看看经营

**识别关键词**：
- "营业情况"、"营业数据"
- "经营指标"、"经营数据"
- "门店指标"
- "今天/昨天/本周/本月营业怎么样"
- "看看经营"（不加任何限定词）

**输出格式**：
- **核心指标卡片**（4个）：账单数、客流量、营业额（应收）、单均消费
- **完整指标表格**（17个）：含开台率、翻台率、坪效、人效等

### 经营指标说明

| 指标 | 计算口径 | 单位 |
|------|----------|------|
| 单均消费 | 全量 `recv_money` ÷ 全量 `bill_count` | 元/单 |
| 桌均消费 | 堂食 `recv_money` ÷ 堂食 `open_table_count` | 元/桌 |
| 人均消费 | 堂食 `recv_money` ÷ 堂食 `people_qty` | 元/人 |
| 开台率 | 总开台数 ÷ Σ(桌数 × 市别数) | % |
| 翻台率 | 开台率 - 1（若<0则显示0） | % |
| 坪效 | `real_income` ÷ area | 元/㎡ |
| 人效 | `real_income` ÷ emp_num | 元/人 |

### SQL 模板（基础版）

```sql
SELECT
    SUM(bill_count) AS 账单数,
    SUM(open_table_count) AS 开台数,
    SUM(people_qty) AS 客流量,
    ROUND(SUM(recv_money), 2) AS 营业应收,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(real_income), 2) AS 纯收金额,
    ROUND(SUM(recv_money) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费,
    ROUND(SUM(service_free), 2) AS 服务费,
    ROUND(SUM(disc_money_total), 2) AS 优惠总金额
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if brand_name}} AND brand_name = :brand_name
{{#if store_name}} AND store_name LIKE CONCAT('%', :store_name, '%')
LIMIT 10;
```

---

## Intent 41: TableAreaAnalysis — 桌区运营分析

**触发**：桌区营收/包间翻台/大厅效率/卡座分析/区域分析

**业务说明**：分析不同桌区（大厅/包间/卡座等）的营收和翻台效率，指导座位配置优化。

**枚举值**：`table_area_name`：大厅 / 包间 / 卡座 / 散座 / 其他（实际值需查询）

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 桌区/门店/品牌 | 聚合维度 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `region` | String | 大区名称 | 区域过滤 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:table_area_name}} AS 桌区,
    COUNT(DISTINCT id) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    SUM(open_table_count) AS 开台数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(busi_income) / NULLIF(SUM(open_table_count), 0), 2) AS 台均营收,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT id), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND table_area_name IS NOT NULL
    {{#if region}} AND region = :region
GROUP BY {{group_by:table_area_name}}
ORDER BY 实收金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（桌区 / 账单数 / 开台数 / 实收金额 / 台均营收）
