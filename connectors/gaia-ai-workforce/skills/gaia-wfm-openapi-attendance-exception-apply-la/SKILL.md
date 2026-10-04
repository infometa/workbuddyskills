---
name: gaia-wfm-openapi-attendance-exception-apply-la
description: 处理当前登录用户的考勤异常申诉申请、修改和撤回，并按异常日期范围获取可用异常类型与异常原因。用户提出“申诉考勤异常”“申请异常申诉”“修改异常申诉单”“撤回异常申诉”或查询某天/某周可用异常类型和原因等本人异常处理请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 考勤异常申诉流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的异常申诉业务。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人异常申诉：先检查权限；确定异常日期范围后获取该范围内真实可用的异常类型和原因；用户选择并确认后提交申请。
- 修改本人已有异常申诉单：用户必须提供或在当前对话中确认 `formNumber`；缺少新的异常类型或原因时，先获取并展示联合列表，再提交修改。
- 撤回本人异常申诉单：用户必须提供或确认 `formNumber`；撤回属于破坏性操作，执行前二次确认。
- 查询辅助信息：按异常日期范围获取可用异常类型和异常原因。

不处理他人的异常申诉、审批代办、附件上传/下载、权限授予，或本 Skill 未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取异常申诉权限 | `gaia YA ATD_FORM_APPLY getExceptionAccess` | read |
| 获取日期范围内可用异常类型和原因 | `gaia YA ATD_FORM_APPLY getExceptionTypeAndReason` | read |
| 申请异常申诉 | `gaia YA ATD_FORM_APPLY applyException` | write |
| 修改异常申诉 | `gaia YA ATD_FORM_APPLY modifyException` | write |
| 撤回异常申诉 | `gaia YA ATD_FORM_APPLY cancelException` | destructive |

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中均为 `unspecified`，只有当前对话或可信上游明确提供时才放入 Header，缺失时依据 CLI 原始错误追问，不猜测。

## 参数契约

Discovery 与各方法 `--help` 均未声明必填字段；以下字段状态均为 `unspecified`，不能擅自改成必填或填充空值。

### `getExceptionTypeAndReason` body

`startDate` string（异常日期开启）和 `endDate` string（异常日期结束）。接口返回的 `details` 是对象数组，内容为该日期范围内可用的异常类型与异常原因；只展示返回的真实字段和值，不根据字段名猜测额外含义。

### `applyException` body

`attachmentIds` array（附件 Id 列表）、`confirm` boolean（是否提交）、`startDate`/`endDate` string（异常开始/结束日期）、`exceptionName` string（异常名称）、`exceptionReason` string（异常原因）、`forceShouldTime` string（应修改打卡时间）和 `remark` string（详细说明）。仅传入用户提供或已从联合查询结果确认的字段。

### `modifyException` body

除申请字段外，还包括 `attachmentOperateType` string（`add`、`delete`、`modify`）和 `formNumber` string（表单号）。修改只发送用户明确要求变更的新值，不推测原值。

### `cancelException` body

`formNumber` string（表单号）和 `remark` string（详细描述）。撤回时不得从未声明的查询接口猜测表单号。

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

“本周/上周/下周”以周一为起始日；月份按自然月。用户给出明确日期或日期范围时原样解析为同一格式。异常申诉接口契约只声明日期字段，不声明时间字段；不要自行添加时间参数或猜测时分。日期语义有歧义时，一次只追问最关键的日期边界。

## 工作流

### 申请

