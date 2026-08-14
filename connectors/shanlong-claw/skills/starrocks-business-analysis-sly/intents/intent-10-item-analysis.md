# 🍽️ 分类十：菜品明细分析

基于 `dm.v_item_sale_analysis_with_sly` 表（2.7亿+ 条菜品明细）

> 卖什么菜、卖多少、赚多少、退多少、怎么卖的

> ⚠️ 菜品表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`
> 4. 分析粒度：品项 × 规格（`item_standard_name`）× 单位（`item_unit_name`），**不是账单粒度**

### 核心字段说明

#### 品项维度字段

| 字段 | 说明 |
|------|------|
| `id` | 品项行**主键**（UUID，非账单号，**不可用于账单去重**） |
| `item_id` | 菜品 ID |
| `item_name` | 菜品名称 |
| `item_standard_id` | 菜品规格 ID |
| `item_standard_name` | 菜品规格名称（如：普通装、大份） |
| `item_unit_name` | 菜品单位（如：张、份、个） |
| `big_class_name` | 大类名称 |
| `small_class_name` | 小类名称 |
| `setmeal_name` | 所属套餐名称（`meal_flg`=套餐明细时有值） |
| `meal_flg` | 品项类型：普通品项 / 套餐明细 |

#### 金额字段

| 字段 | 说明 |
|------|------|
| `income_money` | 品项**纯收**金额（折后实收） |
| `actual_money` | 品项**实收**金额 |
| `pre_discount_price` | 品项**应收**金额（折前原价） |
| `cost_money` | 品项**理论成本** |
| `last_qty` | 品项实售数量（已扣退菜） |
| `return_qty` | 退菜数量 |
| `return_subtotal` | 退菜金额 |
| `present_qty` | 赠送数量 |
| `present_money` | 赠送金额 |

#### 渠道/场景字段

| 字段 | 说明 |
|------|------|
| `sale_type_name` | 销售渠道（堂食/外卖等） |
| `is_applet_bill` | 是否小程序下单 |
| `is_member_bill` | 是否会员账单 |

### 毛利计算公式

| 指标 | 公式 | 说明 |
|------|------|------|
| **折前理论毛利** | `pre_discount_price - cost_money` | 按原价计算 |
| **折后理论毛利** | `income_money - cost_money` | 按实收计算 |
| **折前毛利率** | `(pre_discount_price - cost_money) / pre_discount_price` | |
| **折后毛利率** | `(income_money - cost_money) / income_money` | |

> ⚠️ 用户问毛利相关问题时，**必须同时展示折前和折后**两组指标。

---

## Intent 42: ItemSalesRanking — 菜品销售排行与区域分布

**触发**：菜品排行/最畅销的菜/销量TOP/哪道菜卖得最好/菜品营收排名/热销品项/小类排行/大类排行/省份分布/城市分布/各省营收/各城市营收/菜品区域分布/品项销售门店明细/各门店菜品明细

**业务说明**：按销量或营收对菜品进行排名，支持按品项/小类/大类/省份/城市五种维度分组汇总，默认品项层。区域分组可快速了解菜品在不同地域的销售表现。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 品项/小类/大类/省份/城市/门店 | 分组维度，默认品项 |
| `rank_by` | Enum | 营收/数量 | 排名依据，默认营收 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `small_class_name` | String | - | 小类过滤（可选） |
| `province` | String | - | 省份过滤（可选） |
| `meal_flg` | Enum | 普通品项/套餐明细/全部 | 品项类型过滤，默认全部 |
| `top_n` | Integer | 默认20 | 排名数量 |

**统一 SQL 模板**：

```sql
SELECT
    {{#if group_by_eq '品项'}}
        item_name AS 菜品名称,
        small_class_name AS 小类,
        big_class_name AS 大类,
        COUNT(DISTINCT item_id) AS 品项数,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(pre_discount_price), 2) AS 应收金额,
        ROUND(SUM(actual_money), 2) AS 实收金额,
        ROUND(SUM(income_money), 2) AS 纯收金额,
{{#if group_by_eq '小类'}}
        small_class_name AS 小类名称,
        big_class_name AS 大类,
        COUNT(DISTINCT item_id) AS 品项数,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(pre_discount_price), 2) AS 应收金额,
        ROUND(SUM(actual_money), 2) AS 实收金额,
        ROUND(SUM(income_money), 2) AS 纯收金额,
{{#if group_by_eq '大类'}}
        big_class_name AS 大类名称,
        COUNT(DISTINCT item_id) AS 品项数,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(pre_discount_price), 2) AS 应收金额,
        ROUND(SUM(actual_money), 2) AS 实收金额,
        ROUND(SUM(income_money), 2) AS 纯收金额,
{{#if group_by_eq '省份'}}
        province AS 省份,
        COUNT(DISTINCT item_id) AS 品项数,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(pre_discount_price), 2) AS 应收金额,
        ROUND(SUM(actual_money), 2) AS 实收金额,
        ROUND(SUM(income_money), 2) AS 纯收金额,
{{#if group_by_eq '城市'}}
        province AS 省份,
        city AS 城市,
        COUNT(DISTINCT item_id) AS 品项数,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(pre_discount_price), 2) AS 应收金额,
        ROUND(SUM(actual_money), 2) AS 实收金额,
        ROUND(SUM(income_money), 2) AS 纯收金额,
{{#if group_by_eq '门店'}}
        store_name AS 门店名称,
        item_name AS 菜品名称,
        small_class_name AS 小类,
        big_class_name AS 大类,
        ROUND(SUM(pre_discount_price), 2) AS 品项应收,
        ROUND(SUM(last_qty), 2) AS 销售数量,
        ROUND(SUM(actual_money), 2) AS 品项实收,
        ROUND(SUM(income_money), 2) AS 品项纯收,
        ROUND(SUM(present_money), 2) AS 赠送金额,
        ROUND(SUM(present_qty), 2) AS 赠送数量,
        ROUND(SUM(return_subtotal), 2) AS 退菜金额,
        ROUND(SUM(return_qty), 2) AS 退菜数量,
        ROUND(SUM(cost_money), 2) AS 理论成本,
        ROUND(SUM(pre_discount_price) - SUM(cost_money), 2) AS 折前理论毛利,
        ROUND((SUM(pre_discount_price) - SUM(cost_money)) * 100.0 / NULLIF(SUM(pre_discount_price), 0), 2) AS 折前毛利率,
        ROUND(SUM(income_money) - SUM(cost_money), 2) AS 折后理论毛利,
        ROUND((SUM(income_money) - SUM(cost_money)) * 100.0 / NULLIF(SUM(income_money), 0), 2) AS 折后毛利率,
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
        AND store_code IN (#{omShopCodes})
{{#if big_class_name}} AND big_class_name = :big_class_name
{{#if small_class_name}} AND small_class_name = :small_class_name
{{#if province}} AND province = :province
{{#if meal_flg AND meal_flg != '全部'}} AND meal_flg = :meal_flg
{{#if group_by_eq '门店'}}{{#else}}AND last_qty > 0
GROUP BY
    {{#if group_by_eq '品项'}}
        item_name, small_class_name, big_class_name
{{#if group_by_eq '小类'}}
        small_class_name, big_class_name
{{#if group_by_eq '大类'}}
        big_class_name
{{#if group_by_eq '省份'}}
        province
{{#if group_by_eq '城市'}}
        province, city
{{#if group_by_eq '门店'}}
        store_name, item_name, small_class_name, big_class_name
ORDER BY
    {{#if group_by_eq '门店'}}
        SUM(pre_discount_price)
    {{else}}
        {{#if rank_by_eq '数量'}}SUM(last_qty)
{{#if rank_by_eq '营收' OR not rank_by}}SUM(income_money)

DESC
LIMIT {{top_n:20}};
```

> 💡 `group_by=门店` 时不过滤 `last_qty > 0`，以保留赠送/退菜等零销量记录，确保金额对账完整。

**输出格式**：

| group_by | 列名 |
|---------|------|
| 品项 | 菜品名称 / 小类 / 大类 / 品项数 / 销售数量 / 纯收金额 / 实收金额 / 应收金额 |
| 小类 | 小类名称 / 大类 / 品项数 / 销售数量 / 纯收金额 / 应收金额 |
| 大类 | 大类名称 / 品项数 / 销售数量 / 纯收金额 / 应收金额 |
| 省份 | 省份 / 品项数 / 销售数量 / 纯收金额 / 应收金额 |
| 城市 | 省份 / 城市 / 品项数 / 销售数量 / 纯收金额 / 应收金额 |
| 门店 | 门店名称 / 菜品名称 / 小类 / 大类 / 品项应收 / 销售数量 / 品项实收 / 品项纯收 / 赠送金额 / 赠送数量 / 退菜金额 / 退菜数量 / 理论成本 / 折前理论毛利 / 折前毛利率% / 折后理论毛利 / 折后毛利率% |

> 💡 如需区分规格（大份/小份等），可在 GROUP BY 中追加 `item_standard_name, item_unit_name`。

---

## Intent 43: ItemCategoryAnalysis — 菜品大类占比分析

**触发**：大类占比/各大类营收/品类分析/饮品类/主食类/大类贡献/菜品分类汇总/小类占比/小类营收排行

**业务说明**：按大类或小类汇总营收和销量，支持同时看大类和按小类排名，了解品类结构及哪类菜最赚钱。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 大类/小类 | 分组维度，默认大类 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（仅 level=小类时生效） |
| `top_n` | Integer | 默认20 | 排名数量 |

**统一 SQL 模板**：

```sql
SELECT
    {{#if group_by_eq '大类'}}
        big_class_name AS 大类名称,
{{#if group_by_eq '小类'}}
        big_class_name AS 大类,
        small_class_name AS 小类名称,
COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(pre_discount_price), 2) AS 应收金额,
    ROUND(SUM(income_money) * 100.0 / SUM(SUM(income_money)) OVER(), 2) AS 纯收占比
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
        AND store_code IN (#{omShopCodes})
{{#if big_class_name AND group_by_eq '小类'}} AND big_class_name = :big_class_name
AND last_qty > 0
GROUP BY
    {{#if group_by_eq '大类'}}
        big_class_name
{{#if group_by_eq '小类'}}
        big_class_name, small_class_name
ORDER BY SUM(income_money) DESC
LIMIT {{top_n:20}};
```

**输出格式**：

| group_by | 列名 |
|---------|------|
| 大类 | 大类名称 / 品项数 / 销售数量 / 纯收金额 / 应收金额 / 纯收占比% |
| 小类 | 大类 / 小类名称 / 品项数 / 销售数量 / 纯收金额 / 纯收占比% |

---

## Intent 44: SetmealSalesRanking — 套餐销售排行

**触发**：套餐排行/哪个套餐最受欢迎/套餐销量榜/套餐收入分析/套餐详情

**业务说明**：按套餐名称汇总销量和收入，了解套餐受欢迎程度，支持查看套餐包含的品项明细。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `rank_by` | Enum | 营收/数量 | 排名依据，默认营收 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（套餐汇总排行）**：
```sql
SELECT
    setmeal_name AS 套餐名称,
    COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(last_qty), 2) AS 套餐品项销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(pre_discount_price), 2) AS 应收金额
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND meal_flg = '套餐明细'
    AND setmeal_name IS NOT NULL
    AND setmeal_name != ''
        AND store_code IN (#{omShopCodes})
GROUP BY setmeal_name
ORDER BY SUM(income_money) DESC
LIMIT {{top_n:20}};
```

**SQL 模板（某套餐内品项明细）**：
```sql
-- 查看指定套餐包含哪些菜品
SELECT
    item_name AS 菜品名称,
    big_class_name AS 大类,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND meal_flg = '套餐明细'
    AND setmeal_name = :setmeal_name
GROUP BY item_name, big_class_name
ORDER BY SUM(last_qty) DESC
LIMIT 30;
```

**输出格式**：排名表格（套餐名称 / 品项数 / 销售数量 / 纯收金额 / 应收金额）

---

## Intent 45: ItemReturnDetailAnalysis — 菜品退菜明细分析

**触发**：哪道菜退的最多/退菜品项排名/菜品退货率/退货最多的菜/品项退菜分析

**业务说明**：从菜品明细维度分析退菜，识别退菜率高的具体品项，定位质量或服务问题。

> ⚠️ 与 Intent 22（退菜分析）的区别：Intent 22 是**账单层**退菜门店排名，Intent 45 是**品项层**退菜品项排名。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `rank_by` | Enum | 退菜数量/退菜金额 | 排名依据，默认退菜金额 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    item_name AS 菜品名称,
    big_class_name AS 大类,
    small_class_name AS 小类,
    ROUND(SUM(last_qty), 2) AS 实售数量,
    ROUND(SUM(return_qty), 2) AS 退菜数量,
    ROUND(SUM(return_subtotal), 2) AS 退菜金额,
    ROUND(SUM(return_qty) * 100.0 / NULLIF(SUM(last_qty) + SUM(return_qty), 0), 2) AS 退菜率
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND return_qty > 0
        AND store_code IN (#{omShopCodes})
{{#if big_class_name}} AND big_class_name = :big_class_name
GROUP BY item_name, big_class_name, small_class_name
HAVING SUM(return_qty) > 0
ORDER BY SUM(return_subtotal) DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（菜品名称 / 大类 / 实售数量 / 退菜数量 / 退菜率% / 退菜金额）

---

## Intent 46: ItemGrossProfitAnalysis — 菜品毛利分析

**触发**：菜品毛利/哪道菜利润高/毛利率分析/成本分析/理论毛利/菜品盈利能力/折前毛利/折后毛利/小类毛利/大类毛利

**业务说明**：计算菜品的折前/折后理论毛利和毛利率，支持品项/小类/大类三种粒度，**必须同时展示折前和折后**两组指标。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 品项/小类/大类 | 分组维度，默认品项 |
| `rank_by` | Enum | 折后毛利/折前毛利/折后毛利率/折前毛利率 | 排名依据，默认折后毛利 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `small_class_name` | String | - | 小类过滤（仅 level=品项时生效） |
| `top_n` | Integer | 默认20 | 排名数量 |

**统一 SQL 模板**：

```sql
SELECT
    {{#if group_by_eq '品项'}}
        item_name AS 菜品名称,
        small_class_name AS 小类,
{{#if group_by_eq '小类'}}
        small_class_name AS 小类名称,
{{#if group_by_eq '大类'}}
        big_class_name AS 大类名称,
big_class_name AS 大类,
    COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    -- 折前指标
    ROUND(SUM(pre_discount_price), 2) AS 应收金额,
    ROUND(SUM(cost_money), 2) AS 理论成本,
    ROUND(SUM(pre_discount_price) - SUM(cost_money), 2) AS 折前理论毛利,
    ROUND((SUM(pre_discount_price) - SUM(cost_money)) * 100.0 / NULLIF(SUM(pre_discount_price), 0), 2) AS 折前毛利率,
    -- 折后指标
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(income_money) - SUM(cost_money), 2) AS 折后理论毛利,
    ROUND((SUM(income_money) - SUM(cost_money)) * 100.0 / NULLIF(SUM(income_money), 0), 2) AS 折后毛利率
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND last_qty > 0
    AND cost_money > 0
        AND store_code IN (#{omShopCodes})
{{#if big_class_name}} AND big_class_name = :big_class_name
{{#if small_class_name}} AND small_class_name = :small_class_name
GROUP BY
    {{#if group_by_eq '品项'}}
        item_name, small_class_name, big_class_name
{{#if group_by_eq '小类'}}
        small_class_name, big_class_name
{{#if group_by_eq '大类'}}
        big_class_name
ORDER BY
    {{#if rank_by_eq '折前毛利'}}
        (SUM(pre_discount_price) - SUM(cost_money))
{{#if rank_by_eq '折后毛利' OR not rank_by}}
        (SUM(income_money) - SUM(cost_money))
{{#if rank_by_eq '折前毛利率'}}
        (SUM(pre_discount_price) - SUM(cost_money)) * 100.0 / NULLIF(SUM(pre_discount_price), 0)
{{#if rank_by_eq '折后毛利率'}}
        (SUM(income_money) - SUM(cost_money)) * 100.0 / NULLIF(SUM(income_money), 0)
DESC
LIMIT {{top_n:20}};
```

**输出格式**：双组毛利表格

| group_by | 必选列 |
|---------|--------|
| 品项 | 菜品名称 / 小类 / 大类 / 品项数 / 销售数量 / 应收金额 / 理论成本 / 折前理论毛利 / 折前毛利率% / 纯收金额 / 折后理论毛利 / 折后毛利率% |
| 小类 | 小类名称 / 大类 / 品项数 / 销售数量 / 同上四组毛利指标 |
| 大类 | 大类名称 / 品项数 / 销售数量 / 同上四组毛利指标 |

---

## Intent 47: ItemChannelDistribution — 菜品渠道分布分析

**触发**：外卖点最多的菜/堂食vs外卖品项差异/哪些菜主要靠外卖/渠道品项分析

**业务说明**：分析不同销售渠道（堂食/外卖等）的菜品销售差异，支持渠道差异化定价决策。

**枚举值**：`sale_type_name`：堂食 / 外卖 / 其他（以实际数据为准）

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `sale_type` | String | 堂食/外卖 | 渠道过滤（可选，不填则对比全渠道） |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `top_n` | Integer | 默认15 | 排名数量 |

**SQL 模板（渠道×品项交叉）**：
```sql
SELECT
    sale_type_name AS 销售渠道,
    item_name AS 菜品名称,
    big_class_name AS 大类,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(income_money) * 100.0 / SUM(SUM(income_money)) OVER(PARTITION BY sale_type_name), 2) AS 渠道内占比
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND last_qty > 0
    {{#if sale_type}} AND sale_type_name = :sale_type
    AND store_code IN (#{omShopCodes})
{{#if big_class_name}} AND big_class_name = :big_class_name
GROUP BY sale_type_name, item_name, big_class_name
ORDER BY sale_type_name, SUM(income_money) DESC
LIMIT {{top_n:15}};
```

**SQL 模板（各渠道TOP菜品对比）**：
```sql
-- 各渠道Top菜品
SELECT
    sale_type_name AS 销售渠道,
    item_name AS 菜品名称,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND last_qty > 0
        AND store_code IN (#{omShopCodes})
GROUP BY sale_type_name, item_name
QUALIFY ROW_NUMBER() OVER(PARTITION BY sale_type_name ORDER BY SUM(income_money) DESC) <= 10
ORDER BY sale_type_name, SUM(income_money) DESC;
```

**输出格式**：分渠道排名表格（渠道 / 菜品名称 / 销售数量 / 纯收金额 / 渠道内占比%）

---

## Intent 48: ItemPresentAnalysis — 赠送品项分析

**触发**：赠送最多的菜/赠送排行/免费送了什么/赠送金额占比/赠送菜品分析/哪些菜常被赠送

**业务说明**：分析被赠送（`present_qty > 0`）的品项，了解促销力度最大的菜品及其成本贡献。

**赠送识别**：`present_qty > 0 AND present_money > 0`（有赠送数量且有赠送金额）

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 品项/小类/大类 | 分组维度，默认品项 |
| `rank_by` | Enum | 赠送金额/赠送数量/赠送率 | 排名依据，默认赠送金额 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `small_class_name` | String | - | 小类过滤（仅 level=品项时生效） |
| `top_n` | Integer | 默认20 | 排名数量 |

**统一 SQL 模板**：

```sql
SELECT
    {{#if group_by_eq '品项'}}
        item_name AS 菜品名称,
        small_class_name AS 小类,
{{#if group_by_eq '小类'}}
        small_class_name AS 小类名称,
{{#if group_by_eq '大类'}}
        big_class_name AS 大类名称,
big_class_name AS 大类,
    COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(present_qty), 2) AS 赠送数量,
    ROUND(SUM(present_money), 2) AS 赠送金额,
    ROUND(SUM(cost_money), 2) AS 赠送成本,
    ROUND(SUM(present_money) * 100.0 / SUM(SUM(present_money)) OVER(), 2) AS 赠送金额占比,
    ROUND(SUM(present_qty) * 100.0 / NULLIF(SUM(last_qty) + SUM(present_qty), 0), 2) AS 赠送率
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND present_qty > 0
    AND present_money > 0
        AND store_code IN (#{omShopCodes})
{{#if big_class_name}} AND big_class_name = :big_class_name
{{#if small_class_name}} AND small_class_name = :small_class_name
GROUP BY
    {{#if group_by_eq '品项'}}
        item_name, small_class_name, big_class_name
{{#if group_by_eq '小类'}}
        small_class_name, big_class_name
{{#if group_by_eq '大类'}}
        big_class_name
ORDER BY
    {{#if rank_by_eq '赠送数量'}}
        SUM(present_qty)
{{#if rank_by_eq '赠送率'}}
        SUM(present_qty) * 100.0 / NULLIF(SUM(last_qty) + SUM(present_qty), 0)
{{#if rank_by_eq '赠送金额' OR not rank_by}}
        SUM(present_money)
DESC
LIMIT {{top_n:20}};
```

**输出格式**：

| group_by | 列名 |
|---------|------|
| 品项 | 菜品名称 / 小类 / 大类 / 品项数 / 赠送数量 / 赠送金额 / 赠送成本 / 赠送金额占比% / 赠送率% |
| 小类 | 小类名称 / 大类 / 品项数 / 赠送数量 / 赠送金额 / 赠送金额占比% / 赠送率% |
| 大类 | 大类名称 / 品项数 / 赠送数量 / 赠送金额 / 赠送金额占比% / 赠送率% |

> 💡 赠送率% = 赠送数量 / (实售数量 + 赠送数量)，反映该菜品被赠送的比例。

---

## Intent 49: StoreItemDifferenceAnalysis — 门店菜品差异分析

**触发**：各门店卖什么不一样/哪家店比萨卖得最好/门店菜品对比/门店特色菜/哪家店某菜卖得最多

**业务说明**：对比多个门店在特定菜品或大类上的销售差异，支持门店选品策略本地化。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `item_name` | String | - | 指定菜品名称（可选） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（指定菜品跨门店排名）**：
```sql
SELECT
    v.store_name AS 门店名称,
    v.item_name AS 菜品名称,
    v.big_class_name AS 大类,
    ROUND(SUM(v.last_qty), 2) AS 销售数量,
    ROUND(SUM(v.income_money), 2) AS 纯收金额
FROM dm.v_item_sale_analysis_with_sly v
WHERE v.group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND v.settle_biz_date >= :start_date
    AND v.settle_biz_date < :end_date_plus_1
    AND v.last_qty > 0
    {{#if item_name}} AND v.item_name = :item_name
{{#if big_class_name}} AND v.big_class_name = :big_class_name
GROUP BY v.store_name, v.item_name, v.big_class_name
ORDER BY SUM(v.income_money) DESC
LIMIT {{top_n:20}};
```

**SQL 模板（门店TOP菜品各异）**：
```sql
-- 各门店销售额最高的菜品（找出门店特色菜）
SELECT
    store_name AS 门店名称,
    item_name AS 头牌菜,
    big_class_name AS 大类,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND last_qty > 0
GROUP BY store_name, store_code, item_name, big_class_name
QUALIFY ROW_NUMBER() OVER(PARTITION BY store_name ORDER BY SUM(income_money) DESC) = 1
ORDER BY SUM(income_money) DESC
LIMIT {{top_n:20}};
```

**输出格式**：门店×菜品对比表格（门店名称 / 菜品名称 / 大类 / 销售数量 / 纯收金额）

---

## Intent 50: CategoryChannelCrossAnalysis — 品项及类别×渠道交叉分析

**触发**：外卖和堂食各大类占比/各渠道品类差异/堂食vs外卖大类对比/渠道品类结构/外卖小类/堂食品项对比/各渠道品项结构/品项×渠道/小类×渠道

**业务说明**：交叉分析菜品（大类/小类/品项）× 销售渠道的组合，支持三种粒度——大类×渠道看整体结构、小类×渠道看细分品类、品项×渠道看具体菜品在渠道间的差异。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 品项/小类/大类 | 分组维度，默认大类 |
| `date_range` | DateRange | YYYY-MM-DD ~ YYYY-MM-DD | 日期范围（必填） |
| `store_code` | String | - | 门店过滤（系统始终注入） |
| `sale_type` | String | 堂食/外卖 | 渠道过滤（可选，不填则对比全渠道） |
| `big_class_name` | String | - | 大类过滤（可选） |
| `top_n` | Integer | 默认10 | 每渠道展示数量 |

**统一 SQL 模板**：

```sql
SELECT
    sale_type_name AS 销售渠道,
    {{#if group_by_eq '品项'}}
        item_name AS 菜品名称,
        small_class_name AS 小类,
        big_class_name AS 大类,
{{#if group_by_eq '小类'}}
        small_class_name AS 小类名称,
        big_class_name AS 大类,
{{#if group_by_eq '大类'}}
        big_class_name AS 大类名称,
COUNT(DISTINCT item_id) AS 品项数,
    ROUND(SUM(last_qty), 2) AS 销售数量,
    ROUND(SUM(income_money), 2) AS 纯收金额,
    ROUND(SUM(income_money) * 100.0 / SUM(SUM(income_money)) OVER(PARTITION BY sale_type_name), 2) AS 渠道内占比,
    ROUND(SUM(income_money) * 100.0 / SUM(SUM(income_money)) OVER(), 2) AS 全局占比
FROM dm.v_item_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date >= :start_date
    AND settle_biz_date < :end_date_plus_1
    AND last_qty > 0
        AND store_code IN (#{omShopCodes})
{{#if sale_type}} AND sale_type_name = :sale_type
{{#if big_class_name}} AND big_class_name = :big_class_name
GROUP BY sale_type_name,
    {{#if group_by_eq '品项'}}
        item_name, small_class_name, big_class_name
{{#if group_by_eq '小类'}}
        small_class_name, big_class_name
{{#if group_by_eq '大类'}}
        big_class_name
ORDER BY sale_type_name, SUM(income_money) DESC
LIMIT {{top_n:10}};
```

**输出格式**：

| group_by | 列名 |
|---------|------|
| 品项 | 销售渠道 / 菜品名称 / 小类 / 大类 / 品项数 / 销售数量 / 纯收金额 / 渠道内占比% / 全局占比% |
| 小类 | 销售渠道 / 小类名称 / 大类 / 品项数 / 销售数量 / 纯收金额 / 渠道内占比% / 全局占比% |
| 大类 | 销售渠道 / 大类名称 / 品项数 / 销售数量 / 纯收金额 / 渠道内占比% / 全局占比% |
