# Session 定义列表
> 工具 `analysis.session-list` · 命令 `sensors analytics session-list` · 类型 查询

## 用途

查询当前项目下全部自定义 Session 定义（id、英文名、事件列表、间隔时间、切割配置等）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--dry-run` | flag | 否 | 关闭 | 打印将发送的空 query params dict（`{}`），不发起真实请求 | — |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`；`pretty` 按中文字段标签分段展示 | — |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | — |

## 输入 Schema

本命令无 `--input`，不接收任何筛选条件；如需按名称消歧，在返回的 `sessions` 中按 `name` / `cname` 查找。以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

本命令与「Session 分析查询」（[analyze-session.md](analyze-session.md)）是两个不同工具：本命令管理平台侧 Session 定义；Session 分析通过 `session_name` 引用这里的定义执行指标查询。创建与更新定义分别见 [create-session-definition.md](create-session-definition.md) 与 [update-session-definition.md](update-session-definition.md)。

## 输出

| 字段 | 含义 | 示例值 |
|---|---|---|
| `total` | Session 定义总数（由 CLI 按列表长度计算） | `75` |
| `sessions[]` | Session 定义列表，字段见下 | `[{"id":156,"name":"test07281",...}]` |
| `request_id` | 请求追踪 ID | `7b44901c0ad4488aa7a158c49a7e03cc` |

`sessions[]` 每项字段：

| 字段 | 含义 | 示例值 |
|---|---|---|
| `id` | Session 定义编号；`session-update` 定位目标用 | `156` |
| `name` | 英文名；写入 [analyze-session.md](analyze-session.md) 查询 `session_name` 的精确值 | `test07281` |
| `cname` | 中文展示名，与 `name` 配合消歧 | `test0728-1` |
| `events` | 定义覆盖的事件英文名列表 | `["$AppStart","$AppViewScreen","$AppEnd"]` |
| `session_interval_seconds` | Session 间隔时间（秒） | `300` |
| `is_event_split` | 是否启用事件切割 | `true` |
| `start_event` / `stop_event` | 开启事件切割时的起止事件；未开启事件切割（`is_event_split=false`）时仍返回这两个字段，值为空字符串 `""` | `$Anything` / `$AppEnd` |
| `comment` | 备注说明 | `""` |
| `create_time` / `update_time` / `user_name` | 创建时间 / 更新时间 / 所属人 | `2026-07-28T09:03:10Z` / `2026-07-28T09:03:10.032Z` / `jizhihong` |

`json` 输出保留原始字段键名；`pretty` 输出将上述字段按中文标签（编号 / 英文名 / 中文名 / 事件列表 / 间隔时间（秒）/ 是否事件切割 / 开始事件 / 结束事件 / 备注 / 创建时间 / 更新时间 / 所属人）分段展示，便于直接阅读。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| SA 版本不满足 | 组件 ≤ 3.0.4.573 | 升级神策组件 |
| 认证 / 权限 / 网络错误 | 配置或环境问题 | 停止重试，返回错误与 `request_id` 交调用方处理 |
| 返回结构与 Schema 不符 | 上游接口异常 | 原样返回错误，不猜测字段 |
| `业务命令必须指定 --ai-session-id` | 缺会话 ID | 先经 `context.session-start` 建立会话再调用 |

## 使用约束

- 多候选 Session 定义时禁止自行二选一，把候选 `id/name/cname/events` 交还调用方确认。
- 返回的 `name` 是后续 Session 分析 `session_name` 的唯一合法来源，不得用中文名或猜测名替代。
- 空列表表示项目当前无 Session 定义，属正常结果。
