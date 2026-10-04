# 属性更新

> 工具 `metadata.field-update` · 命令 `sensors metadata field-update` · 类型 写入

## 用途

更新 schema 下单个已有属性的白名单字段（显示名、可见性、启用状态、示例说明）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--schema-name` | 字符串 | 是 | — | 完整 schema 名，如 `events.order_submit`、`users`；不做自动补全或推断 | `events.trading_day_management` |
| `--name` | 字符串 | 是 | — | 属性名，定位 schema 下已存在的目标属性；不自动查询或补全 | `is_trading_day` |
| `--changes` | JSON | 是 | — | 待更新字段集合，JSON object 或 `@file.json`，字段见下节 | `{"display_name":"是否交易日V2","visible":true,"enable":true,…}` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON 并退出，不调用更新接口 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata field-update --help`。

## 输入 Schema

`--changes` JSON object 仅允许四个键，且至少提供一个（否则 CLI 直接报错、不发请求）：

| 字段 | 类型 | 说明 | 示例值 |
|---|---|---|---|
| `display_name` | 字符串 | 新的属性显示名，不能为空字符串或纯空白 | `是否交易日V2` |
| `visible` | 布尔 | 新的可见状态 | `true` |
| `enable` | 布尔 | 新的启用状态 | `true` |
| `remark` | 字符串 | 新的属性示例或说明 | `示例：99.90，单位为元` |

- 不支持更新 `data_type`，也不支持传入其它未列出键（`extra=forbid`，多余键直接报错）。
- CLI 根据显式传入的字段自动生成 `update_mask`（如 `display_name,enable`）；`remark` 映射为 `custom_params.meta_desc`。
- 以 `--schema` 实时输出为最终事实源；本命令无 `--schema` 时以 `--dry-run` 打印的请求 JSON 为准。

## 构造流程

从业务输入到更新执行的步骤化映射（读取现状 → 构造 changes → dry-run 预览 → 确认 → 执行 → 回读）：

### 1. 读取现状

用 `metadata.field-get --schema-name <schema> --field-name <name>` 取当前属性定义，作为变更摘要的「变更前」基线；目标不存在时先核对 schema 与属性名。

### 2. 构造 --changes

只放本次要改的键（`display_name` / `visible` / `enable` / `remark` 至少一个），CLI 按显式键自动生成 `update_mask`：

| 业务输入 | `--changes` 键 | 请求映射 |
|---|---|---|
| 新的属性显示名 | `display_name` | `field.display_name` |
| 可见 / 启用开关 | `visible` / `enable` | `field.visible` / `field.enable` |
| 新的示例或说明 | `remark` | `field.custom_params.meta_desc` |

`data_type` 不可更新，不放入 changes；一次只更新一个属性，批量修改逐个构造。

### 3. dry-run 预览

```bash
sensors metadata field-update --ai-session-id <ai_session_id> --schema-name events.order_submit \
  --name order_amount --changes '{"display_name":"订单金额V2","visible":false}' --dry-run
```

### 4. 确认与执行

向调用方展示「变更前 → 变更后」摘要与待执行命令，收到精确回复 `Approved` 后用相同输入执行。

### 5. 回读

用 `metadata.field-get --schema-name <schema> --field-name <name>` 回读核对更新后字段。

## 输出

- `--dry-run`：输出请求体 JSON——`schema_name`、`field.name`、`field.*` 本次显式更新字段、`field.custom_params.meta_desc`（传 `remark` 时）、`update_mask`。
- 真实执行：输出服务端返回的更新后属性核心字段（如 `name`、`display_name`、`visible`、`enable`）。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| UsageError（changes 校验失败） | 未提供任何可更新字段、含未允许键（如 `data_type`） | 按错误信息修正 `--changes` 后重试，此阶段不会发起请求 |
| Schema / 属性不存在 | `--schema-name` 或 `--name` 未注册 | 用 `metadata.fields` / `metadata.event-fields` / `metadata.field-get` 核对名称 |
| 认证 / 权限 / 写开关错误 | 服务端拒绝写入 | 立即停止并返回修复提示，不重试 |

## 使用约束

- 一次只更新一个属性；批量修改需逐个调用，每个目标单独确认。
- 真实执行按 SKILL.md「写操作安全联锁」：先读取现状（`metadata.field-get`），再 `--dry-run` 预览，向调用方展示变更摘要与待执行命令，取得精确回复 `Approved`（提示语固定为「如确认执行，请回复：Approved」）后才执行；输入或目标变化后旧确认失效。
- 执行成功后用 `metadata.field-get --schema-name <schema> --field-name <name>` 回读确认；回读失败时不得宣称最终状态已验证。
- 更新属性与更新事件本体是不同命令；事件级字段用 `metadata.event-update`。
