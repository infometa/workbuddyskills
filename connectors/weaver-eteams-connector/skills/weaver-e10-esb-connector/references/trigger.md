# 触发动作流（esb.trigger.prepare → esb.trigger.apply）

## 何时使用

- 用户表达「执行动作流 XXX」「触发这条 ESB 动作流」「按动作流 ID 跑一下流程」「用唯一值触发动作流」。
- 需要由 Agent 主动驱动后端动作流完成后续编排（表单提交、数据变更或外部事件之后）。

本 operation 会产生业务副作用，必须走 `prepare → apply` 确认链。

## 输入要点

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `esbFlowId` | 二选一 | 普通触发：动作流 ID（数字串）。 |
| `uniqueIndent` | 二选一 | 唯一值触发：动作流的 `primary_key`。 |
| `employeeId` | 是 | 触发人员 ID，用于标识动作流执行上下文中的操作人。 |
| `customParams` | 是 | 必须含 `mainTable` 对象；字段按 `esb.input-format` 的模板组装。 |
| `moduleSource` | 否 | 触发来源标识，默认不要传，仅二开场景传 `ecode`。 |

`esbFlowId` 与 `uniqueIndent` 不能同时传、也不能都缺；两者都传会报 `trigger_target_conflict`。

## 命令

### 1. prepare（不触发动作流）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json esb run esb.trigger.prepare --input-json '{"esbFlowId":"900000000000000001","employeeId":"10001","customParams":{"mainTable":{"dataId":"D1001"}}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json esb run esb.trigger.prepare --input-json '{"esbFlowId":"900000000000000001","employeeId":"10001","customParams":{"mainTable":{"dataId":"D1001"}}}'
```

带明细表的复杂 `customParams` 建议先写入 UTF-8 JSON 文件，再传 `--input <file>`。

Windows PowerShell：

```powershell
Set-Content -Path .\esb-params.json -Encoding utf8 -Value '{"esbFlowId":"900000000000000001","employeeId":"10001","customParams":{"mainTable":{"dataId":"D1001"}}}'
weaver-work-cli --profile eteams --json esb run esb.trigger.prepare --input .\esb-params.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./esb-params.json <<'JSON'
{"esbFlowId":"900000000000000001","employeeId":"10001","customParams":{"mainTable":{"dataId":"D1001"}}}
JSON
weaver-work-cli --profile eteams --json esb run esb.trigger.prepare --input ./esb-params.json
```

`data` 返回 `target`（触发方式与标识）、`requestPreview`（即将发出的请求体）、`templateFields` 与 `continuation`（有效期 600 秒）。

### 2. apply（真实触发）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json esb run esb.trigger.apply --input-json '{"continuation":"REPLACE_WITH_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json esb run esb.trigger.apply --input-json '{"continuation":"REPLACE_WITH_CONTINUATION","confirm":true}'
```

`confirm` 必须显式为 `true`；缺失或为 `false` 时报 `confirm_required`，不会发出任何请求。

## 输出处理

`data` 字段：

- `resultCode`：固定为 `200`（非 200 会在 CLI 层转为结构化错误，不会出现在成功输出里）。
- `resultMsg`：服务端返回的执行结果信息。
- `nextAction`：`0` 表示后续操作正常执行，`1` 表示后续操作不执行。
- `actionData`：动作流输出集合，含 `pageAction`（0 无 / 1 刷新 / 2 关闭 / 3 跳转）、`reminder`（0 无 / 1 提醒 / 2 确认 / 3 警告 / 4 错误）、`reminderMsg`、`hasData`（1 时数据在 `responseData`）、`responseData`、`customData`。
- `followUp`：对 `actionData` 的中文摘要，直接用于向用户汇报后续动作。

## 注意

- **副作用**：触发动作流会真实执行业务逻辑，可能修改业务数据、发送通知或触发下游流程。执行前必须把目标动作流、触发人员、`requestPreview` 和风险摘要展示给用户，并取得明确确认。
- **continuation 绑定**：continuation 与签发时的登录身份绑定，有效期 10 分钟；过期或身份变化需重新 prepare。
- **唯一值触发**：同一租户下多条动作流可能有相同唯一值，系统只执行 `create_time` 最新的一条；需要精确控制时改用 `esbFlowId`。
- **限流**：短时间重复触发可能被幂等限流（`throttled`）拒绝，禁止高频重试。

## 失败处理

- `confirm_required`：未显式确认，先向用户确认后重试。
- `continuation_*`：continuation 无效、过期、不属于当前操作或身份变化，重新执行 `esb.trigger.prepare`。
- `parameter_invalid`：按 `customParams` 模板核对必填字段与类型。
- `flow_not_bound` / `flow_not_found` / `flow_disabled` / `flow_in_recycle_bin`：核对触发标识或在 ESB 中心处理，不要重试。
- `permission_denied` / `tenant_permission_denied` / `tenant_missing` / `license_required`：权限、租户或 license 问题，交由用户或管理员处理。
- `throttled` / `flow_running` / `execute_timeout`：稍后重试或查看动作流运行日志。
- `write_uncertain`：**立即停止**。请求已发出但结果未知，不能判定动作流未执行，禁止自动重试；先在 ESB 中心查看动作流运行日志，确认后再决定是否重新触发。
