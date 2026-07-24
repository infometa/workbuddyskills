# 🎁 分类四：优惠与结算

基于 `dm.v_pos_corp_sale_analysis_with_sly` 表（40亿+ 条）

> 省多少钱、怎么结账，优惠折扣、服务费、押金、签单、发票分析

> ⚠️ 营业表查询规则：
> 1. 必须带 `settle_biz_date` 日期过滤（强制，未指定则询问）
> 2. `group_code` = `SL_UNIFIED_G_ID`（强制注入）；`store_code` IN (`omShopCodes`)（始终强制注入，默认全部授权门店）
> 3. 必须带 `LIMIT`

---

## Intent 15: DiscountAnalysis — 优惠折扣分析

**触发**：折扣/优惠/减免/会员价 + 分析

**优惠字段说明**：

| 字段 | 含义 |
|------|------|
| `item_member_money` | 会员价优惠 |
| `item_promote_money` | 促销优惠 |
| `item_present_money` | 赠送金额 |
| `item_disc_money` | 折扣金额 |
| `asitem_fix_money` | 定额优惠 |
| `item_wipe_money` | 抹零金额 |
| `disc_money_total` | 优惠总金额 |

**SQL 模板**：
```sql
SELECT
    sale_type_name AS 销售渠道,
    SUM(bill_count) AS 账单数,
    ROUND(SUM(busi_income), 2) AS 实收金额,
    ROUND(SUM(item_member_money), 2) AS 会员价优惠,
    ROUND(SUM(item_promote_money), 2) AS 促销优惠,
    ROUND(SUM(item_present_money), 2) AS 赠送金额,
    ROUND(SUM(item_disc_money), 2) AS 折扣金额,
    ROUND(SUM(item_wipe_money), 2) AS 抹零金额,
    ROUND(SUM(asitem_fix_money), 2) AS 定额优惠,
    ROUND(SUM(disc_money_total), 2) AS 优惠总金额
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if sale_type}} AND sale_type_name = :sale_type
GROUP BY sale_type_name
ORDER BY 实收金额 DESC
LIMIT 100;
```

---

## Intent 16: ServiceAndFeeAnalysis — 服务费与杂项费用分析

**触发**：服务费/最低消费补齐/定额优惠/抹零 + 分析

**费用字段说明**：

| 字段 | 含义 |
|------|------|
| `service_free` | 服务费 |
| `low_consume_polish_free` | 最低消费补齐 |
| `asitem_fix_money` | 定额优惠 |
| `item_wipe_money` | 抹零金额 |

**SQL 模板**：
```sql
SELECT
    store_name AS 门店名称,
    city AS 城市,
    brand_name AS 品牌,
    ROUND(SUM(service_free), 2) AS 服务费,
    ROUND(SUM(low_consume_polish_free), 2) AS 最低消费补齐,
    ROUND(SUM(asitem_fix_money), 2) AS 定额优惠,
    ROUND(SUM(item_wipe_money), 2) AS 抹零金额,
    ROUND(SUM(service_free) + SUM(low_consume_polish_free) + SUM(asitem_fix_money) + SUM(item_wipe_money), 2) AS 杂费合计
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'  -- 🔐 注入 SL_UNIFIED_G_ID（统一集团码）
 AND store_code IN (#{omShopCodes})
AND settle_biz_date >= :start_date  -- 🔒 日期过滤（强制）
    AND settle_biz_date < :end_date_plus_1  -- 🔒 日期过滤（强制）
    {{#if region}} AND region = :region
{{#if city}} AND city = :city
{{#if brand_name}} AND brand_name = :brand_name
GROUP BY store_code, store_name, city, brand_name
ORDER BY 杂费合计 DESC
LIMIT 100;
```

---

## Intent 17: DepositAnalysis — 押金收缴分析

**触发**：押金/保证金/加押金/退押金/没收押金 + 分析

