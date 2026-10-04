---
name: gaia-wfm-openapi-attendance-cancelleave-apply-la
description: 处理当前登录用户的销假申请、销假修改和销假撤回，并按请假日期范围查询可销假的请假记录。用户提出“我要销假”“申请销假”“修改销假单”“撤回销假”“查询本周可销假记录”等本人销假流程请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 销假申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的销假业务。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人销假：先检查销假权限，再按日期范围获取可销假的请假记录；用户选择记录并确认后提交销假申请。
- 修改本人已有销假单：用户必须提供或在当前对话中确认 `formNumber`，同时确认要修改的记录、日期范围和说明后提交修改。
- 撤回本人销假单：用户必须提供或确认 `formNumber`；撤回属于破坏性操作，执行前二次确认。
- 查询辅助信息：按日期范围查询当前用户可销假的请假记录。

不处理他人的销假、请假申请、销假审批、附件上传/下载、权限授予，或本 Skill 未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取销假权限 | `gaia YA ATD_FORM_APPLY getCancelLeaveApplyAccess` | read |
| 获取日期范围内可销假的请假记录 | `gaia YA ATD_FORM_APPLY getLeaveRecordList` | read |
| 申请销假 | `gaia YA ATD_FORM_APPLY applyCancelLeave` | write |
| 修改销假 | `gaia YA ATD_FORM_APPLY modifyCancelLeave` | write |
| 撤回销假 | `gaia YA ATD_FORM_APPLY cancelCancelLeave` | destructive |

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中为 `unspecified`，`language` 仅在 `getLeaveRecordList` 的契约中声明为 Header，同样只有当前对话或可信上游明确提供时才传入，缺失时依据 CLI 原始错误追问，不猜测。

## 参数契约

Discovery 与各方法 `--help` 均未声明必填字段；以下字段状态均为 `unspecified`，不能擅自改成必填或填充空值。

### `getLeaveRecordList` body

`startDate` string（开始日期）和 `endDate` string（结束日期）。响应 `details` 是对象数组，表示该范围内可销假的请假记录；数组项未声明子字段，只展示真实返回内容，不预设字段结构。

### `applyCancelLeave` body

`confirm` boolean（是否提交）、`startDate`/`endDate` string（销假开始/结束日期）、`recordId` array（请假记录 ID 列表）和 `remark` string（详细说明）。仅传入用户选择并确认的记录 ID、日期范围和说明。

### `modifyCancelLeave` body

除申请字段外，还包括 `formNumber` string（表单号）。修改只发送用户明确要求变更的新值，不推测原值。

### `cancelCancelLeave` body

仅声明 `formNumber` string（表单号）。撤回时不要自行添加日期、记录 ID、原因或确认字段。

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

“本周/上周/下周”以周一为起始日；月份按自然月。用户给出明确日期或日期范围时解析为同一格式。销假接口只声明日期字段，不声明时间字段；不自行添加时间或猜测时分。日期语义有歧义时，一次只追问最关键的日期边界。

## 工作流

### 查询可销假记录

1. 调用 `getCancelLeaveApplyAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集查询日期范围，将“明天、昨天、前天、后天、上周、本周、下周、本月、上月”等表达映射为 `startDate/endDate`；缺少或有歧义时先追问日期。
3. 调用 `getLeaveRecordList`，展示返回的真实记录数组并标明实际日期范围。不得从未声明字段推断记录 ID、表单号或状态；若用户要执行销假，要求其从真实结果中明确选择目标记录。

### 申请销假

1. 按“查询可销假记录”流程取得并展示候选记录；用户必须明确选择一个或多个记录，并确认对应的 `recordId`、销假日期范围及 `remark`（如有）。
2. 展示申请摘要（销假开始/结束日期、选中的请假记录 ID、说明）并取得明确确认。
3. 确认后调用 `applyCancelLeave`。`confirm` 仅按用户或可信上游明确给出的值传递，不自行推断。只有返回明确成功标志时才报告已提交；该响应没有声明表单号字段，不能自行承诺可凭响应中的未声明字段继续操作。

### 修改

仅在用户明确表达修改意图且已确认 `formNumber` 时调用 `modifyCancelLeave`。若用户没有表单号但给出日期范围，可先调用 `getLeaveRecordList` 展示候选记录；只有候选真实字段明确提供表单号且用户选择后才能使用。展示表单号、待修改的日期范围、记录 ID 和说明并取得确认；只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与 `details.resultFlag` 等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认 `formNumber` 时调用 `cancelCancelLeave`。撤回是 destructive 操作，执行前展示表单号和影响并取得二次确认；该方法只传入契约声明的 `formNumber`。只有明确成功响应才报告已撤回。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `getCancelLeaveApplyAccess` 成功响应；可信 `employeeNum`、`tenantCode`、`language` Header | `getLeaveRecordList`、`applyCancelLeave`、`modifyCancelLeave`、`cancelCancelLeave` 同名 Header（`language` 仅传给 `getLeaveRecordList`） | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言日期范围 | `getLeaveRecordList.startDate/endDate` | 按 `Asia/Shanghai` 映射为 `yyyy-MM-dd`；边界不明确时追问，不能猜测 |
| `getLeaveRecordList.details` 的真实请假记录 ID | `applyCancelLeave.recordId` 或 `modifyCancelLeave.recordId` | 仅当返回项实际包含记录 ID 且用户明确选择后传递；空或多候选未选时停止并询问 |
| 用户确认的销假日期范围 | `applyCancelLeave.startDate/endDate` 或 `modifyCancelLeave.startDate/endDate` | 与查询使用相同的已确认日期值，不重新解释或改写 |
| 用户提供或当前对话确认的 `formNumber` | `modifyCancelLeave.formNumber` 或 `cancelCancelLeave.formNumber` | 未确认时追问；不得从未声明字段或模糊结果猜测 |
| `applyCancelLeave` 成功响应 | 后续修改/撤回 | 响应契约未声明 `formNumber`，无可靠表单号映射；后续操作必须由用户另行提供并确认表单号 |

## 结果、空结果与错误恢复

- 查询结果按真实 `details` 数组展示，并说明实际日期范围；不猜测记录项未声明字段的含义。
- 申请/修改响应 `details` 可包含 `cancelLeaveDetails`（其中可能有 `cancelLeaveRemark`、`cancelLeaveTimeRange`、`cancelLeaveType`、`scheduleDate`）、`remark`、`resultFlag` 和 `errorMsg`；撤回响应 `details` 可包含 `formNumber`、`resultFlag` 和 `errorMsg`。只展示实际返回内容。
- 空的 `details` 或记录数组不是成功提交。说明实际日期范围和为空的字段，给出补充明确日期或重新选择记录的方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限、记录 ID 或表单号为空时继续写操作。

## 安全边界与确认

权限和记录查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，scope `cancelLeave.batch.apply.queryByPerson`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-16。
- 参考流程：`gaia-wfm-openapi-attendance-leave-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。
