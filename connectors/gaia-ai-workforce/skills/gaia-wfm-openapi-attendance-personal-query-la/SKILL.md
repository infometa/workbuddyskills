---
name: gaia-wfm-openapi-attendance-personal-query-la
description: "查询当前登录人员的个人考勤数据，包括打卡记录、打卡结果、出勤结果、工时、排班、津贴、假期余额、个人表单和待审批表单。用户询问自己的考勤、工时、排班、津贴、假期余额或相关表单时使用；不用于查询团队、部门或他人的数据。"
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# Gaia WFM 个人考勤查询

开始工作前遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。只使用 `gaia module resource method` 三段式命令；Gaia CLI 自动注入认证信息，不在本 Skill 中保存或索取 Token、Secret、服务 URL 或其他凭据。

## 适用范围

当用户查询“我的”或当前登录人员的下列信息时使用：

- 打卡原始记录、打卡结果或出勤结果
- 工时记录、排班信息
- 津贴记录、假期余额
- 个人表单或待本人审批的表单

不处理团队、部门、下属或指定他人的查询，也不处理请假/出差/加班的申请、修改、撤回，不修改任何考勤数据。意图无法区分打卡记录、打卡结果、出勤结果或其他类别时，先询问查询类别，不并行猜测多个接口。

## 可用 Gaia CLI 方法

以下方法均为只读查询，不需要额外确认。命令、HTTP 方法、参数位置和 Discovery scope 以 2026-09-04 在 `la_test` 测试环境通过的契约为准。

| 用户意图 | Gaia CLI 命令 | HTTP | 输入契约 | Scope |
|---|---|---|---|---|
| 查询打卡原始记录 | `gaia YA ATD_PERSONNAL_QUERY queryAtdRecord` | POST `/open-scene-api-la/api/v1/agent/attendance/record` | Header `employeeNum`、`tenantCode`（均 unspecified）；Body `startDate`、`endDate`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 200） | `S010300` |
| 查询打卡结果 | `gaia YA ATD_PERSONNAL_QUERY queryAtdResult` | POST `/open-scene-api-la/api/v1/agent/attendance/result` | Header `employeeNum`、`tenantCode`（均 unspecified）；Body `startDate`、`endDate`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 200） | `S010300` |
| 查询假期余额 | `gaia YA ATD_PERSONNAL_QUERY queryBalance` | POST `/open-scene-api-la/api/v1/agent/person/balance` | Header `employeeNum`、`tenantCode`（均 unspecified）；Body `leaveName`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 100） | `gaia.assistant.chat` |
| 查询出勤结果/考勤分类结果 | `gaia YA ATD_PERSONNAL_QUERY queryPaycodeResult` | POST `/open-scene-api-la/api/v1/agent/paycode/result` | Header `tenantCode`（unspecified）；Body `attendanceType`、`startDate`、`endDate`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 200） | `S010300` |
| 查询个人表单 | `gaia YA ATD_PERSONNAL_QUERY queryPersonForms` | POST `/open-scene-api-la/api/v1/agent/person/forms` | Header `employeeNum`、`tenantCode`（均 unspecified）；Body `startDate`、`endDate`、`formStatus`、`formType`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 200） | `S010060` |
| 查询个人排班 | `gaia YA ATD_PERSONNAL_QUERY queryPersonSchedule` | POST `/open-scene-api-la/api/v1/agent/person/schedule` | Header `employeeNum`、`tenantCode`（均 unspecified）；Body `startDate`、`endDate`、`pageNum`、`pageSize`（均 unspecified，`pageSize` 最大 200） | `S010020` |
| 查询津贴记录 | `gaia YA ATD_PERSONNAL_QUERY queryPersonalAllowance` | GET `/open-scene-api-la/api/v1/agent/personal/allowance` | Query `startDate`、`endDate`（required）；Header `employeeNum`、`language`、`tenantCode`（均 unspecified） | `S010300` |
| 查询待本人审批表单 | `gaia YA ATD_PERSONNAL_QUERY queryUnApproveForms` | POST `/open-scene-api-la/api/v1/agent/approvals/pending` | Header `tenantCode`（unspecified）；Body `startDate`、`endDate`、`formType`（array）、`pageNum`、`pageSize`（均 unspecified） | `900110030001001` |
| 查询工时记录 | `gaia YA ATD_PERSONNAL_QUERY queryWorkHours` | GET `/open-scene-api-la/api/v1/agent/personal/workhours` | Query `startDate`、`endDate`（required）；Header `employeeNum`、`language`、`tenantCode`（均 unspecified） | `S010300` |

`Authorization` 是受保护 Header，始终由 Gaia CLI 注入，不能通过 `--header` 覆盖。除表中列出的字段外，不自行添加 `tenantCode`、`employeeNum`、`language` 或其他字段；字段状态为 `unspecified` 时，优先使用用户已经提供的值，缺失不阻塞，只有 CLI 明确报缺少字段时才追问。