1. 调用 `getExceptionAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集异常日期范围。若用户使用“明天、昨天、前天、后天、上周、本周、下周、本月、上月”等表达，按上表映射成 `startDate` 和 `endDate`；缺少或有歧义时先追问日期，不调用联合查询。
3. 调用 `getExceptionTypeAndReason`，展示该范围返回的真实异常类型和异常原因列表。用户未说明异常类型或异常原因时，必须从该列表中让用户选择；两项均未说明时，仍只调用一次联合接口并同时展示两类选项。不得创建或猜测默认值。
4. 用户明确选择 `exceptionName` 和 `exceptionReason` 后，补齐其他已声明字段，展示申请摘要（异常日期、异常名称、异常原因、应修改打卡时间、说明和附件摘要）并取得明确确认。
5. 确认后调用 `applyException`。`confirm` 仅按用户或可信上游明确给出的值传递，不自行推断。只有返回明确成功标志时才报告已提交，并记录 `details.formNumber` 供本次对话后续操作。

### 修改

仅在用户明确表达修改意图且已确认 `formNumber` 时调用 `modifyException`。若新的异常类型或异常原因未提供，先根据已确认的异常日期范围调用 `getExceptionTypeAndReason`，展示真实列表并等待选择；两项均缺少时同时展示类型和原因。展示表单号、待修改字段和影响范围并取得确认；只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与 `details.resultFlag` 等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认 `formNumber` 时调用 `cancelException`。撤回是 destructive 操作，执行前展示表单号、撤回原因和影响并取得二次确认。只有明确成功响应才报告已撤回。

### 辅助查询

`getExceptionTypeAndReason` 是唯一的类型/原因查询接口。它必须使用明确的 `startDate` 和 `endDate`，返回空时说明实际日期范围并要求新的明确范围或停止申请，不扩大范围、不重复盲目重试。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `getExceptionAccess` 成功响应；可信 `employeeNum`、`tenantCode` Header | `getExceptionTypeAndReason`、`applyException`、`modifyException`、`cancelException` 同名 Header | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言异常日期范围 | `getExceptionTypeAndReason.startDate/endDate` | 按 `Asia/Shanghai` 映射为 `yyyy-MM-dd`；边界不明确时追问，不能猜测 |
| 联合查询返回的真实异常类型 | `applyException.exceptionName` 或 `modifyException.exceptionName` | 仅用户选择并确认后传递；空或多匹配时停止并询问 |
| 联合查询返回的真实异常原因 | `applyException.exceptionReason` 或 `modifyException.exceptionReason` | 仅用户选择并确认后传递；空或多匹配时停止并询问 |
| 用户确认的异常日期范围 | `applyException.startDate/endDate` 或 `modifyException.startDate/endDate` | 与查询使用相同的已确认日期值，不重新解释或改写 |
| `applyException.details.formNumber` | 后续 `modifyException.formNumber` 或 `cancelException.formNumber` | 仅限同一对话且用户明确确认目标；无表单号或未确认时追问 |
| `getExceptionTypeAndReason.details` | 无 | 除用户选择的类型/原因外，不把未确认字段映射到写操作 |

## 结果、空结果与错误恢复

- 成功结果按真实响应字段组织。申请响应的 `details` 可包含 `formNumber`、`exceptionName`、`exceptReason`、`exceptionDate`、`forceShouldTime`、`planPunchDate`、`remark`、`resultFlag`、`errorMsg` 和 `uploadFileName`；不根据字段名臆测业务含义。
- 修改响应的 `details` 可包含 `formNumber`、`punchDate`、`punchTime`、`punchReason`、`remark`、`resultFlag`、`errorMsg` 和 `uploadFileName`；按接口真实字段展示，不擅自改名为其他业务字段。
- 撤回响应的 `details` 可包含 `formNumber`、`replacePunchSign`、`replacePunchData`、`resultFlag` 和 `errorMsg`，其中 `replacePunchData` 只按真实返回展示。
- 空的 `details` 或空数组不是成功提交。说明实际日期范围和返回为空的字段，给出可操作的补充方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限或类型/原因为空时继续申请或修改。

## 安全边界与确认

权限和类型/原因查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，scope `abnormal.appeal.previewProcess`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-15。
- 参考流程：`gaia-wfm-openapi-attendance-overtime-apply-la/SKILL.md`、`gaia-wfm-openapi-attendance-leave-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。
