# 📦 分类十二：供应链原物料分析

## 📌 表说明

> ⚠️ **供应链分析使用独立数据表，与 POS 营业分析共用 `group_code`（集团 G 号）和 `store_code`（门店 C 号）字段，**与 POS/菜品/CRM 等业务表**完全统一**，可直接通过 `group_code` + `store_code` 关联。**

### SCM8 原物料耗用分析表

| 表名 | 用途 | 数据量 |
|------|------|--------|
| `dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view` | SCM8 原物料日粒度耗用视图 | 2.6亿行 |

### ⚠️ 核心使用约定

| 约定 | 说明 |
|------|------|
| **期初/期末禁止 SUM** | `begin_*` / `end_*` / `theory_begin_*` / `theory_end_*` 只能在**单日** `biz_date` 点取，不能按时间累加 |
| **期初取法** | 月初 = `biz_date = 月份第1天` 的 `begin_inventory_*` |
| **期末取法** | 月末 = `biz_date = 月份最后1天` 的 `end_inventory_*` |
| **流量字段可 SUM** | `instore_*`、`outstore_*`、`actual_consume_*`、`theory_consume_*`、`loss_report_*`、`purchase_instore_*`、`transfer_*` 等均可在时间范围内 SUM |
| **关联 POS** | 毛利率/采购占销比等指标需关联 `dm.v_pos_corp_sale_analysis_with_sly`，关联键为 `group_code` + `store_code`（**与 SCM8 视图完全一致**） |

### 关键字段速查

| 字段分类 | 字段名 | 中文含义 | 可SUM? |
|---------|--------|---------|--------|
| **期初库存** | `begin_inventory_qty` / `begin_inventory_amount` | 期初库存数量/金额 | ❌ 点取 |
| **期末库存** | `end_inventory_qty` / `end_inventory_amount` | 期末库存数量/金额 | ❌ 点取 |
| **理论期初** | `theory_begin_inventory_qty` / `theory_begin_inventory_amount` | 理论期初库存 | ❌ 点取 |
| **理论期末** | `theory_end_inventory_qty` / `theory_end_inventory_amount` | 理论期末库存 | ❌ 点取 |
| **入库流量** | `purchase_instore_qty` / `purchase_instore_non_tax_cost_amount` / `instore_amount` | 采购入库量/不含税金额/含税金额 | ✅ |
| **调拨入库** | `transfer_instore_qty` / `transfer_instore_non_tax_cost_amount` | 调入数量/不含税金额 | ✅ |
| **耗用流量** | `actual_consume_qty` / `actual_consume_amount` | 实际耗用数量/金额 | ✅ |
| **理论耗用** | `theory_consume_qty` / `tax_theory_cost_amount` | 理论耗用数量/含税金额 | ✅ |
| **报损流量** | `loss_report_qty` / `loss_report_amount` | 报损数量/金额 | ✅ |
| **维度字段** | `rm_item_name` / `rm_item_small_type_name` / `rm_item_parent_type_name` / `main_unit_name` | 原料名称/小类/大类/单位 | 分组 |
| **时间字段** | `biz_date` / `ap_year` / `ap_month` | 业务日期/会计年/月 | — |

### 分差计算口径（必须严格遵守）

> ⚠️ 分差是理解供应链成本的核心，需严格按以下口径计算：

| 指标 | 公式 | 正分差含义 | 负分差含义 |
|------|------|-----------|-----------|
| **耗用分差** | 理论耗用金额 − 实际耗用金额 | ✅ 节约（理论 > 实际） | 超耗（实际 > 理论） |
| **毛利分差** | 理论毛利 − 实际毛利 | 损失了毛利（理论毛利 > 实际毛利） | 多赚了毛利（实际毛利 > 理论毛利） |

**正分差** = 分差 > 0 的原料求和（节约了多少 / 损失了多少毛利）  
**负分差** = 分差 < 0 的原料取绝对值求和（超耗了多少 / 多赚了毛利）

---

## Intent 98: SCMPurchaseAnalysis — 原物料采购分析

**触发**：采购/进货/采购金额/采购品种/采购占销比/单价环比/采购异常/涨价/降价

**业务说明**：统计期间采购入库情况，包含采购规模、占销比监控、单价格环比异常（识别涨价/降价/新增/停采品种）。

