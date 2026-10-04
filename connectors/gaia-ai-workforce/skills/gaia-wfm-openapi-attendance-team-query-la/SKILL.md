---
name: gaia-wfm-openapi-attendance-team-query-la
description: "查询当前主管可见团队的考勤记录、累计数据、考勤卡、设备卡和排班。用户询问下属、团队或部门成员在指定日期范围内的考勤、假期累计、打卡卡片、设备卡或排班时使用；不用于个人查询或修改考勤数据。"
metadata:
  requires:
    bins: ["gaia"]
  gaia:
    modes: [common]
---

# Gaia WFM 团队考勤查询

开始前遵循 [`../gaia-cli/SKILL.md`](../gaia-cli/SKILL.md) 的 WorkBuddy 认证、租户、权限、安全确认和错误恢复规则。仅使用 `gaia <module> <resource> <method>` 三段式命令和该命令支持的 `--body`、`--header` 参数；Gaia CLI 自动注入认证信息，绝不索取、显示或保存 Token、Secret、密码或业务服务 URL。

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

| 查询类别 | 权限命令 | 数据命令 | 数据请求体字段 | Discovery scope |
|---|---|---|---|---|
| 考勤记录 | `gaia YA ATD_TEAM_QUERY getrecordaccess` | `gaia YA ATD_TEAM_QUERY getattendancelist` | `attendanceType`、`employeeId`、`employeeIdList`、`employeeNameList`、`startDate`、`endDate`、`pageNum`、`pageSize`、`unitNameList` | `050208001` |
| 累计数据 | `gaia YA ATD_TEAM_QUERY tbGetAccess` | `gaia YA ATD_TEAM_QUERY getbalancelist` | `employeeId`、`employeeIdList`、`employeeNameList`、`leaveTypeName`、`startDate`、`endDate`、`pageNum`、`pageSize`、`unitNameList` | `dacc.amountQuery.dataExport`（权限）/ `dacc.amountQuery.operateLog`（数据） |
| 考勤卡 | `gaia YA ATD_TEAM_QUERY gettimecardaccess` | `gaia YA ATD_TEAM_QUERY getcardlist` | `employeeId`、`employeeIdList`、`employeeNameList`、`startDate`、`endDate`、`pageNum`、`pageSize`、`unitNameList` | `050208001` |
| 设备卡 | `gaia YA ATD_TEAM_QUERY getdeviceaccess` | `gaia YA ATD_TEAM_QUERY getdevicecardlist` | `employeeId`、`employeeIdList`、`employeeNameList`、`startDate`、`endDate`、`pageNum`、`pageSize`、`unitNameList` | `050300002` |
| 排班 | `gaia YA ATD_TEAM_QUERY tsGetAccess` | `gaia YA ATD_TEAM_QUERY tsGetScheduleList` | `employeeId`、`employeeIdList`、`employeeNameList`、`startDate`、`endDate`、`pageNum`、`pageSize`、`unitNameList` | `attendance.managerview.agree` |

所有方法的业务 Header 都是 `employeeNum` 和 `tenantCode`，且均在 Discovery 中标记为 `unspecified`。只使用用户当前对话中已确认的值；未知时不猜测，也不因这些字段未提供而阻塞用户。仅当 CLI 或服务明确报告字段缺失时，追问相应字段。`Authorization` 是受保护 Header，始终由 Gaia CLI 注入，不能通过 `--header` 覆盖。

表中全部 Body 字段在 Discovery 中均标记为 `unspecified`。只传入用户明确提供、相对时间解析得到、后续翻页需要，或本 Skill 已确认业务默认的字段；不得为填满 CLI 示例发送空数组、空字符串、`0` 或其他未经确认的默认值。当前五个数据接口统一使用业务默认 `pageNum:1`、`pageSize:10`。

## 操作风险与确认条件

| 命令 | 操作类型 | 风险来源 | 确认条件 |
|---|---|---|---|
| `getrecordaccess`、`gettimecardaccess`、`getdeviceaccess`、`tbGetAccess`、`tsGetAccess` | read | 仅读取当前用户的团队查询权限状态 | 无需额外确认 |
| `getattendancelist`、`getbalancelist`、`getcardlist`、`getdevicecardlist`、`tsGetScheduleList` | read | 仅读取当前用户有权访问的团队考勤数据 | 无需额外确认 |

本 Skill 没有 write 或 destructive 命令。禁止借由权限查询修改授权、申请权限或改变任何考勤记录。

## 日期与范围解析

对于支持 `startDate`、`endDate` 的五个数据方法，先按执行时的 `Asia/Shanghai` 时区将用户的自然语言映射为 `yyyy-MM-dd`。单日表达的开始和结束日期相同；一周从周一开始，到周日结束；月份使用自然月。

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
| 明确日期 | 该日期 | 该日期 |
| 明确日期范围 | 用户提供的开始日期 | 用户提供的结束日期 |
| 最近 N 天 | 包含今天在内往前 N-1 天 | 今天 |

