---
name: xrxs-attendance-archive
display_name: 考勤月度报表归档
display_name_en: Attendance Monthly Report Archive
description: "考勤月度报表归档能力：检查不能归档的异常员工、区分是否开启考勤组、归档考勤组/非考勤组报表、预览确认归档。当用户问「哪些员工不能归档」「这个月考勤报表归档了吗」「帮我归档考勤组报表」时使用。"
description_zh: "提供考勤月度报表归档相关能力，覆盖：查询当前管理员权限范围内不能归档的异常员工及其原因；查询可选择的考勤组列表以区分公司是否开启考勤组（判断是否开启考勤组只用 mcp__xrxs_attendance_getReportAttendanceGroupList，不用归档预览接口）；按账套月份和考勤组集合归档考勤组报表；归档活动账套的非考勤组报表（仅公司未开启考勤组时使用，两个归档接口不可混用）；查询归档预览数据（考勤组数、员工总数、各考勤组归档状态、操作人、归档时间）用于确认归档，预览确认仅在公司开启考勤组时执行。数据范围仅限当前管理员权限范围内的考勤数据。典型问句：「哪些员工不能归档」「这个月考勤报表归档了吗」「帮我归档考勤组报表」。"
description_en: "Attendance monthly report archiving capabilities: list employees that cannot be archived (with reasons) within the current administrator's scope; query the selectable attendance group list to tell whether the company has attendance groups enabled (use only mcp__xrxs_attendance_getReportAttendanceGroupList for this check, never the archive preview tool); archive reports by attendance groups for a given account month; archive non-attendance-group reports for the active account month (only when attendance groups are not enabled; the two archiving tools must not be mixed); preview archive confirmation data (attendance group count, total employees, per-group archive status, operator, archive time) before archiving, and this preview step runs only when attendance groups are enabled. Covers only attendance data within the current administrator's permission scope. Use for questions like 'which employees cannot be archived', 'has this month's attendance report been archived', or 'archive the attendance group reports for me'."
category: automation
version: 1.0.0
author: 薪人薪事
---

# 考勤月度报表归档

帮考勤管理员完成月度报表归档全流程：先检查异常员工、预览确认，再按公司是否开启考勤组选择对应的归档接口执行归档。只编排以下 5 个工具：

- `mcp__xrxs_attendance_getEmployeeErrorMessageByArchive`
- `mcp__xrxs_attendance_getReportAttendanceGroupList`
- `mcp__xrxs_attendance_archiveReportsByAttendanceGroups`
- `mcp__xrxs_attendance_reportAttendanceGroupPreview`
- `mcp__xrxs_attendance_archiveReports`

## 选择工具

- 问「哪些员工不能归档」「这批员工为什么归档不了」——`mcp__xrxs_attendance_getEmployeeErrorMessageByArchive`，无需入参，单步直达，返回当前管理员权限范围内不能归档的员工姓名与异常原因。
- 问「公司有没有开考勤组」「可选择的考勤组有哪些」——`mcp__xrxs_attendance_getReportAttendanceGroupList`，判断是否开启考勤组只用这个工具；查询可选择的考勤组列表，用返回结果区分是否开启考勤组，并据此选择后续归档接口。
- 问「归档考勤组报表」「把某几个考勤组的本月报表归档掉」——`mcp__xrxs_attendance_archiveReportsByAttendanceGroups`，仅在公司开启考勤组时使用；传 `yearmo`（账套月份，格式 yyyyMM，可不传按接口缺省）和可选的 `attendanceGroupIds`（考勤组 ID 集合，多个逗号分隔）；先经 `mcp__xrxs_attendance_getReportAttendanceGroupList` 取考勤组 ID 集合再传入，属两段式调用，执行前需确认。
- 问「归档前看看本月要归档哪些考勤组」「各考勤组归档到哪一步了」——`mcp__xrxs_attendance_reportAttendanceGroupPreview`，仅在公司开启考勤组时用于归档前的预览确认，必须传入 `yearmo`（账套月份，格式 yyyyMM），返回考勤组数、员工总数和每个考勤组的归档状态、人数、操作人、归档时间；公司未开启考勤组时不要调用它，也不要用它判断公司是否开启考勤组。
- 问「归档非考勤组报表」「把当前账套的非考勤组报表归档」——`mcp__xrxs_attendance_archiveReports`，仅在公司未开启考勤组时使用，与考勤组归档接口不可混用；无需入参，账套月份由接口内部按活动账套获取，执行前需确认。

## 操作流程

按以下顺序执行，每一步都有明确结果后再进入下一步：

