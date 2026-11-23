# gaia-wfm-openapi-attendance-personal-query-la 完整业务流程

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

# Gaia WFM 个人考勤查询

开始工作前遵循 `gaia-cli` 的认证、租户、权限、安全确认和错误恢复规则。只使用 `gaia module resource method` 三段式命令；Gaia CLI 自动注入认证信息，不在本 Skill 中保存或索取 Token、Secret、服务 URL 或其他凭据。

使用本 Skill 前按 `gaia-cli` 执行 `gaia status --json`，核对当前租户的 `release_channel` 为 `LA` 且与本 Skill 的 `metadata.releaseChannel` 匹配；不匹配或无法确认时停止使用，不执行其中的业务命令。

## 当前业务接口契约

本 Skill 维护当前业务范围、方法目录和业务流程，不固化任何方法的请求参数、响应字段、Header、路径或示例值。执行任一方法前，先使用方法表中的“当前契约查询命令”读取该方法的最新 `--help`；帮助不足时，再运行 `gaia api show <module> <resource> --json`。仅按本次读取到的当前业务契约组装命令和解释结果。

如果方法不存在、当前契约无法读取，或当前方法含义已经变化，停止执行并说明原因；不要猜测其他方法替代。

## 适用范围

当用户查询“我的”或当前登录人员的下列信息时使用：

- 打卡原始记录、打卡结果或出勤结果
- 工时记录、排班信息
- 津贴记录、假期余额
- 个人表单或待本人审批的表单

不处理团队、部门、下属或指定他人的查询，也不处理请假/出差/加班的申请、修改、撤回，不修改任何考勤数据。意图无法区分打卡记录、打卡结果、出勤结果或其他类别时，先询问查询类别，不并行猜测多个接口。

## 可用 Gaia CLI 方法

以下方法均为只读查询，不需要额外确认。命令和当前契约查询命令见方法表；参数位置和结果结构运行时读取。

| 用户意图 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 查询打卡原始记录 | `gaia YA ATD_PERSONNAL_QUERY queryAtdRecord` | read | `gaia YA ATD_PERSONNAL_QUERY queryAtdRecord --help` |
| 查询打卡结果 | `gaia YA ATD_PERSONNAL_QUERY queryAtdResult` | read | `gaia YA ATD_PERSONNAL_QUERY queryAtdResult --help` |
| 查询假期余额 | `gaia YA ATD_PERSONNAL_QUERY queryBalance` | read | `gaia YA ATD_PERSONNAL_QUERY queryBalance --help` |
| 查询出勤结果/考勤分类结果 | `gaia YA ATD_PERSONNAL_QUERY queryPaycodeResult` | read | `gaia YA ATD_PERSONNAL_QUERY queryPaycodeResult --help` |
| 查询个人表单 | `gaia YA ATD_PERSONNAL_QUERY queryPersonForms` | read | `gaia YA ATD_PERSONNAL_QUERY queryPersonForms --help` |
| 查询个人排班 | `gaia YA ATD_PERSONNAL_QUERY queryPersonSchedule` | read | `gaia YA ATD_PERSONNAL_QUERY queryPersonSchedule --help` |
| 查询津贴记录 | `gaia YA ATD_PERSONNAL_QUERY queryPersonalAllowance` | read | `gaia YA ATD_PERSONNAL_QUERY queryPersonalAllowance --help` |
| 查询待本人审批表单 | `gaia YA ATD_PERSONNAL_QUERY queryUnApproveForms` | read | `gaia YA ATD_PERSONNAL_QUERY queryUnApproveForms --help` |
| 查询工时记录 | `gaia YA ATD_PERSONNAL_QUERY queryWorkHours` | read | `gaia YA ATD_PERSONNAL_QUERY queryWorkHours --help` |

`Authorization` 始终由 Gaia CLI 注入。其他参数位置和字段只按执行时当前契约决定，不在本 Skill 中固定。

## 日期与范围解析

对支持日期范围的方法，将用户自然语言先转换为当前本地时区 `Asia/Shanghai` 的明确日期，命令中使用 `yyyy-MM-dd`。单日表达的开始和结束日期相同。默认周一为一周起始日，周日为结束日；月份按自然月首日到末日计算。

| 用户表达 | 开始日期 | 结束日期 |
|---|---|---|
| 今天/今日 | 今天 | 今天 |
| 明天 | 今天 + 1 天 | 今天 + 1 天 |
| 昨天 | 今天 - 1 天 | 今天 - 1 天 |
| 前天 | 今天 - 2 天 | 今天 - 2 天 |
| 后天 | 今天 + 2 天 | 今天 + 2 天 |
| 本周/这周 | 本周周一 | 本周周日 |
| 上周 | 上周周一 | 上周周日 |
| 下周 | 下周周一 | 下周周日 |
| 本月/这个月 | 本月 1 日 | 本月最后一日 |
| 上月/上个月 | 上月 1 日 | 上月最后一日 |
| 明确日期（如 2026-09-04） | 该日期 | 该日期 |
| 明确日期范围 | 用户给出的起始日 | 用户给出的结束日 |

