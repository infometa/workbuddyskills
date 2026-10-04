# 单条流程操作（workflow.operatePrepare / workflow.operateApply）

## 什么时候读取

用户要对**单条**流程执行同意 / 提交 / 退回 / 转办 / 委托 / 转发 / 抄送 / 加审 / 强制收回 / 强制结束 / 意见征询 / 删除 / 催办时读取本文件。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.operatePrepare` | read-before-write | 只解析定位、接收人名称转 ID、预览，不写入；产出 continuation |
| `workflow.operateApply` | high-risk-write | 必须 `confirm: true` 且携带 `operatePrepare` 的 continuation |

## 确认链

1. `operatePrepare` → 向用户摘要目标 `requestId` / `action` / 接收人 / 意见 / 删除或强制类不可逆风险。
2. 等用户**明确确认**。
3. `operateApply` 带 `confirm: true` 与 `continuation`（`action` 必须与 Prepare 一致且必填），由 CLI 真正提交。
4. 返回 `partial/write_uncertain` 时**立即停止**，先做只读回查确认流程状态，**禁止自动重放** `apply`。

## 输入

- `requestId`（`string` / `integer`，仅数字）或 `group` + `index` 定位流程；`requestId` 必须来自查询索引，模型不能自己编。
- `action`：必填，枚举见下方对照表。
- `opinion`：签字 / 操作意见（同意 / 退回 / 强制结束 / 意见征询 / 催办等使用）。
- `receiverName`：接收人类动作（transfer / turnTodo / forward / cc / addreview / consul）接收人名称，逗号分隔，支持 `"名称(ID)"`。
- `agent`：`delegate` 代理人用户 ID。
- `rejectType`：`reject` 退回类型 `0` 自由 / `1` 逐级 / `2` 指定范围 / `3` 按出口。
- `nodeid`：`reject` 退回目标节点 ID。
- `deleteType`：`deleteRequest` 删除方式 `0` 回收站（默认）/ `1` 彻底删除。
- `otherParamJson`：附加参数 JSON 字符串（`forceDrawBack` / `forceOver` / `consul` 的 otherParam / otherParams）。
- `continuation`（仅 Apply）：Prepare 返回的短句柄（形如 `wc-1a2b3c4d5e6f7a8b`），载荷由 CLI 托管在本机状态目录；Agent 只原样回传，禁止解析、手工构造、修改或复用。
- `confirm`（仅 Apply）：固定为 `true`。

## action 取值对照表（按用户原话选，不靠英文名猜）

| 用户说法 | `action` 值 | 语义 | 附加输入 |
| --- | --- | --- | --- |
| 同意 / 批准 / 通过 | `agree` | 同意审批 | `opinion` |
| 提交 | `submit` | 提交 / 同意审批 | `opinion` |
| 退回 / 驳回 / 打回 | `reject` | 退回流程 | `opinion`、`rejectType`、`nodeid` |
| 返回 / 回退 | `return` | 返回 | `opinion` |
| 转办（把流程转给某人处理） | `turnTodo` | 处理权转移给接收人 | `receiverName` |
| 转发（把流程转发给某人看 / 知会） | `forward` | 转发分享给接收人 | `receiverName` |
| 委托 / 代理人 | `delegate` | 委托代理人处理 | `agent` |
| 抄送 / 知会 | `cc` | 抄送给接收人 | `receiverName` |
| 加审 / 加签 | `addreview` | 加会审人 | `receiverName` |
| 强制收回 | `forceDrawBack` | 强制收回流程 | `opinion`（可选），监控权限 `otherParamJson` |
| 强制结束 | `forceOver` | 强制结束流程 | `opinion`，监控权限 `otherParamJson` |
| 意见征询 | `consul` | 发起意见征询给接收人 | `opinion`、`receiverName`，限时 `otherParamJson` |
| 删除流程 | `deleteRequest` | 删除流程 | `deleteType`（0 回收站默认；1 彻底删除） |
| 催办 | `supervise` | 催办流程 | `opinion`；默认提醒当前审批人，自定义提醒对象用 `otherParamJson`（`messageRemind`/`emailRemind`/`otherReminder`/`currentOperator`/`doneOperator`/`submitOperator`/`ccOperator`） |
| （schema 枚举含 `transfer`） | `transfer` | schema 枚举含此值，但 schema 描述未说明语义；按用户原话选，不臆造含义 | 视具体业务 |

说明：用户说"转发 / 转发给 X" → `forward`；说"转办 / 转给 X 处理 / 交给 X 办" → `turnTodo`。按用户原话字面选，不替换、不试错。**action 必须查表确定后再执行，禁止用试错方式探索 action 值。**

## 定位与门禁

- 单条操作按 `requestId`（或 `group` + `index`）解析目标流程，并检查流程的 `canSubmitRejectTransfer` 操作权限——**权限不足时 CLI 直接拒绝该操作，不要绕过、不要换 action 试探**（意见征询类的提交自动放行走征询回复）。
- `receiverName` 类动作（`turnTodo`/`forward`/`cc`/`addreview`/`transfer`/`consul`）的接收人必须是用户 ID；用户给姓名时交给 CLI 内部转换（多命中会报错并在 `error.message` 列出候选，见「注意」）。
- 目标来自列表序号时，**序号必须是最近一次查询的结果**（`index` 基于会话序号映射），禁止凭记忆或猜测填序号。

## 示例

### 同意审批

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"agree","opinion":"同意"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"agree","opinion":"同意"}'
```

