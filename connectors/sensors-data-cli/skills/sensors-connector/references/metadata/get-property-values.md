# 属性取值查询

> 工具 `metadata.values` · 命令 `sensors metadata values` · 类型 查询

## 用途

查询某个属性的候选取值列表（如枚举值），用于构造过滤条件或核对取值上报状态。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | 属性所属 schema，与 `metadata.fields` / `metadata.field-get` 同构：`events` / `users` / `events.<事件原始名>`（可从 event-fields 结果原样传入） | `events.$pageview` |
| `--field-name` | 字符串 | 是 | — | 属性内部名，精确匹配（如 `'$country'`、`e2e_vip_level`） | `'$brand'` |
| `--limit` | 正整数 | 否 | 不填 | 最大返回候选值个数（≥1）；不填由服务端决定返回规模 | `10` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON（`method` / `action` / `body` 包裹结构），不发起真实请求 | — |

参数风格与 fields 家族一致（`--schema-name` + `--field-name`），没有 `--property` / `--table-type` 选项；事件属性与用户属性的区分由 `--schema-name` 表达（`events*` → 事件属性，`users` → 用户属性）。

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata values --help`。

调用示例（来自 CLI 帮助）：

```bash
sensors metadata values --schema-name events --field-name '$country' --ai-session-id <ai_session_id> --format json
sensors metadata values --schema-name events.e2e_submit_order --field-name '$province' --format json
sensors metadata values --schema-name users --field-name e2e_vip_level --limit 20 --format json
```

## 输入 Schema

无 `--input` 复杂输入，参数见上表。`--schema-name` 与 `--field-name` 均来自 `metadata.event-fields` / `metadata.fields` 的结果字段（`schema_name` / `name`），原样下传即可。

## 输出

| 字段 | 说明 | 示例值 |
|---|---|---|
| `values` | 候选取值数组（字符串列表），按服务端返回原样透传 | `["SONY","NUBIA","LIANTONG",...]` |

- 返回被 `--limit` 截断时，结果为当前条件下的部分取值，不代表全集。
- 空列表表示该属性尚无任何取值上报，属结构事实，原样返回调用方。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `No such option '--property'` / `'--table-type'` | 使用了旧版参数 | 已统一为 `--schema-name` + `--field-name`，按上表重试 |
| schema 不支持 | `--schema-name` 传了 `items` 等 | 属性取值仅支持 events / users 两类，换正确 schema |
| 属性不存在 / 无数据 | `--field-name` 未注册或从未上报 | 用 `metadata.fields` / `metadata.event-fields` 核对属性名与归属后重试 |
| `--limit` 非法 | 取值小于 1 或不是整数 | 改传正整数 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |

## 使用约束

- 属性归属必须明确：事件属性与用户属性同名时，靠 `--schema-name` 区分；需要两类都查时分别调用两次，不做跨表合并。
- 高基数属性（取值极多）应传 `--limit` 控制返回规模；截断状态必须原样传回调用方。