用户表达明确日期或范围时，执行前说明解析后的日期范围。日期字段未被 Discovery 声明为必填：用户未提供日期时不默认本周、最近 7 天或其他范围，而是省略日期字段；只有 CLI 或服务明确要求时才追问。开始日期晚于结束日期时，要求用户更正；接口若返回范围限制，保留原始错误并要求用户缩短范围，不自动拆分或扩大查询。仅给出可能跨年的月份（例如“7 月”）时，先确认年份。

## 筛选与分页边界

按 Discovery 契约原样传递用户明确提供的筛选条件：

| 字段 | 适用命令 | 契约含义与处理 |
|---|---|---|
| `employeeId` | 全部数据命令 | 当前人员的员工工号；仅用户明确以该字段提供时传入。 |
| `employeeIdList` | 全部数据命令 | 员工工号列表；将用户明确提供的工号原样组成列表。 |
| `employeeNameList` | 全部数据命令 | 员工姓名列表，接口明确支持模糊匹配；将用户明确提供的姓名原样组成列表。 |
| `unitNameList` | 全部数据命令 | 组织名称列表，接口明确支持模糊匹配；将用户明确提供的组织名称原样组成列表。 |
| `attendanceType` | `getattendancelist` | 考勤类型过滤；仅使用 `leave`、`overtime`、`exception`、`travel`、`workHours`、`allowance` 中用户明确选择的值，不传则按接口契约返回全部类型。 |
| `leaveTypeName` | `getbalancelist` | 假期类型名称，接口明确支持模糊匹配；使用用户明确的名称，例如“年假”。 |
| `pageNum`、`pageSize` | 全部数据命令 | 五个数据命令用户未提供分页时均按已确认业务默认传 `pageNum: 1`、`pageSize: 10`；用户明确分页时使用用户值，用户要求继续读取下一页时递增 `pageNum` 并保持 `pageSize`。 |

`unitNameList` 在 Discovery 中为 `unspecified`，不是必填字段。用户说明部门、组织或团队名称时，将名称原样放入 `unitNameList` 数组并传入；用户未说明部门时省略该字段，不追问补充。不要把姓名、组织名称、工号之间自行转换。用户同时提供多个字段时，按字段原样传入；组合筛选语义未被契约定义，不解释为并集或交集。

所有五个数据查询的分页默认值均为当前页 `1`、每页 `10` 人；不因接口字段标记为 `unspecified` 而追问。用户只明确其中一个分页值时，保留该值，并对另一个未提供值使用默认值。用户要求继续下一页时，递增 `pageNum` 并保持已确认的 `pageSize`。

## 统一分页规则

五个数据查询命令 `getattendancelist`、`getbalancelist`、`getcardlist`、`getdevicecardlist` 和 `tsGetScheduleList` 均按统一业务默认处理分页：用户未提供 `pageNum` 或 `pageSize` 时自动传入当前页 `1`、每页 `10` 人，不因字段在 Discovery 中标记为 `unspecified` 而追问。用户只明确其中一个值时保留该值，另一项使用默认值；用户要求继续读取下一页时递增 `pageNum` 并保持 `pageSize`。该规则覆盖下方“筛选与分页边界”中对分页的通用说明。

## 查询工作流

1. 确定查询类别、团队筛选条件与用户是否提供日期范围。用户一次明确要求多个类别时，为每个类别运行独立的权限和数据步骤；可以复用用户已经确认的日期范围和 Header，不复用任一接口的响应字段。
2. 将相对日期解析为 `startDate`、`endDate`，检查日期格式与先后顺序，并在将要执行的摘要中展示实际范围。
3. 调用所选类别的权限命令。按用户已确认的 `employeeNum`、`tenantCode` 追加 `--header` JSON；未确认字段不猜测。
4. 权限命令成功且没有明确拒绝后，调用对应数据命令。POST 参数放入 `--body` JSON；只放入本次已确认的筛选、日期和分页字段。调用任一五个数据命令时，如用户未提供分页，自动加入 `pageNum:1`、`pageSize:10`；`unitNameList` 仅在用户说明部门、组织或团队名称时加入。
5. 依据真实响应的顶层 `code`、`message`、`reason` 及 `details` 展示结果。数据接口已声明的 `details` 字段为 `resultList`、`pageNum`、`pageSize`、`personTotal`、`resultFlag`、`errorMsg`；只解释实际返回的字段，不能根据字段名猜测记录内的业务含义。

示例仅说明命令形态，尖括号和示例日期不能作为真实值发送：

```bash
gaia YA ATD_TEAM_QUERY getrecordaccess --header '{"employeeNum":"<employeeNum>","tenantCode":"<tenantCode>"}'
gaia YA ATD_TEAM_QUERY getattendancelist --header '{"employeeNum":"<employeeNum>","tenantCode":"<tenantCode>"}' --body '{"employeeIdList":["<employeeId>"],"startDate":"2026-09-07","endDate":"2026-09-13"}'
gaia YA ATD_TEAM_QUERY tsGetScheduleList --body '{"startDate":"2026-09-14","endDate":"2026-09-20","pageNum":1,"pageSize":10,"unitNameList":["研发部"]}'
```

## 跨命令字段映射

