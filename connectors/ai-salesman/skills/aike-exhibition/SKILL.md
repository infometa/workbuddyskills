---
name: aike-exhibition
display_name: 展会查询
display_name_en: Exhibitions
description: 查询展会信息，按名称模糊匹配、按阶段（即将开始/进行中/已结束）或参展人过滤检索展会。当用户说"最近有什么展会""广交会什么时候开始""查下我参加的那个展会"时触发。
description_zh: 按名称、阶段（即将开始/进行中/已结束）或参展人检索展会。
description_en: Search exhibitions by name, stage or participant.
category: sales-commerce
version: 1.0.0
author: AI销客
---

# 展会查询

面向「展会现场专家」与「客户管理专家」的展会检索技能。

## 功能描述

- 按名称模糊匹配、按**阶段**、按**参展人**查询展会
- 返回展会名称、起止时间、阶段、参展人数等关键信息
- 查到的展会 id 可衔接「上传对话录音」（`exhibition_id`）与「新增客户」（现场建档）

## 触发场景（自然语言示例）

- "最近有什么展会？"
- "广交会什么时候开始？"
- "查下我参加的那个展会"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`full` 开关**：读工具默认 `full=false`，返回精简字段；显式 `full=true` 返回后端原始全量字段。
- **分页**：`page`（默认 1）、`pageSize`（默认 10，上限 50）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:exhibitions:list；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`participantUserId` 必须是数字用户 id，传姓名查不到时改用名称模糊搜索。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `search_exhibitions` | 检索展会信息 | `pc:exhibitions:list` | ✅ 已开放 |

## 工具调用说明

### `search_exhibitions`
- **用途**：查展会列表（newest first）
- **入参**：
  - `name`（string，可选）：展会名称，模糊匹配（注意参数名是 `name`，不是 `keyword`）
  - `stage`（enum，可选）：阶段过滤，`upcoming`（即将开始）/ `ongoing`（进行中）/ `finished`（已结束）
  - `participantUserId`（int，可选）：按参展人员过滤，传**用户 id**（数字），不是姓名字符串
  - `page`（int，可选，默认 1）
  - `pageSize`（int，可选，默认 10，上限 50）
  - `full`（boolean，可选，默认 `false`）
- **返回**：`{ total, page, pageSize, items[] }`；`items` 每项字段：
  - `id`（string）：展会 id（衔接上传录音 / 建档用）
  - `name`：展会名称
  - `startTime` / `endTime`：起止时间
  - `stage`：阶段（`upcoming` / `ongoing` / `finished`）
  - `participantCount`：参展人数
  - `updatedAt`
- **注意**：精简字段不含地点 / 展品范围等（若后端有），需要时传 `full=true`；按"我参加的"过滤时先拿到当前用户的数字 id 再传 `participantUserId`。

## 返回格式

- 列表卡：名称 + 起止时间 + 阶段 + 参展人数
- 可衔接「上传对话录音」（带 `exhibition_id`）与「新增客户」（展会现场获客）
