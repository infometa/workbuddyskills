---
name: gaia-wfm-openapi-attendance-replacepunch-apply-la
description: 处理当前登录用户的补卡申请、补卡修改和补卡撤回，并按日期范围查询补卡单与补卡记录、获取补卡原因。用户提出“申请补卡”“修改补卡单”“撤回补卡”“查询某天或某周补卡记录”等本人补卡流程请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 补卡申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的补卡业务。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人补卡：先检查权限，再按日期范围查询补卡单和打卡记录；用户未说明补卡原因时获取真实原因列表，确认后提交申请。
- 修改本人已有补卡单：通过用户提供或日期范围查询得到候选表单，用户明确确认 `formNumber` 和变更内容后提交修改。
- 撤回本人补卡单：通过用户提供或日期范围查询得到候选表单/记录，用户明确确认目标标识后执行撤回。
- 查询辅助信息：按日期范围查看补卡单与补卡记录，或获取补卡原因列表。

不处理他人的补卡、补卡审批、附件上传/下载、权限授予，或本 Skill 未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取补卡权限 | `gaia YA ATD_FORM_APPLY getAccess` | read |
| 获取日期范围内补卡单和补卡记录 | `gaia YA ATD_FORM_APPLY getFormAndRecord` | read |
| 获取补卡原因 | `gaia YA ATD_FORM_APPLY getReason` | read |
| 申请补卡 | `gaia YA ATD_FORM_APPLY applyPunch` | write |
| 修改补卡 | `gaia YA ATD_FORM_APPLY modifyPunch` | write |
| 撤回补卡 | `gaia YA ATD_FORM_APPLY cancelPunch` | destructive |

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中均为 `unspecified`，只有当前对话或可信上游明确提供时才放入 Header，缺失时依据 CLI 原始错误追问，不猜测。

## 参数契约

Discovery 与各方法 `--help` 均未声明必填字段；以下字段状态均为 `unspecified`，不能擅自改成必填或填充空值。

### `getFormAndRecord` body

`startDate` string（补卡日期开启）和 `endDate` string（补卡日期结束）。响应 `details` 包含 `formList`（表单列表）和 `recordList`（补卡记录列表）；列表项没有声明子字段，只能展示真实返回内容，不能预设字段结构。

### `applyPunch` body

`attachmentIds` array（附件列表）、`confirm` boolean（是否提交）、`missedEntryDate` string（补卡日期）、`missedEntryTime` string（补卡时间）、`missedEntryReason` string（原因）和 `remark` string（详细说明）。仅传入用户提供或已从可信查询结果确认的字段。

### `modifyPunch` body

除申请字段外，还包括 `formNumber` string（表单号）和 `attachmentOperateType` string（`add` 追加、`modify` 替换、`delete` 删除全部）。修改只发送用户明确要求变更的新值，不推测原值。

### `cancelPunch` body

`formNumber` string（表单号）、`recordId` string（补卡记录 Id）、`startDate`/`endDate` string（补卡区间开始/结束日期）、`missedEntryDate`/`missedEntryTime`/`missedEntryReason`、`attachmentIds`、`confirm` 和 `remark`。仅传入用户明确提供或从真实候选记录中确认的字段，不为撤回自动补齐未知值。

### `getReason`

该方法只接收已确认的业务 Header。响应 `details` 在 Discovery 中未声明子字段；将真实返回内容作为补卡原因候选展示，不推断代码、名称或默认原因。

## 日期与时间表达式

日期解析使用 `Asia/Shanghai` 时区，以执行时当地日期为基准，转换后按接口字段传递 `yyyy-MM-dd`。支持以下自然语言范围：

| 用户表达 | 映射 |
|---|---|
| 今天 | 当地当天 |
| 明天 | 当地当天 + 1 天 |
| 昨天 | 当地当天 - 1 天 |
| 前天 | 当地当天 - 2 天 |
| 后天 | 当地当天 + 2 天 |
| 本周 | 本周一至本周日 |
| 上周 | 上周一至上周日 |
| 下周 | 下周一至下周日 |
| 本月 | 当月 1 日至月末 |
| 上月 | 上月 1 日至月末 |

“本周/上周/下周”以周一为起始日；月份按自然月。用户给出明确日期或日期范围时解析为同一格式。`getFormAndRecord` 和撤回区间只接收日期；`missedEntryTime` 的格式未在契约中声明，保留用户明确提供的时间表达，若 CLI 返回格式错误再针对该字段追问。日期或时间有歧义时，一次只追问最关键的边界。

## 工作流

### 申请

