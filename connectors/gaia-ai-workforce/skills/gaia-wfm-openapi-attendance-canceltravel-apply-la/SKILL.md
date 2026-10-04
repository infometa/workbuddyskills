---
name: gaia-wfm-openapi-attendance-canceltravel-apply-la
description: 处理当前登录用户的销出差申请、销出差修改和销出差撤回，并按出差日期范围查询可销出差的出差记录。用户提出“我要销出差”“申请销出差”“修改销出差单”“撤回销出差”“查询本周可销出差记录”等本人销出差流程请求时使用。
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# 销出差申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的销出差业务。执行前先阅读并遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

## 适用场景

- 申请本人销出差：先检查销出差权限，再按日期范围获取可销出差的出差记录；用户选择记录并确认后提交申请。
- 修改本人已有销出差单：用户必须提供或在当前对话中确认 `formNumber`，同时确认要修改的记录、日期范围和说明后提交修改。
- 撤回本人销出差单：用户必须提供或确认 `formNumber`；撤回属于破坏性操作，执行前二次确认。
- 查询辅助信息：按日期范围查询当前用户可销出差的出差记录。

不处理他人的销出差、普通出差申请或撤回、销出差审批、附件传输、权限授予，或本 Skill 未列出的命令。普通出差的 `travelCancel` 不属于本 Skill。

## Gaia CLI 命令

| 用途 | 命令 | 类型 |
|---|---|---|
| 获取销出差权限 | `gaia YA ATD_FORM_APPLY getCancelTravelAccess` | read |
| 获取日期范围内可销出差的出差记录 | `gaia YA ATD_FORM_APPLY getTravelRecordList` | read |
| 申请销出差 | `gaia YA ATD_FORM_APPLY applyCancelTravel` | write |
| 修改销出差 | `gaia YA ATD_FORM_APPLY modifyCancelTravel` | write |
| 撤回销出差 | `gaia YA ATD_FORM_APPLY cancel` | destructive |

调用时仅使用 CLI 支持的 `--header JSON` 和 `--body JSON`。`Authorization` 由 CLI 自动注入且不可覆盖；`employeeNum`、`tenantCode` 在 Discovery 中为 `unspecified`，`language` 仅在 `getTravelRecordList` 中声明。只有当前对话或可信上游明确提供时才传入，缺失时依据 CLI 原始错误追问，不猜测。`cancel` 只声明 `tenantCode` Header，不向它传入 `employeeNum` 或 `language`。

## 参数契约

Discovery 与各方法 `--help` 均未声明必填字段；以下字段状态均为 `unspecified`，不能擅自改成必填或填充空值。

### `getTravelRecordList` body

`startDate` string（开始日期）和 `endDate` string（结束日期）。响应 `details` 是对象数组，表示该范围内可销出差的出差记录；数组项未声明子字段，只展示真实返回内容，不预设字段结构。

### `applyCancelTravel` body

`confirm` boolean（是否提交）、`startDate`/`endDate` string（出差开始/结束日期）、`recordId` array（出差记录 ID 列表）和 `remark` string（详细说明）。用户先选择业务记录，系统仅在内部传入对应的真实 `recordId`、日期范围和说明；不要求用户提供或确认记录 ID。

### `modifyCancelTravel` body

除申请字段外，还包括 `formNumber` string（表单号）。修改只发送用户明确要求变更的新值，不推测原值。

### `cancel` body

仅声明 `formNumber` string（表单号）。撤回时不要自行添加日期、记录 ID、原因、说明或确认字段。

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

“本周/上周/下周”以周一为起始日；月份按自然月。用户给出明确日期或日期范围时解析为同一格式。销出差接口只声明日期字段，不声明时间字段；不自行添加时间或猜测时分。日期语义有歧义时，一次只追问最关键的日期边界。

## 工作流

### 查询可销出差记录

