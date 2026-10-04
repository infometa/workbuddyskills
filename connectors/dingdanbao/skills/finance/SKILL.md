---
name: dingdanbao-finance
description: "订单豹催款、收款码与财务查询。"
description_zh: "客户欠款、待收款、收款码、收付款记录与财务总览。"
description_en: "Customer outstanding balances, pending collections, payment QR codes, payment records, and finance overview."
version: "1.0.0"
author: "订单豹"
---

# 订单豹 · 财务

催款、待收款和欠款订单、收款码，以及收付款记录与财务总览。生成收款码前必须已确定客户、欠款订单和金额，禁止自动选单。

## 认证说明

登录失败时请用户打开连接器设置重填账号密码。不要在对话里要密码。

## 对用户说话

只说客户名、订单号、金额。不要说内部编号或工具名。

## 模型路由（不要向用户复述）

出收款码用本技能，不要用订单分享海报代替。欠款客户名单、掉单预警用客户技能。

## 可用工具

### ddb_get_customer_debt

客户欠款。参数：`keyword` 或 `member_id`。

### ddb_list_pending_receipt_orders

待收款订单。参数：`page`、`page_size`、`keyword`。

### ddb_list_debt_orders

欠款订单。参数：`page`、`page_size`、`keyword`、`member_id`。

### ddb_create_receipt_qrcode

生成收款码。须用户确认客户、订单、金额后再调。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| member_id / keyword | string | ✅ 其一 | 客户 |
| order_id / order_no | string | ✅ 其一 | 欠款订单 |
| amount | string | ✅ | 收款金额（元） |
| discount_amount | string | - | 优惠，默认 0 |

### ddb_get_collection_list

收款记录。参数：`period`(默认 month)、`start_time`、`end_time`、`keyword`、`page`、`page_size`。

### ddb_get_payment_list

付款记录。参数：`period`、`start_time`、`end_time`、`page`、`page_size`。

### ddb_get_debt_summary

欠款汇总。参数：`keyword`。

### ddb_get_finance_overview

财务总览。参数：`period`、`start_time`、`end_time`。

## 使用示例

- 「王老板还欠多少，帮我出个收款码」→ 查欠款 → 列出欠款订单让用户选 → 确认金额 → `ddb_create_receipt_qrcode`。
- 「这个月收了多少钱」→ `ddb_get_collection_list` 或 `ddb_get_finance_overview`。

## 错误场景

| 现象 | 处理 |
|------|------|
| 请先选择客户/欠款订单/金额 | 补齐三要素，不要猜测 |
| 登录失败 | 设置页重填 |
| 金额无效 | 让用户给大于 0 的金额 |