**关键约定**：
- 采购不含税金额 = `purchase_instore_non_tax_cost_amount`（成本核算用）
- 采购含税金额 = `instore_amount`（财务对账用）
- 采购占销比 = 采购不含税金额 ÷ POS实收金额（需关联 POS 表）
- ⚠️ SCM8 表**无供应商/采购渠道字段**

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/大类/小类 | 聚合维度 |
| `top_n` | Integer | 默认50 | 排名数量 |

**SQL 模板（采购汇总看板）**：
```sql
WITH pos AS (
  SELECT SUM(real_income) AS 实收金额
  FROM dm.v_pos_corp_sale_analysis_with_sly
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
),
scm AS (
  SELECT COUNT(DISTINCT CASE WHEN purchase_instore_qty > 0 THEN rm_item_id END) AS 采购品种数,
    SUM(purchase_instore_qty) AS 采购总量,
    SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额,
    SUM(instore_amount) AS 采购含税金额,
    SUM(transfer_instore_qty) AS 调入数量,
    SUM(transfer_instore_non_tax_cost_amount) AS 调入不含税金额,
    SUM(other_instore_qty) AS 其他入库数量
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
)
SELECT
  ROUND((SELECT 实收金额 FROM pos), 2) AS 实收金额,
  s.采购品种数,
  ROUND(s.采购不含税金额, 2) AS 采购不含税金额,
  ROUND(s.采购含税金额, 2) AS 采购含税金额,
  ROUND(s.采购不含税金额 / NULLIF((SELECT 实收金额 FROM pos), 0) * 100, 2) AS 采购占销比Pct,
  ROUND(s.采购总量, 4) AS 采购总量,
  ROUND(s.调入数量, 4) AS 调入数量,
  ROUND(s.调入不含税金额, 2) AS 调入不含税金额
FROM scm s;
```

**SQL 模板（采购品种明细 + 单价格环比）**：
```sql
WITH this_m AS (
  SELECT rm_item_id, rm_item_name, rm_item_small_type_name, rm_item_parent_type_name, main_unit_name,
    SUM(purchase_instore_qty) AS 本月采购量,
    SUM(purchase_instore_non_tax_cost_amount) AS 本月不含税金额,
    SUM(purchase_instore_non_tax_cost_amount) / NULLIF(SUM(purchase_instore_qty), 0) AS 本月单价
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
    AND purchase_instore_qty > 0
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id, rm_item_name, rm_item_small_type_name, rm_item_parent_type_name, main_unit_name
),
last_m AS (
  SELECT rm_item_id,
    SUM(purchase_instore_qty) AS 上月采购量,
    SUM(purchase_instore_non_tax_cost_amount) / NULLIF(SUM(purchase_instore_qty), 0) AS 上月单价
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN DATE_SUB(:start_date, INTERVAL 1 MONTH) AND DATE_SUB(:end_date, INTERVAL 1 MONTH)
    AND purchase_instore_qty > 0
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id
)
SELECT
  t.rm_item_name AS 原料名称,
  t.rm_item_small_type_name AS 小类,
  t.rm_item_parent_type_name AS 大类,
  t.main_unit_name AS 单位,
  ROUND(t.本月采购量, 4) AS 本月采购量,
  ROUND(t.本月不含税金额, 2) AS 本月不含税金额,
  ROUND(t.本月单价, 4) AS 本月单价,
  ROUND(l.上月单价, 4) AS 上月单价,
  ROUND((t.本月单价 - l.上月单价) / NULLIF(l.上月单价, 0) * 100, 2) AS 单价环比Pct,
  CASE
    WHEN l.上月单价 IS NULL THEN '新增采购'
    WHEN t.上月采购量 IS NULL THEN '停止采购'
    WHEN (t.本月单价 - l.上月单价) / NULLIF(l.上月单价, 0) > 0.3 THEN '⚠️涨价超30%'
    WHEN (l.上月单价 - t.本月单价) / NULLIF(l.上月单价, 0) > 0.3 THEN '⚠️降价超30%'
    ELSE '正常'
  END AS 单价状态
FROM this_m t
LEFT JOIN last_m l USING (rm_item_id)
ORDER BY t.本月不含税金额 DESC
LIMIT {{top_n:50}};
```