确认后提交：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.operateApply --input-json '{"action":"agree","confirm":true,"continuation":"<operatePrepare 返回的句柄，形如 wc-1a2b3c4d5e6f7a8b>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.operateApply --input-json '{"action":"agree","confirm":true,"continuation":"<operatePrepare 返回的句柄，形如 wc-1a2b3c4d5e6f7a8b>"}'
```

### 转办给某人（姓名自动转 ID）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"turnTodo","receiverName":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"turnTodo","receiverName":"张三"}'
```

### 强制结束

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"forceOver","opinion":"业务终止","otherParamJson":"{\"ismonitor\":\"1\"}"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"forceOver","opinion":"业务终止","otherParamJson":"{\"ismonitor\":\"1\"}"}'
```

### 删除流程到回收站

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"deleteRequest","deleteType":"0"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.operatePrepare --input-json '{"requestId":"1307945196792242242","action":"deleteRequest","deleteType":"0"}'
```

## 返回

- `operatePrepare` 返回定位结果、接收人名称解析、操作预览与 `continuation`；不写入。
- `operateApply` 返回操作结果；网络中断 / 结果不确定时返回 `partial/write_uncertain`。
- **结果展示**：单条操作结果简洁说明动作、流程名称、状态和接口消息，不展示 `requestId`，除非用户明确要求技术定位信息。
- 按退出码 / `error.type` / `error.subtype` / `error.message` 判断成败，不盲目重试。

## 注意

- `deleteRequest`（删除流程）不可恢复，执行前必须明确告知用户不可逆影响并征得确认。
- 接收人名称由 CLI 调人员浏览器解析：**多命中**报 `receiver_ambiguous`（`error.message` 说明需回传 `"名称(ID)"`）、**0 命中**报 `receiver_not_found`——CLI **不会静默取第一个**。用户确认后按 `"名称(ID)"` 回传，其余已确认的接收人按同样格式一并带上（逗号分隔）。
- 失败一律看 **stderr** 的 `{ok:false, error:{type, subtype, message, retryable}}`（**没有** `success`/`stopReason`/`userMessage` 字段）；`error.message` 原样转述，不自行改写或补造结果。
- `continuation` 是 CLI 托管的短句柄（形如 `wc-1a2b3c4d5e6f7a8b`），Agent 只原样回传，禁止解析、手工构造、修改或复用；`confirm` 必须且只能为 `true`。
- Apply 被重复执行、且上一次已经成功时，返回 `ok:true` + `data.status = "ALREADY_APPLIED"`（含 `previousResult`；若上一次是"服务端已成功回执、只是没来得及写回结果"，还会给出 `requestId`）——**这不是失败**，本次没有重复写入，按上一次结果汇报即可，不要重跑 Prepare。
- Apply 报 `validation/continuation_busy` 时，说明句柄正被另一次执行占用、**上一次还没发出任何写入**：**稍后原样重试同一条命令**即可，不必重跑 Prepare、也不要换句柄。
- Apply 报 `validation/continuation_consumed` 时，说明占用该句柄的那次执行停在无法判定的旧状态：先只读核对目标流程是否已生效，确认没生效才重跑 Prepare。
- 写操作遇登录失效 / 超时 / 断连，CLI 返回 `partial/write_uncertain`（对应原 operation_unknown）；**禁止自动重放**，必须先做只读回查确认流程状态，不得重复提交。
- 同一操作连续 2 次失败必须停止，不得第 3 次重试。
- 不写任何凭据（Cookie / ETEAMSID / Token / 操作员标识由 CLI 托管）。
