---
name: gaia-wfm-openapi-attendance-cancelpunch-apply-la
description: 处理当前登录用户基于已有补卡记录发起的撤销补卡申请，并按日期范围查询审批中的撤销补卡单和可选补卡记录。用户提出“申请撤销补卡”“撤销昨天的补卡”“查询本周可撤销补卡记录”等本人撤销补卡申请请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 撤销补卡申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令，对当前登录人员已有的补卡记录发起撤销补卡申请并生成撤销补卡单。它不是撤回补卡申请单的流程，不得调用或复用 `gaia-wfm-openapi-attendance-replacepunch-apply-la` 的 `cancelPunch`。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人撤销补卡：先检查撤销补卡权限，再按日期范围查询审批中的撤销补卡单和可选补卡记录；用户选择已有补卡记录并确认后，提交新的撤销补卡申请，不要求表单号。
- 撤回本人已提交的撤销补卡单：用户明确提供或确认已生成撤销补卡单的 `formNumber` 后，二次确认并调用专用撤回命令。
- 查询撤销补卡候选：按用户给出的日期或日期范围展示真实的撤销补卡单和可选补卡记录；用户可使用日期、时间、原因等非 ID 字段选择目标。

不处理普通补卡申请、修改或撤回普通补卡单，不处理他人的补卡、审批、附件上传/下载、权限授予，或本 Skill 未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取撤销补卡权限 | `gaia YA ATD_FORM_APPLY getCancelPunchAccess` | read |
| 获取日期范围内审批中的撤销补卡单和可选补卡记录 | `gaia YA ATD_FORM_APPLY getCancelPunchAvailableRecords` | read |
| 基于已有补卡记录申请撤销补卡 | `gaia YA ATD_FORM_APPLY applyCancelPunch` | write |
| 撤回已提交的撤销补卡单 | `gaia YA ATD_FORM_APPLY cancelCancelPunch` | destructive |

以下相似命令不属于本 Skill：`getAccess`、`getFormAndRecord`、`applyPunch`、`modifyPunch`、`cancelPunch` 属于普通补卡流程。`cancelCancelPunch` 属于本 Skill，但只用于撤回已提交的撤销补卡单，不能替代 `applyCancelPunch`。

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中均为 `unspecified`，只有当前对话或可信上游明确提供时才传入 Header，缺失时依据 CLI 原始错误追问，不猜测。

## 参数契约

Discovery 与方法 `--help` 未声明以下字段为必填；字段状态按 `unspecified` 处理，不擅自改成必填，也不填充空值。

### `getCancelPunchAvailableRecords` body

`startDate` string（日期区间开始）和 `endDate` string（日期区间结束）。响应 `details.formList` 是审批中的撤销补卡申请单列表，`details.recordList` 是可选的已有补卡记录列表；列表项只展示真实返回的非敏感业务字段，不预设未声明的子字段。

### `applyCancelPunch` body

契约声明：

- `recordId` string：已有补卡记录 Id；可不传，CLI 契约说明为空时可用补卡日期和时间匹配记录。
- `startDate` / `endDate` string：撤销补卡申请的开始/结束日期。
- `missedEntryDate` / `missedEntryTime` / `missedEntryReason`：已有补卡记录的日期、时间和原因。
- `attachmentIds` array：附件列表。
- `remark` string：详细说明。
- `confirm` boolean：是否提交。

用户不需要提供表单号。`applyCancelPunch` 的成功响应会返回新生成撤销补卡单的 `details.formNumber`，但该表单号只作为真实结果展示或后续由其他明确授权流程使用，不作为本 Skill 的输入前置条件。

### `cancelCancelPunch` body

仅声明 `formNumber` string（已提交的撤销补卡单表单号）。该字段只在用户要求撤回已提交的撤销补卡单时使用，不是申请新的撤销补卡时的输入。

## 日期表达式

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

“本周/上周/下周”以周一为起始日，月份按自然月。用户给出明确日期或日期范围时按同一格式传递。`missedEntryTime` 的格式未在契约中声明，保留用户确认或真实候选中的明确值，若 CLI 返回格式错误再针对该字段追问。日期边界有歧义时，一次只追问最关键的边界。

## 工作流

### 查询可撤销补卡记录

