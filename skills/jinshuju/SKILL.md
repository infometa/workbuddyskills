---
name: jinshuju
description: "Use when the user wants to create or edit forms, collect or query entries, bulk-update form data, check invoices or payment history, or manage their Jinshuju (金数据) account and team members. Also activate for keywords: 金数据, 表单, 问卷, 报名表, form_token, 数据录入, 数据查询, 批量修改."
description_zh: "金数据（Jinshuju）表单平台操作专家，用一句话完成表单搭建、数据查询与批量修改、账单查询，替代登录后台手工操作。"
description_en: "Jinshuju form platform expert. Create and edit forms, query and bulk-update entries, and check invoices in natural language — replaces manual operations in the web console."
version: 1.3.0
author: Jinshuju
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Forms, Data Collection, Survey, Productivity, CRM, 金数据]
    category: productivity
    related_skills: []
display_name: "金数据"
display_name_en: "Jinshuju"
visibility: "public"
---

# 金数据（Jinshuju）操作专家

金数据（jinshuju.net）是中国领先的在线表单与数据收集平台。通过金数据 MCP，你可以用自然语言完成表单搭建、数据管理与账单查询的全流程，**替代登录后台手动操作**。

## When to Use

- 用户提到"金数据"、"Jinshuju"、"表单"、"问卷"、"报名表"、"登记表"
- 用户想创建、复制、编辑、移动表单，或修改表单主题
- 用户想查询、新建、更新、删除表单数据（entries）
- 用户想批量修改或导出数据
- 用户询问账单、发票、付款记录、套餐额度、团队成员
- 用户给出了 `form_token` 或说"帮我操作这张表单"

## Quick Reference

| 场景 | MCP 工具 |
|------|----------|
| 列出文件夹 | `list_folders` |
| 列出表单 | `list_forms` |
| 查看表单详情（字段结构） | `get_form` |
| 创建表单 | `create_form` |
| 复制表单 | `copy_form` |
| 移动表单到文件夹 | `move_form` |
| 修改表单字段/设置 | `edit_form` |
| 修改表单主题 | `edit_theme` |
| 列出数据 | `list_entries` |
| 查看单条数据 | `get_entry` |
| 新建数据 | `create_entry` |
| 更新数据（单条） | `update_entry` |
| 删除数据（单条） | `delete_entry` |
| 当前用户信息 | `get_current_user` |
| 当前企业账户/套餐 | `get_current_billing_account` |
| 列出团队成员 | `list_account_users` |
| 列出发票 | `list_invoices` |
| 列出付款记录 | `list_payment_histories` |

## Procedure

### 原则

1. **先看再动**：操作未知表单前，先 `get_form` 拿字段结构——每个字段的 `api_code`、选项的 `choices[].api_code`、表格的 `dimensions[].api_code`。`create_entry` / `update_entry` 的键**必须是 `api_code`**，传中文 label 会被服务端丢弃。

2. **filters 优先**：`list_entries` 支持 `filters=[{field, operator, value}]` 下推过滤，比拉全量再本地筛选快几个数量级。单次上限 50 条，超过用 `next`（serial_number 游标）翻页。

3. **先列再改**：批量操作前先 `list_entries` 拉出命中记录展示给用户，**用户确认后**再逐条循环调用 `update_entry` / `delete_entry`，每 20 条汇报一次进度。

4. **永不主动开 PUT**：`update_entry` 默认 `is_put=false`（PATCH，只改提供的字段）。`is_put=true` 会把未提供字段全部清空，只有用户明确说"整条替换"且已列全所有字段时才允许，且需二次确认。

5. **脱敏展示**：输出手机号/邮箱/身份证默认打码（`138****1234`），除非用户明确要求原文。

6. **不静默吞错**：字段类型不支持、套餐限制、权限不足的报错原文回显并给出替代方案。

### 典型任务流

**① 新建表单**
```
1. create_form，传字段列表 + setting
2. 返回表单链接和 form_token
3. 如需特殊样式，追加 edit_theme（可用 generate_header_image 让 AI 生成头图）
```

**② 条件查询 / 导出**
```
1. get_form → 记下字段 api_code 和选项 api_code
2. list_entries 用 filters 下推条件（选项字段传 api_code 不是 label）
3. next 翻页拿全部数据
4. Markdown 表格展示，表头用 get_form 的 label，关键字段脱敏
5. 询问用户是否需要生成 CSV artifact
```

