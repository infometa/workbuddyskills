---
name: "scm-supplier-reconcile"
description: "用户问供应商应付、对账单、账期或付款进度时触发；涉及财务数据，按套餐可能被拒"
version: "1.0.1"
author: "领猫科技"
display_name: "供应商应付对账"
display_name_en: "Supplier Payables Reconciliation"
description_zh: "供应商应付账单、对账单、付款单与账期分布，只读不做任何付款动作。"
description_en: "Supplier payables, statements, payments and aging buckets. Read-only, never initiates payment."
---

# 供应商应付对账

## 什么时候用

用户问某供应商欠多少、账期分布、对账单状态、付款进度。

## 会用到的工具

| 工具 | 用途 |
|---|---|
| `op_get_payable_list_paged` / `op_payable_detail` | 应付账单列表与详情【读】 |
| `op_get_payable_bill_list_paged` / `op_get_payable_bill_detail` | 对账单列表与详情【读】 |
| `op_query_payable_payment` / `op_get_payable_payment_detail` | 付款单列表与详情【读】 |
| `op_supplier_page_list_query` / `op_get_supplier_detail` | 供应商档案【读】 |

## 调用流程

1. 先用供应商档案确认主体（名称可能有简称 / 全称两种写法，用编码更稳）。
2. 再拉应付账单与对账单，按供应商聚合。
3. 本地计算：总应付、已付、未结余额、账期分布（≤30 / 31–60 / 61–90 / 90+ 天）。
4. 输出表格，把 90 天以上单独标出来。

## 业务口径从哪来

财务口径歧义最多，以下**一律不要自行推断**：

- 应付账单、对账单、付款单三者的关系与生成顺序；
- 「已核销」「已对账」「已付款」各自的判定标准，未审核的单算不算在内；
- 账期从哪个日期起算（开单日 / 对账日 / 收货日）。

按总纲（`lingmao-scm-cloud/SKILL.md`）的规则调 `ask_knowledge`；知识库也没覆盖时，明确告诉用户这个数是按什么口径算的，
让用户自己判断是否符合他们的会计口径。

## 边界

- **永不发起付款、核销、状态变更**。付款单的更新状态 / 核销工具属于写操作，
  本场景不调用；用户要求时必须单独确认，并说明影响。
- 财务模块受套餐控制，套餐不允许财务读时服务端会直接拒绝，
  这时如实告诉用户是套餐限制，不要绕道用别的接口拼凑。