**业务说明**：押金是顾客用餐前预付的保证金，结账后根据消费情况退还或没收。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/管理类型 | 聚合维度 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 管理类型过滤 |
| `region` | String | 大区名称 | 区域过滤 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    SUM(bill_add_deposit) AS 加押金总额,
    SUM(bill_forfeiture_deposit) AS 没收押金总额,
    SUM(bill_residue_deposit) AS 剩余押金总额,
    SUM(bill_settle_deposit) AS 结账押金总额,
    SUM(bill_manual_return_deposit) AS 手动退押金,
    COUNT(DISTINCT id) AS 押金笔数,
    ROUND(SUM(bill_forfeiture_deposit) / NULLIF(SUM(bill_add_deposit), 0) * 100, 2) AS 没收率%
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date BETWEEN '{{start_date}}' AND '{{end_date}}'
    {{#if manage_type}} AND manage_type = '{{manage_type}}'
{{#if region}} AND region = '{{region}}'
GROUP BY {{group_by:store_name}}
ORDER BY 加押金总额 DESC
LIMIT 50;
```

**输出格式**：排名表格（维度 / 加押金 / 没收押金 / 退还押金 / 没收率%）

---

## Intent 18: SigningManagerAnalysis — 签单经理业绩分析

**触发**：签单/经理签单/签单金额/经理业绩 + 分析/排名

**业务说明**：签单是指大客户或企业客户通过签单方式挂账消费，月底统一结算。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `top_n` | Integer | 默认20 | 排名数量 |
| `manage_type` | Enum | 直营/加盟/托管/合作 | 管理类型过滤 |
| `region` | String | 大区名称 | 区域过滤 |

**SQL 模板**：
```sql
SELECT
    COALESCE(signing_manager_name, '未知') AS 签单经理,
    signing_manager_code AS 经理编号,
    SUM(signing_manager_money) AS 签单金额,
    COUNT(DISTINCT id) AS 签单笔数,
    SUM(busi_income) AS 关联营收,
    ROUND(SUM(signing_manager_money) / NULLIF(SUM(busi_income), 0) * 100, 2) AS 签单占比%
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date BETWEEN '{{start_date}}' AND '{{end_date}}'
    AND signing_manager_money > 0
    {{#if manage_type}} AND manage_type = '{{manage_type}}'
{{#if region}} AND region = '{{region}}'
GROUP BY signing_manager_code, signing_manager_name
ORDER BY 签单金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（序号 / 经理名 / 编号 / 签单金额 / 签单笔数 / 占比%）；Top3 高亮

---

## Intent 19: InvoiceAnalysis — 发票开具分析

**触发**：发票/电子发票/开票/发票金额 + 分析/占比

**业务说明**：分析电子发票的开具情况，了解顾客索取发票的习惯和税务合规情况。

**Slots**：

| Slot | 类型 | 枚举值 | 说明 |
|------|------|--------|------|
| `group_by` | Enum | 门店/品牌/管理类型 | 聚合维度 |
| `top_n` | Integer | 默认20 | 排名数量 |

**SQL 模板**：
```sql
SELECT
    {{group_by:store_name}} AS 维度,
    SUM(busi_income) AS 实收金额,
    SUM(e_invoice_mny) AS 发票金额,
    SUM(invoice_num) AS 发票张数,
    COUNT(DISTINCT id) AS 总账单数,
    ROUND(SUM(e_invoice_mny) / NULLIF(SUM(busi_income), 0) * 100, 2) AS 开票率%,
    ROUND(SUM(invoice_num) / NULLIF(COUNT(DISTINCT id), 0) * 100, 2) AS 发票索取率%
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
 AND store_code IN (#{omShopCodes})
AND settle_biz_date BETWEEN '{{start_date}}' AND '{{end_date}}'
GROUP BY {{group_by:store_name}}
ORDER BY 发票金额 DESC
LIMIT {{top_n:20}};
```

**输出格式**：排名表格（维度 / 实收金额 / 发票金额 / 发票张数 / 开票率% / 索取率%）
