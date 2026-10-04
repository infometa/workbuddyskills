---
name: dingdanbao-stock
description: "订单豹库存快查、预警与出入库/调拨/盘点。"
description_zh: "商品库存、缺货积压预警、出入库、调拨、盘点与组装拆分。"
description_en: "Product stock, out-of-stock and overstock alerts, inbound/outbound, transfers, inventory counts, and assembly/disassembly."
version: "1.0.0"
author: "订单豹"
---

# 订单豹 · 库存

查商品库存、预警、出入库、调拨、盘点和组装拆分。

## 认证说明

登录失败时请用户打开连接器设置重填账号密码。不要在对话里要密码。

## 对用户说话

只说商品名、仓库名、单号和数量。不要说内部编号或工具名。

## 模型路由（不要向用户复述）

本技能不下单、不提交采购补货计划。

## 可用工具

### ddb_search_sku_stock

按商品关键词查库存。参数：`keyword`(必填)、`stash_id`、`stash_keyword`、`page`、`page_size`。

### ddb_get_sku_stock_map

某 SKU 分仓库存。参数：`sku_id` 或 `keyword`。

### ddb_stock_warning_overview

预警总览。参数：`stash_id`。

### ddb_stock_warning_above / ddb_stock_warning_below / ddb_stock_warning_out_of_stock

超上限 / 低于下限 / 缺货。参数：`stash_id`、`page_size`。

### ddb_list_out_storage

出库单列表。参数：`status`、`out_type`、`stash_id`、`out_storage_no`、`relation_no`、`sku_name`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_list_put_storage

入库单列表。参数：`status`、`put_type`、`stash_id`、`put_storage_no`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_list_swap

调拨单。参数：`status`、`stash_id`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_list_inventory

盘点单。参数：`status`、`stash_id`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_list_assembly

组装拆分单。参数：`status`、`as_type`、`as_no`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_out_storage_detail / ddb_swap_detail / ddb_inventory_detail / ddb_assembly_detail

详情。参数：`id`(内部单据 ID，对用户展示单号)。

## 使用示例

- 「酱油还剩多少」→ `ddb_search_sku_stock`。
- 「哪些货缺货 / 积压」→ warning 系列。
- 「今天出库单 / 看看这张调拨单」→ 列表再详情。

## 错误场景

| 现象 | 处理 |
|------|------|
| 请提供商品关键词 | 向用户要商品名 |
| 登录失败 | 设置页重填 |
| 单号找不到 | 放宽时间或仓库筛选后再查 |
