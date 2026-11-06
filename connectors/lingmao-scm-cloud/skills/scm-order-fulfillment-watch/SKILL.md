---
name: "scm-order-fulfillment-watch"
description: "用户关注订单履约、生产进度、节点异常或交期风险时触发"
version: "1.0.1"
author: "领猫科技"
display_name: "订单与生产跟进监控"
display_name_en: "Order & Production Follow-up"
description_zh: "销售订单、订单需求与生产跟进：排产进度、交期风险与节点异常。"
description_en: "Watch sales orders, demands and production follow-up: progress, delivery risk and node exceptions."
---

# 订单与生产跟进监控

## 什么时候用

用户问订单排产到哪了、哪些单要延期、有没有异常汇报、某款生产计划是什么。

## 会用到的工具

| 工具 | 用途 |
|---|---|
| `op_get_sales_order_list_paged` / `op_get_sales_order_detail` | 销售订单列表与详情【读】 |
| `op_order_demand_pagination_query` / `op_order_demand_info` | 订单需求列表与详情【读】 |
| `op_thrid_party_page_query_order_follow_ups` | 订单跟进列表——生产进度主入口【读】 |
| `op_order_follow_up_detail` | 单张订单跟进详情【读】 |
| `op_order_follow_up_get_production_plans` | 生产计划信息【读】 |
| `op_get_order_follow_up_exception_record` | 节点异常汇报记录【读】 |

## 调用流程

1. 先用订单跟进列表定位单据，拿到跟进 Id 后再取详情——直接按业务单号查生产计划
   可能返回空序列，那通常表示「这张单还没进跟进流程」，不是接口坏了。
2. 超期判断在本地算（交期 vs 当前时间），并**说明用的是哪个日期字段**。
3. 输出三段：今日新增、超期风险、异常单，每段给单号 + 关键字段，不要只给数量。

## 业务口径从哪来

- 生产跟进的节点有哪些、节点完成的判定条件；
- 异常汇报的类型与处理流程，「已解决」意味着什么；
- 订单需求、销售订单、生产跟进三者的关系（哪个先生成、哪个字段串起来）。

这些口径接口里没有，按总纲（`lingmao-scm-cloud/SKILL.md`）的规则调 `ask_knowledge`。

## 边界

- 本场景默认只读。进度汇报、异常增删、解决异常都是写操作，
  **不要在监控类问题里顺手调用**；用户明确要求时再单独确认后执行。
- 订单跟进是只读区，扩展字段的回写要走款式 / SKU，不在本场景范围内。