**③ 批量更新**
```
1. get_form → 拿目标字段 api_code + 目标选项 api_code
2. list_entries + filters 拉出命中集，展示前 10 条 + 总数
3. 用户确认后，逐条循环 update_entry（is_put=false）
4. 每 20 条汇报进度，结束时汇总成功/失败数
```

**④ 批量删除**
```
1. list_entries + filters 拉出命中集，记录 serial_number
2. 必须得到用户显式"确认删除"
3. 逐条循环 delete_entry
4. 每 20 条汇报进度
```

### 关键格式规范

**entry payload 的键是 `api_code`，不是中文 label：**

| 字段类型 | 正确值格式 |
|----------|-----------|
| TextField / TextArea / NameField | 纯字符串 `"张三"` |
| MobileField | 纯字符串 `"13812345678"` |
| NumberField | 数字 `123` 或字符串 `"123"` |
| RadioButton / DropDown | 选项 api_code `"city_sh"`（不是 label "上海"） |
| CheckBox | api_code 数组 `["topic_a", "topic_b"]` |
| DateTimeField | ISO 字符串 `"2026-05-01 14:30"` |
| TableField | 对象数组 `[{"dim_api_code": value, ...}]` |

**list_entries filters operator 速查：**

| operator | 适用字段 | value 形式 |
|----------|----------|-----------|
| `eq` / `ne` | 所有 | 标量 |
| `gt` / `gte` / `lt` / `lte` | 数字、日期 | 标量 |
| `between` | 数字、日期 | `[min, max]` |
| `any_in` / `none_in` | 文本、选项 | 数组 |
| `like` / `not_like` | 文本、选项 | 子串（**不带 % 通配符**） |
| `null` / `not_null` | 所有 | 省略 |

## Pitfalls

- **entry 键写成中文 label** → 服务端静默丢弃，报 "Entry attributes cannot be empty"；键必须是 `api_code`
- **选项字段传 label**（如 `"男"` / `"上海"`）→ 400 invalid choice；传 `choices[].api_code`
- **`is_put=true` 做部分更新** → 未提供字段全部清空；部分更新永远保持默认 `is_put=false`
- **`like` 带 SQL 通配符**（`"张%"` / `"%张%"`）→ 按字面匹配 `%`，永远查不到；直接传 `"张"`
- **`operator` 与字段类型不匹配** → 400，错误信息会列出该字段的可用 operator，照着改
- **简单字段包成对象**（`{"value": "张三"}`）→ 直接传字符串
- **TableField 按二维数组传** → 必须是对象数组，键是 dimension 的 `api_code`
- **`update_entry` / `delete_entry` 找批量版本** → 没有，只支持单条，批量逐条循环
- **测试号段**（`13800138000`）→ 号段正则校验 400 拒；用真实在用号段
- **删除整张表单** → MCP 不支持 `delete_form`，引导用户去后台手动操作
- **`ESignatureField` / `FormulaField` 写入 entry** → 服务端忽略，写入无效
- **改选项文案用 remove + add** → 会换 api_code，历史数据引用失效；改名用 `fields.update_choices.update`

## Verification

操作完成后确认：
- **创建/编辑表单**：返回中包含有效 `form_token`，可访问 `https://jinshuju.net/f/{form_token}`
- **create_entry**：返回包含 `serial_number`（整数）
- **update_entry**：返回的字段值与提交值一致
- **delete_entry**：后续 `get_entry` 返回 404 或条目不再出现在 `list_entries`
- **批量操作**：向用户汇报"共 N 条，成功 X 条，失败 Y 条"

## MCP 配置

金数据 MCP 端点：`https://jinshuju.net/mcp`

**方式 A · HTTP Basic（API Key/Secret）**
```bash
echo -n "YOUR_API_KEY:YOUR_API_SECRET" | base64
```
```json
{
  "mcpServers": {
    "jinshuju": {
      "url": "https://jinshuju.net/mcp",
      "headers": { "Authorization": "Basic <BASE64>" }
    }
  }
}
```

**方式 B · OAuth 2.0**
```json
{
  "mcpServers": {
    "jinshuju": { "url": "https://jinshuju.net/mcp" }
  }
}
```

常见配置错误：漏 `/mcp` 后缀、用 `http://`、`Authorization` 缺 `Basic ` 前缀、用 `command/args`（stdio 写法，金数据是远程 HTTP MCP 不支持）。
