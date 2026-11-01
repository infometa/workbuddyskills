---
name: aike-follow-record
display_name: 写跟进
display_name_en: Follow-up
description: 为指定客户新增一条跟进记录，记录洽谈内容与下一步计划。当用户说"给 XYZ 公司写条跟进""记录一下刚和 ABC 的电话沟通"时触发。
description_zh: 为指定客户写一条跟进记录（洽谈内容与下一步计划）。
description_en: Add a follow-up record with notes and a next-step plan to a customer.
category: sales-commerce
version: 1.1.0
author: AI销客
---

# 写跟进

面向「客户管理专家」的跟进记录创建技能。

## 功能描述

- 为指定客户新增一条手动跟进记录
- 记录洽谈内容与下一步跟进计划
- 写入后进入客户时间线，在客户管理中可回看

## 触发场景（自然语言示例）

- "给 XYZ 公司写一条跟进"
- "记录一下刚和 ABC 的电话沟通"
- "给这个客户加条跟进：已发报价，等回复"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`dry_run` 预演**：`create_follow_record` 支持 `dry_run=true`，仅回显载荷、**不落库**；默认 `false` 正式写入。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:customers:ls:edit；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`customer_id` 不存在时先 `search_customers` 确认再写。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `create_follow_record` | 新增跟进记录 | `pc:customers:ls:edit` | ✅ 已开放 |

## 工具调用说明

### `create_follow_record`
- **用途**：为指定客户添加一条手动跟进记录
- **入参**：
  - `customer_id`（string uuid，**必填**）：客户 id（先用 `search_customers` / `create_customer` 拿到）
  - `content`（string，可选）：本次跟进/洽谈内容
  - `plan`（string，可选）：下一步跟进计划
  - `follow_time`（string，可选）：跟进时间（ISO 8601），默认当前
  - `exhibition_id`（string uuid，可选）：关联展会 ID（展会期间的跟进可挂展会，2026-09 补齐）
  - `image_urls`（string[]，可选，最多 10 张）：跟进配图地址列表；可传 `presign_file_upload({ kind: "image", file_ext })` 直传完成后的 objectUrl（2026-09 补齐）
  - `dry_run`（boolean，可选，默认 `false`）：为 `true` 时返回 `{ dryRun: true, wouldCreate: <载荷> }`
- **返回**：`{ id, message: '跟进记录已写入客户时间线' }`
- **注意**：
  - 除了 `customer_id` 外其余字段皆可省，但**建议至少写 `content` 或 `plan` 其一**，空跟进对销售无价值
  - **没有"跟进方式 / 渠道"入参**（电话/邮件/微信等不用传，需要时写进 `content` 文案里）
  - 客户不存在 / 无权访问时后端报错，先 `search_customers` 确认 id

## 返回格式

- 成功：返回记录 id 与提示；如需回看可再查该客户详情或客户动态
- 失败（客户不存在 / 无权限）：转述后端错误，提示先确认客户

## 典型链路

1. `search_customers({ customerName: 'XYZ' })` → 拿到 `id`
2. `create_follow_record({ customer_id, content, plan })`
3. 追问："要把'下一步计划'同时建一条待办提醒吗？" → 衔接「我的待办」`create_todo`