1. 调用 `getCancelPunchAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集查询日期范围，将“明天、昨天、前天、后天、上周、本周、下周、本月、上月”等表达映射为 `startDate/endDate`；缺少或有歧义时先追问日期。
3. 调用 `getCancelPunchAvailableRecords`，分别展示 `formList` 和 `recordList` 的真实业务信息，并标明实际查询范围。查询结果不得展示 `recordId`、表单内部 ID 或任何可直接识别记录的技术 ID；使用日期、时间、原因等非 ID 字段区分候选。

### 申请撤销补卡

1. 按“查询可撤销补卡记录”流程获取候选；用户必须明确选择一条或多条已有补卡记录。不得要求用户提供表单号。
2. 从用户选择的真实候选中内部映射 `recordId`；若用户未提供或候选没有可用 `recordId`，按契约允许的规则使用已确认的 `missedEntryDate` 与 `missedEntryTime` 匹配，不向用户索取技术 ID。
3. 收集并确认撤销申请的 `startDate`、`endDate`、补卡日期、补卡时间、补卡原因、说明和附件等实际需要字段。未声明或未确认的字段不猜测、不补齐。
4. 展示申请摘要：补卡日期/时间、原因、撤销申请日期范围、说明和附件摘要；不得展示 `recordId`、表单内部 ID 或任何技术 ID。取得明确提交确认。
5. 确认后调用 `applyCancelPunch`。`confirm` 只按用户或可信上游明确给出的值传递，不自行推断。只有返回明确成功标志时才报告已提交，并展示真实返回的撤销补卡单结果，包括新生成的 `details.formNumber`（如响应实际返回）。

### 撤回已提交的撤销补卡单

1. 仅在用户明确表达“撤回撤销补卡单”意图，并提供或确认已生成的 `formNumber` 时执行；不能把普通补卡的 `cancelPunch` 当作替代命令。
2. 展示撤销补卡单表单号和撤回影响，取得二次确认。
3. 确认后调用 `cancelCancelPunch`，请求体只传契约声明的 `formNumber`。只有明确成功响应才报告已撤回；超时或连接中断时标记为结果未知，不自动重试。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `getCancelPunchAccess` 成功响应；可信 `employeeNum`、`tenantCode` Header | `getCancelPunchAvailableRecords`、`applyCancelPunch` 同名 Header | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言日期范围 | `getCancelPunchAvailableRecords.startDate/endDate` | 按 `Asia/Shanghai` 映射为 `yyyy-MM-dd`；边界不明确时追问，不能猜测 |
| `getCancelPunchAvailableRecords.details.recordList` 的真实候选 | `applyCancelPunch.recordId`、`missedEntryDate`、`missedEntryTime`、`missedEntryReason` | 仅映射真实存在且经用户确认的字段；技术 ID 仅内部使用，未声明或缺失字段不推断 |
| 用户确认的撤销申请日期范围 | `applyCancelPunch.startDate/endDate` | 与查询使用的已确认日期值保持一致，不重新解释或改写 |
| `applyCancelPunch` 成功响应 `details.formNumber` | 结果展示或后续 `cancelCancelPunch.formNumber` | 仅使用真实返回值；申请新撤销补卡时不要求表单号，撤回已提交撤销补卡单时须由用户确认该表单号 |
| 用户提供或确认的已提交撤销补卡单 `formNumber` | `cancelCancelPunch.formNumber` | 仅用于撤回已提交的撤销补卡单；未确认时追问，不从普通补卡记录猜测 |

## 结果、空结果与错误恢复

- 查询结果按真实的 `details.formList` 和 `details.recordList` 展示，但用户可见内容必须过滤 `recordId`、内部表单 ID 和其他技术标识；不猜测列表项未声明字段的含义。
- `applyCancelPunch` 和 `cancelCancelPunch` 响应只展示真实返回的顶层 `code`、`message`、`reason`、`details` 及其中已声明的 `formNumber`、`missedEntryDate`、`missedEntryTime`、`missedEntryReason`、`remark`、`resultFlag`、`errorMsg`、`uploadFileName` 等字段。
- 空的 `details`、`formList` 或 `recordList` 不是成功提交。说明实际日期范围和为空的列表，给出补充明确日期或重新选择已有补卡记录的方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复提交；请用户先核对考勤系统是否已生成撤销补卡单。
- 查询前置步骤失败立即停止；不要在权限、目标补卡记录或提交确认未满足时继续申请。

## Operation Risk and Confirmation Requirements

Operation risk: `applyCancelPunch` is a write operation that creates a new cancel-punch application against an existing punch record; `cancelCancelPunch` is a destructive operation that withdraws an already submitted cancel-punch application. Neither command withdraws a normal punch application. Confirmation requirements: for `applyCancelPunch`, show the selected punch date/time, reason, application date range, and impact, then obtain one explicit submission confirmation; for `cancelCancelPunch`, show the confirmed cancel-punch form number and impact, then obtain a second explicit confirmation immediately before execution. Permission and candidate queries are read-only and need no extra confirmation. Never expose record IDs or internal record IDs to the user.

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help`、`gaia api check YA ATD_FORM_APPLY <method>` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，撤销补卡 scope `901180`，路径前缀 `/open-scene-api-la/api/v1/agent/cancelreplacepunch/`。
- 已核验方法：`getCancelPunchAccess`、`getCancelPunchAvailableRecords`、`applyCancelPunch`、`cancelCancelPunch`；明确排除普通补卡的 `cancelPunch`。
- 参考流程：`gaia-wfm-openapi-attendance-cancelleave-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。
