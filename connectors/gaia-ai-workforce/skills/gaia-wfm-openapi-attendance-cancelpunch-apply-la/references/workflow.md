# gaia-wfm-openapi-attendance-cancelpunch-apply-la 完整业务流程

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

# 撤销补卡申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令，对当前登录人员已有的补卡记录发起撤销补卡申请并生成撤销补卡单。它不是撤回补卡申请单的流程，不得调用或复用 `gaia-wfm-openapi-attendance-replacepunch-apply-la` 的 `cancelPunch`。执行前先阅读并遵循 `gaia-cli` 的认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

使用本 Skill 前按 `gaia-cli` 执行 `gaia status --json`，核对当前租户的 `release_channel` 为 `LA` 且与本 Skill 的 `metadata.releaseChannel` 匹配；不匹配或无法确认时停止使用，不执行其中的业务命令。

## 当前业务接口契约

本 Skill 维护当前业务范围、方法目录和业务流程，不固化任何方法的请求参数、响应字段、Header、路径或示例值。执行任一方法前，先使用方法表中的“当前契约查询命令”读取该方法的最新 `--help`；帮助不足时，再运行 `gaia api show <module> <resource> --json`。仅按本次读取到的当前业务契约组装命令和解释结果。

如果方法不存在、当前契约无法读取，或当前方法含义已经变化，停止执行并说明原因；不要猜测其他方法替代。

## 适用场景

- 申请本人撤销补卡：先检查撤销补卡权限，再按日期范围查询审批中的撤销补卡单和可选补卡记录；用户选择已有补卡记录并确认后，提交新的撤销补卡申请，不要求表单号。
- 撤回本人已提交的撤销补卡单：用户明确提供或确认已生成撤销补卡单的表单号后，二次确认并调用专用撤回命令。
- 查询撤销补卡候选：按用户给出的日期或日期范围展示真实的撤销补卡单和可选补卡记录；用户可使用日期、时间、原因等非 ID 字段选择目标。

不处理普通补卡申请、修改或撤回普通补卡单，不处理他人的补卡、审批、附件上传/下载、权限授予，或本 Skill 未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取撤销补卡权限 | `gaia YA ATD_FORM_APPLY getCancelPunchAccess` | read | `gaia YA ATD_FORM_APPLY getCancelPunchAccess --help` |
| 获取日期范围内审批中的撤销补卡单和可选补卡记录 | `gaia YA ATD_FORM_APPLY getCancelPunchAvailableRecords` | read | `gaia YA ATD_FORM_APPLY getCancelPunchAvailableRecords --help` |
| 基于已有补卡记录申请撤销补卡 | `gaia YA ATD_FORM_APPLY applyCancelPunch` | write | `gaia YA ATD_FORM_APPLY applyCancelPunch --help` |
| 撤回已提交的撤销补卡单 | `gaia YA ATD_FORM_APPLY cancelCancelPunch` | destructive | `gaia YA ATD_FORM_APPLY cancelCancelPunch --help` |

以下相似命令不属于本 Skill：`getAccess`、`getFormAndRecord`、`applyPunch`、`modifyPunch`、`cancelPunch` 属于普通补卡流程。`cancelCancelPunch` 属于本 Skill，但只用于撤回已提交的撤销补卡单，不能替代 `applyCancelPunch`。

调用时按当前方法 `--help`/Discovery 声明的参数位置和字段组装；Authorization 由 CLI 自动注入。

## 运行时契约读取

本 Skill 不保存各方法的请求参数、响应字段、Header、路径、枚举或示例值。执行方法前必须使用方法表中的当前契约查询命令读取最新定义，再根据当前结果决定参数位置、必填项、请求体、Header、响应解释和分页方式；读取失败或方法含义变化时停止并说明原因，不猜测替代方法。

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
## 工作流

### 查询可撤销补卡记录

