---
name: yunke-cli
description: "通过 yunke 操作云客 CRM：组织架构查询、员工/客户/通话数据统计、AI 智能分析。登录由 WorkBuddy 连接器经 OAuth 自动完成，使用前需确保 yunke 已安装且已登录。"
metadata:
  requires:
    bins: ["yunke"]
---

# yunke-cli（云客 CRM）

通过 yunke 的 yunke-crm 插件操作云客 CRM。凭证（`~/.yunke/crm.json`）由 WorkBuddy 连接器经 OAuth 登录流程自动写入，无需手动登录。

> **前置条件**：连接器已安装 yunke 并完成 OAuth 登录（`crm.auth.login-web`）。首次使用前，用户须先在云枢完成「AI 助手登录」生成 agentapp 凭证，否则登录会返回 `access_denied`。

所有业务命令输出统一为 JSON 信封：

```json
{ "success": true, "data": ..., "error": null, "metadata": { "command": "...", "duration_ms": 0, "timestamp": "...", "plugin": "crm" } }
```

失败时 `success: false`、`data: null`，`error` 为 `{ "code": "...", "message": "...", "details": ... }`。按 `success` 字段判断成败。例外：`crm.auth.login-web` / `crm.auth.status` 输出不是 JSON 信封，以退出码判定。

## 命令分类

| 类别 | 命令前缀 | 用途 |
|---|---|---|
| 组织架构 | `crm.org.*` | 部门树、员工搜索 |
| 用户信息 | `crm.user.*` | 当前登录用户详情 |
| 报表统计 | `crm.report.*` | 员工/客户/设备统计 |
| 通话 | `crm.call.*` | 通话记录、ASR 转写 |
| AI 分析 | `crm.ai.*` | SOP、情绪、意向、痛点等智能分析 |
| 定位 | `crm.location.*` | 部门/员工定位轨迹 |
| 其他 | `crm.misc.*` | 飞单预警、短信、管控日志 |

## ⚠️ 参数命名陷阱（必读）

**不同命令族参数名不同，没有统一惯例。** 未识别的参数会被静默剥离（不报错但过滤失效），务必按下表使用正确参数名，不确定时先查 schema：

| 命令族 | 部门参数 | 时间参数 | 时间格式 |
|---|---|---|---|
| `report.employee-statistics` | `depart_id`（空=全公司） | `start_time` / `end_time` | `YYYY-MM-DD`，空=近7天 |
| `report.customer-statistics` | `department_ids`（JSON 数组，必填） | `time_range`（枚举） | — |
| `call.log-list` | `department_id`（空=默认部门） | `start_voice_time` / `end_voice_time` | `YYYY-MM-DD HH:mm:ss` |
| `ai.*`（分析类） | `dept_id`（空=默认部门） | `start_time` / `end_time`（**必填**；例外：`employee-emotion`、`communication-keywords` 可选，`customer-intention` 无时间参数） | `YYYY-MM-DD HH:mm:ss` |
| `location.*` | `department_id` / `user_id` | `start_time` / `end_time`（仅 `by-user`） | `YYYY-MM-DD HH:mm:ss` |

## 常用示例

### 组织架构

查询部门树（顶层部门）：

```bash
yunke crm.org.department-tree
```

按姓名搜索员工：

```bash
yunke crm.org.search --keyword "张伟"
```

### 报表统计

查询员工统计（`--option department`=部门维度汇总，`--option employee`=员工维度明细）：

```bash
yunke crm.report.employee-statistics --option employee --depart_id "d001" --start_time "2026-07-01" --end_time "2026-07-31"
```

设备统计：

```bash
yunke crm.report.device-statistics
```

### 通话与 ASR

查询通话记录列表（后端每页最多 10 条，需翻页汇总）：

```bash
yunke crm.call.log-list --start_voice_time "2026-07-01 00:00:00" --end_voice_time "2026-07-31 23:59:59" --page 1 --page_size 10
```

获取某通通话的 ASR 语音转写（`call_action_id` 取自 log-list 返回的通话记录）：

```bash
yunke crm.call.asr-result --call_action_id "call_xxx"
```

### AI 智能分析

员工 SOP 分析（`start_time`/`end_time` 必填，含时分秒）：

```bash
yunke crm.ai.sop-analysis --dept_id "d001" --start_time "2026-07-01 00:00:00" --end_time "2026-07-31 23:59:59"
```

客户情绪分析（同样必填时间范围）：

