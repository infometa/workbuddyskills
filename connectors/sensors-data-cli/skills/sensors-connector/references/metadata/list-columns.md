# 表列信息查询

> 工具 `metadata.columns` · 命令 `sensors metadata columns` · 类型 查询

## 用途

查询指定表的列定义（列名、显示名、类型、注释），列名可直接用于 SQL 的 SELECT / WHERE。与 `metadata.fields` 相对：本命令返回物理 SQL 视角的列，`metadata.fields` 返回业务语义的逻辑属性。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--db-name` | 字符串 | 是 | — | 数据库名；来自 `metadata.databases` 输出的 `name` | `horizon_production_3` |
| `--table` | 字符串 | 是 | — | 表名；来自 `metadata.tables` 输出的 `name` | `analy_huobi` |
| `--expand` | 字符串 | 否 | `columns` | 额外返回字段，逗号分隔；可选值 `custom_params` / `columns` / `source` / `business_scopes` / `access_info` | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata columns --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。获取链路：`metadata.databases` 拿 `db_name` → `metadata.tables` 拿表名 → 本命令查列。

## 输出

默认（`--expand` 为 `columns`）输出裁剪后的表详情：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 表名 | `analy_huobi` |
| `display_name` | 表显示名 | `明细表` |
| `columns[].name` | 列名（直接用于 SQL） | `id` |
| `columns[].display_name` | 列显示名 | `id` |
| `columns[].data_type` | 数据类型 | `STRING` |
| `columns[].comment` | 列注释 | — |

- `--expand` 含默认 `columns` 以外的值时（如 `columns,source`），透传服务端完整响应，不做裁剪。
- 顶层其余字段按服务端返回原样透传。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 数据库 / 表不存在 | `--db-name` 或 `--table` 错误 | 用 `metadata.databases` / `metadata.tables` 核对名称后重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| 项目不存在 / 无权限 | `--project` 指向不可用项目 | 停止执行，返回配置或权限修复提示 |

## 使用约束

- 列定义按表原样返回；列名到业务口径的对应由调用方判断。
- 物理 `data_type` 与逻辑属性 `data_type` 口径不同，不要把两者直接等同。
