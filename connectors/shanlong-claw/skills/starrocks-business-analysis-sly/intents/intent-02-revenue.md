# 💰 分类二：营收分析

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 收入核心指标，营收趋势、门店排名、品项原价、坪效

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 6: RevenueTrendAnalysis — 营收趋势分析

**触发**：营收趋势/销售额趋势/每天营收/月度营收

**输出格式**：折线图描述 + 时序数据表（时间点 / 营业额 / 实收金额 / 纯收金额 / 账单数 / 单均消费）；标注最高/最低时间点；含对比模式时加增长率列

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | **必填** |
| `granularity` | Enum | 日/周/月/年 | 时间粒度，默认月 |
| `region` | String | 自由输入 | 可选地区 |
| `city` | String | 自由输入 | 可选城市 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 可选管理类型 |
| `brand_name` | String | 自由输入 | 可选品牌 |
| `compare_mode` | Enum | 无/同比/环比 | 对比模式 |

**SQL 模板**：
```sql
SELECT
    DATE_FORMAT(settle_biz_date, '%Y-%m') AS 月份,
    ROUND(SUM(recv_money), 2) AS 营业应收,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(real_income), 2) AS 纯收金额,
    SUM(bill_count) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if manage_type}} AND manage_type = :manage_type
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY DATE_FORMAT(settle_biz_date, '%Y-%m')
ORDER BY 月份
LIMIT 100;
```

---

## Intent 7: StoreRevenueRanking — 门店营收排名

**触发**：门店营收排名/最赚钱的门店/营收最高

**输出格式**：排名表格（序号 / 门店名 / 城市 / 管理类型 / 实收金额 / 账单数 / 单均消费）；Top3加 ⭐ 标注；超20条提示分页

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `date_range` | DateRange | **必填** | 日期范围 |
| `metric` | Enum | 实收金额/营业金额/账单数/单均消费 | 排名指标 |
| `region` | String | 自由输入 | 可选地区 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 可选管理类型 |
| `top_n` | Integer | 默认20 | 前N名 |

**SQL 模板**：
```sql
SELECT
    store_name AS 门店名称,
    city AS 城市,
    manage_type AS 管理类型,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    SUM(bill_count) AS 账单数,
    SUM(people_qty) AS 用餐人数,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if manage_type}} AND manage_type = :manage_type
GROUP BY store_code, store_name, city, manage_type
ORDER BY {{metric:实收金额}} DESC
LIMIT {{top_n:20}};
```

---

## Intent 8: ItemSalesAnalysis — 品项消费分析

**触发**：品项消费/菜品销售/原价分析

**品项字段说明**：

| 字段 | 含义 |
|------|------|
| `item_orig_money` | 品项原价（理论销售额） |
| `recv_money` | 营业应收 |
| `real_income` | 纯收金额 |
| 折扣率 | (品项原价 - 实收) / 品项原价 × 100% |

**SQL 模板**：
```sql
SELECT
    store_name AS 门店名称,
    city AS 城市,
    brand_name AS 品牌,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(item_orig_money), 2) AS 品项原价,
    ROUND(SUM(recv_money), 2) AS 营业应收,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND((SUM(item_orig_money) - SUM(busi_income)) / NULLIF(SUM(item_orig_money), 0) * 100, 2) AS 折扣率,
    ROUND(SUM(busi_income) / NULLIF(SUM(bill_count), 0), 2) AS 单均消费
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY store_code, store_name, city, brand_name
ORDER BY 营业应收 DESC
LIMIT 100;
```

---

## Intent 9: EfficiencyAnalysis — 门店效能分析

> ⚠️ **变更说明（2026-06-30）**：`e000.dt_store_view` 已不暴露 `area`（面积）字段，POS 视图也不含面积数据。原"坪效"分析需 JOIN dt_store 旧表的 `area` 字段，**当前暂不支持**。

**触发**：坪效/日均营业额/效能分析

**输出格式**：排名表格 + KPI摘要（序号 / 门店 / 总实收 / 营业天数 / 日均营业额）

**降级方案**：仅提供"日均营业额"维度（坪效需等数据源补充）：

```sql
SELECT
    store_name AS 门店,
    city AS 城市,
    brand_name AS 品牌,
    SUM(busi_income) AS 总实收,
    SUM(bill_count) AS 总账单,
    COUNT(DISTINCT settle_biz_date) AS 营业天数,
    ROUND(SUM(busi_income) / NULLIF(COUNT(DISTINCT settle_biz_date), 0), 2) AS 日均营业额
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
     AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY store_code, store_name, city, brand_name
ORDER BY {{metric:日均营业额}} DESC
LIMIT {{top_n:20}};
```

> 💡 **坪效字段恢复建议**：联系数据团队将 `area` 字段加入 `dm.v_pos_corp_sale_analysis_with_sly` 视图或 `e000.dt_store_view` 视图。