```bash
yunke crm.ai.customer-emotion --start_time "2026-07-01 00:00:00" --end_time "2026-07-31 23:59:59"
```

客户意向分析（不接收时间参数，用 `intension_levels` / 分页筛选）：

```bash
yunke crm.ai.customer-intention --dept_id "d001" --page_index 1
```

### 定位

部门定位（建议先用 `org.search` 缩小部门范围）：

```bash
yunke crm.location.by-department --department_id "d001"
```

## 调用规范

- **先看 schema**：不确定参数时运行 `yunke schema.detail --command <命令名>` 查看完整 JSON Schema（参数、类型、默认值、示例）。`yunke schema` 列出全部命令。注意：`--help` 不是子命令级帮助，会被当未知参数剥离后直接执行命令。
- **核对参数名**：未知参数被静默剥离，参数名拼错不会报错但过滤条件失效。传参前对照上方参数命名表或 schema.detail。
- **显式传时间范围**：各命令族时间参数名与格式不同（见上表），建议显式传入较短范围，不要依赖默认。
- **翻页**：列表类命令返回分页信息（`pageCount > 当前页` 或 `total > page*page_size` 时），继续翻页取全再汇总。
- **企业上下文**：所有命令以已登录用户所属企业为范围，无需手动传 `company_code`。

---

# yunke-cli (Yunke CRM) — English

Operate Yunke CRM via the yunke `yunke-crm` plugin. Credentials (`~/.yunke/crm.json`) are written automatically by the WorkBuddy connector through the OAuth login flow — no manual login required.

> **Prerequisite**: The connector has installed yunke and completed OAuth login (`crm.auth.login-web`). Before first use, the user must complete "AI Assistant login" in Yunshu to generate the agentapp credential, otherwise login returns `access_denied`.

All business commands output a JSON envelope:

```json
{ "success": true, "data": ..., "error": null, "metadata": { "command": "...", "duration_ms": 0, "timestamp": "...", "plugin": "crm" } }
```

On failure: `success: false`, `error: { "code", "message", "details" }`. Check the `success` field. Exception: `crm.auth.login-web` / `crm.auth.status` output non-JSON; use exit codes.

## Parameter naming pitfall (read first)

**Parameter names differ per command family — there is no shared convention.** Unknown flags are silently stripped (no error, filters just don't apply):

| Family | Department param | Time params | Time format |
|---|---|---|---|
| `report.employee-statistics` | `depart_id` (empty = whole company) | `start_time` / `end_time` | `YYYY-MM-DD`, empty = last 7 days |
| `report.customer-statistics` | `department_ids` (JSON array, required) | `time_range` (enum) | — |
| `call.log-list` | `department_id` (empty = default dept) | `start_voice_time` / `end_voice_time` | `YYYY-MM-DD HH:mm:ss` |
| `ai.*` (analysis) | `dept_id` (empty = default dept) | `start_time` / `end_time` (**required**; exceptions: `employee-emotion`, `communication-keywords` optional, `customer-intention` takes no time params) | `YYYY-MM-DD HH:mm:ss` |
| `location.*` | `department_id` / `user_id` | `start_time` / `end_time`（仅 `by-user`） | `YYYY-MM-DD HH:mm:ss` |

## Common Examples

Search employees:

```bash
yunke crm.org.search --keyword "Zhang Wei"
```

Employee statistics for a department:

```bash
yunke crm.report.employee-statistics --option employee --depart_id "d001" --start_time "2026-07-01" --end_time "2026-07-31"
```

Call records:

```bash
yunke crm.call.log-list --start_voice_time "2026-07-01 00:00:00" --end_voice_time "2026-07-31 23:59:59" --page 1 --page_size 10
```

ASR transcript (ID comes from log-list):

```bash
yunke crm.call.asr-result --call_action_id "call_xxx"
```

Customer emotion analysis (time range required, with HH:mm:ss):

```bash
yunke crm.ai.customer-emotion --start_time "2026-07-01 00:00:00" --end_time "2026-07-31 23:59:59"
```

## Conventions

- Run `yunke schema.detail --command <name>` to inspect parameters when unsure; `yunke schema` lists all commands. Do NOT use `--help` on subcommands — it is silently stripped and the command executes instead.
- Verify parameter names against the table above; wrong names are stripped silently, so filters fail without errors.
- Pass explicit, narrow date ranges rather than relying on defaults.
- Paginate list commands until all pages are fetched, then aggregate.
- Commands are scoped to the logged-in user's company; no need to pass `company_code`.