**SQL 模板（采购异常汇总）**：
```sql
WITH this_m AS (
  SELECT rm_item_id,
    SUM(purchase_instore_qty) AS qty,
    SUM(purchase_instore_non_tax_cost_amount) AS amt
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
    AND purchase_instore_qty > 0
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id
),
last_m AS (
  SELECT rm_item_id,
    SUM(purchase_instore_qty) AS qty,
    SUM(purchase_instore_non_tax_cost_amount) AS amt
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN DATE_SUB(:start_date, INTERVAL 1 MONTH) AND DATE_SUB(:end_date, INTERVAL 1 MONTH)
    AND purchase_instore_qty > 0
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id
)
SELECT
  COUNT(DISTINCT t.rm_item_id) AS 采购品种数,
  COUNT(DISTINCT CASE WHEN l.qty > 0 AND t.qty > 0
    AND (t.amt/t.qty - l.amt/l.qty) / (l.amt/l.qty) > 0.3 THEN t.rm_item_id END) AS 涨价品种数,
  COUNT(DISTINCT CASE WHEN l.qty > 0 AND t.qty > 0
    AND (l.amt/l.qty - t.amt/t.qty) / (l.amt/l.qty) > 0.3 THEN t.rm_item_id END) AS 降价品种数,
  COUNT(DISTINCT CASE WHEN t.qty > 0 AND l.rm_item_id IS NULL THEN t.rm_item_id END) AS 新增采购品种数,
  COUNT(DISTINCT CASE WHEN l.qty > 0 AND t.rm_item_id IS NULL THEN l.rm_item_id END) AS 停止采购品种数,
  COUNT(DISTINCT CASE WHEN l.qty > 0 AND t.qty > 0
    AND (t.qty - l.qty) / l.qty > 0.5 THEN t.rm_item_id END) AS 采购量突增品种数,
  COUNT(DISTINCT CASE WHEN l.qty > 0 AND t.qty > 0
    AND (l.qty - t.qty) / l.qty > 0.5 THEN t.rm_item_id END) AS 采购量骤降品种数
FROM this_m t LEFT JOIN last_m l USING (rm_item_id);
```

**输出格式**：
- 汇总看板：采购品种数 / 采购不含税金额 / 采购含税金额 / 采购占销比%
- 异常汇总：涨价品种数 / 降价品种数 / 新增采购 / 停止采购 / 量突增 / 量骤降
- 明细表格：原料名称 / 采购量 / 采购金额 / 本月单价 / 上月单价 / 环比% / 状态标签

---

## Intent 99: SCMConsumeAnalysis — 原物料耗用分析

**触发**：耗用/实际耗用/理论耗用/耗用分差/超耗/节约/报损/分差品种数

**业务说明**：统计期间原料耗用情况，对比理论耗用与实际耗用的差异，识别超耗和节耗品种；同时监控报损情况。

**关键约定**：
- 耗用分差 = 理论耗用金额 − 实际耗用金额
  - 分差 > 0：节约（正分差）
  - 分差 < 0：超耗（负分差）
- 正分差（节约）= 所有耗用分差 > 0 的原料求和
- 负分差（超耗）= 所有耗用分差 < 0 的原料取绝对值求和

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/大类/小类 | 聚合维度 |
| `top_n` | Integer | 默认50 | 排名数量 |

**SQL 模板（耗用汇总看板）**：
```sql
WITH daily AS (
  SELECT rm_item_id,
    SUM(actual_consume_qty) AS 实际耗用数量,
    SUM(actual_consume_amount) AS 实际耗用金额,
    SUM(tax_theory_cost_amount) AS 理论耗用金额,
    SUM(tax_theory_cost_amount) - SUM(actual_consume_amount) AS 耗用分差
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id
)
SELECT
  COUNT(DISTINCT rm_item_id) AS 原料品种数,
  COUNT(DISTINCT CASE WHEN 实际耗用数量 > 0 THEN rm_item_id END) AS 有耗用品种数,
  ROUND(SUM(实际耗用数量), 4) AS 实际耗用总量,
  ROUND(SUM(实际耗用金额), 2) AS 实际耗用金额,
  ROUND(SUM(理论耗用金额), 2) AS 理论耗用金额,
  ROUND(SUM(耗用分差), 2) AS 耗用分差合计,
  ROUND(SUM(CASE WHEN 耗用分差 > 0 THEN 耗用分差 ELSE 0 END), 2) AS 耗用正分差节约,
  ROUND(ABS(SUM(CASE WHEN 耗用分差 < 0 THEN 耗用分差 ELSE 0 END)), 2) AS 耗用负分差超耗,
  COUNT(CASE WHEN 耗用分差 > 0 THEN 1 END) AS 正分差品种数,
  COUNT(CASE WHEN 耗用分差 < 0 THEN 1 END) AS 负分差品种数
FROM daily;
```