1. 调用 `getCancelPunchAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 收集查询日期范围，将用户明确的自然语言日期解析为当前方法契约要求的范围；缺少或有歧义时先追问日期。
3. 调用 `getCancelPunchAvailableRecords`，展示真实返回的候选记录并标明实际查询范围。查询结果不得展示记录标识、内部表单标识 或其他技术标识；使用日期、时间、原因等业务信息区分候选。

### 申请撤销补卡
1. 按“查询可撤销补卡记录”流程获取候选；用户必须明确选择一条或多条已有补卡记录。不得要求用户提供表单号。
2. 从用户选择的真实候选中，按当前方法契约内部映射目标标识；候选无法提供可用标识时，按当前契约允许的业务字段匹配，不向用户索取技术 ID。
3. 收集并确认撤销申请所需的日期、时间、原因、说明和附件等业务信息，具体字段和位置按当前方法契约读取；未确认的信息不猜测、不补齐。
### 撤回已提交的撤销补卡单
1. 仅在用户明确表达“撤回撤销补卡单”意图，并提供或确认已生成的目标表单号时执行；不能把普通补卡的 `cancelPunch` 当作替代命令。
2. 展示撤销补卡单表单号和撤回影响，取得二次确认。
3. 确认后调用 `cancelCancelPunch`，请求体只传当前方法契约声明的字段。只有明确成功响应才报告已撤回；超时或连接中断时标记为结果未知，不自动重试。


## 跨命令业务顺序

保留本 Skill 规定的权限检查、辅助查询、用户选择、确认和提交顺序。前一步的结果只能在当前对话中真实返回且用户确认后，按下一步方法本次读取到的契约映射；不在 Skill 中固定响应字段名、路径或目标参数名。前置方法失败、结果为空或当前契约无法读取时停止后续调用。

## 结果、空结果与错误恢复

- 查询结果按真实的 响应中的表单列表和响应中的记录列表 展示，但用户可见内容必须过滤 记录标识、内部表单标识 和其他技术标识；不猜测列表项未声明字段的含义。
- 空的响应内容、`表单列表` 或 `记录列表` 不是成功提交。说明实际日期范围和为空的列表，给出补充明确日期或重新选择已有补卡记录的方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和响应中的错误信息，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复提交；请用户先核对考勤系统是否已生成撤销补卡单。
- 查询前置步骤失败立即停止；不要在权限、目标补卡记录或提交确认未满足时继续申请。

## Operation Risk and Confirmation Requirements

Operation risk: `applyCancelPunch` is a write operation that creates a new cancel-punch application against an existing punch record; `cancelCancelPunch` is a destructive operation that withdraws an already submitted cancel-punch application. Neither command withdraws a normal punch application. Confirmation requirements: for `applyCancelPunch`, show the selected punch date/time, reason, application date range, and impact, then obtain one explicit submission 确认信息ation; for `cancelCancelPunch`, show the 确认信息ed cancel-punch form number and impact, then obtain a second explicit 确认信息ation immediately before execution. Permission and candidate queries are read-only and need no extra 确认信息ation. Never expose record IDs or internal record IDs to the user.

## 契约来源

- 运行时契约来源：对应方法的 `--help`，必要时补充 `gaia api show <module> <resource> --json`。
- 已核验方法：`getCancelPunchAccess`、`getCancelPunchAvailableRecords`、`applyCancelPunch`、`cancelCancelPunch`；明确排除普通补卡的 `cancelPunch`。
- 参考流程：`gaia-wfm-openapi-attendance-cancelleave-apply-la/SKILL.md` 与 `gaia-cli`。

## 统一权限与排障输出

权限错误按证据区分三层：租户未获得 OpenAPI 授权时提示联系租户管理员；当前登录账号未获得业务接口权限时提示联系公司管理员或业务负责人；前两层通过后接口仍返回 403 时，标记为接口自身业务或数据限制，携带任务 ID 联系 CLI 业务负责人排查。无法从响应确认具体层级时，不武断归因，保留原始诊断和任务 ID。

缺少必填参数时只询问缺失字段；认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复；业务接口 4xx/5xx、网络错误、解析失败或未知异常时停止依赖步骤，说明具体操作、接口错误信息和下一步。写操作超时、连接中断或最终状态无法确认时报告“提交结果未知”，不自动重试或重复提交。普通回复先给问题摘要、已确认事实、用户动作和任务 ID；用户明确要求完整链路时才使用 `gaia logs --info` 整理 stages、请求方法/路径、脱敏参数、响应、权限判断、重试关系和 Correlation/Trace ID，不原样转发日志 JSON。业务流程不得使用 `--debug`，不得展示 Token、密码、Secret 或服务地址。

## 契约适用说明

本次调整仅校正WorkBuddy Connector 适配，未在线调用业务接口。正文中的历史核验记录不代表当前租户的最新契约；首次使用时，在入口模式和 `release_channel=LA` 检查通过后，通过对应方法的 `--help` 或 `gaia api show` 核对当前 Discovery。出现差异时停止使用旧字段并报告差异，不猜测替代接口。
