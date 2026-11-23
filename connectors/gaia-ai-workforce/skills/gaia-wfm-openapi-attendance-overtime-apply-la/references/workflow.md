# gaia-wfm-openapi-attendance-overtime-apply-la 完整业务流程

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

# 加班申请流程（LA）

本 Skill 仅通过 Gaia CLI 的 `YA ATD_FORM_APPLY` 命令处理当前登录人员的加班业务。执行前先阅读并遵循 `gaia-cli` 的认证、租户、权限、安全确认和错误恢复规则。不得使用 curl、wget、SDK、直接 URL 或自建 HTTP 客户端，也不得索取或写入 Token、Secret、私钥等凭据。

使用本 Skill 前按 `gaia-cli` 执行 `gaia status --json`，核对当前租户的 `release_channel` 为 `LA` 且与本 Skill 的 `metadata.releaseChannel` 匹配；不匹配或无法确认时停止使用，不执行其中的业务命令。

## 当前业务接口契约

本 Skill 维护当前业务范围、方法目录和业务流程，不固化任何方法的请求参数、响应字段、Header、路径或示例值。执行任一方法前，先使用方法表中的“当前契约查询命令”读取该方法的最新 `--help`；帮助不足时，再运行 `gaia api show <module> <resource> --json`。仅按本次读取到的当前业务契约组装命令和解释结果。

如果方法不存在、当前契约无法读取，或当前方法含义已经变化，停止执行并说明原因；不要猜测其他方法替代。

## 适用场景

- 申请本人加班：先检查权限；只要用户未说明加班类型或加班原因，就调用对应列表接口并展示真实选项；用户选择并确认后提交申请。
- 修改本人已有加班单：用户必须提供或在当前对话中确认表单号；只要待修改内容缺少加班类型或加班原因，也先获取并展示对应列表，再提交变更。
- 撤回本人加班单：用户必须提供或确认表单号；撤回属于破坏性操作，执行前二次确认。
- 查询辅助信息：获取加班原因、时间范围内的可用加班类型，或调用契约声明的加班记录方法。

不处理他人的加班、审批代办、附件上传/下载、权限授予，或本表未列出的命令。

## Gaia CLI 命令

| 用途 | 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 获取加班权限 | `gaia YA ATD_FORM_APPLY overtimeGetAccess` | read | `gaia YA ATD_FORM_APPLY overtimeGetAccess --help` |
| 获取时间范围内可用加班类型 | `gaia YA ATD_FORM_APPLY overtimeGetAvailableOvertimeTypeByPeriod` | read | `gaia YA ATD_FORM_APPLY overtimeGetAvailableOvertimeTypeByPeriod --help` |
| 获取加班原因 | `gaia YA ATD_FORM_APPLY overtimeGetreason` | read | `gaia YA ATD_FORM_APPLY overtimeGetreason --help` |
| 获取指定日期的班单和加班结果 | `gaia YA ATD_FORM_APPLY overtimeGetRecordByDate` | read | `gaia YA ATD_FORM_APPLY overtimeGetRecordByDate --help` |
| 申请加班 | `gaia YA ATD_FORM_APPLY overtimeApply` | write | `gaia YA ATD_FORM_APPLY overtimeApply --help` |
| 修改加班 | `gaia YA ATD_FORM_APPLY overtimeModify` | write | `gaia YA ATD_FORM_APPLY overtimeModify --help` |
| 撤回加班 | `gaia YA ATD_FORM_APPLY overtimeCancel` | destructive | `gaia YA ATD_FORM_APPLY overtimeCancel --help` |

调用时按当前方法 `--help`/Discovery 声明的参数位置和字段组装；Authorization 由 CLI 自动注入。

## 运行时契约读取

本 Skill 不保存各方法的请求参数、响应字段、Header、路径、枚举或示例值。执行方法前必须使用方法表中的当前契约查询命令读取最新定义，再根据当前结果决定参数位置、必填项、请求体、Header、响应解释和分页方式；读取失败或方法含义变化时停止并说明原因，不猜测替代方法。

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
## 工作流

### 申请
1. 调用 `overtimeGetAccess`，仅在成功且未拒绝时继续；权限失败、认证失败、网络错误或业务错误均停止。
2. 检查用户是否已说明加班类型、加班原因和当前方法契约要求的其他业务信息：
3. 用户从列表中明确选择类型和/或原因后，补齐日期/时间及其他字段，展示申请摘要（时间、排班日期、类型、原因、调休/扣餐、说明和附件摘要）并取得明确确认。
4. 确认后调用 `overtimeApply`。当前方法契约要求的字段仅按用户或可信上游明确给出的值传递，不自行推断。只有返回成功标志时才报告已提交，并记录实际返回的业务标识供本次对话后续操作。

   - 未说明加班类型：收集已确认的开始/结束日期和必要时间，按自然语言范围映射后调用 `overtimeGetAvailableOvertimeTypeByPeriod`，展示返回的真实类型列表。
   - 未说明加班原因：调用 `overtimeGetreason`，展示返回的真实原因列表。
   - 两项都未说明：在具备类型查询所需时间范围后，依次调用上述两个 read 接口并在同一轮回复中展示类型和原因列表；不得自行填充默认值。