**SQL 模板（超耗/节约原料明细）**：
```sql
WITH daily AS (
  SELECT rm_item_id, rm_item_name, rm_item_small_type_name, rm_item_parent_type_name, main_unit_name,
    SUM(actual_consume_qty) AS 实际耗用数量,
    SUM(actual_consume_amount) AS 实际耗用金额,
    SUM(tax_theory_cost_amount) AS 理论耗用金额,
    SUM(tax_theory_cost_amount) - SUM(actual_consume_amount) AS 耗用分差
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
GROUP BY rm_item_id, rm_item_name, rm_item_small_type_name, rm_item_parent_type_name, main_unit_name
)
SELECT
  rm_item_name AS 原料名称,
  rm_item_small_type_name AS 小类,
  main_unit_name AS 单位,
  ROUND(实际耗用数量, 4) AS 实际耗用数量,
  ROUND(实际耗用金额, 2) AS 实际耗用金额,
  ROUND(理论耗用金额, 2) AS 理论耗用金额,
  ROUND(理论耗用金额 - 实际耗用金额, 2) AS 耗用分差,
  ROUND(ABS(实际耗用金额 - 理论耗用金额), 2) AS 分差绝对值,
  ROUND((实际耗用金额 - 理论耗用金额) / NULLIF(理论耗用金额, 0) * 100, 2) AS 超耗率Pct,
  CASE WHEN 耗用分差 > 0 THEN '节约' WHEN 耗用分差 < 0 THEN '超耗' ELSE '一致' END AS 状态
FROM daily
ORDER BY 耗用分差
LIMIT {{top_n:50}};
```

**SQL 模板（报损分析）**：
```sql
SELECT
  COUNT(DISTINCT CASE WHEN loss_report_qty > 0 THEN rm_item_id END) AS 报损品种数,
  ROUND(SUM(loss_report_qty), 4) AS 报损总量,
  ROUND(SUM(loss_report_amount), 2) AS 报损金额,
  ROUND(SUM(actual_consume_amount), 2) AS 实际耗用金额,
  ROUND(SUM(loss_report_amount) / NULLIF(SUM(actual_consume_amount), 0) * 100, 2) AS 报损率Pct
FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
WHERE group_code = '#{SL_UNIFIED_G_ID}'
  AND biz_date BETWEEN :start_date AND :end_date
      AND store_code IN (#{omShopCodes})
;
```

**输出格式**：
- 汇总看板：原料品种数 / 实际耗用金额 / 理论耗用金额 / 耗用分差合计 / 节约 / 超耗 / 正分差品种数 / 负分差品种数
- 明细表格：原料 / 小类 / 单位 / 实际耗用 / 理论耗用 / 分差 / 分差绝对值 / 超耗率% / 状态
- 报损汇总：报损品种数 / 报损总量 / 报损金额 / 报损率%

---

## Intent 100: SCMGrossProfitAnalysis — 经营毛利分析

**触发**：毛利率/毛利分差/理论毛利率/实际毛利率/正分差/负分差/毛利分析

**业务说明**：联查 POS 实收金额与 SCM8 耗用成本，计算毛利率及分差。毛利率分差揭示实际毛利与理论毛利之间的利润损失。

