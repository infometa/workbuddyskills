---
name: "scm-warehouse-snapshot"
description: "用户问出入库单据、预约入库进度、物料库存或装箱情况时触发"
version: "1.0.1"
author: "领猫科技"
display_name: "仓储出入库与库存"
display_name_en: "Warehouse In/Out & Inventory"
description_zh: "成品与物料出入库单、预约单入库进度、物料库存与装箱情况。"
description_en: "Warehouse in/out orders, scheduled inbound progress, material inventory and packing status."
---

# 仓储出入库与库存

## 什么时候用

用户问某段时间的出入库单、预约单入库到哪一步了、物料库存还有多少、装箱进度。

## 会用到的工具

| 工具 | 用途 |
|---|---|
| `op_page_query_warehouse_in_order` / `op_get_warehouse_in_order_detail_by_code` | 成品入库单列表与详情【读】 |
| `op_page_query_warehouse_out_order` / `op_get_warehouse_out_detail` | 成品出库单列表与详情【读】 |
| `op_page_query_material_warehouse_in_order` / `op_page_query_material_warehouse_out_order` | 物料出入库单列表【读】 |
| `op_get_material_warehouse_inventory_paged` | 物料库存【读】 |
| `op_get_warehouse_schedule_order_list` / `op_get_warehouse_schedule_order` | 预约单列表与详情【读】 |
| `op_get_warehouse_schedule_order_in_storage_sku_received_quantity` | 预约单已入库 SKU 数量【读】 |
| `op_page_query_warehouse_archives` | 仓库档案【读】 |

## 能力边界（先看这条）

开放平台**没有成品库存查询接口**。库存类只有物料库存
（`op_get_material_warehouse_inventory_paged`）和采购单模块下的款式使用情况
（`op_purchase_order_get_product_sku_inventory`）。

用户问「成品还有多少库存」时，**据实说明这个接口不开放**，
可以改用出入库单据推算并说清这是推算值——不要拿物料库存冒充成品库存。

## 调用流程

1. 按单据类型选对工具（成品 / 物料是两套单据，工具名不同，别混用）。
2. 预约单进度：先取预约单详情，再取已入库 SKU 数量，两者对比。
3. 本地聚合后输出表格，注明统计区间和口径。

## 业务口径从哪来（这个场景最容易错）

预约单和入库单的数量字段有多个相似名字，含义差别很大，**必须先取口径再解释数字**：

- 「可入库数量」「已入库数量」「本次预约数量」各自怎么算，未审核的入库单算不算；
- 入库单来源单据的字段口径（来源指错会出现「超收」）；
- 各类单据审核 / 作废对库存的影响时点。

⚠️ 已知的一处接口与页面差异：预约单接口返回的 `availableInboundQuantity`
**已经把本单预约数扣掉了**，而页面「可入库数量」列没扣，
即 **页面值 = 接口值 + 本次预约数**。两者对不上时按总纲（`lingmao-scm-cloud/SKILL.md`）
「口径冲突」处理——把两个数各自的含义摆给用户，不要折中成一个数。

## 边界

- 审核、反审核、作废、删除、保存预约单都是写操作，本场景默认不调用。
- 出入库单据量大，先用时间区间和仓库过滤再拉，不要无条件全量翻页。
