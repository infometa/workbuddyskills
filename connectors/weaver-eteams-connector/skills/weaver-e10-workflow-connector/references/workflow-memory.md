# 记忆读取与保存

## 什么时候读取

新一轮对话或距上次成功读取记忆超过 6 小时、需要工作流消歧/摘要字段优先级/展示偏好，或判 OA 版本与用户身份时读取本文件；每轮完整实质任务结束判断是否有新语义记忆时也读取。

覆盖 `workflow.memoryPrompt` / `workflow.memoryExtract`。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.memoryPrompt` | read | 可选 `workflowId`；顺带返回 `oaContext`（OA 版本 + 当前用户身份），无需再单独查组织信息 |
| `workflow.memoryExtract` | write | 高层抽取保存接口；`msgList` 或 `userMessage`+`assistantMessage` 二选一；返回真实 `saved` 结果，禁止 fire-and-forget |

## 输入

### workflow.memoryPrompt

- `workflowId`（string，可选）：工作流维度记忆的 workflowId；不传读全局记忆。

### workflow.memoryExtract

- `msgList`（array，可选）：记忆消息数组，每项 `{"msgRole":"user"|"assistant","msgValue":"..."}`。
- `userMessage`（array of string，可选）：用户消息列表，与 `msgList` 二选一。
- `assistantMessage`（array of string，可选）：模型消息列表，与 `msgList` 二选一。
- `dynamicContext`（object，可选）：动态上下文参数（合并进 dynamicContextParams）。
- `workflowId`（string，可选）：关联工作流 ID；已确定具体 workflowId 时放入，抽取会落到该工作流维度。**保存「业务别名 → 工作流」映射时，ID 还必须同时写进 `msgValue` 的事实句，不要只依赖这个入参**——实测：别名条目的 `workflowId` 仍是「（待确认）」时，带 `workflowId` 的调用并没有把它补上。
- `memoryAppId`（string，可选）：记忆应用 ID。
- `async`（boolean，可选）：语义为同步发送并返回真实结果（禁止 fire-and-forget）。

## 示例

### 读取用户记忆（全局）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.memoryPrompt --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.memoryPrompt --input-json '{}'
```

### 读取某工作流维度记忆

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.memoryPrompt --input-json '{"workflowId":"100003460000000060"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.memoryPrompt --input-json '{"workflowId":"100003460000000060"}'
```

### 保存工作流澄清映射（同步返回真实结果）

Windows PowerShell（用 UTF-8 文件传入消息列表）：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\mem-extract.json -Value @'
{
  "msgList": [
    {"msgRole":"user","msgValue":"我本月发起的报销流程怎么样了"},
    {"msgRole":"assistant","msgValue":"匹配到多个报销相关工作流，请确认要查看哪一个。"},
    {"msgRole":"user","msgValue":"5"}
  ],
  "workflowId": "100003460000000060",
  "async": true
}
'@
weaver-work-cli --profile eteams --json workflow run workflow.memoryExtract --input .\mem-extract.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./mem-extract.json <<'JSON'
{
  "msgList": [
    {"msgRole":"user","msgValue":"我本月发起的报销流程怎么样了"},
    {"msgRole":"assistant","msgValue":"匹配到多个报销相关工作流，请确认要查看哪一个。"},
    {"msgRole":"user","msgValue":"5"}
  ],
  "workflowId": "100003460000000060",
  "async": true
}
JSON
weaver-work-cli --profile eteams --json workflow run workflow.memoryExtract --input ./mem-extract.json
```

## 返回

- memoryPrompt：`available`、记忆提示词、`oaContext`（可能缺失）。
- `oaContext.version`：OA 版本（如 `10.0.9909.01`），判版本场景直接用；缺失时按低版本处理。
- `oaContext.user.position`：岗位；`oaContext.user.department`：部门；`oaContext.user.subcompany`：分部（可能为空，为空忽略）；`oaContext.user.employeeId`：用户标识。
- `oaContext` 取不到时为 `null` 并带 `oaContextMissing: true`，不影响记忆主体。
- memoryExtract：`saved`（true/false 真实结果）。

## 记忆规则（保存时机与处理）

每轮完整实质任务结束后（输出最终回复前），模型自行判断本轮是否出现**新的、有价值的语义记忆**（用户新澄清/确认了具体工作流、本次新表达字段偏好，或对某字段值有新约定；与已有记忆重复的不算）：

- **有** → 组装本轮"用户原始意图 + 澄清过程 + 确认结果"的消息列表并调用 `workflow.memoryExtract`（同步，`async` 语义为返回真实结果）：
  - `saved:true` → 用自然语言告知用户会记住什么（如"后续发起请假流程会默认按本次偏好填写"），不展示接口原文；
  - `saved:false` → 按静默失败处理，不告知用户、不重试，直接继续回答。
- **没有** → 不调用，直接输出最终回复。

**硬禁令（必须遵守）**：

- **不允许只在思考中写"保存记忆"**：判断"有"后必须**实际调用** `workflow.memoryExtract` 命令，命令完成（拿到真实 `saved`）后再输出最终回复。只在思考/内心说"应该保存"而不执行命令 = 没保存，属于违规。
- **`workflow.createApply` 成功后命令不会自动保存记忆**：发起流程的语义记忆（本次发起的工作流与关键字段偏好）**由模型在任务结束后主动调用 `workflow.memoryExtract` 保存**，不要假设命令已自动保存。
- **别名条目的 `workflowId` 是「（待确认）」时，它是一张待办不是终态**：本轮只要把该别名唯一解析出了 `workflowId`（**`cards[].workflowId`** 或 `countDetails[].workflowId` 里就有），任务结束时**必须再保存一次把 ID 补上**，不要放着不管——否则下一轮读到的还是「（待确认）」，只能拿纯名称去试探，多命中还要再澄清一次。

