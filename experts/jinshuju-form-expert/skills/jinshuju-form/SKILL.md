---
name: jinshuju-form
slug: jinshuju-form
displayName: 金数据表单管理
description: "通过金数据（Jinshuju，jinshuju.net）MCP 操作用户托管在金数据平台上的在线表单：创建 / 复制 / 编辑表单与主题，含自动判分的考试表单、选项计分的测评表单；查询、新增（单条或批量）、更新、删除、批量修改数据；用上传凭证上传本地图片或文件；查询账户套餐额度与团队成员。仅在用户操作其金数据平台数据时使用——触发信号：提到 金数据 / Jinshuju / jinshuju.net、给出 form_token，或要操作一张已托管在金数据上的表单或数据。不要用于：用代码开发表单 / 问卷系统、处理本地文件或表格（Excel / CSV）、图片 / 票据 OCR、物流或监控等与平台无关的自动化，以及与金数据平台无关的通用数据处理。"
version: 1.8.0
author: Jinshuju
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Forms, Data Collection, Survey, Productivity, CRM, 金数据]
    category: productivity
    related_skills: []
---

# 金数据（Jinshuju）

金数据（jinshuju.net）是中国领先的在线表单与数据收集平台。通过金数据 MCP，你可以用自然语言完成表单搭建与数据管理的全流程，**替代登录后台手动操作**。

## When to Use

本 skill **仅处理金数据线上表单平台（jinshuju.net）** 的表单搭建与数据管理，且需满足以下任一**平台信号**才触发：

- 用户明确提到"金数据"、"Jinshuju"、"jinshuju.net"
- 用户给出了 `form_token`，或要操作一张**已在金数据上**的表单 / 数据（创建、复制、编辑、移动表单，修改主题，增删改查或批量修改 entries，导出数据）
- 用户要查询本账户的套餐额度、团队成员

## When NOT to Use

以下场景**不要**用本 skill，直接退出、交给通用能力处理：

- 用代码 / 程序开发表单、问卷、评估系统（如在 Python / 前端项目里"做一个报名表 / 问卷"）
- 处理本地文件、Excel / CSV、文档分析
- 图片、账单、票据的 OCR / 识别
- 物流、监控等与金数据平台无关的业务自动化
- 仅出现"表 / 表单 / 问卷"字眼，但并非操作金数据线上平台

判断不属于金数据平台操作时，**不要调用任何 MCP 工具**，按通用能力回答即可。

## Quick Reference

| 场景 | MCP 工具 |
|------|----------|
| 列出文件夹 | `list_folders` |
| 新建文件夹 | `create_folder` |
| 列出表单 | `list_forms` |
| 查看表单详情（字段结构） | `get_form` |
| 创建表单 | `create_form` |
| 创建考试表单（答案 + 自动判分） | `create_exam_form` |
| 编辑考试表单 | `edit_exam_form` |
| 创建测评表单（选项计分 / 维度报告） | `create_evaluation_form` |
| 编辑测评表单 | `edit_evaluation_form` |
| 复制表单 | `copy_form` |
| 移动表单到文件夹 | `move_form` |
| 修改表单字段/设置 | `edit_form` |
| 查看字段显示规则 | `get_field_rules` |
| 增删改字段显示规则（外科式） | `edit_field_rules` |
| 修改表单主题 | `edit_theme` |
| 上传本地图片（头图 / 选项配图） | `prepare_form_image_upload` |
| 上传文件写入附件字段 | `prepare_entry_attachment_upload` |
| 列出数据 | `list_entries` |
| 列出我填写 / 提交过的表单 | `list_my_submitted_forms` |
| 列出我在某表单提交的数据 | `list_my_submitted_entries` |
| 查看单条数据 | `get_entry` |
| 新建数据（单条） | `create_entry` |
| 批量新建数据（一次最多 200 条） | `create_entries` |
| 更新数据（单条） | `update_entry` |
| 批量更新数据（一次最多 200 条，PATCH） | `patch_entries` |
| 删除数据（单条） | `delete_entry` |
| 当前用户信息 | `get_current_user` |
| 当前企业账户/套餐 | `get_current_billing_account` |
| 列出团队成员 | `list_account_users` |

## Procedure

### 原则

> ⚠️ **绝不绕过 MCP**：金数据 MCP 工具不可用（未连接 / 授权失败 / 调用持续报错）时**立即停止**，**禁止**改用浏览器自动化（Playwright 等）、直接调 GraphQL / REST API、curl 或模拟后台操作来替代——这类非标方式会产出中文乱码、字段不兼容的错误表单。正确做法见下方「MCP 不可用时」。

