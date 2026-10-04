# 事件列表查询

> 工具 `metadata.events` · 命令 `sensors metadata events` · 类型 查询

## 用途

分页查询当前项目的事件 schema 列表，返回每个事件的精确名、显示名、原始名与数据状态。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--page-size` | 整数 | 否 | `100` | 每页条数；`-1` 返回所有事件 | `100` |
| `--schema-type` | 枚举 | 否 | 不填 | 过滤 Schema 类型：`LOGICAL` 逻辑事件 / `VIRTUAL` 虚拟事件；不填返回两者 | `LOGICAL` |
| `--display-names` | 字符串 | 否 | 不填 | 按显示名过滤，多个用逗号分隔（如 `提交订单,页面浏览`），精确匹配 | `交易日历` |
| `--include-empty` | 开关 | 否 | 关闭 | 包含 `has_data=false` 的无数据事件；默认过滤掉无数据事件 | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata events --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。服务端只按显式条件（`schema_type`、`display_names`）过滤，不做模糊匹配；口语描述到精确名的匹配由调用方完成。

## 输出

| 字段 | 说明 | 示例值 |
|---|---|---|
| `schemas[].name` | 事件内部标识名，下游命令直接使用 | `events.sa_query_analytics` |
| `schemas[].display_name` | 事件显示名，用于展示与语义匹配 | `任意分析模型查询` |
| `schemas[].original_name` | 事件原始名，用于构造 `metadata.event-fields` 的 `--schema-name`（`events.<original_name>`）和 `metadata.event-get` 的 `--name` | `sa_query_analytics` |
| `schemas[].has_data` | 事件是否有数据；仅 `--include-empty` 时输出 | `true` |
| `total_size` | 服务端返回的事件总数；默认过滤 `has_data=false` 时可能大于 `schemas[]` 实际返回条数 | `1486` |
| `has_next` | 是否还有下一页 | `true` |

- `has_data` 表示历史是否有过上报，不代表近期活跃度。
- 默认输出已裁剪掉管理类字段，仅保留上表字段。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| `--display-names` 过滤结果为空 | 显示名不存在或拼写不符 | 核对显示名；或去掉过滤拉全量列表后由调用方匹配 |
| 项目不存在 / 无权限 | `--project` 指向不可用项目 | 停止执行，返回配置或权限修复提示，不换项目重试 |

## 使用约束

- 确认「事件是否存在 / 是否有数据」的场景必须加 `--include-empty`：默认会过滤 `has_data=false` 的事件且不输出 `has_data` 字段。
- 需要排查无数据事件时一次带 `--include-empty` 拉取，不要先查一遍再补查一遍。
- 空结果原样返回调用方；`schemas[]` 为空只说明当前过滤条件下无匹配，不编造绝对结论。
