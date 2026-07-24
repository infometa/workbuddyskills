# 🏪 分类一：门店画像

> ⚠️ **重要变更（2026-06-30）**：`e000.dt_store` 已重构为 `e000.dt_store_view`，**仅含 4 字段**（`store_code` / `group_code` / `cy_store_code` / `cy_group_code`）。所有门店维度信息（`brand_name` / `area` / `capacity` / `emp_num` / `is_open` / `manage_type` / `region` / `province` / `city` 等）**需从业务表 `dm.v_pos_corp_sale_analysis_with_sly` 获取**（该视图自带这些维度字段）。
>
> 静态基础信息，查询门店列表、地理分布、品牌规模、管理类型、容量规模

---

## Intent 1: StoreListQuery — 门店列表查询

**触发**：查看/列出/找出 + 门店

**输出格式**：明细表格（序号 / 门店名 / 品牌 / 管理类型 / 城市 / 面积 / 是否营业）；超20条时提示"共X家，显示前20条"

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `region` | String | 华北/华东/华南/华中/西北/西南/东北 | 大区 |
| `province` | String | 自由输入 | 省份 |
| `city` | String | 自由输入 | 城市 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 管理类型 |
| `brand_name` | String | 自由输入（当前集团内） | 品牌名 |
| `is_open` | Enum | 是/否 | 是否营业（需通过营业表判断） |

**SQL 模板**：

> 💡 **门店维度字段**（region/brand_name/manage_type 等）从 POS 视图获取，`store_name` 通过 GROUP BY + ANY_VALUE 提取。

```sql
SELECT
    ANY_VALUE(store_name)         AS 门店名称,
    ANY_VALUE(brand_name)         AS 品牌,
    ANY_VALUE(manage_type)        AS 管理类型,
    ANY_VALUE(region)             AS 大区,
    ANY_VALUE(province)           AS 省份,
    ANY_VALUE(city)               AS 城市,
    store_code                    AS 门店编码
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团 G 号）
     AND store_code IN (#{omShopCodes})
AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)  -- 近30天有营业记录
    {{#if region}} AND region = :region
{{#if province}} AND province = :province
{{#if city}} AND city = :city
{{#if manage_type}} AND manage_type = :manage_type
{{#if brand_name}} AND brand_name LIKE CONCAT('%', :brand_name, '%')
GROUP BY store_code
ORDER BY province, city, 门店名称
LIMIT 100;
```

---

## Intent 2: GeoDistribution — 地理分布分析

**触发**：分布/有多少/排名 + [地区/省份/城市] + 门店

**输出格式**：排名表格 + 横向条形图描述（序号 / 区域 / 门店数 / 占比）；Top3加 🥇🥈🥉；合计行加粗

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `geo_level` | Enum | 大区/省份/城市/区县 | 聚合层级 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 可选过滤 |
| `brand_name` | String | 自由输入 | 可选品牌 |
| `top_n` | Integer | 默认10 | 前N名 |

**SQL 模板**：

```sql
SELECT
    {{geo_level:region}} AS 区域,
    COUNT(DISTINCT store_code) AS 门店数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团 G 号）
     AND store_code IN (#{omShopCodes})
AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    {{#if manage_type}} AND manage_type = :manage_type
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY {{geo_level:region}}
ORDER BY 门店数 DESC
LIMIT {{top_n:10}};
```

---

## Intent 3: BrandGroupAnalysis — 品牌规模分析

**触发**：品牌排名/品牌对比 + 分析

**输出格式**：排名表格 + 柱状图描述（序号 / 品牌 / 门店数 / 员工总数 / 平均面积 / 总座位数）；Top3高亮；注明"仅含本集团品牌"

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `metric` | Enum | 门店数/员工总数/平均面积/总容纳人数 | 度量指标 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 可选过滤 |
| `region` | String | 自由输入 | 可选地区 |
| `top_n` | Integer | 默认10 | 前N名 |

> ⚠️ 注意：此处分析的是**当前集团内的品牌**

**SQL 模板**：

```sql
SELECT
    brand_name AS 品牌,
    COUNT(DISTINCT store_code) AS 门店数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团 G 号）
    AND store_code IN (#{omShopCodes})
    AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    {{#if manage_type}} AND manage_type = :manage_type
{{#if region}} AND region = :region
GROUP BY brand_name
ORDER BY 门店数 DESC
LIMIT {{top_n:10}};
```

> 💡 **说明**：员工数（`emp_num`）、面积（`area`）、容纳人数（`capacity`）等字段不在 POS 视图中暴露，如需这些指标需从其他数据源补充。本 Intent 当前仅提供门店数维度。

---

## Intent 4: ManageTypeAnalysis — 管理类型分析

**触发**：管理类型/直营加盟 + 分析/占比/对比

**输出格式**：饼图描述 + 汇总表格（管理类型 / 门店数 / 占比%）；按占比降序；明确标注直营/加盟各自数量与比例

**Slots**：

| Slot | 类型 | 说明 |
|------|------|------|
| `region` | String | 可选地区过滤 |
| `brand_name` | String | 可选品牌过滤 |
| `show_ratio` | Boolean | 是否显示占比，默认true |

**SQL 模板**：

```sql
SELECT
    manage_type AS 管理类型,
    COUNT(DISTINCT store_code) AS 门店数,
    ROUND(COUNT(DISTINCT store_code) * 100.0 / SUM(COUNT(DISTINCT store_code)) OVER(), 2) AS 占比
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID
    AND store_code IN (#{omShopCodes})
    AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    {{#if region}} AND region = :region
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY manage_type
ORDER BY 门店数 DESC;
```

---

## Intent 5: StoreCapacityRanking — 门店规模排名

> ⚠️ **暂不支持**：`e000.dt_store_view` 已不含 `area` / `capacity` / `emp_num` 字段，POS 视图也不含这些字段。如需门店规模分析，请联系数据团队补充供应链或人力系统数据源。

**触发**：规模最大/员工最多/面积最大 + 门店

**输出格式**：排名表格（序号 / 门店名 / 城市 / 规模值 / 单位）；注明规模指标名称（㎡/个/人）

**当前建议处理**：
- 转 Level 4：明确告知"门店规模（面积/座位/员工数）数据当前不在已知的 7 张业务表内，暂不支持"
- 引导用户：可基于营收/客流等业务表数据做"营业额排名"替代