1. **先看再动**：操作未知表单前，先 `get_form` 拿字段结构——每个字段的 `api_code`、选项的 `choices[].api_code`、表格的 `dimensions[].api_code`。`create_entry` / `update_entry` 的键**必须是 `api_code`**，传中文 label 会被服务端丢弃。

2. **filters 优先**：`list_entries` 支持 `filters=[{field, operator, value}]` 下推过滤，比拉全量再本地筛选快几个数量级。单次上限 50 条，超过用 `next`（serial_number 游标）翻页。

3. **先列再改**：批量操作前先 `list_entries` 拉出命中记录展示给用户，**用户确认后**再执行——批量更新用 `patch_entries` 一次提交（≤200/批）；删除仍逐条循环 `delete_entry`，每 20 条汇报一次进度。

4. **永不主动开 PUT**：`update_entry` 默认 `is_put=false`（PATCH，只改提供的字段）。`is_put=true` 会把未提供字段全部清空，只有用户明确说"整条替换"且已列全所有字段时才允许，且需二次确认。

5. **脱敏展示**：输出手机号/邮箱/身份证默认打码（`138****1234`），除非用户明确要求原文。

6. **不静默吞错**：字段类型不支持、套餐限制、权限不足的报错原文回显并给出替代方案。

### 典型任务流

**① 新建表单**
```
1. create_form，传字段列表 + setting
   （考试 / 测评场景改用 create_exam_form / create_evaluation_form，
    create_form 的 scene 已不支持 exam / evaluation，也不支持 vote / customer_acquisition，改用 form 场景；
    要"分页式 / 一页一题 / 自动翻页"传 layout:"card"，别拿 PageBreak 拼）
2. 返回表单链接和 form_token
3. 如需特殊样式，追加 edit_theme（可用 generate_header_image 让 AI 生成头图，
   本地已有图片则先 prepare_form_image_upload（type=header）上传）
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
3. 用户确认后，用 patch_entries 一次提交（每行 { serial_number, entry }，PATCH 只改提供字段，每批 ≤200 自行分批）
4. 读返回的 updated_count + failed_rows（按 serial_number），向用户汇总成功/失败
```

**④ 批量删除**
```
1. list_entries + filters 拉出命中集，记录 serial_number
2. 必须得到用户显式"确认删除"
3. 逐条循环 delete_entry
4. 每 20 条汇报进度
```

