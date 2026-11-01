---
name: aike-marketing-feedback
display_name: 营销结果分析
display_name_en: Marketing Feedback
description: 查询营销邮件任务的结果反馈：先看营销任务列表（各状态发送计数）与最近业务通知，选定任务后再查该任务的发送统计（送达率/打开/回复）与逐封邮件投递状态。当用户说"看下这周XX任务的反馈""分析下营销意向度""谁回复了我的邮件"时触发。
description_zh: 营销任务列表与最近业务通知，下钻单任务发送统计（送达/打开/回复）与逐封邮件投递状态。
description_en: Marketing task list and per-task email delivery, open and reply statistics.
category: sales-commerce
version: 1.1.0
author: AI销客
---

# 营销结果分析

面向「客户管理专家」的营销反馈查询技能（营销任务的"生成/发送"仍在外贸销客系统内完成，本技能只查结果）。

## 功能描述

- 查询营销任务列表：任务编号 / 名称 / 状态 + 各状态发送计数（已发 / 待发 / 失败 / 退信）
- 查看最近业务通知（营销任务完成 / 客户邮件回复）
- 选定任务后下钻：发送统计（总数 / 已发 / 待发 / 失败 / 已回复 / 送达率 / 打开数与打开率 / 异常数）+ 逐封邮件的投递与回复状态
- 聚合分析客户意向度（谁回复了、回复了几次、最近回复时间），辅助给出跟进建议

## 触发场景（自然语言示例）

- "看下营销反馈"
- "上周那次群发效果怎么样？"
- "谁回复了我的邮件？"
- "分析下这些营销反馈，谁意向最高？"

## 交互流程：先问清查询条件，再两步下钻

工具**没有时间范围 / 客户 / 动作类型的过滤参数**，查询范围靠"澄清 + 两步交互"收窄：

0. **先澄清查询条件（用户问题宽泛时必做，勿直接调工具）**：用户只说"看下营销反馈""效果怎么样"时，先向用户问清再查询，一次问全：
   - **范围**：看全部任务的概览，还是某个任务的逐封明细？
   - **任务筛选**：有心里的任务名 / 编号吗？（可转 `keyword` 模糊匹配）；要按状态筛吗？（`status`：`executing` 进行中 / `completed` 已完成 / `failed` 失败等）
   - **时间**：用户说"这周 / 上周"时，工具没有时间过滤参数——列任务后按 `createdAt` / `completedAt` 在客户侧挑出落在时间窗内的任务，向用户确认
   - **关注点**：更关心**谁回复了**（要下钻看回复名单），还是整体**送达 / 打开率**（概览即可）？
   - 用户已明确点名任务、或明确说"看全部任务列表"时不必追问，直接进入查询
1. **先看任务面**：需要概览或用户未指明任务时，**不带 `task_id`** 调用（可用 `keyword` / `status` 收窄），返回营销任务列表 + 最近业务通知
2. **让用户选任务**：把任务清单呈现给用户（编号 / 名称 / 状态 / 发送计数），确认要看哪一个
3. **再下钻明细**：带该任务 `task_id` 重新调用，拿到 `stats` 发送统计 + 逐封邮件状态
4. **聚合建议**：按 `replied` / `replyCount` / `latestReplyAt` 找出已回复客户，结合 `openedEmailCount` / `openRate` / `deliveryRate` 给出"优先跟进"提示

> 示例 A（宽泛提问 → 先澄清）：
> 用户："看下营销反馈"
> 专家（**先问，不调工具**）："您是想看全部任务的概览，还是某个任务的逐封明细？有没有指定的任务或状态（进行中/已完成）？想重点看回复名单还是送达打开情况？"
> 用户："就看上周广交会那次，谁回复了"
> 专家：调用 `get_marketing_feedback({ keyword: '广交会' })` → 按 `createdAt` 确认是上周那次 → 展示任务并确认："是这个『广交会群发』吗？" → 用户确认后带 `task_id` 下钻 → 呈现统计 + 已回复客户清单 + 跟进建议
>
> 示例 B（明确提问 → 直接查）：
> 用户："看下全部营销任务的状态"
> 专家：直接调用 `get_marketing_feedback({})` 展示任务清单，无需追问

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`full` 开关**：读工具默认 `full=false`，返回精简字段；显式 `full=true` 返回后端原始全量字段。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供；本技能只查结果、不代发。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:marketing:tasks:list；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`404`=任务 id 不存在 → 先列任务确认 id 再下钻。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用（任务列表 / 任务邮件端点 2026-09-04 D-045 起挂码，**连接器授权已包含该权限**；通知端点同面开放）：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `get_marketing_feedback` | 营销任务列表 + 最近业务通知 / 任务详情下钻 | `pc:marketing:tasks:list` | ✅ 已开放 |

## 工具调用说明

### `get_marketing_feedback`

- **行为（关键）**：
  - **不带 `task_id`** → 任务列表模式：返回**营销任务列表 + 最近业务通知**
  - **带 `task_id`** → 任务详情模式：返回该任务的**发送统计**与**逐封邮件状态**
- **入参**：
  - `task_id`（string uuid，可选）：营销任务 id（带上即进入任务详情模式）
  - `keyword`（string，可选）：按任务编号/名称模糊匹配（仅任务列表模式）
  - `status`（enum，可选）：任务状态过滤（仅任务列表模式），`draft`（草稿）/ `executing`（执行中）/ `completed`（已完成）/ `partial_failed`（部分失败）/ `failed`（失败）
  - `page`（int，可选，默认 1）
  - `pageSize`（int，可选，上限 50；任务列表模式默认 10，任务详情模式默认 20）
  - `full`（boolean，可选，默认 `false`）
- **返回（任务列表模式）**：`{ tasks: { total, page, pageSize, items[] }, recentNotifications[] }`
  - `tasks.items[]` 每项：`id` / `taskCode`（任务编号）/ `taskName` / `type` / `status` / `createdAt` / `completedAt` / `totalToGenerate`（计划生成数）/ `sentCount`（已发）/ `pendingSendCount`（待发）/ `sendFailedCount`（发送失败）/ `bouncedCount`（退信）
  - `recentNotifications[]` 每项：`id` / `title` / `content` / `category` / `isRead` / `createdAt` / `taskStatus` / `actionType`（有值时附 `emailSubject`）
- **返回（任务详情模式）**：`{ stats, total, page, pageSize, items[] }`
  - `stats`：`{ total, sent, pending, failed, replied, deliveryRate, openedEmailCount, openRate, abnormalCount }`——`deliveryRate` / `openRate` 为 0~1 小数（`openRate` 送达数为 0 时为 null）
  - `items[]` 每封邮件：`id` / `customerName` / `recipientEmail` / `recipientName` / `emailSubject` / `status` / `actualSentAt`（实际发送时间）/ `replied`（是否已回复）/ `replyCount`（回复次数）/ `latestReplyAt`（最近回复时间）/ `sendError`（失败原因）
- **口径边界**：
  - "打开"只在 `stats` 里聚合（`openedEmailCount` / `openRate`），**没有逐封打开明细**
  - "链接点击"明细不在本工具返回内（点击追踪未接入 MCP 工具面）；用户问"谁点了链接"时如实说明

## 返回格式

- 不带 `task_id`：任务清单卡（编号 / 名称 / 状态 / 发送计数）+ 最近业务通知
- 带 `task_id`：统计卡（送达率 / 打开率 / 回复数）+ 逐封邮件列表（按回复/失败置顶）
- 专家层结合 `replied` / `replyCount` / `latestReplyAt` 给出"优先跟进建议"，并可衔接「查客户」「写跟进」「我的待办」
