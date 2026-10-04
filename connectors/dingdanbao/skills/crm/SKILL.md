---
name: dingdanbao-crm
description: "订单豹客户档案、画像、发券与客户预警。"
description_zh: "客户档案、最近订单、画像、发券与客户预警。"
description_en: "Customer profiles, recent orders, customer personas, issuing coupons, and customer alerts."
version: "1.0.0"
author: "订单豹"
---

# 订单豹 · 客户

查客户档案、最近订单、常购、TOP 客户、画像、发券与预警。

## 认证说明

登录失败时请用户打开连接器设置重填账号密码。不要在对话里要密码。

## 对用户说话

只说姓名、手机号、订单号、金额。不要说内部编号或工具名。

## 模型路由（不要向用户复述）

本技能不创建销售订单。某客户欠多少、出收款码用财务技能。

## 可用工具

### ddb_get_customer_profile

客户档案。参数：`keyword` 或 `member_id`。多人时列出供用户选择，勿自动挑。

### ddb_list_customer_recent_orders

最近订单。参数：`keyword` / `member_id`、`page`、`page_size`。展示订单号与金额，不展示内部 ID。

### ddb_list_customer_frequent_goods

常购商品。参数：`keyword` / `member_id`、`page`、`page_size`。

### ddb_list_top_customers

销售 TOP 客户。参数：`limit`(默认 10)、`start_time`、`end_time`、`sort_field`(默认 total_goods_money)。

### ddb_get_customer_portrait

客户画像。参数：`keyword` 或 `member_id`。

### ddb_list_member_coupons

客户优惠券。参数：`keyword` 或 `member_id`。

### ddb_send_coupon

给客户发券。**必须用户明确确认**后再调用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword / member_id | string | ✅ 其一 | 客户 |
| salesman_coupon_id | string | - | 指定券 |
| coupon_keyword | string | - | 按名称选券 |

### ddb_get_warning_summary

预警汇总。无参数。

### ddb_list_warning_customers

预警客户。参数：`warning_type`(默认 order_down)、`page`、`page_size`、`keyword`、`salesman_id`。

### ddb_list_debt_customers

欠款客户。参数：`page`、`page_size`、`keyword`。

### ddb_list_high_risk_overdue

高风险逾期。参数：`min_overdue_days`(默认 30)、`page`、`page_size`。

## 使用示例

- 「王老板是谁 / 最近买过什么」→ profile + recent orders。
- 「这个月 TOP10 客户」→ `ddb_list_top_customers`。
- 「给张三发一张满减券」→ 先查券列表，用户确认后再 `ddb_send_coupon`。
- 「哪些客户掉单 / 欠款很久」→ warning / debt / overdue。

## 错误场景

| 现象 | 处理 |
|------|------|
| 登录失败 | 设置页重填凭证 |
| 匹配到多个客户 | 列出姓名+手机号，让用户选 |
| 发券失败 | 展示错误，不要连发多张 |