**关键约定**：
- 实际毛利 = 实收 − 实际耗用；实际毛利率 = 实际毛利 ÷ 实收
- 理论毛利 = 实收 − 理论耗用；理论毛利率 = 理论毛利 ÷ 实收
- 毛利分差 = 理论毛利 − 实际毛利
- 毛利正分差 = 理论毛利 > 实际毛利的差额求和（损失了多少毛利）
- 毛利负分差 = 实际毛利 > 理论毛利的差额求和（多赚了毛利）
- ⚠️ **理论耗用存在数据质量问题**（部分门店配方跳变导致理论耗用异常偏大），**建议以实际毛利率为主要指标，理论毛利仅作参考标注**

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/大类/小类 | 聚合维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（毛利汇总看板）**：
```sql
WITH pos AS (
  SELECT SUM(real_income) AS 实收金额
  FROM dm.v_pos_corp_sale_analysis_with_sly
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND settle_biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
),
scm AS (
  SELECT SUM(actual_consume_amount) AS 实际耗用金额,
    SUM(tax_theory_cost_amount) AS 理论耗用金额,
    SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :start_date AND :end_date
        AND store_code IN (#{omShopCodes})
)
SELECT
  ROUND((SELECT 实收金额 FROM pos), 2) AS 实收金额,
  ROUND((SELECT 实收金额 FROM pos) - (SELECT 实际耗用金额 FROM scm), 2) AS 实际毛利,
  ROUND(((SELECT 实收金额 FROM pos) - (SELECT 实际耗用金额 FROM scm)) / NULLIF((SELECT 实收金额 FROM pos), 0) * 100, 2) AS 实际毛利率Pct,
  ROUND((SELECT 实收金额 FROM pos) - (SELECT 理论耗用金额 FROM scm), 2) AS 理论毛利,
  ROUND(((SELECT 实收金额 FROM pos) - (SELECT 理论耗用金额 FROM scm)) / NULLIF((SELECT 实收金额 FROM pos), 0) * 100, 2) AS 理论毛利率Pct,
  ROUND((SELECT 理论耗用金额 FROM scm) - (SELECT 实际耗用金额 FROM scm), 2) AS 耗用分差合计,
  ROUND((SELECT 理论毛利 FROM scm) - (SELECT 实际毛利 FROM scm), 2) AS 毛利分差合计,
  ROUND((SELECT 采购不含税金额 FROM scm), 2) AS 采购不含税金额,
  ROUND((SELECT 采购不含税金额 FROM scm) / NULLIF((SELECT 实收金额 FROM pos), 0) * 100, 2) AS 采购占销比Pct
FROM scm;
```

