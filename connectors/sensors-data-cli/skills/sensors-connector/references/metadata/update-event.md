# 事件更新

> 工具 `metadata.event-update` · 命令 `sensors metadata event-update` · 类型 写入

## 用途

更新已有事件 schema 的白名单字段（显示名、可见性、启用状态、应埋点平台、触发时机、备注）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--name` | 字符串 | 是 | — | 事件原始名（内部映射为 `events.<name>`）；CLI 拒绝带 `events.` 前缀或完整 schema 名，不自动查询或补全目标事件 | `trading_day_management` |
| `--changes` | JSON | 是 | — | 待更新字段集合，JSON object 或 `@file.json`，字段见下节 | `{"display_name":"交易日历V2","visible":true,"enable":true,…}` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON 并退出，不调用更新接口 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata event-update --help`。

## 输入 Schema

`--changes` JSON object 仅允许六个键，且至少提供一个（否则 CLI 直接报错、不发请求）：

| 字段 | 类型 | 说明 | 示例值 |
|---|---|---|---|
| `display_name` | 字符串 | 新的事件显示名，不能为空字符串或纯空白 | `交易日历V2` |
| `visible` | 布尔 | 新的可见状态 | `true` |
| `enable` | 布尔 | 新的启用状态 | `true` |
| `platforms` | 字符串数组 | 新的应埋点平台枚举名数组，**全量覆盖**；元素仅支持 `ANDROID` / `IOS` / `WEB` / `MINI_APP` / `SERVER` / `OTHER` 且不可重复；空数组表示清空应埋点平台 | `["ANDROID","IOS"]` |
| `trigger_timing` | 字符串 | 新的事件触发时机说明 | `用户提交订单成功时` |
| `remark` | 字符串 | 新的事件备注 | `核心事件` |

- CLI 根据显式传入的字段自动生成 `update_mask`（如 `display_name,enable`），未传入的字段不受影响。
- 以 `--schema` 实时输出为最终事实源；本命令无 `--schema` 时以 `--dry-run` 打印的请求 JSON 为准。

## 构造流程

从业务输入到更新执行的步骤化映射（读取现状 → 构造 changes → dry-run 预览 → 确认 → 执行 → 回读）：

### 1. 读取现状

用 `metadata.event-get --name <原始名>` 取当前定义，作为变更摘要的「变更前」基线；目标不存在时先核对原始名。

### 2. 构造 --changes

只放本次要改的键，未列入的键保持不动（CLI 按显式键自动生成 `update_mask`）：

| 业务输入 | `--changes` 键 | 请求映射 |
|---|---|---|
| 新的事件显示名 | `display_name` | `schema.display_name` |
| 可见 / 启用开关 | `visible` / `enable` | `schema.visible` / `schema.enable` |
| 应埋点平台 | `platforms` | 独立 `statistics_update` 请求，全量覆盖：传目标平台全集（逐个映射为 `ANDROID` / `IOS` / `WEB` / `MINI_APP` / `SERVER` / `OTHER`），`[]` 表示清空 |
| 触发时机 / 备注 | `trigger_timing` / `remark` | `schema.custom_params.meta_trigger_action_desc` / `meta_desc` |

`--name` 只传事件原始名（不带 `events.` 前缀、不含 `.`），CLI 内部映射为 `events.<name>`。

### 3. dry-run 预览

```bash
sensors metadata event-update --ai-session-id <ai_session_id> --name order_submit \
  --changes '{"display_name":"提交订单V2","enable":false}' --dry-run
```

含 `platforms` 时预览输出 `event_update` 与 `statistics_update` 两个请求分支，对应真实执行的两个请求；`--changes` 只含 `platforms` 时 `event_update` 分支为 `null`（无事件更新请求，仅发统计更新请求）。

### 4. 确认与执行

向调用方展示「变更前 → 变更后」摘要与待执行命令，收到精确回复 `Approved` 后用相同输入执行；`platforms` 与其它字段混合时两个请求非原子，逐分支核对结果。

### 5. 回读

用 `metadata.event-get --name <原始名>` 回读核对更新后字段。

## 输出

- `--dry-run`：不含 `platforms` 时输出单个事件更新请求体（`schema.name` 固定映射为 `events.<name>`、`schema.*` 本次显式更新字段、`update_mask`）；含 `platforms` 时输出 `event_update` 与 `statistics_update` 两个请求分支，只含 `platforms` 时 `event_update` 为 `null`。
- 真实执行：不含 `platforms` 时输出服务端返回的更新后事件核心字段；含 `platforms` 时输出 `event_update` 与 `statistics_update` 两个响应分支，只含 `platforms` 时 `event_update` 为 `null`。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| UsageError（name 非法） | `--name` 带 `events.` 前缀或含 `.` | 只传事件原始名，不带前缀 |
| UsageError（changes 校验失败） | 未提供任何可更新字段、含未允许键、`platforms` 重复 / 未知枚举 | 按错误信息修正 `--changes` 后重试，此阶段不会发起请求 |
| 事件不存在 | `--name` 未注册 | 用 `metadata.events` / `metadata.event-get` 核对原始名 |
| 认证 / 权限 / 写开关错误 | 服务端拒绝写入 | 立即停止并返回修复提示，不重试 |

## 使用约束

- `platforms` 走独立统计接口全量覆盖；与其它字段同时更新时为两个请求、**不具备原子性**（可能一成一败），执行后分别核对输出分支。
- 真实执行按 SKILL.md「写操作安全联锁」：先读取现状（`metadata.event-get`），再 `--dry-run` 预览，向调用方展示变更摘要与待执行命令，取得精确回复 `Approved`（提示语固定为「如确认执行，请回复：Approved」）后才执行；输入或目标变化后旧确认失效。
- 执行成功后用 `metadata.event-get --name <原始名>` 回读核心字段；回读失败时不得宣称最终状态已验证。
- CLI 不提供事件删除命令（亦无 `event-delete` / `field-delete`）；删除类请求返回不支持，不发明或猜测旁路命令。
- 更新事件本体与更新事件下属性是不同命令；属性更新用 `metadata.field-update`。
