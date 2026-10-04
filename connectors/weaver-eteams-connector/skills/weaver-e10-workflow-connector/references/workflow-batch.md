# 批量流程处理（6 个单命令）

## 什么时候读取

用户要一次性处理多条流程：批量提交、批量置已读 / 已办、批量催办、批量共享、批量转发、批量退回时读取本文件。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.batchSubmit` | high-risk-write | **单命令**：一次调用完成门禁校验 + 置已办 + 提交；必须 `confirm: true` |
| `workflow.batchRead` | high-risk-write | **单命令**：一次调用完成门禁校验 + 置已读 / 已办（doBatchRead）；必须 `confirm: true` |
| `workflow.batchSupervise` | high-risk-write | **单命令**：一次调用完成提醒人解析 + 催办；必须 `confirm: true` |
| `workflow.batchShare` | high-risk-write | **单命令**：一次调用完成门禁校验 + 共享对象解析 + 共享（分批）；必须 `confirm: true` |
| `workflow.batchForward` | high-risk-write | **单命令**：一次调用完成门禁校验 + 接收人解析 + 「转发所有人」配置检查 + 转发（分批）；必须 `confirm: true` |
| `workflow.batchReject` | high-risk-write | **单命令**：一次调用完成门禁校验 + 退回（分批，不传提交参数）；必须 `confirm: true` |

**6 个批量操作全部是单命令**：没有 `Prepare` / `Apply` 两阶段，也没有 `continuation` 句柄；`confirm: true` 与 `requestIds`（及其余参数）都在**同一次调用**里传。

## 确认链（6 个批量操作完全一致）

1. **向用户确认**：**一句话**说明将执行什么（动作 + 条数 + 目标来源，如"把上一轮列表的前 2 条批量提交掉"），然后**等用户明确确认**。**这一步就是确认本身**——不要为它再另发一段"摘要 / 计划"；目标条数、requestId 来源、操作差异、风险只在用户主动问起、或目标确实不明确时才展开。
2. 用户明确确认后**一次调用**对应命令，同一份入参里带 `confirm: true` 与 `requestIds`（及该操作自身参数）。
   **不需要先跑一次 Prepare，也不需要把 requestIds 先"准备"到某个句柄里**——门禁校验、名称解析与写入都在这一次调用内完成。
3. 返回 `partial/write_uncertain` 时**立即停止**，先只读回查（`workflow.search --category done --requestId <目标ID>`，或看 `--category mine` 是否已出现目标流程），**不自动重放**。核对确认**没生效**后，等约 1 分钟再原样重跑同一条命令——同一批在保护窗口内还会被拦一次（防止机械式重复执行），窗口过去即可正常执行。
4. 返回 `ok:true` + `data.status = "ALREADY_APPLIED"` 时，说明**同一批流程、同一批写向对象刚刚已经执行成功**（例如宿主把同一条命令重跑了一次）——本次没有重复写入。直接按返回值里的 `previousResult` 汇报即可，**不要重复执行同一条命令**。
5. 报 `validation/batch_gate_required` 时，说明 `details.missingRequestIds` 里的流程**不在最近一次查询结果里**（门禁只认查询落下的那份结果，不认别的口径）。正确做法：先做 `workflow.search --batchType <类型> --pageSize 100` 查询一页，再立即用该页返回的 ID 调用批量命令。若这些流程其实已被处理过，先只读核对 `workflow.search --category done --requestId <目标ID>`，已处理就按成功汇报，**不要重复执行同一条命令**。
6. 同一操作连续 2 次失败必须停止。

## 输入

- `requestIds`：待操作流程 ID，类型可为数组（元素为数字或仅数字字符串）或逗号分隔串；**必须来自查询索引结果，模型不能自己编**；拿到后直接用——CLI 按本机索引核对，**不需要为了"校验"再查一次服务端**。
- `remark`：批量统一意见（submit / supervise / forward / reject 适用；**置已读没有意见参数**）。
- `batchSize`：单批最大条数，`integer` 1–100，默认 100；CLI 自动分批循环。
- `confirm`：固定为 `true`，与 `requestIds` 在**同一次调用**里带上。
- `category` / `async`：仅 `workflow.batchSubmit` 使用（分类判断、异步提交开关）。
- 各操作专属字段见下方分节。
- **6 个批量操作都没有 `continuation` 字段**：它们是单命令，不存在需要模型搬运的句柄。

## 请求来源与分批循环

**先判断操作目标的来源：**

**① 目标就是「上一轮查询结果」**（用户直接用指代——"前两条 / 刚才那些 / 上一次列表里的流程 / 都处理掉"，或点名该轮里的条目）→ **直接从最近一次查询结果中取对应流程作为操作目标并执行批量命令**。
**指代基准只有一份：最近一次查询结果**（与批量门禁的放行快照同源）；"前两条"＝该列表第 1、2 条（按列表顺序数）。**不要跨轮回溯更早的列表，也不要反问"是哪一份列表"**。**不需要先检查是否可批量操作**（CLI 内部按各流程状态分流：可提交的提交、抄送不需提交／转发不需批注／传阅不需批示类置已办），**也不需要先做一次 `workflow.search --batchType` 来"校验"这些 ID**（门禁按本机索引放行，这一次查询对放行没有帮助）。

**② 目标是一个范围**（"把这些待办都处理了"且未限定上一轮结果，因此没有准确的 requestId）→ 必须**先查询、再循环**（**无需先查数量生成计划再等确认**），条件与顺序如下：

1. 用 `workflow.search` 取数，且**必须带 `batchType`**（提交用 `submit`，其余按操作取对应值）与 `pageSize: 100`——不带 `batchType` 查出来的数据不是可批量操作的那一批，门禁会判成不在查询结果里。
2. 拿到这一页的 requestId 后**立即**用它们调用批量命令，**不要**先翻完所有页、也**不要**先把全部 requestId 收集起来一次提交。
3. 执行完再查一次（批量提交 / 置已读会清掉已处理的流程，通常仍从第 1 页开始；催办 / 共享 / 转发 / 退回后流程不消失，多页时用 `current: 2/3/...` 逐页推进）。
4. 重复 2–3，直到 `total` 归零或没有可操作数据为止。

**为什么要循环、且不许先收集全部**：批量门禁的放行依据是**最近一次查询结果**——每次查询都会覆盖上一份结果；若先把所有页的 ID 收集起来再一次性提交，前面几页的 ID 已经被后来的查询挤掉，门禁会判成"不在最近一次查询结果里"。且流程一旦被处理就从查询结果里消失。**只有来源 ② 以及命令报 `batch_gate_required` 时，才需要 `--batchType` 查询。**

**requestId 提取**：优先用查询返回的**结构化字段** `cards[].requestId` 取本页全部 requestId；只有在需要从 `finalMarkdown` 文本里提取时才用正则 `` \]\(https?://[^\)]*requestId=(\d+)\) ``（**只匹配卡片链接**，避开描述文字里嵌套的 requestId）。批量查询默认跳过卡片业务摘要（只返回系统字段卡片，提速显著）。

- `requestIds` 必须取自上一轮查询结果，或跟随查询分页逐页取本页 ID；**禁止模型臆造 ID**。
- `batchSize`（默认 100）由 CLI 自动分批；任一批失败立即停止，如实转述该批结果（含已成功条数），不自行补造。

## 置已读与提交的区别

- `batchRead`：仅把待办置为已读 / 已办（抄送不需提交、转发不需批注、传阅不需批示类，置已读同时置为已办，即"已阅"）。
- `batchSubmit`：先置已办（BATCH_READ）再提交（BATCH_SUBMIT），同样会处理上述"不需提交"类为已办。
- `batchReject`：**只退回，不传任何提交参数**，退回意见作为签字意见放入请求。

## 各批量操作

### 批量提交 batchSubmit

适用："批量提交 / 全部提交 / 一起提交"多条待办。入参 = `confirm: true` + `requestIds`（+ `remark` / `batchSize` / `async`）。

返回 `readCount`、`submittedCount`、`skippedRequestIds`（`isRemark=100` 不可批量提交被跳过时出现）、`batchRead`、`submitResponse`；原样转述返回的结果与提示文案。

### 批量置已读 batchRead

适用："把流程置为已读 / 已阅"。入参 = `confirm: true` + `requestIds`（+ `batchSize`）。

返回 `readCount`、`response`；原样转述返回的结果与提示文案。

### 批量催办 batchSupervise

适用："批量催办 / 全部催办 / 催一催多条流程"。提醒对象按用户说法设置，未指定时默认催当前节点未操作者。

| 字段 | 取值 | 默认 | 含义 |
| --- | --- | --- | --- |
| `currentOperator` | `0`/`1` | `1` | 催办当前节点未操作者 |
| `messageRemind` | `0`/`1` | `0` | 短信提醒 |
| `emailRemind` | `0`/`1` | `0` | 邮件提醒 |
| `doneOperator` | `0`/`1` | `0` | 已审批人 |
| `ccOperator` | `0`/`1` | `0` | 抄送人 |
| `submitOperator` | `0`/`1` | `0` | 发起人 |
| `otherReminder` | 姓名 / `"姓名(ID)"` 逗号分隔 | 空 | 其他提醒人 |

返回 `successNum`、`failNum`、`batches`。

### 批量共享 batchShare

适用："把多条流程共享给 X / 共享给部门 / 共享给所有人"。共享对象 `shareObjects` 每项 `{"type": <类型>, "name": <名称>}`（`all` 不需要 name）：

| type | 共享对象 |
| --- | --- |
| `user` | 人员 |
| `dept` | 部门 |
| `subcompany` | 分部 |
| `group` | 群组 |
| `role` | 角色 |
| `position` | 岗位 |
| `all` | 所有人（无 name） |

名称自动转 ID；`name` 支持 `"名称(ID)"`（此时直接采用括号里的 ID、不再搜名称）。多命中返回候选列表让用户确认，禁止静默全选；0 命中报错提示核对。可选 `minSeclevel` / `maxSeclevel`（用户明确要求限制时传）。返回透传每批 addRequestShare2 响应（含每流程 `sourceId` / `result` / `msg`），任一批失败立即停止。

### 批量转发 batchForward

适用："批量转发 / 把多条流程转给 X 看 / 发给 X"。接收人 `receiveTargets` 每项 `{"type": <类型>, "name": <名称>}`（`all` 不需要 name）：

| type | 接收人 |
| --- | --- |
| `user` | 人员 |
| `dept` | 部门 |
| `group` | 群组 |
| `all` | 所有人（无 name） |

`name` 支持 `"名称(ID)"`（此时直接采用括号里的 ID、不再搜名称）。接收人含 `all` 时会检查系统是否允许转发给所有人；不允许则停止并提示联系系统管理员，不得去掉 all 后静默继续。返回逐条 `status` / `requestId` / `requestName` / `resultType` / `resultMessage`，批内失败立即停止。

### 批量退回 batchReject

适用："批量退回 / 把多条流程退回去"。退回意见同时作为签字意见放入请求。返回逐条 `status` / `requestId` / `requestName` / `resultMessage`，批内失败立即停止。

## 示例

### 批量提交

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.batchSubmit --input-json '{"confirm":true,"requestIds":["id1","id2","id3"],"remark":"批量同意","batchSize":100}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.batchSubmit --input-json '{"confirm":true,"requestIds":["id1","id2","id3"],"remark":"批量同意","batchSize":100}'
```

