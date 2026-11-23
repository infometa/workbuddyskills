# gaia-wfm-openapi-attendance-team-query-la 完整业务流程

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

# Gaia WFM 团队考勤查询

开始前遵循 `gaia-cli` 的认证、租户、权限、安全确认和错误恢复规则。仅使用 `gaia <module> <resource> <method>` 三段式命令和该命令支持的 `--body`、`--header` 参数；Gaia CLI 自动注入认证信息，绝不索取、显示或保存 Token、Secret、密码或业务服务 URL。

使用本 Skill 前按 `gaia-cli` 执行 `gaia status --json`，核对当前租户的 `release_channel` 为 `LA` 且与本 Skill 的 `metadata.releaseChannel` 匹配；不匹配或无法确认时停止使用，不执行其中的业务命令。

## 当前业务接口契约

本 Skill 维护当前业务范围、方法目录和业务流程，不固化任何方法的请求参数、响应字段、Header、路径或示例值。执行任一方法前，先使用方法表中的“当前契约查询命令”读取该方法的最新 `--help`；帮助不足时，再运行 `gaia api show <module> <resource> --json`。仅按本次读取到的当前业务契约组装命令和解释结果。

如果方法不存在、当前契约无法读取，或当前方法含义已经变化，停止执行并说明原因；不要猜测其他方法替代。

## 适用范围

当当前用户查询自己可见的团队、下属、部门成员或指定团队成员的下列信息时使用：

- 考勤记录，或其中的请假、加班、异常、出差、工时、津贴分类。
- 考勤卡或设备卡。
- 假期累计数据。
- 团队成员排班。

不用于当前用户本人的个人考勤查询，不申请、修改、撤回或审批任何考勤表单，不授予权限，也不调用本 Skill 未列出的命令推测团队、人员或组织数据。若用户没有说明要查询哪一类数据，只追问考勤记录、累计、考勤卡、设备卡或排班中的一个最关键类别。

## 触发场景

以下表达均可触发本 Skill，日期和筛选条件按用户原话继续解析：

- “查一下团队明天的考勤记录”“看看下属上周有没有考勤异常”。
- “查询本月研发部成员的设备卡”“看张三昨天的考勤卡”。
- “查王五上月的年假累计”“团队本周的假期累计数据”。
- “查看下周团队排班”“看看运营组本月排班”。

用户请求“我的考勤”“我的工时”“我要请假”或“审批表单”时不使用本 Skill，应转交相应的个人查询、申请或审批能力。用户同时明确提出多种团队数据时，分别查询这些类别并汇总真实结果。

## 可用 Gaia CLI 方法

所有方法均为 `read` 操作，无需执行前确认。每一种数据查询必须先调用同类权限方法；权限调用失败或返回明确拒绝时，停止该类别的查询，不调用相应数据方法。

| 查询类别 | 权限命令 | 数据命令 | 当前契约查询命令 |
|---|---|---|---|
| 考勤记录 | `gaia YA ATD_TEAM_QUERY getrecordaccess` | `gaia YA ATD_TEAM_QUERY getattendancelist` | 权限：`gaia YA ATD_TEAM_QUERY getrecordaccess --help`<br>数据：`gaia YA ATD_TEAM_QUERY getattendancelist --help` |
| 累计数据 | `gaia YA ATD_TEAM_QUERY tbGetAccess` | `gaia YA ATD_TEAM_QUERY getbalancelist` | 权限：`gaia YA ATD_TEAM_QUERY tbGetAccess --help`<br>数据：`gaia YA ATD_TEAM_QUERY getbalancelist --help` |
| 考勤卡 | `gaia YA ATD_TEAM_QUERY gettimecardaccess` | `gaia YA ATD_TEAM_QUERY getcardlist` | 权限：`gaia YA ATD_TEAM_QUERY gettimecardaccess --help`<br>数据：`gaia YA ATD_TEAM_QUERY getcardlist --help` |
| 设备卡 | `gaia YA ATD_TEAM_QUERY getdeviceaccess` | `gaia YA ATD_TEAM_QUERY getdevicecardlist` | 权限：`gaia YA ATD_TEAM_QUERY getdeviceaccess --help`<br>数据：`gaia YA ATD_TEAM_QUERY getdevicecardlist --help` |
| 排班 | `gaia YA ATD_TEAM_QUERY tsGetAccess` | `gaia YA ATD_TEAM_QUERY tsGetScheduleList` | 权限：`gaia YA ATD_TEAM_QUERY tsGetAccess --help`<br>数据：`gaia YA ATD_TEAM_QUERY tsGetScheduleList --help` |

Header、Body、分页和响应结构均以执行时读取到的当前契约为准，不在本 Skill 中固定。

## 操作风险与确认条件

| 命令 | 操作类型 | 风险来源 | 确认条件 |
|---|---|---|---|
| `getrecordaccess`、`gettimecardaccess`、`getdeviceaccess`、`tbGetAccess`、`tsGetAccess` | read | 仅读取当前用户的团队查询权限状态 | 无需额外确认 |
| `getattendancelist`、`getbalancelist`、`getcardlist`、`getdevicecardlist`、`tsGetScheduleList` | read | 仅读取当前用户有权访问的团队考勤数据 | 无需额外确认 |

本 Skill 没有 write 或 destructive 命令。禁止借由权限查询修改授权、申请权限或改变任何考勤记录。

## 日期与范围解析

对于支持 `开始日期`、`结束日期` 的五个数据方法，先按执行时的 `Asia/Shanghai` 时区将用户的自然语言映射为 `yyyy-MM-dd`。单日表达的开始和结束日期相同；一周从周一开始，到周日结束；月份使用自然月。

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
| 明确日期 | 该日期 | 该日期 |
| 明确日期范围 | 用户提供的开始日期 | 用户提供的结束日期 |
| 最近 N 天 | 包含今天在内往前 N-1 天 | 今天 |