1. 调用 `getAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集补卡日期或查询范围，将“明天、昨天、前天、后天、上周、本周、下周、本月、上月”等表达映射为 `startDate/endDate`；缺少或有歧义时先追问日期。
3. 调用 `getFormAndRecord`，展示该范围内真实返回的 `formList` 和 `recordList`。让用户从候选记录中确认要补卡的日期/时间；没有唯一候选时不得替用户选择。
4. 用户未说明 `missedEntryReason` 时调用 `getReason`，展示真实原因列表并等待选择；用户已明确原因时无需重复调用。原因列表为空时停止申请，不创建默认原因。
5. 用户明确 `missedEntryDate`、`missedEntryTime` 和原因后，展示申请摘要（补卡日期、时间、原因、说明和附件摘要）并取得明确确认。
6. 确认后调用 `applyPunch`。`confirm` 仅按用户或可信上游明确给出的值传递，不自行推断。只有返回明确成功标志时才报告已提交，并记录 `details.formNumber` 供本次对话后续操作。

### 修改

仅在用户明确表达修改意图且已确认 `formNumber` 时调用 `modifyPunch`。若用户没有表单号但提供了日期范围，可先调用 `getFormAndRecord` 展示候选表单；只有候选的真实字段明确包含表单号且用户选择后才能使用。新原因未提供时调用 `getReason` 并展示列表供选择。提交前展示表单号、待修改字段和影响范围并取得确认；只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与 `details.resultFlag` 等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认目标时调用 `cancelPunch`。目标可由用户直接提供，或先按日期范围调用 `getFormAndRecord` 展示候选后选择；仅把候选中实际返回并经用户确认的 `formNumber`、`recordId` 和相关字段传入。撤回是 destructive 操作，执行前展示目标标识、补卡日期/时间、原因和影响并取得二次确认。只有明确成功响应才报告已撤回。

### 辅助查询

查询补卡单和记录必须使用明确的 `startDate/endDate`。结果按 `formList` 与 `recordList` 分组展示，并说明实际日期范围；某一列表为空时只说明该列表为空，不把另一列表忽略，也不自动扩大日期范围。`getReason` 可独立用于列出补卡原因。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `getAccess` 成功响应；可信 `employeeNum`、`tenantCode` Header | `getFormAndRecord`、`getReason`、`applyPunch`、`modifyPunch`、`cancelPunch` 同名 Header | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言日期范围 | `getFormAndRecord.startDate/endDate` | 按 `Asia/Shanghai` 映射为 `yyyy-MM-dd`；边界不明确时追问，不能猜测 |
| `getFormAndRecord.formList` 的真实候选项 | `modifyPunch.formNumber` 或 `cancelPunch.formNumber` | 仅当返回项实际包含表单号且用户明确选择后传递；缺失或多候选未选时停止并询问 |
| `getFormAndRecord.recordList` 的真实候选项 | `applyPunch.missedEntryDate/missedEntryTime` 或 `cancelPunch.recordId` 等同名字段 | 仅映射响应中实际存在且经用户确认的字段；未声明/缺失字段不推断 |
| `getReason.details` 的真实原因候选 | `applyPunch.missedEntryReason` 或 `modifyPunch.missedEntryReason` | 仅用户选择并确认后传递；空结果时停止并说明 |
| `applyPunch.details.formNumber` | 后续 `modifyPunch.formNumber` 或 `cancelPunch.formNumber` | 仅限同一对话且用户明确确认目标；无表单号或未确认时追问 |
| 用户确认的查询范围 | `cancelPunch.startDate/endDate` | 仅在撤回契约或真实候选需要这些字段时复用，不作为默认必填字段 |

## 结果、空结果与错误恢复

- 查询结果按真实的 `details.formList` 和 `details.recordList` 展示；不猜测列表项未声明的字段含义。
- 申请响应 `details` 可包含 `formNumber`、`missedEntryDate`、`missedEntryTime`、`missedEntryReason`、`remark`、`resultFlag`、`errorMsg` 和 `uploadFileName`。
- 修改响应还可包含 `attachmentOperateType`；撤回响应使用与申请相同的已声明结果字段。只展示实际返回内容，不自行改名或扩展含义。
- 空的 `details`、`formList`、`recordList` 或原因列表不是成功提交。说明实际日期范围和为空的字段，给出补充明确日期、时间或原因的方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限、目标记录或补卡原因为空时继续申请、修改或撤回。

## 安全边界与确认

权限、补卡单/记录和原因查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，scope `replace.punch.apply.personal`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-15。
- 参考流程：`gaia-wfm-openapi-attendance-exception-apply-la/SKILL.md`、`gaia-wfm-openapi-attendance-overtime-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。