也支持“最近 N 天”这类表达：范围包含今天，开始日期为今天往前 `N-1` 天，结束日期为今天。仅给出“7 月”等缺少年份的月份表达可能跨年时，先询问年份。没有可确定的日期或范围时必须追问，不默认本周、最近 7 天或其他范围。校验开始日期不晚于结束日期；若接口契约或服务返回范围限制，保留原始错误并要求用户缩短范围，不自动拆分或放宽条件。

假期余额 `queryBalance` 没有日期字段；不要为了该查询强行附加日期。`queryAtdRecord`、`queryAtdResult`、`queryPaycodeResult`、`queryPersonForms`、`queryPersonSchedule`、`queryUnApproveForms` 的日期字段在 Discovery 中为 `unspecified`，用户提供范围时按上述规则传入；用户未提供时不擅自填充。

## 工作流

1. 识别查询类别并确认查询对象是当前用户；类别不清时只追问一个最关键的问题。
2. 对当前方法支持的日期范围解析用户表达，展示将使用的明确日期范围；日期缺失或有歧义时先追问。
3. 读取所选方法的当前 `--help`，按当前契约确定参数位置和字段；不使用 Skill 中的旧字段或示例组装请求。
4. 执行对应的只读命令。用户一次明确要求多个类别时，按类别分别执行并合并真实结果；一个方法失败时保留已成功结果并明确说明部分失败。
5. 依据当前响应和契约确认的语义展示结果；不从字段名猜测金额、时长、状态或分页含义。

## 跨命令业务顺序

保留本 Skill 规定的权限检查、辅助查询、用户选择、确认和提交顺序。前一步的结果只能在当前对话中真实返回且用户确认后，按下一步方法本次读取到的契约映射；不在 Skill 中固定响应字段名、路径或目标参数名。前置方法失败、结果为空或当前契约无法读取时停止后续调用。

## 结果、空结果与错误恢复

- 成功：说明查询类别和实际日期范围，按 响应内容中真实字段整理记录；不从字段名猜测金额、时长或状态含义。
- 空结果：说明实际筛选条件和日期范围内没有记录，不扩大范围、不改员工、不重复调用。
- 参数错误：保留 CLI 返回的具体字段和消息，只追问缺失或格式错误的字段；用户修正后再执行。
- 未登录或 401：遵循 `gaia-cli` 的 登录恢复流程，恢复后仅重试原命令一次；仍失败则停止并报告原始错误。
- 403 或权限不足：展示 CLI 返回的 scope、resource 和提示信息，不申请权限、不绕过检查。
- 业务错误、网络错误或非零退出：保留 `code/message/reason/响应内容`。除认证恢复外不自动更换方法、日期、租户或员工。

所有方法都是 `read` 操作，无需执行前确认；`--debug` 仅用于排障，因其可能输出完整 Token 和请求细节，不得写入 Skill 或展示给用户。

## 统一权限与排障输出

权限错误按证据区分三层：租户未获得 OpenAPI 授权时提示联系租户管理员；当前登录账号未获得业务接口权限时提示联系公司管理员或业务负责人；前两层通过后接口仍返回 403 时，标记为接口自身业务或数据限制，携带任务 ID 联系 CLI 业务负责人排查。无法从响应确认具体层级时，不武断归因，保留原始诊断和任务 ID。

缺少必填参数时只询问缺失字段；认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复；业务接口 4xx/5xx、网络错误、解析失败或未知异常时停止依赖步骤，说明具体操作、接口错误信息和下一步。写操作超时、连接中断或最终状态无法确认时报告“提交结果未知”，不自动重试或重复提交。普通回复先给问题摘要、已确认事实、用户动作和任务 ID；用户明确要求完整链路时才使用 `gaia logs --info` 整理 stages、请求方法/路径、脱敏参数、响应、权限判断、重试关系和 Correlation/Trace ID，不原样转发日志 JSON。业务流程不得使用 `--debug`，不得展示 Token、密码、Secret 或服务地址。

## 契约来源与核验

- 运行时契约来源：对应方法的 `--help`，必要时补充 `gaia api show <module> <resource> --json`。
- 核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-04。
- 已核验：`gaia commands list --module YA --json`、9 个方法的 `gaia api check YA ATD_PERSONNAL_QUERY <method>` 及对应 `--help`。
- Discovery 未声明的字段状态保持 `unspecified`；未在本文件中保存 Token、Secret、真实 URL 或凭据。

## 契约适用说明

本次调整仅校正WorkBuddy Connector 适配，未在线调用业务接口。正文中的历史核验记录不代表当前租户的最新契约；首次使用时，在入口模式和 `release_channel=LA` 检查通过后，通过对应方法的 `--help` 或 `gaia api show` 核对当前 Discovery。出现差异时停止使用旧字段并报告差异，不猜测替代接口。
