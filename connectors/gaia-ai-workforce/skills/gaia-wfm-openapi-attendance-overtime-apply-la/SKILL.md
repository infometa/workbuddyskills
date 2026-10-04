---
name: gaia-wfm-openapi-attendance-overtime-apply-la
description: 处理当前登录用户的加班申请、加班修改、加班撤回，以及按加班时间范围获取可用加班类型、获取加班原因和加班记录。用户提出“申请加班”“修改加班单”“撤回加班”“查某天/本周可用加班类型”等本人加班流程请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 加班申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的加班业务。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人加班：先检查权限；只要用户未说明加班类型或加班原因，就调用对应列表接口并展示真实选项；用户选择并确认后提交申请。
- 修改本人已有加班单：用户必须提供或在当前对话中确认 `formNumber`；只要待修改内容缺少加班类型或加班原因，也先获取并展示对应列表，再提交变更。
- 撤回本人加班单：用户必须提供或确认 `formNumber`；撤回属于破坏性操作，执行前二次确认。
- 查询辅助信息：获取加班原因、时间范围内的可用加班类型，或调用契约声明的加班记录方法。

不处理他人的加班、审批代办、附件上传/下载、权限授予，或本表未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取加班权限 | `gaia YA ATD_FORM_APPLY overtimeGetAccess` | read |
| 获取时间范围内可用加班类型 | `gaia YA ATD_FORM_APPLY overtimeGetAvailableOvertimeTypeByPeriod` | read |
| 获取加班原因 | `gaia YA ATD_FORM_APPLY overtimeGetreason` | read |
| 获取指定日期的班单和加班结果 | `gaia YA ATD_FORM_APPLY overtimeGetRecordByDate` | read |
| 申请加班 | `gaia YA ATD_FORM_APPLY overtimeApply` | write |
| 修改加班 | `gaia YA ATD_FORM_APPLY overtimeModify` | write |
| 撤回加班 | `gaia YA ATD_FORM_APPLY overtimeCancel` | destructive |

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中均为 `unspecified`，只有当前对话或可信上游明确提供时才放入 Header，缺失时依据 CLI 原始错误追问，不猜测。

## 参数契约

Discovery 与各方法 `--help` 均未声明必填字段；以下字段状态均为 `unspecified`，不能擅自改成必填或填充空值。

### `overtimeApply` body

`attachmentIds` array（附件列表）、`confirm` boolean（是否提交）、`startDate`/`endDate` string（加班开始/结束日期）、`startDateTime`/`endDateTime` string（加班开始/结束时间）、`scheduleDate` string（排班日期）、`overtimeCode`/`overtimeName` string（加班类型代码/名称）、`overtimeReason` string（加班原因）、`isCompensation`/`isDeductDine` string（是否转调休/扣用餐）、`remark` string（详细说明）。仅传入用户提供或已从可信查询结果确认的字段。

### `overtimeModify` body

除上述字段外，还包括 `formNumber` string（表单号）和 `attachmentOperateType` string（`add` 追加、`modify` 替换、`delete` 删除全部）。修改只发送用户明确要求变更的值，不推测原值。

### `overtimeCancel` body

`formNumber` string、`remark` string（撤回原因描述）、`attachmentIds` array。撤回时不得从未声明的查询接口猜测表单号。

### Read 方法

`overtimeGetAccess`、`overtimeGetreason` 和 `overtimeGetRecordByDate` 的 CLI 契约只声明 Header，没有 body 参数；不要为了“指定日期”自行添加 JSON 字段。`overtimeGetAvailableOvertimeTypeByPeriod` 的 body 仅声明 `startDate`、`endDate`、`startDateTime`、`endDateTime`。

## 日期与时间表达式

日期解析使用 `Asia/Shanghai` 时区，以执行时的当地日期为基准，转换后按接口字段传递 `yyyy-MM-dd`；时间字段按契约描述使用 `yyyy-MM-dd HH:mm`。支持以下自然语言范围：

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

“本周/上周/下周”以周一为起始日；月份按自然月。用户给出明确日期或日期范围时原样解析为同一格式。若只给出日期而未给出时分，不替用户猜测时间；当调用需要时间字段且 CLI/业务错误明确要求时，只追问缺失的开始或结束时间。日期语义有歧义时一次只追问最关键的边界。

