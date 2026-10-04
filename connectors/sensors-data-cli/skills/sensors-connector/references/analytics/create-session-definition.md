# Session 定义创建
> 工具 `analysis.session-create` · 命令 `sensors analytics session-create` · 类型 写入

## 用途

在当前项目创建一个自定义 Session 定义，供 Session 分析（[analyze-session.md](analyze-session.md)）以 `session_name` 引用。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径；须包含 `name` / `cname` / `events` / `session_interval_seconds` | `{"name":"test07281",...}` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 session/create Request JSON，不发起真实请求；设置后仍执行写操作门禁 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

真实写入受配置项 `write_operations_enabled` 门禁控制，关闭时拒绝执行。

## 输入 Schema

`--input` JSON 字段（禁止传入未列出的额外字段）：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `name` | string | 是 | 非空白 | Session 定义英文名；创建后作为 Session 分析 `session_name` 的精确值 | `test07281` |
| `cname` | string | 是 | 非空白 | 中文名，用于展示与消歧 | `test0728-1` |
| `events` | string[] | 是 | 至少 1 项，元素非空白 | Session 定义包含的事件英文名列表 | `["$AppStart","$AppViewScreen","$AppEnd"]` |
| `session_interval_seconds` | int | 是 | 正整数 | Session 间隔时间（秒），超过该间隔无事件则切分 Session | `300` |
| `is_event_split` | bool | 否 | 默认 `false` | 是否开启事件切割 | `true` |
| `start_event` | string | 条件 | 非空白 | 事件切割开启时的 Session 开始事件；`is_event_split=true` 时必填 | `$Anything` |
| `stop_event` | string | 条件 | 非空白 | 事件切割开启时的 Session 结束事件；`is_event_split=true` 时必填 | `$AppEnd` |
| `comment` | string | 否 | — | 备注说明 | `connector 示例` |
| `id` | int | 否 | 正整数；创建场景不传 | 仅更新语义使用，创建时勿传 | — |

本命令无过滤树 / 日期范围等共享结构；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

从业务输入到合法 JSON 的构造映射：

1. **定事件集**：确认纳入 Session 的全部事件英文名（经调用方确认为精确名），写入 `events[]`。
2. **定切分口径**：
   - 只按时间间隔切分：`is_event_split` 不传或 `false`，不填 `start_event` / `stop_event`。
   - 按起止事件切割：`is_event_split=true`，并填 `start_event`（Session 开始事件）与 `stop_event`（结束事件）——两者必须同时出现。
3. **定间隔**：业务口径的「无事件多久后切分」换算为秒写入 `session_interval_seconds`（如「30 分钟」→ `1800`）。
4. **命名**：`name` 用英文标识（后续 Session 分析 `session_name` 的精确值），`cname` 用中文展示名。

最小示例（时间间隔切分）：

```bash
sensors analytics session-create --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_SESSION__'
{
  "name": "my_session",
  "cname": "我的会话",
  "events": ["page_view", "product_click", "order_submit"],
  "session_interval_seconds": 1800
}
__SENSORS_SESSION__
```

事件切割变体（`is_event_split=true` 时 `start_event` / `stop_event` 必填）：

```json
{
  "name": "order_session",
  "cname": "下单会话",
  "events": ["product_click", "cart_add", "order_submit"],
  "session_interval_seconds": 1800,
  "is_event_split": true,
  "start_event": "product_click",
  "stop_event": "order_submit"
}
```

按写操作安全联锁推进：`session-list` 确认无同名定义 → `--dry-run` 预览 → 调用方确认 → 执行 → `session-list` 回读。

## 输出

| 字段 | 含义 | 示例值 |
|---|---|---|
| `id` | 创建成功后的 Session 定义编号 | `156` |
| `request_id` | 请求追踪 ID | `7b44901c0ad4488aa7a158c49a7e03cc` |

创建结果可通过 [list-session-definitions.md](list-session-definitions.md) 回读验证。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `字段不能为空` | `name` / `cname` 为空白字符串 | 填非空文本 |
| `events 至少包含一个事件名` / `events 中不能包含空事件名` | 列表为空或含空白项 | 提供至少一个非空事件英文名 |
| `session_interval_seconds 必须为正整数` | 间隔 ≤ 0 | 传正整数（秒） |
| `is_event_split=true 时 start_event 必填` / `stop_event 必填` | 开启切割但缺起止事件 | 补齐两个切割事件 |
| `id 必须为正整数` | `id` ≤ 0 | 创建场景直接去掉 `id` |
| 额外字段被拒 | 传入未定义字段 | 删除 schema 外字段 |
| 写操作被拒绝 | `write_operations_enabled` 关闭 | 由调用方确认后开启写开关再执行 |
| SA 版本不满足 | 组件 ≤ 3.0.4.573 | 升级神策组件 |

## 使用约束

- 写入工具：执行真实创建前按写操作安全联锁执行——`session-list` 读取现状、`--dry-run` 预览、取得调用方明确确认、执行后回读。
- `events` / `start_event` / `stop_event` 必须是已确认的精确事件名，多候选时禁止自行二选一。
- 创建后的 `name` 即为后续 Session 分析的 `session_name`，须原样使用。
