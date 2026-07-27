---
name: jinshuju-table
slug: jinshuju-table
displayName: 金数据AI表格
description: "通过金数据（Jinshuju，jinshuju.net）MCP 操作用户托管在金数据平台上的数据表格：创建 / 编辑数据表与列（含自动计算的公式列）；查询、新增（单条或批量）、更新、批量更新、删除行数据；用上传凭证把本地文件写入附件列；查询账户套餐额度与团队成员。仅在用户操作其金数据数据表时使用——触发信号：提到 金数据表格 / Jinshuju 表格 / 数据表，或要在金数据上建表、加改列、批量维护行数据。不要用于：用代码开发表格系统、处理本地文件或表格（Excel / CSV）、搭建对外收集的表单 / 问卷、图片 / 票据 OCR，以及与金数据平台无关的通用数据处理。"
version: 1.0.0
author: Jinshuju
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Tables, Database, Data Management, Productivity, 金数据表格]
    category: productivity
    related_skills: []
---

# 金数据表格（Jinshuju Tables）

金数据（jinshuju.net）的**数据表格**是以「列 + 行」组织的结构化数据表（类似多维表格 / 在线数据库）。通过金数据 MCP，你可以用自然语言完成数据表搭建与行数据管理的全流程，**替代登录后台手动操作**。

数据表格与用于对外收集的「在线表单」是不同产品：数据表用 `create_table` / `edit_table` 建改；行数据（entries）两者共用同一批 entries 工具。本 skill 只处理数据表格。

## When to Use

本 skill **仅处理金数据数据表格（jinshuju.net）** 的表结构与行数据管理，且需满足以下任一**平台信号**才触发：

- 用户明确提到"金数据表格"、"Jinshuju 表格"、"数据表"
- 用户要在金数据上**建数据表、加/改列、增删改查或批量维护行数据**
- 用户要查询本账户的套餐额度、团队成员

> ⚠️ **前置条件**：表格工具需账户开通「新版表格」（billing 侧 `all_new_table_enabled`）。未开通时 `list_tables` 等会报错，说明原因并引导用户在金数据后台开通。

## When NOT to Use

以下场景**不要**用本 skill，直接退出、交给通用能力处理：

- 用代码 / 程序开发表格、数据库系统
- 处理本地文件、Excel / CSV、文档分析
- 搭建对外收集的**表单 / 问卷 / 报名表**（那是金数据表单产品，另有专家 / skill）
- 图片、账单、票据的 OCR / 识别
- 与金数据平台无关的通用数据处理

判断不属于金数据数据表操作时，**不要调用任何 MCP 工具**，按通用能力回答即可。

## Quick Reference

| 场景 | MCP 工具 |
|------|----------|
| 列出数据表 | `list_tables` |
| 查看数据表详情（列结构） | `get_table` |
| 创建数据表 | `create_table` |
| 改表名 / 增删改列 | `edit_table` |
| 列出行数据 | `list_entries`（`form_token` 传表 token） |
| 查看单行 | `get_entry` |
| 新建行（单条） | `create_entry` |
| 批量新建行（一次最多 200 行） | `create_entries` |
| 更新行（单条） | `update_entry` |
| 批量更新行（一次最多 200 行，PATCH） | `patch_entries` |
| 删除行（单条） | `delete_entry` |
| 上传文件写入附件列 | `prepare_entry_attachment_upload` |
| 当前用户信息 | `get_current_user` |
| 当前企业账户/套餐（确认是否开通新版表格） | `get_current_billing_account` |
| 列出团队成员 | `list_account_users` |

## Procedure

### 原则

> ⚠️ **绝不绕过 MCP**：金数据 MCP 工具不可用（未连接 / 授权失败 / 未开通新版表格 / 调用持续报错）时**立即停止**，**禁止**改用浏览器自动化（Playwright 等）、直接调 GraphQL / REST API、curl 或模拟后台操作来替代。正确做法见下方「MCP 不可用时」。

1. **先看再动**：操作未知数据表前，先 `get_table` 拿列结构——每列的 `api_code`、选项列的 `choices[].api_code`。`create_entry` / `update_entry` 的键**必须是列 `api_code`**，传中文列名会被服务端丢弃。

2. **filters 优先**：`list_entries` 支持 `filters=[{field, operator, value}]` 下推过滤，比拉全量再本地筛选快几个数量级。单次上限 50 行，超过用 `next`（serial_number 游标）翻页。

3. **先列再改**：批量操作前先 `list_entries` 拉出命中行展示给用户，**用户确认后**再执行——批量更新用 `patch_entries` 一次提交（≤200/批）；删除仍逐行循环 `delete_entry`，每 20 行汇报一次进度。