目标是一个范围时，先查一页、再立即提交该页：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.search --input-json '{"category":"todo","batchType":"submit","pageSize":100}'
# 用返回的 cards[].requestId 组成 requestIds，立即提交这一页
weaver-work-cli --profile eteams --json workflow run workflow.batchSubmit --input-json '{"confirm":true,"requestIds":["<本页 id1>","<本页 id2>"]}'
# 再查一次、再提交这一页，循环到 total 归零为止
```

### 批量置已读

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.batchRead --input-json '{"confirm":true,"requestIds":["id1","id2"],"batchSize":100}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.batchRead --input-json '{"confirm":true,"requestIds":["id1","id2"],"batchSize":100}'
```

### 批量催办（未指定提醒对象 → 默认当前节点未操作者）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.batchSupervise --input-json '{"confirm":true,"requestIds":["id1","id2"],"remark":"请尽快处理","currentOperator":1}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.batchSupervise --input-json '{"confirm":true,"requestIds":["id1","id2"],"remark":"请尽快处理","currentOperator":1}'
```

### 批量共享

Windows PowerShell：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\batch-share.json -Value @'
{
  "confirm": true,
  "requestIds": ["id1","id2"],
  "shareObjects": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"dept\",\"name\":\"产品研发中心\"}","{\"type\":\"all\"}"],
  "batchSize": 100
}
'@
weaver-work-cli --profile eteams --json workflow run workflow.batchShare --input .\batch-share.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./batch-share.json <<'JSON'
{
  "confirm": true,
  "requestIds": ["id1","id2"],
  "shareObjects": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"dept\",\"name\":\"产品研发中心\"}","{\"type\":\"all\"}"],
  "batchSize": 100
}
JSON
weaver-work-cli --profile eteams --json workflow run workflow.batchShare --input ./batch-share.json
```

