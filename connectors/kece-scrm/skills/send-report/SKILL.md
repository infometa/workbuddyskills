---
name: send-report
display_name: 群发效果查询
display_name_en: Mass Send Report
description: 查询企微群发任务列表与执行状态，回答最近群发做得怎么样、某次群发是否发出等问题。触发词：群发效果、群发结果、发送情况、送达、任务状态。
description_zh: 查询企微群发任务列表与执行状态，了解发送进展与任务结果。
description_en: Query WeCom mass-send task lists and execution status.
version: 1.0.0
author: 网易云商
allowed-tools: list_mass_send_tasks
examples_zh:
  - 最近几次群发的执行情况怎么样
  - 上周那批 VIP 回流群发发出去了吗
examples_en:
  - How did my recent mass sends perform?
  - Did last week's VIP comeback send go out?
---

# 群发效果查询

## 何时使用

用户询问群发结果、发送状态、最近群发情况时使用。

## 执行顺序

1. 调用 `list_mass_send_tasks` 查询群发任务列表（可按需指定数量）。
2. 若上文群发环节已有任务 ID，优先定位该任务。
3. 用表格或列表展示：任务、状态、创建时间、内容摘要。
4. 用户追问某一条时，展开该任务的字段详情。

## 展示格式

列表：

```
1. [状态] 内容摘要 | 创建时间
2. ...
```

## 规则

- 状态含义以接口 `flag` 字段为准，无法确定时如实说明，不要编造。
- 接口未返回的深度统计（如送达率、未发送原因明细）不要杜撰；用户追问时引导其到科策后台查看。
- 手机号等敏感信息脱敏展示。
- 查询类操作无需确认，直接执行。
