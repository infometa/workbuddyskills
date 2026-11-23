---
name: smart-targeting
display_name: 智能圈人
display_name_en: Smart Targeting
description: 根据业务意图推荐并筛选目标客户人群，支持按标签、时间、客层等条件组合筛选。触发词：圈人、找客户、找用户、人群、筛选、回流、拉新、促活、沉默用户。
description_zh: 根据业务意图推荐并筛选目标客户人群，支持按标签、时间、客层等条件组合筛选，并预估人数。
description_en: Recommend and filter target customer audiences by tags, time, and segments, with audience size estimation.
version: 1.0.0
author: 网易云商
allowed-tools: get_customer_fields, search_customers, list_segments, create_segment, import_segment
examples_zh:
  - 帮我找最近14天没互动、且打了VIP标签的客户，看看有多少人
  - 有哪些现成的人群包可以直接用
  - 把这批筛选出来的客户存成一个人群包
examples_en:
  - Find customers with the VIP tag who haven't interacted in 14 days
  - What audience segments already exist?
  - Save this filtered group as a segment
---

# 智能圈人

## 何时使用

用户描述业务目标（回流、拉新、促活、活动触达）或直接给出筛选条件时使用。目标是产出一组可交给群发环节的人群条件。

## 执行顺序

1. 调用 `get_customer_fields` 获取该企业的标签组与标签选项 ID。**每次会话首次使用必须先查，严禁猜测 ID。**
2. 把用户意图映射为 2–3 个候选条件组合，用业务语言说明每个方案的理由与取舍。
3. 对每个方案调用 `search_customers` 估算人数（只取总数时 `pageSize` 传 1）。
4. 用户调整条件后，重新调用 `search_customers` 并展示新人数。
5. 用户确认后，把最终条件整理成一段自然语言摘要，并保留工具参数，交给群发环节。

## 工具与关键参数

### get_customer_fields

无参数。返回全部客户字段定义。标签类字段的 `type`：`4` = 单选标签，`5` = 多选标签，其 `options` 里是可选标签项。

### search_customers

| 参数 | 说明 |
|---|---|
| `filterType` | `quick` 快捷筛选 / `advanced` 多条件 / `segment` 按人群包 |
| `filterFields` | 数组，每项 `{ fieldId: string, filterType: number, filterValue: string }` |
| `segmentIds` | 数字数组，`filterType=segment` 时使用 |
| `page` / `pageSize` | 分页，`pageSize` 最大 100；只看人数时传 1 |

`filterFields[].filterType` 取值：

| 值 | 含义 |
|---|---|
| 1 | 满足 / 包含 |
| 2 | 不为空 |
| 3 | 包含所有 |
| 4 | 不包含 |
| 5 | 等于 |
| 6 | 不等于 |
| 7 | 介于 |
| 8 | 大于 |
| 9 | 小于 |

### list_segments / create_segment / import_segment

仅在用户明确要求"存成人群包、以后复用"时使用。默认路径是**不建包**，把条件直接带到群发环节。

## 规则

- 严禁猜测字段 ID、标签 ID、标签选项 ID，必须先查 `get_customer_fields`。
- 人数为 0 时主动建议放宽条件；人数超过 50000 时提示缩小范围或分批。
- 展示条件时使用业务语言（如"沉默超过 14 天 + VIP"），不要暴露 `fieldId`、`filterType` 等技术参数。
- 锁定人群前必须经用户确认，确认内容包含：条件摘要、预估人数、是否建包。
- 用户意图不明确时追问，不要自行假设。
- 手机号等敏感信息脱敏展示。