**SQL 模板（按门店多维度毛利对比）**：
```sql
WITH pos AS (
  SELECT store_code,
    SUM(real_income) AS 实收金额
  FROM dm.v_pos_corp_sale_analysis_with_sly
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
   AND store_code IN (#{omShopCodes})
AND settle_biz_date BETWEEN :start_date AND :end_date
  GROUP BY store_code
),
scm AS (
  SELECT store_code,
    SUM(actual_consume_amount) AS 实际耗用金额,
    SUM(tax_theory_cost_amount) AS 理论耗用金额,
    SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
   AND store_code IN (#{omShopCodes})
AND biz_date BETWEEN :start_date AND :end_date
  GROUP BY store_code
)
SELECT
  p.store_code AS 门店编码,
  ROUND(p.实收金额, 2) AS 实收金额,
  ROUND(p.实收金额 - s.实际耗用金额, 2) AS 实际毛利,
  ROUND((p.实收金额 - s.实际耗用金额) / NULLIF(p.实收金额, 0) * 100, 2) AS 实际毛利率Pct,
  ROUND(p.实收金额 - s.理论耗用金额, 2) AS 理论毛利,
  ROUND((p.实收金额 - s.理论耗用金额) / NULLIF(p.实收金额, 0) * 100, 2) AS 理论毛利率Pct,
  ROUND((p.实收金额 - s.理论耗用金额) - (p.实收金额 - s.实际耗用金额), 2) AS 毛利分差合计,
  ROUND(s.采购不含税金额 / NULLIF(p.实收金额, 0) * 100, 2) AS 采购占销比Pct
FROM pos p
LEFT JOIN scm s USING (store_code)
WHERE s.实际耗用金额 > 0
ORDER BY 实收金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：
- 汇总看板：实收金额 / 实际毛利 / 实际毛利率% / 理论毛利 / 理论毛利率% / 毛利分差 / 采购占销比%
- 门店排名表格：门店 / 实收 / 实际毛利 / 实际毛利率% / 理论毛利 / 理论毛利率% / 毛利分差 / 采购占销比%

> 💡 理论毛利率仅供参考，因部分门店理论耗用数据存在配方跳变问题。

---

## Intent 101: SCMInventoryFlow — 进销存月报

**触发**：进销存/月报/期初期末/库存变动/入库出库

**业务说明**：展示某月完整进销存链条：期初库存 + 本月入库 − 本月出库/耗用 = 期末库存。配合理论成本对比，揭示库存流转与成本偏差。

**关键约定**：期初/期末库存**点取**（单日 biz_date），流量字段（入库/耗用/报损）**SUM** 整月

**SQL 模板**：
```sql
WITH begin_inv AS (
  SELECT store_code, rm_item_id, rm_item_name, rm_item_small_type_name,
    rm_item_parent_type_name, main_unit_name,
    SUM(begin_inventory_qty) AS 期初库存数量,
    SUM(begin_inventory_amount) AS 期初库存金额
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date = :month_start
        AND store_code IN (#{omShopCodes})
GROUP BY store_code, rm_item_id, rm_item_name, rm_item_small_type_name, rm_item_parent_type_name, main_unit_name
),
end_inv AS (
  SELECT store_code, rm_item_id,
    SUM(end_inventory_qty) AS 期末库存数量,
    SUM(end_inventory_amount) AS 期末库存金额
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date = :month_end
        AND store_code IN (#{omShopCodes})
GROUP BY store_code, rm_item_id
),
flow AS (
  SELECT store_code, rm_item_id,
    SUM(purchase_instore_qty) AS 采购入库数量,
    SUM(instore_amount) AS 入库含税金额,
    SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额,
    SUM(transfer_instore_qty) AS 调入数量,
    SUM(actual_consume_qty) AS 实际耗用数量,
    SUM(actual_consume_amount) AS 实际耗用金额,
    SUM(tax_theory_cost_amount) AS 理论耗用金额,
    SUM(loss_report_qty) AS 报损数量,
    SUM(loss_report_amount) AS 报损金额
  FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
  WHERE group_code = '#{SL_UNIFIED_G_ID}'
    AND biz_date BETWEEN :month_start AND :month_end
        AND store_code IN (#{omShopCodes})
GROUP BY store_code, rm_item_id
)
SELECT
  b.rm_item_name AS 原料名称,
  b.rm_item_small_type_name AS 小类,
  b.main_unit_name AS 单位,
  ROUND(b.期初库存数量, 4) AS 期初库存数量,
  ROUND(b.期初库存金额, 2) AS 期初库存金额,
  ROUND(f.采购入库数量, 4) AS 采购入库数量,
  ROUND(f.入库含税金额, 2) AS 入库含税金额,
  ROUND(f.调入数量, 4) AS 调入数量,
  ROUND(f.实际耗用数量, 4) AS 实际耗用数量,
  ROUND(f.实际耗用金额, 2) AS 实际耗用金额,
  ROUND(f.理论耗用金额, 2) AS 理论耗用金额,
  ROUND(f.报损数量, 4) AS 报损数量,
  ROUND(f.报损金额, 2) AS 报损金额,
  ROUND(e.期末库存数量, 4) AS 期末库存数量,
  ROUND(e.期末库存金额, 2) AS 期末库存金额,
  ROUND(b.期初库存金额 + f.入库含税金额 - f.实际耗用金额 - f.报损金额, 2) AS 账面期末金额
FROM begin_inv b
LEFT JOIN end_inv e ON b.store_code = e.store_code AND b.rm_item_id = e.rm_item_id
LEFT JOIN flow f ON b.store_code = f.store_code AND b.rm_item_id = f.rm_item_id
WHERE f.实际耗用数量 > 0 OR f.采购入库数量 > 0 OR e.期末库存数量 > 0
ORDER BY f.实际耗用金额 DESC
LIMIT 100;
```

**输出格式**：表格（原料 / 小类 / 单位 / 期初数量&金额 / 采购入库 / 含税金额 / 调入 / 实际耗用数量&金额 / 理论耗用金额 / 报损 / 期末数量&金额 / 账面期末金额）

---

## Intent 102: SCMInventoryVariance — 盘点差异分析

**触发**：盘点差异/理论库存/账实差异/盘盈/盘亏/理论vs实际

**业务说明**：特定日期对比理论期末库存（配方推算）与实际期末库存（盘点），揭示盘点盈亏。

**关键约定**：期末库存取指定 `biz_date` 的 `theory_end_inventory_*` 和 `end_inventory_*`，**单日点取，不可 SUM**

**SQL 模板**：
```sql
SELECT
  rm_item_name AS 原料名称,
  rm_item_small_type_name AS 小类,
  main_unit_name AS 单位,
  theory_end_inventory_qty AS 理论期末数量,
  theory_end_inventory_amount AS 理论期末金额,
  end_inventory_qty AS 实际期末数量,
  end_inventory_amount AS 实际期末金额,
  ROUND(end_inventory_qty - theory_end_inventory_qty, 4) AS 盘点差异数量,
  ROUND(end_inventory_amount - theory_end_inventory_amount, 2) AS 盘点差异金额,
  CASE
    WHEN end_inventory_qty > theory_end_inventory_qty THEN '盘盈'
    WHEN end_inventory_qty < theory_end_inventory_qty THEN '盘亏'
    ELSE '一致'
  END AS 盘点结论
FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
WHERE group_code = '#{SL_UNIFIED_G_ID}'
  AND biz_date = :snapshot_date
  AND (theory_end_inventory_qty > 0 OR end_inventory_qty > 0)
      AND store_code IN (#{omShopCodes})
ORDER BY ABS(end_inventory_amount - theory_end_inventory_amount) DESC
LIMIT {{top_n:50}};
```

**输出格式**：表格（原料 / 小类 / 单位 / 理论期末数量&金额 / 实际期末数量&金额 / 差异数量 / 差异金额 / 盘盈/盘亏/一致）

---

## Intent 103: SCMCostTrend — 原料成本趋势

**触发**：耗用趋势/成本变化/月度耗用/环比/成本走势/超耗品种走势

**业务说明**：按月统计原料耗用金额的趋势，支持按大类或门店分组，帮助发现成本上升/下降趋势和季节性规律。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 月份/大类/门店 | 聚合维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板（月度耗用趋势）**：
```sql
SELECT
  ap_year AS 年,
  ap_month AS 月,
  rm_item_parent_type_name AS 大类,
  SUM(actual_consume_amount) AS 实际耗用金额,
  SUM(tax_theory_cost_amount) AS 理论耗用金额,
  ROUND(SUM(actual_consume_amount) - SUM(tax_theory_cost_amount), 2) AS 超耗金额,
  SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额,
  SUM(loss_report_amount) AS 报损金额,
  COUNT(DISTINCT CASE WHEN actual_consume_amount > tax_theory_cost_amount THEN rm_item_id END) AS 超耗品种数,
  COUNT(DISTINCT CASE WHEN actual_consume_amount < tax_theory_cost_amount AND actual_consume_amount > 0 THEN rm_item_id END) AS 节耗品种数
FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
WHERE group_code = '#{SL_UNIFIED_G_ID}'
  AND biz_date BETWEEN :start_date AND :end_date
      AND store_code IN (#{omShopCodes})
GROUP BY ap_year, ap_month, rm_item_parent_type_name
ORDER BY ap_year, ap_month;
```

**SQL 模板（门店耗用趋势排名）**：
```sql
SELECT
  ap_year AS 年,
  ap_month AS 月,
  store_code AS 门店,
  SUM(actual_consume_amount) AS 实际耗用金额,
  SUM(tax_theory_cost_amount) AS 理论耗用金额,
  ROUND(SUM(actual_consume_amount) - SUM(tax_theory_cost_amount), 2) AS 超耗金额,
  SUM(purchase_instore_non_tax_cost_amount) AS 采购不含税金额
FROM dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND biz_date BETWEEN :start_date AND :end_date
GROUP BY ap_year, ap_month, store_code
ORDER BY ap_year, ap_month, 实际耗用金额 DESC;
```

**输出格式**：
- 大类趋势：时序表格（年 / 月 / 大类 / 实际耗用 / 理论耗用 / 超耗金额 / 采购 / 报损 / 超耗品种数 / 节耗品种数）
- 门店趋势：表格（年 / 月 / 门店 / 实际耗用 / 理论耗用 / 超耗金额 / 采购）