消息列表由模型在本地组装并作为入参传入（`msgList` 或 `userMessage`+`assistantMessage`）；可含多轮原始消息（尤其澄清链路），可精简无用消息（命令执行日志、大段接口原始返回、调试输出），不需要模型提前总结。

记不清字段结构时回读本文档，只用 schema 真实存在的字段名。已确定 workflowId 时放入 `workflowId`（一次调用即可，不要 global/workflow 两次请求）；**保存别名映射时把 ID 同时写进 `msgValue` 事实句**——写漏了就会留下「（待确认）」，而「（待确认）」是**待办不是终态**：后续任一轮只要把该别名唯一解析出 ID，就要再保存一次把它补掉。

**别名映射的保存口径（不要写漏 ID）**：`msgList` 每项的字段名固定为 `msgRole` / `msgValue`（不要写成 `role` / `content`）；保存「业务别名 → 工作流」时，`msgValue` 里要写成可抽取的事实句，例如 `业务别名"问题流程"= 工作流"E10客户问题支持解决流程"，workflowId=1003655203465764898`，并把同一个 ID 放进入参 `workflowId`。

**ID 从哪来（写记忆前必须回看本轮返回）**：别名条目的 `workflowId` 只能来自本轮命令返回，**不要凭名称推断、也不要因为"没看到 ID"就留空**：

| 场景 | 取 ID 的位置 |
| --- | --- |
| `workflow.search` / plan 查到流程（**含用户只澄清了工作流名称、CLI 内部唯一匹配成功那一轮**） | `cards[].workflowId` / `cards[].workflowName`（V12.1.37 起是**唯一**的结构化取 ID 通道） |
| `workflow.createList` 选定/候选过工作流 | 候选对象的 `id` / `workflowname` |
| `workflow.todoStat` 统计过 | `countDetails[].workflowId` |

> `finalMarkdown` 按契约**不渲染工作流名、更不含 ID**，所以上面三个结构化字段是 ID 的**唯一出处**；"最终以 `finalMarkdown` 为准"指的是**渲染呈现**，不是让你只读 `finalMarkdown`。

## 三类记忆职责（保存时按维度选 `workflowId`）

- **user.md**（用户画像）：稳定身份信息、展示偏好、协作方式、沟通风格、通用风险确认偏好。**适合**：不展示 requestId、不输出统计区块、中文简洁回复、异常直接停止。**不适合**：workflowId、fieldId、工作流审批规则、业务别名到工作流映射。
- **memory.md**（长期记忆）：跨项目稳定事实、经验教训、通用工作流、工具配置、反复出现的规律。**适合**：业务别名与工作流消歧、跨流程优先级规律、通用查询经验、接口使用教训。**不适合**：单个工作流关注字段、单个工作流审批规则、用户沟通风格。
- **workflow:{workflowId}**（工作流维度）：单工作流专项记忆。**适合**：该工作流常用别名、关注字段、摘要偏好、优先级与处理节奏、审批规则、风险提醒。**不适合**：其他工作流规则、全局用户画像、临时 requestId。

## 记忆消费方式（影响哪些行为）

记忆可用于：

- **业务别名与工作流消歧**：把用户的口语简称落到具体工作流（落到 `workflowId` 后，查询时直接用 `名称(ID)` 传 `workflow`，不要再用纯名称试探）。
- **每页条数偏好**：用于列表查询的 `pageSize`；**本次用户明确指定的条数优先于记忆偏好**。
- **紧急/超时流程优先展示**、详情摘要关注字段、已确认的审批建议规则、展示/确认/异常处理偏好。

记忆影响了本轮决策时（工作流消歧、摘要字段优先级、审批建议、每页条数、紧急超时优先展示），最终回复**不要展示记忆原文**，但必须保留自然语言说明依据了哪类历史偏好（如"我按你之前确认的偏好，把报销优先理解为总部费用报销。"）。

记忆**不能**用于：猜测当前系统元数据（工作流 ID/字段/节点元数据必须来自当前链路解析）、替代 `index` 序号映射定位、绕过操作门禁（`canSubmitRejectTransfer` 等）、仅凭记忆自动执行审批（记忆只能生成建议，执行以用户本轮明确指示为准）。

## 注意

- 不传凭据：业务输入禁止出现 Cookie/ETEAMSID/Token/`header.operator`（CLI 托管）。
- 读取时机：本轮已成功读取（`available=true`）直接复用，不重复调用；距上次成功读取超过 6 小时才重读。
- 记忆读取失败（`available=false`、CLI 失败信封、无可用提示词）→ 静默忽略，不告诉用户、不重试、不中断主任务。
- `memoryNotSupported=true` → 当前环境不支持记忆，本会话跳过记忆读取/保存，不追问。
- `available=false` 时可看 `diagnosis`（`code`/`status`/`fail`/`dataEmpty`）了解失败环节，但**不要向用户展示、不要重试**。
- 记忆与当前系统解析结果冲突时以当前系统为准（流程改名/ID 变更/环境切换不套用过期记忆标签）。
- 记忆不能用于猜测当前系统元数据、替代定位索引、绕过操作门禁或仅凭记忆自动执行审批（记忆只生成建议，执行以用户本轮明确指示为准）。
- `async` 为同步发送并返回真实 `saved` 结果，禁止 fire-and-forget（不得调用后不等结果）。
- 记忆可用于：业务别名与工作流消歧、每页条数/紧急超时优先展示、详情摘要关注字段、已确认审批建议、展示/确认/异常处理偏好。
