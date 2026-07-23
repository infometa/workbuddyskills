---
name: jinshuju-skill
description: 金数据（Jinshuju，jinshuju.net）操作技能 —— 创建/复制/编辑表单与主题，增删改查与批量修改表单数据，上传图片附件，查询账户套餐与团队成员。触发词：金数据、Jinshuju、jinshuju.net、form_token、表单、报名表、问卷、数据录入、数据查询、批量修改。
version: "1.0.0"
author: "Jinshuju"
---

# 金数据 Skill（Jinshuju）

本 Skill 指导 AI 通过金数据 MCP Server 操作用户托管在 **jinshuju.net** 上的在线表单与数据。所有工具由 MCP 提供，用户完成 OAuth 授权后即可调用。

## 何时使用

满足任一**平台信号**才触发：用户提到「金数据 / Jinshuju / jinshuju.net」、给出 `form_token`、或要操作一张已托管在金数据上的表单或数据（建表、改字段、改主题、增删改查 entries、导出、批量修改）、查询本账户套餐与团队成员。

**不要**用于：用代码开发表单/问卷系统、处理本地 Excel/CSV、图片票据 OCR、与金数据平台无关的通用数据处理。此时不调用任何 MCP 工具。

## 核心概念

- **form_token**：表单唯一标识，出现在表单地址 `https://jinshuju.net/f/<form_token>` 中，几乎所有表单级工具都要它。
- **字段 API 名**：每个字段有稳定的机器名（如 `field_1`、`field_2`），写入/更新数据、下推过滤时用字段 API 名而非中文标题。先 `get_form` 拿字段结构。
- **OAuth scope**：`forms` / `form_setting` / `read_entries` / `write_entries` / `user` / `billing_account`。未授权 scope 调用会报 `Insufficient scope: <name> required`，需提示用户在授权时勾选对应权限。

## 可用工具

### 表单管理（scope: forms / form_setting）

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `list_forms` | 列出可访问的表单 | `name`(正则关键字,可选)、`next`、`limit` |
| `list_folders` | 列出文件夹，取 `folder_token` | — |
| `get_form` | 取表单完整结构（字段、API 名、类型） | `form_token` ✅ |
| `check_field_data` | 写数据前预检字段值是否合法 | `form_token` ✅、`fields` |
| `create_form` | 新建表单 | `name` ✅、`fields` ✅、`folder_token`(可选) |
| `copy_form` | 复制已有表单 | `form_token` ✅ |
| `move_form` | 移动表单到文件夹 | `form_token` ✅、`folder_token` |
| `edit_form` | 编辑表单字段/设置 | `form_token` ✅ |
| `edit_theme` | 调整表单主题外观 | `form_token` ✅ |

### 考试 / 测评表单（scope: forms）

| 工具 | 用途 |
|------|------|
| `create_exam_form` / `edit_exam_form` | 创建/编辑自动判分的考试表单 |
| `create_evaluation_form` / `edit_evaluation_form` | 创建/编辑选项计分的测评表单 |

### 数据管理 Entries（scope: read_entries / write_entries）

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `list_entries` | 按条件查询数据，支持字段值下推过滤 | `form_token` ✅、`filter`、`next`、`limit` |
| `get_entry` | 取单条数据详情 | `form_token` ✅、`entry_id` ✅ |
| `create_entry` | 新增单条数据 | `form_token` ✅、`entry`(字段 API 名→值) ✅ |
| `create_entries` | 批量新增（导入）数据 | `form_token` ✅、`entries`[] ✅ |
| `update_entry` | 更新单条数据 | `form_token` ✅、`entry_id` ✅、`entry` |
| `delete_entry` | 删除单条数据 | `form_token` ✅、`entry_id` ✅ |

### 上传（scope: forms / write_entries）

| 工具 | 用途 |
|------|------|
| `prepare_form_image_upload` | 换取表单头图 / 选项图上传凭证 |
| `prepare_entry_attachment_upload` | 换取 entry 附件字段上传凭证 |

### 账户与团队

| 工具 | 用途 | scope |
|------|------|-------|
| `get_current_user` | 当前用户信息 | `user` |
| `get_current_billing_account` | 企业套餐与用量 | `billing_account` |
| `list_account_users` | 团队成员列表 | `billing_account` |
| `list_my_submitted_forms` / `list_my_submitted_entries` | 我作为填写者提交过的表单/数据 | `forms` / `read_entries` |

## 典型工作流

1. **建表**：`create_form`（先想清字段类型；不确定值是否合法可先 `check_field_data`）→ 返回 `form_token` 与 `form_url`。
2. **查数据**：`list_forms` 找到 `form_token` →（可选 `get_form` 确认字段 API 名）→ `list_entries` 带 `filter` 下推过滤。
3. **写/改数据**：`get_form` 拿字段 API 名 → `create_entry` / `create_entries` / `update_entry`，值按字段 API 名组织。
4. **带附件/图片**：先 `prepare_*_upload` 换凭证上传，再把返回的引用写入对应字段。

## 注意事项

- 写入/更新/过滤数据一律用**字段 API 名**（`field_1`…），不要用中文标题猜。拿不准就先 `get_form`。
- 分页统一走响应里的 `next` 游标；`limit` 越界会自动截断。
- 批量修改/删除不可逆，执行前向用户复述影响范围并确认。
- 报 `Insufficient scope` 时，说明缺哪个 scope，提示用户重新授权勾选对应权限。
