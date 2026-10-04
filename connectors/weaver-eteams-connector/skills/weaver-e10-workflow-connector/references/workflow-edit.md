# 修改已存在流程表单

## 什么时候读取

用户要"修改/更正某条已存在流程的表单内容"（改已发起流程的字段值）时读取本文件。覆盖 `workflow.editLoad` / `workflow.editPrepare` / `workflow.editApply`。只保存表单字段，不调 flow/save、不提交、不校验必填。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.editLoad` | read | 必传 `requestId`；返回 `context`/editableFields/currentValues/fields/requestInfo |
| `workflow.editPrepare` | read-before-write | requiresConfirmation；必传 `context`/`data`；不校验必填；触发字段联动 |
| `workflow.editApply` | high-risk-write | requiresConfirmation；必传 `confirm:true`/`context`；仅 saveFormData，不调 flow/save、不提交；遇 `partial`/`write_uncertain` 禁止重试 |

## 确认链（写操作）

1. `workflow.editLoad` 加载当前表单值与可编辑字段，拿到 `context`。
2. `workflow.editPrepare` 修改字段，向用户摘要变更字段与联动结果。
3. 等用户明确确认。
4. `workflow.editApply` 带 `confirm:true` 与同一 `context` 保存。
5. 成功时返回 `status = EDIT_SAVED` 与 `saved.data_id` / `saved.updateTimeStamp`——**按返回值汇报即可，不需要再去反查**。
6. 遇 `partial`/`write_uncertain` 停止，先只读回查（detail/summary），不自动重放。
7. Apply 被重复执行时按句柄状态分流（**不要一看到"用过"就重跑 Prepare**）：
   - `ok:true` + `data.status = "ALREADY_APPLIED"`：该 `context` 上一次**已经保存成功**，本次没有重复写入——按返回值里的 `requestId` / `previousResult` 汇报即可；
   - `partial`/`write_uncertain`：上一次已经发出保存请求、结果未确认——先只读回查流程表单确认是否已生效，确认没生效才重跑 Prepare；
   - `validation/continuation_busy`：句柄正被另一次执行占用、上一次还没发出写入——**稍后原样重试同一条命令**即可；
   - `validation/continuation_consumed`：占用该句柄的执行停在无法判定的旧状态——先只读回查确认，再决定是否重跑 Prepare。

## 输入

### workflow.editLoad

- `requestId`（string|integer，必填）：流程请求 ID，来自 workflow-search/detail 的 `requestId`。

### workflow.editPrepare

- `context`（string，必填，minLength 1）：复用 editLoad 返回的 `context`；prepare/apply 同一值，原样回传，禁止手工构造/修改/复用他处。
- `data`（object，必填）：要修改的字段值，结构 `{"main":{...},"details":{"<subFormId>":[{...}]}}`。

### workflow.editApply

- `context`（string，必填）：复用 editPrepare 的 `context` 原样回传。
- `confirm`（const true，必填）：声明用户已明确确认保存。

## 示例

### ① 加载流程表单当前值

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.editLoad --input-json '{"requestId":"1307945196792242242"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.editLoad --input-json '{"requestId":"1307945196792242242"}'
```

### ② 修改字段（触发字段联动）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.editPrepare --input-json '{"context":"<editLoad返回的context>","data":{"main":{"报销事由":"客户约谈"}}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.editPrepare --input-json '{"context":"<editLoad返回的context>","data":{"main":{"报销事由":"客户约谈"}}}'
```

### ③ 保存（仅保存表单，不提交）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.editApply --input-json '{"context":"<同一context>","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.editApply --input-json '{"context":"<同一context>","confirm":true}'
```

## 返回

- editLoad：`context`、`EDIT_READY`、`editableFields`（可编辑且可见字段 id）、`currentValues`（当前字段值）、`fields`（id→name/subFormId/componentKey/options）、`requestInfo`（标题/紧急程度/密级当前值，本次不改）。
- editLoad 的**大表单形态**（字段多时才有，与 `createForm` 同一套）：结果最前面多出 `resultFile` / `persistedResult` / `outputBytes` / `largeOutputNotice`，`fields` 要么换成紧凑编码（`columns` + `rows` 每行一字段、`|` 分隔；非列信息按字段 id 放 `extra`），要么带 `fieldsOmitted: true` + `fieldCount` 整体移出 stdout。两种形态都照常 `editPrepare`；要字段全文时从 `resultFile` **按需**提取，**不要重跑 `editLoad`**。
- editPrepare：`READY`（changedFields + linkageResult）/ `NEEDS_CONFIRMATION`（重名用字段 id、明细表用 details 结构、不可编辑字段报 notEditable）。
- editApply：`EDIT_SAVED`（仅 saveFormData，保存前自动触发 EVENT_SAVE_DATA 联动）。

## 注意

- 不传凭据：业务输入禁止出现 Cookie/ETEAMSID/Token/`header.operator`（CLI 托管）。
- 只读字段硬拒绝：只允许修改 `editableFields` 里的字段；用户给只读/禁用/不可见字段赋值时 CLI 报 `notEditable`，如实转述、不要绕过（不要换字段 id 再试）。
- 明细表字段：`data` 用 `{"details":{"<subFormId>":[{"<字段id>":值}]}}`，保存时回传 rowId/dataIndex/subForm。
- 不校验必填（修改态保存语义）；系统字段（流程标题/紧急程度/密级）本次不支持修改，只展示当前值。
- 附件/文件：需上传本地文件时先提醒用户"附件会先经过公网大模型，请谨慎操作"，再调 `weaver-file-upload` skill；上传前核对 `fileUploadParams` 的 `sizeLimit`/`formatLimit`/`maxNum`，不满足先告知、不执行上传。
- `linkageResult`（联动带出）原样转述给用户查看。
- 流程已流转到非编辑节点时 editApply 返回"失去操作权限"，如实转述。
- 不重试：写操作失败、超时或结果不确定（`WRITE_UNCERTAIN`/`partial`）禁止重试，返回恢复信息并让用户人工检查。
- 写操作遇登录失效：禁止自动重登重放，结果未知时不得自动重放。