### 批量转发

Windows PowerShell：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\batch-forward.json -Value @'
{
  "confirm": true,
  "requestIds": ["id1","id2"],
  "receiveTargets": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"all\"}"],
  "remark": "请知悉",
  "batchSize": 100
}
'@
weaver-work-cli --profile eteams --json workflow run workflow.batchForward --input .\batch-forward.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./batch-forward.json <<'JSON'
{
  "confirm": true,
  "requestIds": ["id1","id2"],
  "receiveTargets": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"all\"}"],
  "remark": "请知悉",
  "batchSize": 100
}
JSON
weaver-work-cli --profile eteams --json workflow run workflow.batchForward --input ./batch-forward.json
```

### 批量退回

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.batchReject --input-json '{"confirm":true,"requestIds":["id1","id2"],"remark":"材料不齐全，请补充后重新提交"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.batchReject --input-json '{"confirm":true,"requestIds":["id1","id2"],"remark":"材料不齐全，请补充后重新提交"}'
```

## 返回

- 6 个命令都**直接返回批量结果**：提交（`readCount` / `submittedCount` / `batchRead` / `submitResponse` / 可选 `skippedRequestIds`）、置已读（`readCount`）、催办（`successNum` / `failNum` / `batches`）、共享（`sharedCount`）、转发（`forwardedCount`）、退回（`rejectedCount`）；分批失败时返回 `status: "PARTIAL"` 与逐条失败明细。**没有任何命令返回 `continuation`。**
- 被重复执行、且上一次已经成功时，返回 `ok:true` + `data.status = "ALREADY_APPLIED"`（幂等回报，含 `previousResult`）——**这不是错误**，本次没有重复写入，按上一次结果汇报即可。
- 任一批失败：CLI 立即停止并在 **stderr** 返回 `ok:false` + `error.message`（含已成功条数），Agent 如实转述，不自行补造；**没有** `success`/`userMessage` 字段。
- **结果展示**：动作与条数用一句话说明；**逐条结果可用 Markdown 表格展示**（序号 / 流程名称 / 动作 / 接收人 / 状态 / 说明）；不展示 `requestId`，除非用户明确要技术定位信息。幂等回报（`ALREADY_APPLIED`）同样**只报业务结果**，不要向用户提及"此前已执行过/没有重复写入"。

