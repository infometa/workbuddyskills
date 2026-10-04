# Schema 属性列表查询

> 工具 `metadata.fields` · 命令 `sensors metadata fields` · 类型 查询

## 用途

查询整个 Schema 下注册的全量属性列表（Schema 视角），不区分事件；与 `metadata.event-fields`（事件视角实际上报子集）相对。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | Schema 名：物理表 `events` / `users` / `items`，或逻辑事件 `events.<事件原始名>` | `users` |
| `--field-names` | 字符串 | 否 | 不填 | 按属性名过滤，多个用逗号分隔（如 `'$province,$city'`） | `'$latest_utm_campaign,Age'` |
| `--include-disabled` | 开关 | 否 | 关闭 | 包含不可见或未启用的属性（`visible=false` 或 `enable=false`）；默认过滤 | — |
| `--expand-mapping` | 开关 | 否 | 关闭 | 追加每个属性对应的底层列名（`column`）与映射方式（`source_type`） | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata fields --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。常用 `--schema-name` 取值：

- `events`：事件表全量属性（含内置 `$*` 属性）
- `users`：用户属性全量
- `items`：维度表属性

## 输出

输出为 `fields[]` 数组，每个元素：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 属性名（用于 SQL WHERE / GROUP BY，内置属性以 `$` 开头） | `$latest_utm_campaign` |
| `display_name` | 属性显示名 | `最近一次广告系列名称` |
| `data_type` | 数据类型：`STRING` / `NUMBER` / `BOOL` / `LIST` / `DATE` / `DATETIME` / `OBJECT` | `STRING` |
| `identity` | 是否为身份属性 | `false` |
| `required` | 是否必填 | `false` |
| `has_data` | 是否有数据；仅 `--include-disabled` 时输出 | `false` |
| `visible` | 是否可见；仅 `--include-disabled` 时输出 | `true` |
| `enable` | 是否启用；仅 `--include-disabled` 时输出 | `true` |
| `column` | 底层物理列名；仅 `--expand-mapping` 时输出 | `$latest_utm_campaign` |
| `source_type` | 列映射方式：`MAIN_TABLE_COLUMN` 直接列 / `COMPLEX_EXPRESSION` 计算列；仅 `--expand-mapping` 时输出 | `MAIN_TABLE_COLUMN` |

- 默认输出已裁剪掉管理类字段；`data_type` 只保留类型名。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| Schema 不存在（404 / can not find schema） | `--schema-name` 拼写错误或未注册 | 核对取值（`events` / `users` / `items` / `events.<事件原始名>`）后重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| 属性过滤结果为空 | `--field-names` 中的属性名不存在 | 去掉过滤拉全量属性后由调用方匹配 |

## 使用约束

- 查用户属性固定用 `--schema-name users`；查某事件特有属性用 `metadata.event-fields`，两者不要混用。
- 语义匹配（口语描述到 `name`）与多候选取舍由调用方完成；空结果原样返回。
