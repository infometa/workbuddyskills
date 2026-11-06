# 书签查询定义导出

> 工具 `dashboard.bookmark-export` · 命令 `sensors analytics bookmark-export` · 类型 查询

## 用途

把单个已保存书签的查询定义导出为对应分析模型的输入 schema JSON：书签在平台保存的是最终请求体，本工具把它反转换并校验为用户视角的输入 schema，输出的 `input_schema` 可直接（或在修改口径后）作为对应分析命令 `--input` 的查询对象。适用于「基于已有书签换口径重查」的派生场景，以及查看书签实际保存的查询口径。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--bookmark-id` | int | 是 | — | 书签 ID（正整数），通过 `dashboard-get --id <id>` 获取 | `4` |
| `--dashboard-id` | int | 是 | — | 书签所属看板 ID（正整数），通过 `dashboard-list` 获取 | `7` |
| `--dry-run` | flag | 否 | 关 | 打印将发送的请求参数 dict，不发起真实 HTTP 请求，也不做导出 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。

## 输入 Schema

本工具无复杂 JSON 输入，通过 flag 定位书签。导出的是书签**保存时的查询定义**，无时间覆盖参数（调整时间范围请在导出的 `input_schema` 里修改后执行）。

## 构造流程

从业务输入到合法命令参数的构造映射：

1. 定位书签：`--dashboard-id` 与 `--bookmark-id` 必须配套（看板 ID 来自 `dashboard-list`，书签 ID 与类型来自 `dashboard-get --id` 展开的 `bookmarks[]`）；书签与看板不匹配时命令直接报错。
2. 导出后去哪个命令执行：输出中的 `command` 字段给出对应分析命令名（如 `segmentation` / `funnel` / `user-path` / `sql`），把 `input_schema`（可先修改）作为该命令的 `--input` 查询对象。
3. 基于书签构造新口径查询的推荐路径：`dashboard.get` 定位书签 → 本工具导出 → 在 `input_schema` 上只改用户要求的口径字段（指标 / 筛选 / 时间 / 粒度），其余字段保持导出值不漂移 → 交给对应分析命令执行 → 对比原书签口径与新口径结果。禁止凭书签名称或猜测重新拼查询。

示例变体：

```bash
# 导出书签查询定义
sensors analytics bookmark-export --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101

# 预览请求参数，不发起 HTTP
sensors analytics bookmark-export --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101 --dry-run

# 导出 → 修改 → 执行（示例：事件分析换口径）
sensors analytics bookmark-export --ai-session-id <id> --bookmark-id 5 --dashboard-id 101
# 把输出的 input_schema 改为去重人数口径后执行：
sensors analytics segmentation --ai-session-id <id> --input - <<'JSON'
{"measures": [{"event": "e2e_pay_order", "aggregator": "unique"}],
 "date_range": {"from_date": "2026-05-19", "to_date": "2026-06-10"}}
JSON
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "bookmark_id": 5,
  "bookmark_name": "[e2e] 支付订单分析",
  "dashboard_id": 101,
  "type": "事件分析",
  "status": "success",
  "command": "segmentation",
  "input_schema": {
    "measures": [{"event": "e2e_pay_order", "aggregator": "general", "name": "e2e_pay_order的总次数"}],
    "date_range": {"from_date": "2026-05-19", "to_date": "2026-06-10", "timezone": ""},
    "unit": "day",
    "by_fields": []
  }
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `bookmark_id` / `bookmark_name` / `dashboard_id` | 书签与看板定位信息 | `5` / `[e2e] 支付订单分析` / `101` |
| `type` | 分析类型中文名（如 事件分析 / 漏斗分析），由平台原始类型转换而来 | `事件分析` |
| `status` | 导出状态：`success` / `error` / `unsupported` | `success` |
| `command` | 仅 `status=success` 时存在；`input_schema` 对应的分析命令名（`segmentation` / `distribution` / `funnel` / `retention` / `interval` / `attribution` / `ltv` / `session` / `user-path` / `sql` / `user-property`） | `funnel` |
| `input_schema` | 仅 `status=success` 时存在；已通过对应分析命令输入校验的查询对象 JSON，可直接作为该命令 `--input`（可先修改口径） | 见上例 |
| `warnings` | 仅 `status=success` 且存在参数信息丢失时存在；字符串列表，每条说明一个重放时不会生效或值会变化的书签参数 | 见下文 |
| `error` | 仅 `status=error` 或 `unsupported` 时存在；说明失败原因（校验失败时附具体字段与修正建议） | `参数校验失败: ...` |