## 注意

- `requestIds` 必须来自查询索引，模型不得编造；批量门禁的放行依据是**最近一次查询结果**（与单条操作同一套本地索引口径），不是另做一次实时列表查询；**6 个批量命令都走这道门禁**（催办按 `urge` 口径核对，与 `workflow.search --batchType urge` 共用同一套批量端点）。
- 6 个命令都**没有 Prepare 环节，也没有 continuation**。CLI 用「这次要写什么」作为一次性写入闸门：**同一个操作 + 同一批 requestId + 同一组写向对象**（收件人 / 共享对象 / 提醒人）在约 1 分钟的保护窗口内只写一次。因此宿主重跑同一批只会拿到 `ALREADY_APPLIED`，不会真的写两次；窗口过去后同一批流程可以再次处理（流程被退回后再处理是合法操作）。`remark` / `batchSize` 不参与这个判据：同一批同一对象换个意见再执行一次，仍然算重复执行。
- **换写向对象是另一次操作**：把同一批流程先转给张三、再转给李四，或先共享给甲部门、再共享给乙部门，都必须分别执行（不会被当成重复执行拦下）。
- 写操作报 `batch_gate_required` 时，看 `details.missingRequestIds`：这些 ID 不在最近一次查询结果里。先只读核对 `workflow.search --category done --requestId <目标ID>` 判断是否已被处理；确认没处理就按 `--batchType` 重新查询一页再取该页 ID 执行。**不要**为了"凑上"换 `--tabid`／子分类反复重查，也不要反复重跑同一个命令。
- 分批任一批失败立即停止，如实报告已成功条数与失败原因，不自动重试、不连环重放。
- 写操作遇登录失效 / 超时 / 断连返回 `partial/write_uncertain`，**禁止自动重放**，先只读回查确认状态。
- 同一操作连续 2 次失败必须停止。
- 不写任何凭据（Cookie / ETEAMSID / Token / 操作员标识由 CLI 托管）。