用户表达明确日期或范围时，执行前说明解析后的日期范围。日期字段未被 Discovery 声明为必填：用户未提供日期时不默认本周、最近 7 天或其他范围，而是省略日期字段；只有 CLI 或服务明确要求时才追问。开始日期晚于结束日期时，要求用户更正；接口若返回范围限制，保留原始错误并要求用户缩短范围，不自动拆分或扩大查询。仅给出可能跨年的月份（例如“7 月”）时，先确认年份。

## 筛选与分页边界

用户明确提供的日期、人员、组织、类别和分页意图，均在读取当前方法契约后按该方法实际支持的字段传递。不要把旧版本字段名、默认值、枚举或分页结构写死；契约未声明或当前命令拒绝的字段不猜测、不替换。

## 分页规则

分页字段、默认值和继续读取下一页的方式以执行时对应方法的 `--help`/Discovery 为准。用户未明确分页时遵循当前方法的真实默认行为；无法确认时不擅自补值。

## 查询工作流

1. 确定查询类别、团队筛选条件和用户是否提供日期范围；用户一次要求多个类别时，为每个类别独立执行权限和数据步骤。
2. 按当前方法契约支持的日期范围解析用户表达，并在执行摘要中展示明确的日期范围；日期缺失或有歧义时先追问。
3. 读取所选类别权限方法的当前 `--help` 并执行权限检查；权限调用失败或明确拒绝时，停止该类别，不调用数据方法。
4. 权限通过后读取对应数据方法的当前 `--help`，只放入用户已确认且当前契约支持的筛选、日期和分页信息；不补默认值或猜测字段。
5. 依据当前响应和契约确认的语义展示结果；多个类别中部分失败时明确说明成功与失败类别。

命令参数示例不固化在业务 Skill 中；执行前按对应方法当前 `--help`/Discovery 组装。

## 跨命令业务顺序

保留本 Skill 规定的权限检查、辅助查询、用户选择、确认和提交顺序。前一步的结果只能在当前对话中真实返回且用户确认后，按下一步方法本次读取到的契约映射；不在 Skill 中固定响应字段名、路径或目标参数名。前置方法失败、结果为空或当前契约无法读取时停止后续调用。

## 结果、空结果与错误恢复

- 成功：说明查询类别、实际筛选条件、解析后的日期范围和真实分页信息；列表仅展示实际返回且已确认含义的字段。
- 空结果：说明在实际日期和筛选条件下没有记录，不扩大日期范围、不更换人员或组织、不重复调用。
- 参数错误：保留 CLI 返回的字段名和错误消息，只追问缺失或格式错误的字段；用户修正后继续原查询。
- 认证或 401：遵循 `gaia-cli` 的认证恢复流程，恢复后仅重试原命令一次；仍失败时停止并报告原始错误。
- 权限不足或明确拒绝：展示 CLI 给出的 scope、resource 与诊断信息，不申请权限、不绕过权限，也不尝试其他类别的命令替代。
- 业务、服务或网络错误：保留可得的 `code`、`message`、`reason`、响应中的结果标志、响应中的错误信息；除认证恢复外不自动重试、不改写日期、租户、人员或组织条件。

`--debug` 可能输出完整 Token 和请求细节，仅在排障时使用，且不得把其输出写入 Skill 或展示给用户。

## 统一权限与排障输出

权限错误按证据区分三层：租户未获得 OpenAPI 授权时提示联系租户管理员；当前登录账号未获得业务接口权限时提示联系公司管理员或业务负责人；前两层通过后接口仍返回 403 时，标记为接口自身业务或数据限制，携带任务 ID 联系 CLI 业务负责人排查。无法从响应确认具体层级时，不武断归因，保留原始诊断和任务 ID。

缺少必填参数时只询问缺失字段；认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复；业务接口 4xx/5xx、网络错误、解析失败或未知异常时停止依赖步骤，说明具体操作、接口错误信息和下一步。写操作超时、连接中断或最终状态无法确认时报告“提交结果未知”，不自动重试或重复提交。普通回复先给问题摘要、已确认事实、用户动作和任务 ID；用户明确要求完整链路时才使用 `gaia logs --info` 整理 stages、请求方法/路径、脱敏参数、响应、权限判断、重试关系和 Correlation/Trace ID，不原样转发日志 JSON。业务流程不得使用 `--debug`，不得展示 Token、密码、Secret 或服务地址。

## 契约来源与核验

- 接口契约来源：Gaia CLI `gaia api check YA ATD_TEAM_QUERY`、`gaia api show YA ATD_TEAM_QUERY --json` 与全部 10 个方法的 `--help` 输出。
- 分页和默认值以执行时当前方法契约为准，不在 Skill 中固化。
- Discovery 版本：`YA v1`；CLI 契约来源为 `gaia api check`、`gaia api show --json` 和各方法 `--help` 输出。
- 核验环境：`la_test` / `test` / `huawei`；最近核验日期：2026-09-14。
Header、Body 和响应字段的必填性与结构以运行时当前契约为准。

## 验证用例

验证只检查业务意图、方法顺序、权限门禁和运行时契约读取；不把参数或响应字段写入固定用例。

## 契约适用说明

本次调整仅校正WorkBuddy Connector 适配，未在线调用业务接口。正文中的历史核验记录不代表当前租户的最新契约；首次使用时，在入口模式和 `release_channel=LA` 检查通过后，通过对应方法的 `--help` 或 `gaia api show` 核对当前 Discovery。出现差异时停止使用旧字段并报告差异，不猜测替代接口。
