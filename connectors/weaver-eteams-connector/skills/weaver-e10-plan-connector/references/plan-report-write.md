# 新建 / 修改 / 发布 / 撤回报告

## 何时使用

- 用户明确要求新建、修改、发布、撤回某个周期的报告；
- A 链路汇总完成、用户确认「生成对应周期的报告」后，创建报告；
- 用户已确认要报告但还没创建草稿，又要直接发布（先创建，再发布）。

这些 operation 全部是 `prepare → apply` 写入链，必须先取得用户明确确认。

## 输入要点

### 新建 `plan.report.create.prepare` / `.apply`

| 字段 | 说明 |
| --- | --- |
| `content` | 工作成效（支持 HTML 片段） |
| `summary` | 总结心得 |
| `plans` | 计划内容 |
| `year` | 报告年份；缺省取本年 |
| `type` | `week` / `month` / `season` / `halfYear` / `year`（必填） |
| `serialNumber` | 报告周期（必填，正整数） |
| `userName` | 当前登录人姓名，eb 链路自动生成报告名称时必填（由 weaver-e10-hrm-connector 解析） |
| `title` | 报告名称，直接指定时优先于自动生成 |

- `content` / `summary` / `plans` 至少提供一个。
- eb 链路创建时发布状态固定为草稿（`0`），不允许为空或其它状态；报告名称按「{姓名}{年份}年第{N}周的报告」（周报）等规则动态生成。
- 标准版链路的报告名称由服务端生成并返回，无需传 `title` / `userName`。

### 修改 `plan.report.update.prepare` / `.apply`

用 `id` 或 `year` + `type` + `serialNumber`（+ `creatorUserId`）定位报告，再传要更新的 `content` / `summary` / `plans`（至少一个）。`prepare` 会先查当前内容并给出 before/after 差异；未传的字段保持原值。

### 发布 `plan.report.publish.prepare` / `.apply`

用 `id` 或周期参数定位报告。`prepare` 会校验报告存在且当前不是「已发布」；若还没创建草稿，先走新建流程。

### 撤回 `plan.report.withdraw.prepare` / `.apply`

用 `id` 或周期参数定位报告，`prepare` 会校验当前状态为「已发布（1）」。**仅标准版链路支持**：eb 链路的撤回是 ESB 动作流「eb撤回报告」，源资料未提供动作流唯一标识，CLI 返回 `policy/link_unsupported`，需要改用 `weaver-e10-esb` skill 执行同名动作流。

## 命令

### 新建（先 prepare）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.create.prepare --input-json '{"type":"week","serialNumber":36,"content":"<p>完成A模块联调</p>","summary":"<p>节奏可控</p>","plans":"<p>推进B模块</p>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.create.prepare --input-json '{"type":"week","serialNumber":36,"content":"<p>完成A模块联调</p>","summary":"<p>节奏可控</p>","plans":"<p>推进B模块</p>"}'
```

用户确认后 apply（`continuation` 用原样回传）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.create.apply --input-json '{"confirm":true,"continuation":"PLACEHOLDER_CONTINUATION"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.create.apply --input-json '{"confirm":true,"continuation":"PLACEHOLDER_CONTINUATION"}'
```

### 修改

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.update.prepare --input-json '{"type":"week","serialNumber":36,"plans":"<p>下周三完成B模块验收</p>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.update.prepare --input-json '{"type":"week","serialNumber":36,"plans":"<p>下周三完成B模块验收</p>"}'
```

### 发布

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.publish.prepare --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.publish.prepare --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

### 撤回

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.withdraw.prepare --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.withdraw.prepare --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

复杂或多行内容（例如大段 HTML 报告正文）建议写入 UTF-8 JSON 文件后用 `--input <path>`：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.create.prepare --input "C:\path\to\plan-create.json"
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.create.prepare --input "/path/to/plan-create.json"
```

## 输出处理

`*.prepare` 返回：

- `status`：`AWAITING_CONFIRMATION`（可继续确认执行）或 `ALREADY_EXISTS`（该周期报告已存在，不签发 continuation）。
- `preview`：将要写入的业务内容（新建为完整内容，修改为 `before` / `after` / `changedFields`）。
- `continuation` + `expiresInSeconds`：确认凭据，默认 10 分钟有效。
- `link`：本次生效的链路（`standard` / `eb`）。

`*.apply` 返回：

- `status: COMPLETE`；
- `reportId`（新建时返回新建报告 id）、`detailUrl`（必须呈现为可点击链接）。

## 注意

- **重复创建防护**：`plan.report.create.prepare` 会按周期（年份 + 类型 + 周期 + 当前登录人）先查重。返回 `status: ALREADY_EXISTS` 时**禁止**直接创建，必须先询问用户是否改为编辑已有报告。
- **先草稿后发布**：用户要求直接发布但还没有草稿时，先走新建（prepare→apply），再走发布（prepare→apply）。
- **判断是否已提交**只能通过 `plan.report.get` 按周期查询，不要用列表接口猜。
- **禁止出现数据库英文字段名**：创建出的报告内容与给用户的回复中，不要出现 `content` / `f_content` / `summary` / `f_summary` / `plans` / `f_plans` / `year` / `f_year` / `type` / `f_type` / `serial_number` / `f_serial_number` 等字段名。CLI 输入输出均为业务字段，直接使用即可。
- 涉及「让谁看/共享范围」「按上级或部门层级」等报告名称前缀信息，标准版由服务端处理；不要手工拼报告名称。
- 报告正文可能包含大段 HTML，属于业务数据处理，写入前必须在 `prepare` 预览里让用户确认内容。

## 失败处理

- `confirmation/required`：没有传 `confirm=true`。必须取得用户明确确认后再调用。
- `validation/continuation_invalid` / `continuation_mismatch` / `continuation_expired`：continuation 不合法、串用或过期，重新执行 `prepare`。
- `validation/context_mismatch` / `link_changed`：租户或登录账号变化、链路变化，重新执行 `prepare`。
- `validation/report_exists`：并发或状态变化导致重复。停止创建，改为询问用户是否编辑。
- `validation/not_found`：目标报告不存在；发布/撤回/修改前先创建。
- `validation/already_published`：已发布，无需重复发布。
- `validation/not_published`：不是已发布状态，无法撤回。
- `validation/userName_required`：eb 链路上未提供报告名称与姓名，先由 weaver-e10-hrm-connector 解析当前登录人姓名后重试。
- `policy/link_unsupported`：该能力在当前链路不可用（eb 撤回），按 `message` 给出的替代路径处理。
- `partial` / `write_uncertain`：写请求已发出但结果不确定。**立即停止，禁止自动重试**；先用 `plan.report.get` 做一次只读回查，再向用户说明并让用户决定。
