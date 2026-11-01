---
name: aike-priority-followup
display_name: 今日重点跟进
display_name_en: Priority Follow-ups
description: 查询今日核心跟进客户（外贸销客首页工作台"今日核心跟进"）：按跟进指数排序的客户清单，每条含客户、跟进原因、跟进建议、跟进指数(0-100)与紧急级别；支持忽略单条建议或一键转成跟进待办。当用户说"今天该重点跟进哪些客户""为什么推荐我跟进这家""把这条核心跟进转成待办""这条建议不适用别再推了"时触发。
description_zh: 今日核心跟进客户查询（客户/原因/跟进建议/跟进指数）与忽略、转待办动作。
description_en: Query today's priority customers to follow up (customer, reason, suggestion, score) with ignore and convert-to-todo actions.
category: sales-commerce
version: 1.0.0
author: AI销客
---

# 今日重点跟进

面向「客户管理专家」的首页「今日核心跟进」工作台技能：告诉销售今天最该跟进谁、为什么、怎么跟进。

## 功能描述

- 拉取今日核心跟进建议列表（与 PC/APP 首页"今日核心跟进"同一数据源），每条含：**客户、跟进原因、跟进建议、跟进指数（0-100）、紧急级别**
- 忽略单条建议（当日批次内不再出现，幂等）
- 把建议一键转成跟进待办（幂等，重复转换返回原待办）

## 触发场景（自然语言示例）

- "今天该重点跟进哪些客户？"
- "首页工作台里为什么推荐这家？"
- "把第一条核心跟进转成待办"
- "这条建议不适用，别再推了"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **权限口径**：查询仅要求登录态（无权限码）；忽略与转待办两个动作需 `pc:dashboard`（连接器授权已包含）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（动作依赖 pc:dashboard，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`404`=建议行 id 不存在或不在当日批次 → 重新 `get_priority_followups` 取最新列表。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `get_priority_followups` | 查询今日核心跟进建议列表 | 仅登录态 | ✅ 已开放 |
| `ignore_follow_suggestion` | 忽略一条建议 | `pc:dashboard` | ✅ 已开放 |
| `convert_follow_suggestion_to_todo` | 建议转成跟进待办 | `pc:dashboard` | ✅ 已开放 |

## 工具调用说明

### `get_priority_followups`
- **用途**：获取今日核心跟进客户清单（按跟进指数排序，最多 10 条）
- **入参**：**无参数**（数据范围由授权用户身份决定）
- **返回**：`{ available, hint, sourceLabel, suggestions[] }`
  - `available`（boolean）：工作台是否可用；`false` 时 `suggestions` 为空数组
  - `hint`（string）：数据口径提示语
  - `sourceLabel`（string）：数据来源标签（如来自最近跟进与邮件动态）
  - `suggestions[]` 每条字段：
    - `id`（string）：**建议行 id**（忽略 / 转待办用它，**不是客户 id**）
    - `rank`（int）：排序序号（1 起）
    - `score`（int）：跟进指数 0-100，越高越优先
    - `level`（string）：紧急级别，`urgent`（紧急）/ `high`（高）/ `medium`（中）
    - `customerId` / `customerName`：客户 id 与名称（看客户详情用「查客户」技能）
    - `followStatus`（string）：客户当前跟进状态（枚举同客户列表）
    - `urgency`（string）：紧迫度说明
    - `reason`（string）：推荐原因——为什么今天要跟进这家
    - `suggestion`（string）：跟进建议——具体怎么跟进
- **注意**：数据与 PC/APP 首页同源、按日生成批次；`suggestions` 为空即"今日暂无核心跟进建议"，**不要臆造**。

### `ignore_follow_suggestion`
- **用途**：忽略一条今日核心跟进建议（幂等）
- **入参**：
  - `id`（string uuid，**必填**）：建议行 id（`get_priority_followups` 返回的 `suggestions[].id`，非客户 id）
- **返回**：`{ id, message }`
- **注意**：只影响当日列表展示，不改客户数据；无撤销接口，次日按最新数据重新生成。建议先向用户复述要忽略的客户与原因再执行。

### `convert_follow_suggestion_to_todo`
- **用途**：把一条建议转成跟进待办（幂等）
- **入参**：
  - `id`（string uuid，**必填**）：建议行 id（同上，非客户 id）
- **返回**：`{ todoId, created, message }`；`created=false` 表示此前已转过，返回原待办 id
- **注意**：生成的待办在 PC 首页与「我的待办」均可见，后续改期 / 完成等走「我的待办」技能。

## 返回格式

- 清单卡：按 `rank` 排序，每条展示 **客户名 + 跟进指数（score）+ 紧急级别标签（urgent/high/medium）+ 原因 + 建议**，并标注总数与数据来源
- 忽略 / 转待办：返回操作结果；转待办后提示用户在首页待办与「我的待办」可见
- 建议为空：直接告知"今日暂无核心跟进建议"，不要编造数据