三态结构解读：

| `status` | 含义 | 读取方式 |
|---|---|---|
| `success` | 导出成功 | `command` + `input_schema` 即完整查询定义；重放该输入与书签原样执行的查询口径一致 |
| `error` | 书签 data 不是合法 JSON、或反转换后未通过输入校验 | 无 `input_schema`；`error` 附可读校验信息（含修正建议），多为书签定义过旧与当前口径结构不兼容 |
| `unsupported` | 书签类型不在可导出列表（同可执行列表 11 种，如指标分析 `FANCY_METRIC_MODEL` 不支持） | 原样透传，不猜测口径或用 SQL / HTTP 兜底 |

导出参数丢失提示（`warnings`，仅在实际发生丢失时输出）：

命令会把导出的 `input_schema` 重新转换为执行请求并与书签保存的请求体对比，凡书签携带、但输入 schema 无法表达（重放时不会生效）或重放值会变化的参数，逐条生成 warning，格式如：

- `参数 limit=10 未包含在导出结果中，重放该输入时不会生效`
- `参数 sampling_factor 书签值为 1，重放将使用 64`
- `参数 filter={"conditions": [...]} 未包含在导出结果中，重放该输入时不会生效`（如留存书签的全局 filter，输入层只有 user_filter）
- `参数 measures[1]={...} 未包含在导出结果中，重放该输入时不会生效`（如 Session 书签多指标只导出第一个）
- `分组字段 event.$Anything.$country 为事件通配形式（event.$Anything.*），书签绑定的具体事件名不可还原（不影响重放口径）`

纯展示字段（指标显示名等）、分析命令固定注入的常量与自动派生字段（时间分组、缓存开关等重放时会按既定行为再生成）不产生 warning。**`warnings` 必须原样转述给用户，不得忽略**；基于该书签派生新查询前应先向用户确认丢失参数是否可接受。

导出口径的已知有损点（重放查询结果不受影响，重新执行时按输入 schema 自动补齐）：

- 事件分组字段归一化为 `event.$Anything.<属性>` 通配形式（原书签绑定具体事件名时不可逆还原）。
- 各模型自动注入的默认时间分组（漏斗第一步 `$time`、留存初始事件 `$time`、LTV `$time`）不还原。
- 派生字段（`bucket_params`、`filter_field_steps`、`by_events` 等）与服务端常量（`use_cache`、`sampling_factor` 等）不进入导出结果。
- 间隔分析的 `by_fields` 请求侧不落库，导出后为空。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `书签 ID X 在 Dashboard Y 中不存在` | 书签与看板不匹配，或书签已被删除 | 先 `dashboard-get --id <dashboard_id>` 复核书签列表 |
| `--bookmark-id` / `--dashboard-id` 非正整数 | 传入 0 或负数 | 改用 `dashboard-list` / `dashboard-get` 返回的真实 ID |
| `status: error`（校验失败） | 书签保存的请求体与当前输入 schema 结构不匹配（书签定义过旧或字段超范围） | 按 `error` 中的字段路径与建议修正 `input_schema` 后重试；无法修复时建议在平台 UI 重新保存书签 |
| `status: unsupported` | 书签类型不在可导出列表 | 原样返回，不猜测口径兜底 |

## 使用约束

- 本工具只读：不执行任何分析查询，不修改概览与书签；导出后的新查询默认不回写概览，用户要求保存时走 `dashboard.bookmark-add`。
- `input_schema` 是唯一可信口径来源；基于书签派生新查询时禁止凭书签名称重新拼查询，必须以导出值为基准修改。
- `error` 与 `unsupported` 必须原样透传，不得静默跳过或兜底改写。