## 日期与范围解析

对所有支持 `startDate/endDate` 的方法，将用户自然语言先转换为当前本地时区 `Asia/Shanghai` 的明确日期，命令中使用 `yyyy-MM-dd`。单日表达的开始和结束日期相同。默认周一为一周起始日，周日为结束日；月份按自然月首日到末日计算。

| 用户表达 | `startDate` | `endDate` |
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

也支持“最近 N 天”这类表达：范围包含今天，`startDate` 为今天往前 `N-1` 天，`endDate` 为今天。仅给出“7 月”等缺少年份的月份表达可能跨年时，先询问年份。没有可确定的日期或范围时必须追问，不默认本周、最近 7 天或其他范围。校验开始日期不晚于结束日期；若接口契约或服务返回范围限制，保留原始错误并要求用户缩短范围，不自动拆分或放宽条件。

假期余额 `queryBalance` 没有日期字段；不要为了该查询强行附加日期。`queryAtdRecord`、`queryAtdResult`、`queryPaycodeResult`、`queryPersonForms`、`queryPersonSchedule`、`queryUnApproveForms` 的日期字段在 Discovery 中为 `unspecified`，用户提供范围时按上述规则传入；用户未提供时不擅自填充。

## 工作流

1. 识别查询类别和是否为当前用户；类别不清时只追问一个最关键问题。
2. 解析并展示将使用的日期范围（若该方法支持日期）。检查日期格式、顺序和范围限制。
3. 根据命令契约放置参数：GET 使用 `--params JSON`，POST 使用 `--body JSON`；仅在用户已提供或 CLI 契约要求时使用 `--header JSON`。
4. 执行对应的只读命令。用户一次明确要求多个类别时，共用同一日期范围，按类别分别执行并合并展示；一个方法失败时保留已成功结果并说明失败方法，不把部分成功说成全部成功。
5. 依据真实返回的 `code`、`message`、`reason`、`details` 展示结果。列表优先展示业务字段和记录总数；有分页信息时按真实分页字段说明当前页，不猜测字段含义。

## 跨命令字段映射

这 9 个方法都是相互独立的只读查询，没有任何方法的响应字段必须传给另一个方法，也没有前置命令依赖。用户一次查询多个类别时，只复用用户已经确认的 `startDate/endDate` 和已明确提供的业务 Header；这属于同一输入条件复用，不是响应字段映射。任一方法失败不改变其他方法的参数，也不使用失败或成功响应去猜测另一个方法的输入。

推荐命令形态示例（示例值仅用于说明结构）：

```bash
gaia YA ATD_PERSONNAL_QUERY queryAtdRecord --header '{"employeeNum":"<employeeNum>","tenantCode":"<tenantCode>"}' --body '{"startDate":"2026-09-01","endDate":"2026-09-07","pageNum":0,"pageSize":200}'
gaia YA ATD_PERSONNAL_QUERY queryPersonalAllowance --params '{"startDate":"2026-09-01","endDate":"2026-09-07"}' --header '{"employeeNum":"<employeeNum>","language":"<language>","tenantCode":"<tenantCode>"}'
```

不要把示例占位符当成真实值发送。`pageNum`、`pageSize` 等 unspecified 字段只有在用户明确提供或需要按接口分页继续读取时才传入；不得为了填满示例而猜测默认值。

## 结果、空结果与错误恢复

- 成功：说明查询类别和实际日期范围，按 `details` 中真实字段整理记录；不从字段名猜测金额、时长或状态含义。
- 空结果：说明实际筛选条件和日期范围内没有记录，不扩大范围、不改员工、不重复调用。
- 参数错误：保留 CLI 返回的具体字段和消息，只追问缺失或格式错误的字段；用户修正后再执行。
- 未登录或 401：遵循 `gaia-cli` 的 WorkBuddy 登录恢复流程，恢复后仅重试原命令一次；仍失败则停止并报告原始错误。
- 403 或权限不足：展示 CLI 返回的 scope、resource 和提示信息，不申请权限、不绕过检查。
- 业务错误、网络错误或非零退出：保留 `code/message/reason/details`。除认证恢复外不自动更换方法、日期、租户或员工。

所有方法都是 `read` 操作，无需执行前确认；`--debug` 仅用于排障，因其可能输出完整 Token 和请求细节，不得写入 Skill 或展示给用户。

## 契约来源与核验

- CLI 契约来源：Gaia CLI Discovery 与各方法 `--help` 输出。
- 核验环境：`la_test` / `test` / `huawei`，核验日期 2026-09-04。
- 已核验：`gaia commands list --module YA --json`、9 个方法的 `gaia api check YA ATD_PERSONNAL_QUERY <method>` 及对应 `--help`。
- Discovery 未声明的字段状态保持 `unspecified`；未在本文件中保存 Token、Secret、真实 URL 或凭据。