4. **永不主动开 PUT**：`update_entry` 默认 `is_put=false`（PATCH，只改提供的列）。`is_put=true` 会把未提供列全部清空，只有用户明确说"整行替换"且已列全所有列时才允许，且需二次确认。

5. **脱敏展示**：输出手机号/邮箱默认打码（`138****1234`），除非用户明确要求原文。

6. **不静默吞错**：列类型不支持、套餐限制、权限不足、未开通新版表格的报错原文回显并给出替代方案。

### 典型任务流

**① 新建数据表**
```
1. create_table，传 name + fields（列定义列表）
   - 列类型见「支持的列类型」；单选/多选列（RadioButton / CheckBox）传 choices
   - 需要跨列自动计算传 FormulaField（公式列）
2. 返回表结构与 token
```

**② 加 / 改列**
```
1. get_table → 记下现有列的 api_code
2. edit_table，用 fields 原子操作：
   - add: 新增列（同 create_table 的列定义）
   - remove: 传要删列的 api_code 数组（删有数据的列会永久清除该列数据，先确认）
   - update: 改列属性，带 api_code 保持 identity
   - update_choices: 增删改选项（改名用 update 保留 api_code）
```

**③ 条件查询 / 导出行**
```
1. get_table → 记下列 api_code 和选项 api_code
2. list_entries（form_token 传表 token）用 filters 下推条件（选项列传 api_code 不是 label）
3. next 翻页拿全部数据
4. Markdown 表格展示，表头用 get_table 的列 label，敏感列脱敏
5. 询问用户是否需要生成 CSV artifact
```

**④ 批量更新行**
```
1. get_table → 拿目标列 api_code + 目标选项 api_code
2. list_entries + filters 拉出命中集，展示前 10 行 + 总数
3. 用户确认后，用 patch_entries 一次提交（每行 { serial_number, entry }，PATCH 只改提供列，每批 ≤200 自行分批）
4. 读返回的 updated_count + failed_rows（按 serial_number），向用户汇总成功/失败
```

**⑤ 批量导入行**
```
1. get_table → 拿目标列 api_code + 选项 api_code
2. 把每行整理成 { api_code: value } 对象（选项传 api_code）
3. create_entries 一次提交（每批 ≤200，超过自行分批循环）
4. 读返回的 created_count + errors（按下标），向用户汇总成功/失败
   注意：不幂等，重复提交会产生重复行；失败后不要整批重发，按 errors 下标只补失败行
```

### 支持的列类型

| 列类型 | 说明 |
|--------|------|
| `TextArea` | 文本 |
| `NumberField` | 数字（显示精度用 `displayPrecision`，不可设存储 `precision`） |
| `DateTimeField` | 日期时间（`precision`：month / day / minute / second） |
| `BooleanField` | 布尔（勾选） |
| `MobileField` | 手机号 |
| `EmailField` | 邮箱 |
| `LinkField` | 链接 |
| `RadioButton` | 单选（传 `choices`） |
| `CheckBox` | 多选（传 `choices`） |
| `AttachmentField` | 附件（上传限制固定，不接受 max_file_quantity / max_size） |
| `FormulaField` | 公式列，自动计算（只读；`formula_display` 控制展示；不可设存储精度） |

### 关键格式规范

**entry payload 的键是列 `api_code`，不是中文列名：**

| 列类型 | 正确值格式 |
|----------|-----------|
| TextArea | 纯字符串 `"备注内容"` |
| MobileField | 纯字符串 `"13812345678"` |
| EmailField | 纯字符串 `"a@b.com"` |
| LinkField | 纯字符串 URL `"https://…"` |
| NumberField | 数字 `123` 或字符串 `"123"` |
| DateTimeField | ISO 字符串 `"2026-05-01 14:30"` |
| BooleanField | 布尔 `true` / `false` |
| RadioButton | 选项 api_code `"status_done"`（不是 label "已完成"） |
| CheckBox | api_code 数组 `["tag_a", "tag_b"]` |
| AttachmentField | 上传凭证返回的引用（先 `prepare_entry_attachment_upload`） |
| FormulaField | 只读，写入被忽略 |

**list_entries filters operator 速查：**

| operator | 适用列 | value 形式 |
|----------|----------|-----------|
| `eq` / `ne` | 所有 | 标量 |
| `gt` / `gte` / `lt` / `lte` | 数字、日期 | 标量 |
| `between` | 数字、日期 | `[min, max]` |
| `any_in` / `none_in` | 文本、选项 | 数组 |
| `like` / `not_like` | 文本、选项 | 子串（**不带 % 通配符**） |
| `null` / `not_null` | 所有 | 省略 |

> 特殊字段：`created_at`（创建时间，配 `gte` / `between` 等）；`creator_id`（创建者用户 id，**只支持 `eq`**，value 是行返回的 `creator_id` 字符串）——按创建者查行用它。

