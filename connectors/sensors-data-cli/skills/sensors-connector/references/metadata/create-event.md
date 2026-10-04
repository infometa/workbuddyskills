# 事件创建

> 工具 `metadata.event-create` · 命令 `sensors metadata event-create` · 类型 写入

## 用途

在 `events` 物理 schema 下注册一个新事件 schema（原始名 + 显示名，可附带埋点设计信息）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--name` | 字符串 | 是 | — | 事件原始名，精确注册该事件；CLI 不做自动补全或推断 | `order_submit` |
| `--display-name` | 字符串 | 是 | — | 事件显示名，需在事件 schema 下保持唯一；按传入值原样创建 | `提交订单` |
| `--options` | JSON | 否 | 不写入 | 事件扩展信息，JSON object 或 `@file.json`，字段见下节 | `{"platforms":["ANDROID","IOS"],"trigger_timing":"用户提交订单成功时","remark":"核心事件"}` |
| `--dry-run` | 开关 | 否 | 关闭 | 打印请求 JSON 并退出，不调用创建接口 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata event-create --help`。

## 输入 Schema

`--options` JSON object 仅允许三个键：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `platforms` | 字符串数组 | 否 | 应埋点平台枚举名数组；元素仅支持 `ANDROID` / `IOS` / `WEB` / `MINI_APP` / `SERVER` / `OTHER`，不能为空数组、不能重复 | `["ANDROID","IOS"]` |
| `trigger_timing` | 字符串 | 否 | 事件触发时机说明 | `用户提交订单成功时` |
| `remark` | 字符串 | 否 | 事件备注 | `核心事件` |

- `--name`、`--display-name` 不能为空字符串或纯空白；未传 `--options` 时不写入任何扩展信息。
- 以 `--schema` 实时输出为最终事实源；本命令无 `--schema` 时以 `--dry-run` 打印的请求 JSON 为准。

## 构造流程

从业务输入到创建执行的步骤化映射（读取现状 → dry-run 预览 → 确认 → 执行 → 回读）：

### 1. 读取现状

用 `metadata.events` / `metadata.event-get` 确认 `--name`（原始名）与 `--display-name` 均未被占用；任一冲突时停下交回调用方，不自动改名。

### 2. 映射业务输入

| 业务输入 | 映射目标 |
|---|---|
| 事件英文变量名 | `--name`（原样传，CLI 不补全；首尾空白会被去除） |
| 事件中文名 | `--display-name`（原样创建，不自动生成别名） |
| 应埋点平台（Android / iOS / Web / 小程序 / 服务端 / 其它） | `--options.platforms`，逐个映射为 `ANDROID` / `IOS` / `WEB` / `MINI_APP` / `SERVER` / `OTHER`，不可重复、不可为空数组 |
| 触发时机描述 | `--options.trigger_timing`（请求中映射为 `custom_params.meta_trigger_action_desc`） |
| 备注 | `--options.remark`（请求中映射为 `custom_params.meta_desc`） |

`--options` 只放本次要写入的键；无埋点设计信息时整体省略，不传空对象。

### 3. dry-run 预览

```bash
sensors metadata event-create --ai-session-id <ai_session_id> --name order_submit \
  --display-name "提交订单" \
  --options '{"platforms":["ANDROID","IOS"],"trigger_timing":"用户提交订单成功时","remark":"核心事件"}' \
  --dry-run
```

预览输出即最终请求体：`physical_schema_name` 固定 `events`，名称与扩展信息按上表映射后各就各位。

### 4. 确认与执行

向调用方展示变更摘要与待执行命令，收到精确回复 `Approved` 后去掉 `--dry-run`、用完全相同的输入执行；输入或目标变化则重新预览确认。

### 5. 回读

用 `metadata.event-get --name order_submit` 回读确认注册结果。

## 输出

- `--dry-run`：输出请求体 JSON——`physical_schema_name`（固定 `events`）、`schemas[].original_name`、`schemas[].display_name`、`schemas[].custom_params`（显式传 `trigger_timing` / `remark` 时）、`schemas[].statistics.track_platforms`（显式传 `platforms` 时）。
- 真实执行：输出服务端返回的 data 对象，成功场景通常为空对象；创建结果以 `metadata.event-get` 回读为准。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| UsageError（输入校验失败） | `--options` 非法 JSON、含未允许键、`platforms` 空数组 / 重复 / 未知枚举、名称为空 | 按错误信息修正输入后重试，此阶段不会发起请求 |
| 事件已存在 / 显示名冲突 | 目标事件或 `display_name` 已被注册 | 先用 `metadata.events` / `metadata.event-get` 读取现状，把冲突交回调用方决定 |
| 认证 / 权限 / 写开关错误 | 服务端拒绝写入 | 立即停止并返回修复提示，不重试 |

## 使用约束

- 只创建事件 schema，不会自动创建任何属性字段；属性创建用 `metadata.field-create`。
- 真实执行按 SKILL.md「写操作安全联锁」：先 `--dry-run` 预览，向调用方展示变更摘要与待执行命令，取得对本次输入与目标的精确回复 `Approved`（提示语固定为「如确认执行，请回复：Approved」）后才执行；输入或目标变化后旧确认失效。
- 执行成功后用 `metadata.event-get --name <原始名>` 回读确认；回读失败时不得宣称最终状态已验证。
- 用户只是想确认事件是否存在时不用本命令，改用 `metadata.event-get` / `metadata.events`。