| 来源命令 | 目标命令 | 前置条件 | 失败策略 |
|---|---|---|---|
| `getrecordaccess` 的成功结果 | `getattendancelist` | 没有明确拒绝访问 | 停止考勤记录查询 |
| `tbGetAccess` 的成功结果 | `getbalancelist` | 没有明确拒绝访问 | 停止累计数据查询 |
| `gettimecardaccess` 的成功结果 | `getcardlist` | 没有明确拒绝访问 | 停止考勤卡查询 |
| `getdeviceaccess` 的成功结果 | `getdevicecardlist` | 没有明确拒绝访问 | 停止设备卡查询 |
| `tsGetAccess` 的成功结果 | `tsGetScheduleList` | 没有明确拒绝访问 | 停止排班查询 |

上述映射只表达权限门禁，不将权限响应中的任何未声明字段传入数据接口。所有数据接口之间没有响应字段依赖；多类别查询中仅复用用户已经确认的 Header、日期和筛选条件。某一类别失败不改变其他类别的参数或结果，最终必须明确说明部分成功情况。

## 结果、空结果与错误恢复

- 成功：说明查询类别、实际筛选条件、解析后的日期范围和真实分页信息；列表仅展示实际返回且已确认含义的字段。
- 空结果：说明在实际日期和筛选条件下没有记录，不扩大日期范围、不更换人员或组织、不重复调用。
- 参数错误：保留 CLI 返回的字段名和错误消息，只追问缺失或格式错误的字段；用户修正后继续原查询。
- 认证或 401：遵循 `gaia-cli` 的 WorkBuddy 认证恢复流程，恢复后仅重试原命令一次；仍失败时停止并报告原始错误。
- 权限不足或明确拒绝：展示 CLI 给出的 scope、resource 与诊断信息，不申请权限、不绕过权限，也不尝试其他类别的命令替代。
- 业务、服务或网络错误：保留可得的 `code`、`message`、`reason`、`details.resultFlag`、`details.errorMsg`；除认证恢复外不自动重试、不改写日期、租户、人员或组织条件。

`--debug` 可能输出完整 Token 和请求细节，仅在排障时使用，且不得把其输出写入 Skill 或展示给用户。

## 契约来源与核验

- 统一分页业务规则补充：2026-09-14 功能测试确认，五个数据查询方法未指定分页时统一使用 `pageNum:1`、`pageSize:10`；该规则覆盖当前 CLI `--help` 示例中的 `0/0` 占位值。
- 接口契约来源：Gaia CLI `gaia api check YA ATD_TEAM_QUERY`、`gaia api show YA ATD_TEAM_QUERY --json` 与全部 10 个方法的 `--help` 输出。
- 业务默认来源：2026-09-14 功能测试确认，五个数据查询方法未指定分页时统一使用 `pageNum:1`、`pageSize:10`；这覆盖当前 CLI `--help` 示例中的 `0/0` 占位值。`unitNameList` 维持 Discovery 的 `unspecified` 状态。
- Discovery 版本：`YA v1`；CLI 契约来源为 `gaia api check`、`gaia api show --json` 和各方法 `--help` 输出。
- 核验环境：`la_test` / `test` / `huawei`；最近核验日期：2026-09-14。
- Discovery 未声明的 Header、Body 字段必填性均保持 `unspecified`；本文件不包含未核验字段、凭据或直接 HTTP 调用方式。

## 验证用例

| 用户请求 | 预期行为 |
|---|---|
| “查团队明天的考勤记录” | 解析明天为同一天的 `startDate/endDate`，先调用 `getrecordaccess`，成功后调用 `getattendancelist`。 |
| “看一下上周张三的排班” | 解析上周周一至周日，将“张三”原样放入 `employeeNameList`，先调用 `tsGetAccess`，再调用 `tsGetScheduleList`。 |
| “查询本月研发部的设备卡” | 解析本月自然月，组织名原样放入 `unitNameList`，先调用 `getdeviceaccess`，再调用 `getdevicecardlist`。 |
| “查看下周团队排班”且用户未提供分页 | 在排班 Body 中自动传入 `pageNum:1`、`pageSize:10`，不追问分页。 |
| “查看本月研发部的排班” | 将“研发部”原样放入 `unitNameList`，不追问部门编码或其他组织字段；未提供分页时传入 `pageNum:1`、`pageSize:10`。 |
| “查团队明天的考勤记录”且用户未提供分页 | 在考勤记录 Body 中自动传入 `pageNum:1`、`pageSize:10`，不追问分页。 |
| “查询本月研发部的考勤卡”且用户未提供分页 | 将“研发部”原样放入 `unitNameList`，并自动传入 `pageNum:1`、`pageSize:10`。 |
| “查王五上月的年假累计” | 解析上月自然月，使用 `employeeNameList` 与 `leaveTypeName`，先调用 `tbGetAccess`，再调用 `getbalancelist`。 |
| 权限方法明确拒绝 | 说明拒绝信息并停止该类别；不调用其数据方法。 |
| 数据接口返回空 `resultList` | 说明实际筛选条件下无记录，不自动放宽条件。 |
