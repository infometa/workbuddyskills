# Schema 元信息查询

> 工具 `metadata.schema-get` · 命令 `sensors metadata schema-get` · 类型 查询

## 用途

按名称查询单个 Schema 的元信息（类型、所属类、原始名、数据状态）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--name` | 字符串 | 是 | — | Schema 名：物理 Schema `events` / `users` / `items`，或逻辑事件 Schema `events.<事件原始名>`（如 `events.ViewProduct`） | `events.sa_query_analytics` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata schema-get --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。支持的两种 Schema：

- 物理 Schema：`events` / `users` / `items`，对应底层存储表
- 逻辑事件 Schema：`events.<事件原始名>`

## 输出

输出为单个对象（非数组）：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | Schema 内部标识名 | `events.sa_query_analytics` |
| `display_name` | Schema 显示名 | `任意分析模型查询` |
| `original_name` | 原始名；逻辑事件 Schema 时为事件原始名 | `sa_query_analytics` |
| `type` | Schema 类型：`PHYSICAL` / `LOGICAL` / `VIRTUAL` | `LOGICAL` |
| `schema_class` | 数据类别：`EVENT` / `USER` / `ITEM` | `EVENT` |
| `has_data` | 是否有数据 | `true` |

- 默认输出已裁剪掉管理字段（`visible` / `enable` / `builtin` 等）；本命令不返回底层表映射信息。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| Schema 不存在（404 / not found） | `--name` 拼写错误或未注册 | 事件用 `metadata.events` 核对原始名；物理 Schema 核对 `events` / `users` / `items` 拼写 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| 项目不存在 / 无权限 | `--project` 指向不可用项目 | 停止执行，返回配置或权限修复提示 |

## 使用约束

- 需要属性列表时用 `metadata.fields` / `metadata.event-fields`，本命令只返回 Schema 级元信息。
- `has_data=false` 表示已注册但历史无上报；输出时保留字段原值。
