# 事件属性列表查询

> 工具 `metadata.event-fields` · 命令 `sensors metadata event-fields` · 类型 查询

## 用途

查询某个具体事件实际拥有的属性列表（事件视角）；与 `metadata.fields`（Schema 视角全量注册属性）相对，本命令返回该事件实际上报过的属性子集，不同事件结果不同。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | 完整事件 Schema 名，格式 `events.<事件原始名>`（如 `events.ViewProduct`） | `events.$pageview` |
| `--field-names` | 字符串 | 否 | 不填 | 按属性名过滤，多个用逗号分隔（如 `'$province,date'`） | `'$brand,$wifi'` |
| `--include-disabled` | 开关 | 否 | 关闭 | 包含不可见或未启用的属性（`visible=false` 或 `enable=false`）；默认过滤 | — |
| `--expand-mapping` | 开关 | 否 | 关闭 | 追加每个属性对应的底层列名（`column`）与映射方式（`source_type`） | — |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata event-fields --help`。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。`--schema-name` 中的事件原始名来自 `metadata.events` 的 `original_name` 字段。

## 输出

输出为 `fields[]` 数组，每个元素：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 属性名（用于 SQL WHERE / GROUP BY，内置属性以 `$` 开头） | `$brand` |
| `display_name` | 属性显示名 | `设备品牌` |
| `data_type` | 数据类型：`STRING` / `NUMBER` / `BOOL` / `LIST` / `DATE` / `DATETIME` / `OBJECT` | `STRING` |
| `identity` | 是否为身份属性 | `false` |
| `required` | 是否必填 | `false` |
| `has_data` | 是否有数据；仅 `--include-disabled` 时输出 | `true` |
| `visible` | 是否可见；仅 `--include-disabled` 时输出 | `true` |
| `enable` | 是否启用；仅 `--include-disabled` 时输出 | `true` |
| `column` | 底层物理列名；仅 `--expand-mapping` 时输出 | `$brand` |
| `source_type` | 列映射方式：`MAIN_TABLE_COLUMN` 直接列 / `COMPLEX_EXPRESSION` 计算列；仅 `--expand-mapping` 时输出 | `MAIN_TABLE_COLUMN` |

- 默认输出已裁剪掉管理类字段；`data_type` 只保留类型名。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| Schema 不存在（404 / can not find schema） | `--schema-name` 中的事件未注册或拼写不符 | 用 `metadata.events --include-empty` 核对 `original_name`，拼成 `events.<original_name>` 重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| 属性过滤结果为空 | `--field-names` 中的属性名不存在 | 去掉过滤拉全量属性后由调用方匹配 |

## 使用约束

- 排查「属性存在但无数据 / 被禁用」时一次带 `--include-disabled`，避免重复拉取。
- 语义匹配（口语描述到 `name`）与多候选取舍由调用方完成；空结果原样返回。