### 修改

仅在用户明确表达修改意图且已确认表单号时调用 `overtimeModify`。若用户未提供新的加班类型或加班原因，先按申请流程分别调用 `overtimeGetAvailableOvertimeTypeByPeriod` 和/或 `overtimeGetreason`，展示真实列表并等待选择；两项均缺少时两类列表都必须获取和展示。展示表单号、待修改字段和影响范围并取得确认；只传入用户确认的新值及契约字段。成功判定依据顶层 `code`、`message`、`reason` 与响应中的结果标志等真实响应，不因出现表单号就宣称成功。

### 撤回

仅在用户明确表达撤回意图且已确认表单号时调用 `overtimeCancel`。撤回是 destructive 操作，执行前展示表单号、撤回原因和影响并取得二次确认。只有明确成功响应才报告已撤回。

### 辅助查询

`overtimeGetreason` 独立返回可用加班原因；在申请或修改缺少加班原因时必须调用并展示列表，用户已明确原因时无需重复调用。`overtimeGetRecordByDate` 是否支持日期筛选以及参数位置以运行时契约为准，不得自造参数；无法满足用户范围时说明接口限制或改用其他已声明能力。

## 跨命令业务顺序

保留本 Skill 规定的权限检查、辅助查询、用户选择、确认和提交顺序。前一步的结果只能在当前对话中真实返回且用户确认后，按下一步方法本次读取到的契约映射；不在 Skill 中固定响应字段名、路径或目标参数名。前置方法失败、结果为空或当前契约无法读取时停止后续调用。

## 结果、空结果与错误恢复

- 成功结果按当前响应中真实返回且当前契约确认的业务内容组织。
- 空的响应内容或空数组不是成功提交。说明实际筛选范围和返回为空的字段，给出可操作的补充方向，不自动放宽范围或重试。
- 参数错误：保留 CLI 的字段级错误，只追问对应缺失/非法字段；用户修正后再执行原命令。
- 401/认证失败：按 `gaia-cli` 的认证恢复流程恢复登录或刷新状态后，仅重试原命令一次；仍失败则停止。
- 权限拒绝：展示 CLI 返回的 scope/诊断信息，不绕过检查或代为申请权限。
- 4xx/5xx、业务错误或服务异常：展示可用的 HTTP 状态、`code`、`message`、`reason` 和响应中的错误信息，说明下一步。写操作超时、502/504 或连接中断时，标记为“提交结果未知”，不得自动重试或重复写入；请用户先核对考勤系统记录。
- 多命令流程中，前置步骤失败立即停止；不要在权限或类型为空时继续申请。

## 安全边界与确认

权限、原因、类型和记录查询为 read，无需额外确认；申请和修改为 write，提交前必须展示摘要并明确确认；撤回为 destructive，必须展示目标和影响并二次确认。不得输出凭据、服务 URL 或未被 CLI 契约确认的字段。

## 契约来源

- 运行时契约来源：对应方法的 `--help`，必要时补充 `gaia api show <module> <resource> --json`。
- 最近核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-15。
- 参考流程：`gaia-wfm-openapi-attendance-leave-apply-la/SKILL.md` 与 `gaia-cli`。

## 统一权限与排障输出

权限错误按证据区分三层：租户未获得 OpenAPI 授权时提示联系租户管理员；当前登录账号未获得业务接口权限时提示联系公司管理员或业务负责人；前两层通过后接口仍返回 403 时，标记为接口自身业务或数据限制，携带任务 ID 联系 CLI 业务负责人排查。无法从响应确认具体层级时，不武断归因，保留原始诊断和任务 ID。

缺少必填参数时只询问缺失字段；认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复；业务接口 4xx/5xx、网络错误、解析失败或未知异常时停止依赖步骤，说明具体操作、接口错误信息和下一步。写操作超时、连接中断或最终状态无法确认时报告“提交结果未知”，不自动重试或重复提交。普通回复先给问题摘要、已确认事实、用户动作和任务 ID；用户明确要求完整链路时才使用 `gaia logs --info` 整理 stages、请求方法/路径、脱敏参数、响应、权限判断、重试关系和 Correlation/Trace ID，不原样转发日志 JSON。业务流程不得使用 `--debug`，不得展示 Token、密码、Secret 或服务地址。

## 契约适用说明

本次调整仅校正WorkBuddy Connector 适配，未在线调用业务接口。正文中的历史核验记录不代表当前租户的最新契约；首次使用时，在入口模式和 `release_channel=LA` 检查通过后，通过对应方法的 `--help` 或 `gaia api show` 核对当前 Discovery。出现差异时停止使用旧字段并报告差异，不猜测替代接口。
