---
name: "scm-daily-ops-brief"
description: "用户要每日运营简报、早会汇总、今天整体情况时触发；会连续调用多个工具，消耗较多配额"
version: "1.0.1"
author: "领猫科技"
display_name: "每日运营简报"
display_name_en: "Daily Operations Brief"
description_zh: "跨模块聚合的每日简报：采购、生产、仓储、财务四块概况与异常清单。"
description_en: "Cross-module daily brief: purchasing, production, warehousing and finance overview with exceptions."
---

# 每日运营简报

## 什么时候用

用户说「今天情况怎么样」「出一份早会简报」「日报」。

## 先说成本

这个场景一次要调 6–10 个工具，配额消耗明显（读 1 单位 / 写 2 单位）。
**执行前先告诉用户大致会查哪几块**，用户确认后再开始；
也可以问用户只要其中一两块，不必每次都拉全。

## 调用流程

1. `health` —— 拿租户名与配额余量。**余量不够时先告诉用户，不要跑到一半失败。**
2. `list_capabilities` —— 确认哪些模块有授权。**没授权的板块直接跳过并在报告里注明
   「未授权，未纳入」**，不要因为缺一块就中断整份简报。
3. 按已授权的模块分块取数，各块用对应场景 skill 里的工具：
   - 采购：`op_get_purchase_order_list_paged`（今日新增 / 未审核）
   - 生产：`op_thrid_party_page_query_order_follow_ups`（在跟进 / 异常）
   - 仓储：`op_page_query_warehouse_in_order`、`op_page_query_warehouse_out_order`（今日出入库）
   - 财务：`op_get_payable_list_paged`（应付概况）
4. 汇总成报告：顶部 4 个数字 + 异常清单（按严重度排序）+ 与昨日对比。

## 报告纪律

- **每个数字都要注明是哪个单据、什么时间口径**（创建时间还是审核时间），
  否则用户没法核对，简报就变成了不可信的装饰。
- 与昨日对比时说明对比方式；数据不足以对比就不写同比，不要编。
- 未授权、接口报错、知识库未覆盖的部分，在报告末尾单列「本次未覆盖」，不要静默省略。

## 边界

- 全程只读，简报场景**不做任何写操作**。
- 单块数据量大时只取汇总数 + 前 10 条明细，不要把全部明细堆进报告。
