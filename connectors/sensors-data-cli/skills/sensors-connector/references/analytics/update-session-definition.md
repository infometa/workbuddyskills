# Session 定义更新
> 工具 `analysis.session-update` · 命令 `sensors analytics session-update` · 类型 写入

## 用途

按 `id` 部分更新已有自定义 Session 定义（未传字段保持原值，`name` 不可变）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径；须包含 `id` 与要更新的字段 | `{"id":156,"cname":"test0728-1（新口径）","session_interval_seconds":900}` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 session/update Request JSON（已合并现状），不发起真实写入请求——注意会真实调用一次只读的 session/list 读取定义现状用于合并；设置后仍执行写操作门禁 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

执行时 CLI 自动先调 `session_definition.list` 读取当前定义，与输入合并为完整请求；`id` 不存在直接报错。真实写入受 `write_operations_enabled` 门禁控制。

## 输入 Schema

`--input` JSON 字段（部分更新语义，禁止传入未列出的额外字段）：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `id` | int | 是 | 正整数 | 目标 Session 定义编号，可通过 [list-session-definitions.md](list-session-definitions.md) 查询 | `156` |
| `name` | string | 否 | — | 不可变字段：更新时忽略，始终沿用原值 | `test07281` |
| `cname` | string | 否 | 显式传入时非空白 | 中文名；未传保持原值 | `test0728-1（新口径）` |
| `events` | string[] | 否 | 显式传入时至少 1 项且元素非空白 | 事件英文名列表；未传保持原值 | `["$AppStart","$AppViewScreen","$AppEnd"]` |
| `session_interval_seconds` | int | 否 | 显式传入时正整数 | 间隔时间（秒）；未传保持原值 | `900` |
| `is_event_split` | bool | 否 | — | 是否开启事件切割；未传保持原值；合并后为 `true` 时须满足起止事件必填 | `true` |
| `start_event` | string | 否 | 切割开启时非空白 | 开始事件；未传保持原值 | `$Anything` |
| `stop_event` | string | 否 | 切割开启时非空白 | 结束事件；未传保持原值 | `$AppEnd` |
| `comment` | string | 否 | — | 备注说明；未传保持原值 | `""` |

本命令无过滤树 / 日期范围等共享结构；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

部分更新语义的构造映射（CLI 自动读取现状并合并，`--dry-run` 输出的是合并后的最终请求）：

1. **定位目标**：`session-list` 找到目标定义，记录 `id` 与当前各字段值（合并基准）。
2. **只写变化项**：需要变更的字段才出现在输入 JSON 中；`cname` / `events` / `session_interval_seconds` / `is_event_split` / `start_event` / `stop_event` / `comment` 均可省略，省略即沿用原值。
3. **切割状态合并检查**：显式传 `is_event_split=true`、或原定义已开启切割时，合并后必须同时具备 `start_event` 与 `stop_event`（可只传缺失的一侧）。
4. **不传 `name`**：更新忽略 `name`，改名需求应走新建。

仅改间隔与中文名的最小示例：

```bash
sensors analytics session-update --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_SESSION_UPDATE__'
{
  "id": 12,
  "cname": "我的会话（新口径）",
  "session_interval_seconds": 900
}
__SENSORS_SESSION_UPDATE__
```

从时间间隔切分切换为事件切割的变体（须同时补齐起止事件）：

```json
{
  "id": 12,
  "is_event_split": true,
  "start_event": "product_click",
  "stop_event": "order_submit"
}
```

按写操作安全联锁推进：定位与现状读取 → `--dry-run` 预览合并结果 → 调用方确认 → 执行 → `session-list` 回读。

## 输出

| 字段 | 含义 | 示例值 |
|---|---|---|
| `id` | 更新后的 Session 定义编号 | `156` |
| `request_id` | 请求追踪 ID | `7b44901c0ad4488aa7a158c49a7e03cc` |

更新结果可通过 [list-session-definitions.md](list-session-definitions.md) 回读验证。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `session-update 必须提供 id` | 缺 `id` | 先 `session-list` 确认目标 `id` 再传入 |
| `未找到 id=<N> 的 Session 定义` | `id` 不存在 | 重新 `session-list` 核对编号 |
| `id 必须为正整数` | `id` ≤ 0 | 传正整数编号 |
| `字段不能为空` / `events 至少包含一个事件名` 等 | 显式传入字段非法 | 按约束修正后再提交 |
| `is_event_split=true 时 start_event 必填` / `stop_event 必填` | 合并后开启切割但缺起止事件 | 补齐两个切割事件（含沿用原值的场景） |
| 额外字段被拒 | 传入未定义字段 | 删除 schema 外字段 |
| 写操作被拒绝 | `write_operations_enabled` 关闭 | 由调用方确认后开启写开关再执行 |
| SA 版本不满足 | 组件 ≤ 3.0.4.573 | 升级神策组件 |

## 使用约束

- 写入工具：执行真实更新前按写操作安全联锁执行——`session-list` 定位唯一目标并读取现状、`--dry-run` 预览合并结果、取得调用方对本次输入与目标的明确确认、执行后回读。
- 更新会影响平台侧所有使用该 Session 定义的分析口径；仅本次分析需要不同口径时应改用 `session-create` 新建，而不是更新。
- 输入中的 `name` 会被忽略，不得以改名为目的调用本命令。