**⑤ 批量导入数据**
```
1. get_form → 拿目标字段 api_code + 选项 api_code
2. 把每行整理成 { api_code: value } 对象（选项传 api_code）
3. create_entries 一次提交（每批 ≤200，超过自行分批循环）
4. 读返回的 created_count + errors（按下标），向用户汇总成功/失败
   注意：不幂等，重复提交会产生重复数据；失败后不要整批重发，按 errors 下标只补失败行
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

> 特殊字段：`created_at`（创建时间，配 `gte` / `between` 等）；`creator_id`（提交者用户 id，**只支持 `eq`**，value 是 entry 返回的 `creator_id` 字符串）——按提交者查数据用它。

## Pitfalls

- **entry 键写成中文 label** → 服务端静默丢弃，报 "Entry attributes cannot be empty"；键必须是 `api_code`
- **选项字段传 label**（如 `"男"` / `"上海"`）→ 400 invalid choice；传 `choices[].api_code`
- **`is_put=true` 做部分更新** → 未提供字段全部清空；部分更新永远保持默认 `is_put=false`
- **`like` 带 SQL 通配符**（`"张%"` / `"%张%"`）→ 按字面匹配 `%`，永远查不到；直接传 `"张"`
- **`operator` 与字段类型不匹配** → 400，错误信息会列出该字段的可用 operator，照着改
- **简单字段包成对象**（`{"value": "张三"}`）→ 直接传字符串
- **TableField 按二维数组传** → 必须是对象数组，键是 dimension 的 `api_code`
- **批量新建数据循环调 `create_entry`** → 改用 `create_entries` 一次提交（≤200 条/批，超过自行分批）；它部分成功、按下标返回 `errors`、不幂等（重复调会生成重复数据）
- **批量更新循环调 `update_entry`** → 改用 `patch_entries`（一次 ≤200 行，每行 `{ serial_number, entry }`，PATCH 只改提供字段，单条聚合操作日志、按 serial_number 返回 `failed_rows`）；`delete_entry` 仍无批量版，逐条循环
- **测试号段**（`13800138000`）→ 号段正则校验 400 拒；用真实在用号段
- **删除整张表单** → MCP 不支持 `delete_form`，引导用户去后台手动操作
- **`ESignatureField` / `FormulaField` 写入 entry** → 服务端忽略，写入无效
- **改选项文案用 remove + add** → 会换 api_code，历史数据引用失效；改名用 `fields.update_choices.update`
- **选择字段设默认选中用 `predefined_value`** → 选择类字段（单选 / 多选 / 下拉 / 级联）不接受 `predefined_value`；默认选中改用 `choices[].selected: true`
- **用选项 `quota: 0` 表示"不限量"** → `0` 表示该选项**一开始就满、立即置灰不可选**（选项渲染出来却选不了）；不限量应**省略 `quota`**，正整数才是名额上限
- **字段显示规则 comparator 跟触发字段类型不匹配**（如选择字段用 `like`）→ 该 `edit_field_rules` 调用被拒；选择类用 `equal` / `none_in`、评分 / NPS 用 `between`、文本类用 `like` / `not_like`
- **还在用 edit_form 的 `field_rules` 改显示规则** → 该参数已移除、误传被拒；改用 `edit_field_rules` 做外科式 add / update / remove（按 `get_form(include_field_rules=true)` 或 `get_field_rules` 返回的 0-based `index` 定位），只动你传的那条、其余保留
- **给图片选项字段（ImageRadioButton / ImageCheckBox）`update_choices.add` 不带图片** → 被拒（image choice requires image_url / image_base64 / image_upload_token）；每个图片选项必须带图片，`value` 是文字标签必填
- **edit_form 改预约字段只改一项却不回传 `reservation_items[].api_code`** → reservation_items 是整体替换，丢了 api_code 会让历史预约数据失联；改动前先 get_form 读出各项 api_code 原样回传（省略时后端按 name 匹配保留，改名必须回传 api_code）
- **用 PageBreak 拼分页式 / 一页一题表单** → PageBreak 只在经典式内手动分页；整表分页式传 `layout:"card"`（仅 form / survey 场景生效，且不支持矩阵 / 表格 / 商品 / 签名等字段）
- **create_form 传 vote / customer_acquisition** → 已移除且会被拒（新编辑器打不开）；改用 `form` 场景
- **删字段 / 选项不先查数据** → 删有提交数据的字段 / 选项会永久清除数据且不可恢复；`fields.remove` / `update_choices.remove` 前先对每个目标用 `check_field_data` 查，`has_data=true` 时把影响告诉用户、确认后再删（edit_form 本身不拦截）
- **用 create_form 建考试/测评** → scene 枚举已移除 exam / evaluation；用 `create_exam_form` / `create_evaluation_form`
- **考试开限时又把题目设必填** → `show_timeout=true` 与题目字段 `required` 互斥；默认不开限时，仅用户明确要求时开
- **FormulaField 引用同一请求新增的字段** → 新字段还没有 api_code，公式里用 `<gd-field data-cid="...">` 引用其 `cid`，不要猜 api_code
- **编辑考试/测评题目时只传改动的 answers 项** → answers 是整体替换语义，会重建整个答案库；必须传完整列表
- **限流报错（HTTP 429 / code 14003）把原始 JSON 抛给用户** → 不友好；改为告知"接口请求频繁，请等 1–2 分钟后重试"，并放慢节奏、合并可批量的请求降低调用频次；不要立刻疯狂重试

## Verification

操作完成后确认：
- **创建/编辑表单**：返回中包含有效 `form_token`，可访问 `https://jinshuju.net/f/{form_token}`
- **create_entry**：返回包含 `serial_number`（整数）
- **create_entries**：返回 `created_count` 与提交条数一致，`errors` 为空（有部分失败时按下标核对原因）
- **update_entry**：返回的字段值与提交值一致
- **patch_entries**：返回 `updated_count` 与提交行数一致，`failed_rows` 为空（有部分失败时按 serial_number 核对 reason）
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

### MCP 不可用时

工具未连接 / 授权失败 / 持续报错时，按顺序降级，**不要**用任何非标方式替代：

1. 告知用户"金数据 MCP 未就绪"，不要假装已完成操作。
2. 对照上面的「常见配置错误」引导排查（端点、`Basic ` 前缀、OAuth 授权等）。
3. 仍不行，就给出在金数据后台（jinshuju.net）手动操作的步骤指引。

> 超大表单（数十个字段）即使 MCP 正常，也建议先 `create_form` 建核心字段，再用 `edit_form` 分批补充，降低超长请求被截断 / 超时的风险。
