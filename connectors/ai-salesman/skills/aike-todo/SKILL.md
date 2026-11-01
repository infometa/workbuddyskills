---
name: aike-todo
display_name: 我的待办
display_name_en: My Todos
description: 我的待办事项管理，支持待办的查看（可按完成状态/来源录音/截止时间范围过滤）、新增、完成、修改、删除等完整 CRUD 操作。当用户说"我今天还有什么待办""这周有哪些要逾期的事""加个待办""把这条待办标记完成"时触发。
description_zh: 待办的查看（含截止时间范围筛选）、新增、完成、修改、删除等完整 CRUD。
description_en: Full CRUD management of todo items in GlobalSales Foreign Trade Salesman.
category: sales-commerce
version: 1.2.0
author: AI销客
---

# 我的待办

面向「客户管理专家」的待办管理技能，覆盖增删改查与状态流转。

## 功能描述

- 查看待办列表（全部 / 按完成状态 / 按来源录音 / 按截止时间范围，2026-09 起新增时间筛选）
- 新增待办（可关联客户）
- 修改待办内容 / 优先级 / 截止时间 / 关联客户
- 变更待办状态（完成 / 重新打开）
- 删除待办（二次确认）

## 触发场景（自然语言示例）

- "我今天还有什么待办？"
- "加个待办：明天跟进 ABC 公司报价"
- "把这条待办标记完成"
- "删掉上周那个过期的待办"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`full` 开关**：读工具默认 `full=false`，返回精简字段（省 token）；显式 `full=true` 返回后端原始全量字段。
- **分页**：`page`（默认 1）、`pageSize`（**`list_todos` 默认 20**，上限 50）。
- **`dry_run` 预演**：创建 / 修改类写工具支持 `dry_run=true`，仅回显载荷、**不落库**；默认 `false` 正式写入。建议信息不全时先 `dry_run=true` 预演、经用户确认再正式写入。
- **`confirm` 二次确认**：删除类（`delete_todo`）先不带 `confirm` 返回确认提示；用户确认后带 `confirm=true` 才执行（不可恢复）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:dashboard；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；删除待办忘记带 `confirm=true` 时会返回确认提示，向用户复述摘要确认后再执行。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用（2026-09-04 D-045 起待办端点统一挂 `pc:dashboard` 码，连接器授权已包含该权限）：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `create_todo` | 新增待办 | `pc:dashboard` | ✅ 已开放 |
| `list_todos` | 查询待办列表 | `pc:dashboard` | ✅ 已开放 |
| `update_todo` | 修改待办内容 | `pc:dashboard` | ✅ 已开放 |
| `set_todo_status` | 变更待办状态 | `pc:dashboard` | ✅ 已开放 |
| `delete_todo` | 删除待办 | `pc:dashboard` | ✅ 已开放 |

## 工具调用说明

### `create_todo`
- **用途**：新增一条待办
- **入参**：
  - `title`（string，**必填**，1-500 字）：待办内容
  - `priority`（int，可选）：优先级，数值越大越优先
  - `due_date`（string，可选）：建议截止时间（ISO 8601）
  - `customers`（object[]，可选）：关联客户列表，元素 `{ id, name }`（id 为客户 id，name 为客户名）
  - `audio_record_id`（string，可选）：关联来源录音 ID（须属于当前用户；把待办挂到某段快记上，`get_recording` 返回的 id）（2026-09 补齐）
  - `dry_run`（boolean，可选，默认 `false`）：为 `true` 时返回 `{ dryRun: true, wouldCreate: <载荷> }`，不落库
- **返回**：`{ id, title, dueDate, message }`
- **注意**：`audio_record_id` 只是关联展示（列表的 audioName/recordCode 随之带出）；快记自动派生的待办由系统创建，本工具建的都是 manual 来源。

### `list_todos`
- **用途**：查询待办列表（分页）
- **入参**：
  - `status`（enum，可选）：完成状态过滤，**字符串** `'0'`=未完成、`'1'`=已完成；不传=全部
  - `audio_record_id`（string，可选）：按来源录音 ID 过滤
  - `due_date_from` / `due_date_to`（string，可选，2026-09 新增）：截止时间范围（ISO 8601，如 `2026-09-21`）；"逾期待办"= `due_date_to` 传当前时刻 + `status='0'` 服务端筛出
  - `page`（int，可选，默认 1）
  - `pageSize`（int，可选，默认 20，上限 50）
  - `full`（boolean，可选，默认 `false`）
- **返回**：`{ total, page, pageSize, items[] }`；`items` 每项字段：
  - `id`（string）：待办 id
  - `title`（string）：待办内容
  - `priority`（int）：优先级
  - `dueDate`（string | null）：截止时间
  - `status`（int）：1=已完成，0=未完成
  - `source`：来源（`manual` 手建 / `ai` 快记 AI 派生）
  - `audioName` / `recordCode`：来源录音名 / 编号（快记来源时）
  - `createdAt`（string）：创建时间
  - `customers[]`：关联客户，仅 `{ id, name }`
- **注意**：`due_date_from` / `due_date_to` 按 `dueDate` 过滤，`dueDate` 为空的待办不会被时间范围命中。

### `update_todo`
- **用途**：修改待办，只传需要修改的字段；一个字段都不传时报错「未提供任何要修改的字段」
- **入参**：
  - `id`（string uuid，**必填**）：待办 id（`list_todos` 拿到）
  - `title`（string，可选，1-500 字）
  - `priority`（int，可选）
  - `due_date`（string，可选，ISO 8601）
  - `customers`（object[]，可选）：关联客户，**整体替换**（传全量，而非增量），元素 `{ id, name }`
  - `dry_run`（boolean，可选，默认 `false`）：为 `true` 时返回 `{ dryRun: true, id, wouldUpdate: <载荷> }`
- **返回**：`{ id, message }`

### `set_todo_status`
- **用途**：把待办标记为已完成，或把已完成的重新打开
- **入参**：
  - `id`（string uuid，**必填**）：待办 id
  - `completed`（boolean，**必填**）：`true`=标记完成，`false`=重新打开
  - `dry_run`（boolean，可选，默认 `false`）
- **返回**：`{ id, status, message }`（`status`：1=已完成，0=未完成）
- **注意**：入参是布尔 `completed`，不是 `status` 枚举字符串。

### `delete_todo`
- **用途**：删除待办（不可恢复）
- **入参与流程**：
  - 第一次调用只传 `id`（`confirm` 省略或 `false`）→ 返回 `{ confirmRequired: true, id, message }`，**不删除**
  - 用户确认后，第二次调用带 `confirm: true` → 执行删除
- **返回**：确认阶段见上；删除成功 `{ id, message: '待办已删除' }`

## 返回格式

- 列表场景：以清单呈现，标注截止时间、优先级与完成状态（`status` 0/1）
- 操作场景：返回 `{ id, message }` 类操作结果
- 删除场景：必须先预览确认再执行，向用户复述将删除的待办标题
