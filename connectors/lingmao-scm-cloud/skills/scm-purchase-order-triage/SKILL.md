---
name: "scm-purchase-order-triage"
description: "用户要看采购单的状态、汇总、按供应商/时间/状态切片时触发；也覆盖「这单为什么审不了」这类前提问题"
version: "1.0.1"
author: "领猫科技"
display_name: "采购单分诊"
display_name_en: "Purchase Order Triage"
description_zh: "采购单的列表、汇总、物料进度与审核前提：按供应商或状态切片，定位卡住的单。"
description_en: "Triage purchase orders: list, group, check material progress and audit prerequisites."
---

# 采购单分诊

## 什么时候用

用户提到采购单 / PO，且想要列表、汇总、按维度切片，或问某张单为什么卡住。
关键信号：未审核、超期、待协同、按供应商、物料没齐、审核不了。

## 会用到的工具

| 工具 | 用途 |
|---|---|
| `op_get_purchase_order_list_paged` | 采购单列表（分页 + 时间区间 + 状态筛选）【读】 |
| `op_purchase_order_detail_by_code` | 按单号取详情【读】 |
| `op_get_purchase_order_material_progress` | 该单的物料进度——「物料齐没齐」问这个【读】 |
| `op_get_purchase_order_warehouse_info_data` | 交期与首次入库比例【读】 |
| `op_purchase_order_get_product_sku_inventory` | 款式使用情况【读】 |
| `op_purchase_order_batch_audit` | 批量审核 / 反审核（`operate`：1 审核、2 反审核）【写】 |

## 调用流程

1. 先 `op_get_purchase_order_list_paged` 拉数据，`pageSize` 从 50 起，按创建时间倒序。
2. 要按状态筛之前，**先确认「未审核」在这个租户对应哪些状态值**（见下一节）——
   状态是枚举，猜错会筛出空列表却不报错，比报错更难发现。
3. 汇总在本地做（按供应商、按金额、按交期分组），输出表格 + 一句话结论。
4. 单张单要深挖时再调详情类工具，不要对列表里每一行都调一次详情。

## 业务口径从哪来

接口只给值，不给含义。以下问题**不要自己推断**，按总纲（`lingmao-scm-cloud/SKILL.md`）
「取数 vs 口径」的规则处理 —— 先调本 Connector 内置的 `ask_knowledge`，它答「未收录」再据实说明：

- 「未审核 / 待协同 / 已结案」各自包含哪些状态，状态之间怎么流转；
- 采购单审核的前提条件（缺了什么会审不过）；
- 结案、作废分别有什么前置和后果，能不能反向操作；
- 物料进度里「已到位」的判定口径。

## 边界

- 列表类一次不要超过 200 行，超了引导用户加筛选条件，不要靠翻页硬拉。
- 审核 / 反审核 / 作废 / 结案都是写操作：**调用前把单号和动作复述给用户确认**，
  失败不要重试——先查一次当前状态再决定，否则可能重复操作。
- 该模块未授权时工具不会出现在 `tools/list`，用 `list_capabilities` 确认后引导用户去控制台勾选。