## Pitfalls

- **entry 键写成中文列名** → 服务端静默丢弃，报 "Entry attributes cannot be empty"；键必须是列 `api_code`
- **选项列传 label**（如 `"已完成"`）→ 400 invalid choice；传 `choices[].api_code`
- **`is_put=true` 做部分更新** → 未提供列全部清空；部分更新永远保持默认 `is_put=false`
- **`like` 带 SQL 通配符**（`"张%"` / `"%张%"`）→ 按字面匹配 `%`，永远查不到；直接传 `"张"`
- **`operator` 与列类型不匹配** → 400，错误信息会列出该列可用 operator，照着改
- **简单列值包成对象**（`{"value": "abc"}`）→ 直接传字符串
- **批量新建行循环调 `create_entry`** → 改用 `create_entries` 一次提交（≤200 行/批）；它部分成功、按下标返回 `errors`、不幂等（重复调会生成重复行）
- **批量更新行循环调 `update_entry`** → 改用 `patch_entries`（一次 ≤200 行，每行 `{ serial_number, entry }`，PATCH 只改提供列，按 serial_number 返回 `failed_rows`）；`delete_entry` 仍无批量版，逐行循环
- **给附件列设上传限制**（`max_file_quantity` / `max_size`）→ 表格附件列限制固定，传了会被拒
- **给数字 / 公式列设 `precision`** → 表格数字 / 公式列不支持存储精度；显示格式用 `displayPrecision`
- **给非日期时间列传 `precision`** → `precision`（month/day/minute/second）仅 `DateTimeField` 可用
- **给 `RadioButton` / `CheckBox` 之外的列传 `choices`** → 仅这两类支持选项，其他列传 choices 无效
- **写入 `FormulaField`** → 公式列只读，写入被忽略；它的值由公式自动算
- **改选项文案用 remove + add** → 会换 api_code，历史数据引用失效；改名用 `fields.update_choices` 的 update（保留 api_code）
- **删列 / 删选项不先确认数据** → 删有数据的列 / 选项会永久清除数据且不可恢复；`fields.remove` / `update_choices.remove` 前先向用户说明影响、确认后再删
- **FormulaField 引用同一请求新增的列** → 新列还没有 api_code，公式里用 `<gd-field data-cid="...">` 引用其 `cid`，不要猜 api_code
- **把 table token 当 entry 定位符** → `get_entry` / `update_entry` / `delete_entry` 靠 **`serial_number`**（整数）定位单行，不是 token
- **限流报错（HTTP 429 / code 14003）把原始 JSON 抛给用户** → 改为告知"接口请求频繁，请等 1–2 分钟后重试"，放慢节奏、合并可批量的请求；不要立刻疯狂重试

## Verification

操作完成后确认：
- **创建/编辑数据表**：返回中包含有效表 token 与预期的列结构（列 `api_code`、类型）
- **create_entry**：返回包含 `serial_number`（整数）
- **create_entries**：返回 `created_count` 与提交行数一致，`errors` 为空（有部分失败时按下标核对原因）
- **update_entry**：返回的列值与提交值一致
- **patch_entries**：返回 `updated_count` 与提交行数一致，`failed_rows` 为空（有部分失败时按 serial_number 核对 reason）
- **delete_entry**：后续 `get_entry` 返回 404 或该行不再出现在 `list_entries`
- **批量操作**：向用户汇报"共 N 行，成功 X 行，失败 Y 行"

## MCP 配置

金数据 MCP 端点：`https://jinshuju.net/mcp`（表单与表格共用同一端点）

**方式 A · HTTP Basic（API Key/Secret）**
```bash
echo -n "YOUR_API_KEY:YOUR_API_SECRET" | base64
```
```json
{
  "mcpServers": {
    "jinshuju-table": {
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
    "jinshuju-table": { "url": "https://jinshuju.net/mcp" }
  }
}
```

常见配置错误：漏 `/mcp` 后缀、用 `http://`、`Authorization` 缺 `Basic ` 前缀、用 `command/args`（stdio 写法，金数据是远程 HTTP MCP 不支持）。

### MCP 不可用时

工具未连接 / 授权失败 / 未开通新版表格 / 持续报错时，按顺序降级，**不要**用任何非标方式替代：

1. 告知用户"金数据 MCP 未就绪 / 未开通新版表格"，不要假装已完成操作。
2. 对照上面的「常见配置错误」引导排查（端点、`Basic ` 前缀、OAuth 授权等）；未开通新版表格的引导用户在后台开通。
3. 仍不行，就给出在金数据后台（jinshuju.net）手动操作的步骤指引。

> 超宽表（几十列）即使 MCP 正常，也建议先 `create_table` 建核心列，再用 `edit_table` 分批补列，降低超长请求被截断 / 超时的风险。