1. 调用 `getCancelTravelAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集查询日期范围，将“明天、昨天、前天、后天、上周、本周、下周、本月、上月”等表达映射为 `startDate/endDate`；缺少或有歧义时先追问日期。
3. 调用 `getTravelRecordList`，展示返回的真实记录数组并标明实际日期范围。面向用户展示时必须隐藏 `recordId`，不得输出或复述记录 ID；可用日期、出差类型、时段等非 ID 字段区分候选。不得从未声明字段推断记录 ID、表单号或状态；若用户要执行销出差，要求其从真实结果中明确选择目标记录。

### 申请销出差

1. 按“查询可销出差记录”流程取得并展示候选记录；用户必须使用日期、出差类型、时段等非 ID 业务字段明确选择一个或多个记录，并确认销出差日期范围及 `remark`（如有）。选中后仅在内部映射真实 `recordId`。
2. 展示申请摘要（销出差开始/结束日期、选中记录的业务字段、说明）并取得明确确认；摘要和确认提示不得展示 `recordId` 或任何记录 ID。
3. 确认后调用 `applyCancelTravel`。`confirm` 仅按用户或可信上游明确给出的值传递，不自行推断。只有返回明确成功标志时才报告已提交，并记录真实返回的 `details.formNumber`，供本次对话后续修改或撤回时作为候选目标。

### 修改

仅在用户明确表达修改意图且已确认 `formNumber` 时调用 `modifyCancelTravel`。若用户没有表单号但给出日期范围，可先调用 `getTravelRecordList` 展示候选出差记录；查询契约未声明记录项结构，只有真实结果明确提供可用业务字段且用户选择后才能使用。展示表单号、待修改的日期范围、记录业务字段和说明并取得确认；修改摘要和确认提示不得展示 `recordId` 或任何记录 ID。只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与 `details.resultFlag` 等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认 `formNumber` 时调用 `cancel`。撤回是 destructive 操作，执行前展示表单号和影响并取得二次确认；该方法只传入契约声明的 `tenantCode` Header（如已确认）和 `formNumber` body。只有明确成功响应才报告已撤回。

## 跨命令字段映射

| 来源命令/字段 | 目标命令/字段 | 前置条件与失败策略 |
|---|---|---|
| `getCancelTravelAccess` 成功响应；可信 `employeeNum`、`tenantCode`、`language` Header | `getTravelRecordList`、`applyCancelTravel`、`modifyCancelTravel` 同名 Header；`cancel` 仅接收 `tenantCode` | 仅复用对话或可信上游已确认的值；缺失时追问，权限失败则停止 |
| 用户确认的自然语言日期范围 | `getTravelRecordList.startDate/endDate` | 按 `Asia/Shanghai` 映射为 `yyyy-MM-dd`；边界不明确时追问，不能猜测 |
| `getTravelRecordList.details` 的真实出差记录 | `applyCancelTravel.recordId` 或 `modifyCancelTravel.recordId` | 用户先用非 ID 业务字段选择候选，随后仅在内部映射真实 `recordId`；空或多候选未选时停止并询问，禁止向用户回显记录 ID |
| 用户确认的销出差日期范围 | `applyCancelTravel.startDate/endDate` 或 `modifyCancelTravel.startDate/endDate` | 与查询使用相同的已确认日期值，不重新解释或改写 |
| `applyCancelTravel.details.formNumber` | 后续 `modifyCancelTravel.formNumber` 或 `cancel.formNumber` | 仅限同一对话且用户明确确认目标；未返回或未确认时追问 |
| 用户另行提供并确认的 `formNumber` | `modifyCancelTravel.formNumber` 或 `cancel.formNumber` | 不得从未声明字段或模糊结果猜测 |

## 结果、空结果与错误恢复

- 查询结果按真实 `details` 数组展示，并说明实际日期范围；用户可见内容必须过滤 `recordId`、内部记录 ID 和其他技术标识，不猜测记录项未声明字段的含义。
- 申请/修改响应 `details` 可包含 `cancelTravelDetails`（其中可能有 `cancelTravelRemark`、`cancelTravelTimeRange`、`cancelTravelType`、`scheduleDate`）、`cancelTravelSign`、`formNumber`、`remark`、`resultFlag` 和 `errorMsg`；撤回响应 `details` 可包含 `formNumber`、`resultFlag` 和 `errorMsg`。只展示实际返回内容，不根据描述中的其他业务术语改写字段含义。
- 空的 `details` 或记录数组不是成功提交。说明实际日期范围和为空的字段，给出补充明确日期或重新选择记录的方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的 WorkBuddy 认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和 `details.errorMsg`，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限、内部目标记录或表单号为空时继续写操作。记录 ID 只作为 CLI 请求字段使用，不向用户回显。

## 安全边界与确认

权限和记录查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。查询结果、申请/修改摘要和确认提示不得展示 `recordId`、内部记录 ID 或其他技术标识。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- CLI 契约来源：Gaia CLI 的 `gaia commands list --module YA --json`、各方法 `--help` 和在线 Discovery 输出。
- 在线 Discovery：`gaia api show YA ATD_FORM_APPLY --json`，YA `v1`，scope `cancelTravel.apply`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-16。
- 参考流程：`gaia-wfm-openapi-attendance-cancelleave-apply-la/SKILL.md` 与 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md)。普通出差流程不属于本连接器当前打包范围。