1. **判断是否开启考勤组（所有归档的必做第一步）**：调用 `mcp__xrxs_attendance_getReportAttendanceGroupList` 查可选择的考勤组列表。返回有考勤组 → 走「考勤组归档」分支；返回无考勤组 → 走「非考勤组归档」分支。判断是否开启考勤组只用这个工具，不要用 `mcp__xrxs_attendance_reportAttendanceGroupPreview`。
2. **查异常员工**：调用 `mcp__xrxs_attendance_getEmployeeErrorMessageByArchive`（无需入参）。返回异常员工时，把员工姓名和异常原因如实告诉用户，由用户决定是否继续；未返回则继续下一步。
3. **确认前置状态**：归档前确认审批流数量与归档状态——审批流数量大于 0 时提醒用户处理审批（也可不处理继续归档）；归档状态为 false 时向用户转述报错信息并禁止归档。
4. **预览确认归档范围（仅公司开启考勤组时执行）**：调用 `mcp__xrxs_attendance_reportAttendanceGroupPreview`，必须传 `yearmo`（账套月份，格式 yyyyMM），查看本月考勤组数、员工总数和各考勤组归档状态，把预览结果复述给用户并确认是否执行归档。公司未开启考勤组时跳过本步，不调用预览接口，直接执行第 5 步。
5. **执行归档（两个归档接口按分支二选一，不能混用）**：
   - 公司开启考勤组：调用 `mcp__xrxs_attendance_archiveReportsByAttendanceGroups`，传 `yearmo`（账套月份，格式 yyyyMM，可不传按接口缺省）和 `attendanceGroupIds`（取第 1 步列表中的考勤组 ID，多个逗号分隔）。
   - 公司未开启考勤组：调用 `mcp__xrxs_attendance_archiveReports`，无需入参，归档活动账套的非考勤组报表。
6. **失败处理**：接口自身会校验固化任务、归档锁与考勤组有效性，调用失败时按返回的报错信息如实转述，不要自行猜测原因，也不要改用另一个归档接口强行归档。

易混概念先分清再回答：

- **有考勤组 vs 无考勤组**：判断是否开启考勤组只用 `mcp__xrxs_attendance_getReportAttendanceGroupList` 查可选择的考勤组列表来区分，不要用归档预览接口。公司开启考勤组时用 `mcp__xrxs_attendance_archiveReportsByAttendanceGroups` 按考勤组归档；未开启考勤组时用 `mcp__xrxs_attendance_archiveReports` 归档非考勤组报表，两个归档接口不能混用。
- **判断是否开启考勤组 vs 归档预览确认**：`mcp__xrxs_attendance_getReportAttendanceGroupList` 负责判断公司是否开启考勤组；`mcp__xrxs_attendance_reportAttendanceGroupPreview` 只负责归档前预览确认（考勤组数、员工总数、各考勤组归档状态等），且仅在公司开启考勤组时执行，两者职责不同，不能用预览结果判断是否开启考勤组。
- **考勤组归档 vs 非考勤组归档**：`mcp__xrxs_attendance_archiveReportsByAttendanceGroups` 按指定账套月份与考勤组集合归档；`mcp__xrxs_attendance_archiveReports` 归档活动账套的非考勤组报表，无需指定月份，不可互相替代。
- **归档预览 vs 归档执行**：`mcp__xrxs_attendance_reportAttendanceGroupPreview` 只查预览数据，不产生归档动作；真正归档要用 `mcp__xrxs_attendance_archiveReportsByAttendanceGroups`，先预览确认再执行。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展查询范围，也不替用户补时间条件。
3. 相对日期（「这个月」「上个月」）换算成 yyyyMM 格式的账套月份再调用，并在回答里说明实际查询的月份。
4. 归档属写入操作：执行 `mcp__xrxs_attendance_archiveReportsByAttendanceGroups` 或 `mcp__xrxs_attendance_archiveReports` 前，必须先向用户确认归档月份与范围。
5. 归档前先确认前置状态：审批流数量大于 0 时提醒用户处理审批（也可不处理继续归档）；归档状态为 false 时向用户转述报错信息并禁止归档。
6. 判断是否开启考勤组只用 `mcp__xrxs_attendance_getReportAttendanceGroupList`：开启考勤组时取考勤组 ID 集合（多个逗号分隔）传入 `attendanceGroupIds` 走考勤组归档；未开启时走非考勤组归档，两个归档接口不可混用。不要用 `mcp__xrxs_attendance_reportAttendanceGroupPreview` 判断是否开启考勤组，它只用于归档前预览确认，且仅在公司开启考勤组时执行。
7. 归档预览接口的 `yearmo` 必填；归档接口的 `yearmo` 可不传，按接口缺省处理。

## 结果与权限

- 空结果一律按「未返回数据」处理，不得反推为无权限，也不要断言「没有异常员工 / 没有可归档报表」。
- 字段为 null 或缺失表示该项无数据或企业未启用，不要解读为归档异常。
- 归档状态为 false 时接口会返回报错信息，如实转述，并据此禁止继续归档。
- 权限范围外的数据查不到时按未返回数据处理，不臆断；涉及归档范围时提示用户确认当前账号的管理员权限范围。
- 考勤组列表为空或未返回时，按「未开启考勤组」处理还是「暂无数据」需以接口实际返回为准，不据此臆断归档方式。

## 安全边界

- 数据面仅限当前管理员权限范围：异常员工列表、考勤组列表、考勤组/非考勤组报表归档均只针对当前账号有权限的数据，不能用来查询或操作权限之外的考勤信息。
- 不向用户展示访问令牌、内部标识符（如员工 ID、考勤组 ID）或原始技术响应。
- 不虚构工具未返回的字段、员工、考勤组或归档状态；工具没给的口径不用常识补全。
- 面向用户只用业务语言：没数据说「没有查到」，不引用参数名、枚举值或状态码。
- 不用缓存结果冒充实时数据；每次查询的月份或考勤组变了就重新调用。
- 归档前确认意图再执行，不做未经确认的批量归档。
- 出现未登录或授权失效时，提示用户重新连接后重试，不要求用户在聊天中粘贴任何登录凭证。
