# 事件详情查询

> 工具 `metadata.event-get` · 命令 `sensors metadata event-get` · 类型 查询

## 用途

按事件原始名精确查询单个事件的详情（标识名、显示名、原始名、数据状态）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--name` | 字符串 | 是 | — | 事件原始名，精确匹配且区分大小写（如 `ViewProduct`、`e2e_pay_order`）；不接受显示名，不接受 `events.` 前缀 | `sa_query_analytics` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON，不发起真实请求 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata event-get --help`。

调用示例（来自 CLI 帮助）：

```bash
sensors metadata event-get --name ViewProduct --ai-session-id <ai_session_id> --format json
sensors metadata event-get --name e2e_pay_order --ai-session-id <ai_session_id> --format json
```

## 输入 Schema

无 `--input` 复杂输入，参数见上表。原始名不确定时先用 `metadata.events` 查询 `original_name`。

## 输出

输出为单个对象（非数组）：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `name` | 事件内部标识名 | `events.sa_query_analytics` |
| `display_name` | 事件显示名 | `任意分析模型查询` |
| `original_name` | 事件原始名 | `sa_query_analytics` |
| `has_data` | 是否有数据（历史是否有过上报） | `true` |

- 与 `metadata.events` 不同，本命令是详情接口，`has_data` 默认输出（无 `--include-empty` 参数）。
- 默认输出已裁剪掉管理类字段，仅保留上表字段。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 事件不存在（404 / not found） | `--name` 未注册、拼写或大小写不符 | 用 `metadata.events --include-empty` 核对 `original_name` 后重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |
| 项目不存在 / 无权限 | `--project` 指向不可用项目 | 停止执行，返回配置或权限修复提示，不换项目重试 |

## 使用约束

- 名称精确匹配且区分大小写；查询报不存在时不自行换名重试，交回调用方处理。
- `has_data=false` 表示事件已注册但历史无上报；输出时保留字段原值，不得改写为「事件不存在」。
