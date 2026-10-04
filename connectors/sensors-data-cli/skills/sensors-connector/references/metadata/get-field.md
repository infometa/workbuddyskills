# 属性详情查询

> 工具 `metadata.field-get` · 命令 `sensors metadata field-get` · 类型 查询

## 用途

按 Schema 名 + 属性名精确查询单个属性的详细信息（类型、数据状态、身份属性标记等）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | Schema 名，如 `events` / `users` | `users` |
| `--field-name` | 字符串 | 是 | — | 属性名，精确匹配且区分大小写（如 `'$province'`、`first_id`） | `'$latest_utm_campaign'` |
| `--expand-mapping` | 开关 | 否 | 关闭 | 追加属性对应的底层列名（`column`）与映射方式（`source_type`） | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata field-get --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。属性名不确定时先用 `metadata.fields` / `metadata.event-fields` 查询 `name`。

## 输出

输出为单个对象（非数组）：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 属性名 | `$latest_utm_campaign` |
| `display_name` | 属性显示名 | `最近一次广告系列名称` |
| `data_type` | 数据类型：`STRING` / `NUMBER` / `BOOL` / `LIST` / `DATE` / `DATETIME` / `OBJECT` | `STRING` |
| `has_data` | 是否有数据 | `false` |
| `identity` | 是否为身份属性（如 `distinct_id`） | `false` |
| `primary_identity` | 是否为主身份属性 | `false` |
| `required` | 是否必填 | `false` |
| `column` | 底层物理列名；仅 `--expand-mapping` 时输出 | `$latest_utm_campaign` |
| `source_type` | 列映射方式：`MAIN_TABLE_COLUMN` 直接列 / `COMPLEX_EXPRESSION` 计算列；仅 `--expand-mapping` 时输出 | `MAIN_TABLE_COLUMN` |

- 详情接口默认输出 `has_data` / `identity` / `primary_identity`；管理类字段已裁剪。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| Schema 不存在（404 / can not find schema） | `--schema-name` 拼写错误或未注册 | 核对 Schema 名后重试 |
| 属性不存在（404 / not found） | `--field-name` 未注册、拼写或大小写不符 | 用 `metadata.fields` / `metadata.event-fields` 核对属性名后重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |

## 使用约束

- 查事件特有属性前先确认属性归属：事件视角用 `metadata.event-fields`，Schema 视角用 `metadata.fields`，本命令按 Schema + 属性名精确定位。
- `has_data=false` 表示属性已注册但历史无上报；输出时保留字段原值。
