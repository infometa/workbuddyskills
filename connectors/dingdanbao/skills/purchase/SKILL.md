---
name: dingdanbao-purchase
description: "订单豹 AI 补货计划与采购单跟进。"
description_zh: "AI 补货计划、采购单查询与采购入库跟进。"
description_en: "AI replenishment plans, purchase order lookup, and inbound tracking."
version: "1.0.0"
author: "订单豹"
---

# 订单豹 · 采购

生成补货计划、调整后提交采购，以及采购单状态和入库跟进。提交采购必须用户确认。

## 认证说明

登录失败时请用户打开连接器设置重填账号密码。不要在对话里要密码。

## 对用户说话

只说供应商名、采购单号、商品名和数量。不要说内部编号、会话键或工具名。

## 模型路由（不要向用户复述）

本技能不查销售订单。商品还剩多少用库存技能。

## 可用工具

### ddb_replenish_generate_plan

生成补货计划。参数：`category_id`、`category_name`、`months`(默认 3)、`safety_days`(默认 7)、`stash_id`、`keyword`。返回 `sessionKey` 与计划摘要；向用户讲清建议采购量后再问是否提交。

### ddb_replenish_adjust_plan

改某 SKU 建议数量。参数：`session_key`、`sku_id`、`num` 均必填。

### ddb_replenish_remove_from_plan

从计划移除 SKU。参数：`session_key`、`sku_id`。

### ddb_replenish_submit_plan

用户确认后提交采购计划。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| session_key | string | ✅ | 计划会话 |
| supplier_id | string | ✅ | 供应商 |
| purchase_user_id | string | ✅ | 采购人 |
| delivery_time | string | - | 交货日 |
| stash_id / department_id / remark | string | - | 可选 |

提交前用 `ddb_list_suppliers`、`ddb_list_purchase_users`、`ddb_list_stashes` 让用户选可读名称。

### ddb_replenish_stock_warning

补货用库存预警。参数：`stash_id`、`status`。

### ddb_list_suppliers / ddb_list_purchase_users / ddb_list_stashes

供应商、采购人、仓库。无业务参数。

### ddb_list_supplier_goods

供应商商品。参数：`supplier_id`(必填)、`goods_name`、`page`、`page_size`。

### ddb_list_purchase_orders

采购单列表（不是销售订单）。参数：`status`、`supplier_id`、`search_type`、`search_content`、`start_time`、`end_time`、`creator_id`、`page`、`page_size`。

### ddb_purchase_tab_counts

采购各状态数量。参数：`supplier_id`、`creator_id`。

### ddb_purchase_order_detail

采购单详情。参数：`id`。

### ddb_purchase_put_storage_list

采购单关联入库。参数：`id`。

## 使用示例

- 「按调味品最近三个月销量做补货」→ generate_plan → 展示摘要 → 用户确认供应商和采购人 → submit_plan。
- 「待入库采购单」→ `ddb_list_purchase_orders` + tab_counts。

## 错误场景

| 现象 | 处理 |
|------|------|
| 计划中没有需要采购的商品 | 放宽品类或安全天数后重算 |
| 请选择供应商/采购人 | 先 list 再让用户选 |
| 登录失败 | 设置页重填 |
