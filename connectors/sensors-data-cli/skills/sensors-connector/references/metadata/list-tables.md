# 数据表列表查询

> 工具 `metadata.tables` · 命令 `sensors metadata tables` · 类型 查询

## 用途

查询指定数据库下的 Horizon 表列表（表名、显示名、类型），供 SQL 构造时确定 `database.table` 中的表名。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--db-name` | 字符串 | 是 | — | 数据库名；来自 `metadata.databases` 输出的 `name`（当前项目默认库为 `created_by = sensorsdata.horizon` 的记录，如 `horizon_default_1`） | `horizon_production_3` |
| `--names` | 字符串 | 否 | 不填 | 按表名过滤，多个用逗号分隔（精确匹配），不填返回所有表 | — |
| `--page-size` | 整数 | 否 | 服务端默认 1000 | 每页条数，最大 1000，`-1` 返回所有 | — |
| `--page` | 整数 | 否 | 不填 | 页码，从 0 开始 | — |
| `--expand` | 字符串 | 否 | 不填 | 透传全量字段，逗号分隔；可选值 `custom_params` / `columns` / `source` / `business_scopes` / `access_info`；指定后跳过输出裁剪 | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata tables --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。`db_name` 的获取链路：先用 `metadata.databases` 拿库名，再用本命令列表。

## 输出

默认（未指定 `--expand`）输出 `tables[]` 数组，每个元素：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 表名（用于 `metadata.columns` 的 `--table` 参数与 SQL 表名） | `analy_huobi` |
| `display_name` | 表显示名 | `明细表` |
| `type` | 表类型 | `VIEW` |

- 指定 `--expand` 后透传服务端完整响应（含 `columns` 列定义、`source` 数据源、`custom_params`、`business_scopes`、`access_info` 等），不做裁剪。
- 顶层其余字段（如分页信息）按服务端返回原样透传。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 数据库不存在 / 无权限 | `--db-name` 错误或无权限 | 用 `metadata.databases` 核对库名后重试 |
| `--names` 过滤结果为空 | 表名不存在 | 去掉过滤拉全量表列表后由调用方匹配 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |

## 使用约束

- 表名与显示名的语义匹配由调用方完成；空结果原样返回，不自行换库重试。
- 需要 SQL 可用列时用 `metadata.columns` 查指定表，本命令默认输出不含列定义。