## 工作流

### 申请

1. 调用 `overtimeGetAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 检查用户是否已说明 `overtimeCode/overtimeName` 和 `overtimeReason`：
   - 未说明加班类型：收集已确认的开始/结束日期和必要时间，按自然语言范围映射后调用 `overtimeGetAvailableOvertimeTypeByPeriod`，展示返回的真实类型列表。
   - 未说明加班原因：调用 `overtimeGetreason`，展示返回的真实原因列表。
   - 两项都未说明：在具备类型查询所需时间范围后，依次调用上述两个 read 接口并在同一轮回复中展示类型和原因列表；不得自行填充默认值。
3. 用户从列表中明确选择类型和/或原因后，补齐日期/时间及其他字段，展示申请摘要（时间、排班日期、类型、原因、调休/扣餐、说明和附件摘要）并取得明确确认。
4. 确认后调用 `overtimeApply`。`confirm` 仅按用户或可信上游明确给出的值传递，不自行推断。只有返回成功标志时才报告已提交，并记录 `details.formNumber` 供本次对话后续操作。

### 修改

仅在用户明确表达修改意图且已确认 `formNumber` 时调用 `overtimeModify`。若用户未提供新的加班类型或加班原因，先按申请流程分别调用 `overtimeGetAvailableOvertimeTypeByPeriod` 和/或 `overtimeGetreason`，展示真实列表并等待选择；两项均缺少时两类列表都必须获取和展示。展示表单号、待修改字段和影响范围并取得确认；只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与 `details.resultFlag` 等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认 `formNumber` 时调用 `overtimeCancel`。撤回是 destructive 操作，执行前展示表单号、撤回原因和影响并取得二次确认。只有明确成功响应才报告已撤回。

### 辅助查询

`overtimeGetreason` 独立返回可用加班原因；在申请或修改缺少 `overtimeReason` 时必须调用并展示列表，用户已明确原因时无需重复调用。`overtimeGetRecordByDate` 的 CLI 契约没有日期 body，调用时只传可信 Header，不得宣称可以通过自造参数筛选日期。若用户要求按日期范围筛选，优先使用契约支持日期字段的 `overtimeGetAvailableOvertimeTypeByPeriod`；无法满足时说明接口限制并请求明确范围或改用其他已声明能力。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `overtimeGetAccess` 成功响应；可信 `employeeNum`、`tenantCode` Header | `overtimeGetAvailableOvertimeTypeByPeriod`、`overtimeApply`、`overtimeModify`、`overtimeCancel` 同名 Header | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言时间范围 | `overtimeGetAvailableOvertimeTypeByPeriod.startDate/endDate` 及必要的 `startDateTime/endDateTime` | 先按 `Asia/Shanghai` 映射；边界不明确时追问，不能猜测 |
| 可用类型查询返回的真实类型对象（如用户选择的代码/名称） | `overtimeApply.overtimeCode/overtimeName` 或 `overtimeModify.overtimeCode/overtimeName` | 仅在唯一选择并经用户确认后传递；空/多匹配时停止并询问 |
| `overtimeApply.details.formNumber` | 后续 `overtimeModify.formNumber` 或 `overtimeCancel.formNumber` | 仅限同一对话且用户明确确认目标；无表单号或未确认时追问 |
| `overtimeGetreason` 返回的真实原因 | `overtimeApply.overtimeReason` 或 `overtimeModify.overtimeReason` | 仅用户选择/确认后传递；没有跨命令依赖时不调用 |
| `overtimeGetRecordByDate.details` | 无 | 该方法契约未声明可安全映射到其他命令的字段；只读展示原始业务结果 |

## 结果、空结果与错误恢复

- 成功结果按真实响应字段组织，通常包括 `details.formNumber`、`overtimeCode`、`overtimeName`、`startTime`、`endTime`、`scheduleDate`、`resultFlag`、`errorMsg` 等；不根据字段名臆测业务含义。
- 空的 `details` 或空数组不是成功提交。说明实际筛选范围和返回为空的字段，给出可操作的补充方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限或类型为空时继续申请。

## 安全边界与确认

权限、原因、类型和记录查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，scope `download.exception.data.ot`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-15。
- 参考流程：`gaia-wfm-openapi-attendance-leave-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。
