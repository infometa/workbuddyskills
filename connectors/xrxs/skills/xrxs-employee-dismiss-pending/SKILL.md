---
name: xrxs-employee-dismiss-pending
display_name: 离职待办巡检
display_name_en: Offboarding Pending Task Patrol
description: "检索并检查预计离职员工的离职记录与待处理事项，支持按时间、部门等条件过滤并下钻查看具体员工的待办清单。覆盖要点：离职记录搜索、筛选字段配置获取、个人离职待处理事项汇总（含考勤校验）。当用户问『帮我查一下最近要离职的人有哪些』『张三的离职手续还差哪些』『3月预计离职员工的待办情况如何』时使用。"
description_zh: "面向HR或管理员的离职待办巡检技能：按预计离职时间、部门、员工关键字等条件搜索离职记录，并针对具体员工拉取离职待处理事项清单。技能覆盖『获取离职记录筛选字段配置』『搜索员工离职记录』『获取员工离职待处理事项』三类能力；数据边界以当前系统授权可见的离职记录为准，不处理在职员工信息，也不主动发起离职审批。典型问句包括『最近有哪些员工要离职』『帮我查3月1日到3月31日预计离职名单』『李四的离职待办还剩哪些』等。"
description_en: "An offboarding pending-task patrol skill for HR or admins: search dismissal records by expected leave date, department, employee keyword, etc., and fetch the pending offboarding todo list for specific employees. Covers retrieving dismissal record filter field configurations, searching employee dismissal records, and getting employee offboarding pending items. Data is limited to dismissal records visible under current system permissions; it does not handle active employees or initiate resignation approvals. Typical questions: 'Who is leaving recently?', 'Show me the expected resignation list from March 1 to March 31', or 'What offboarding tasks does Li Si still have?'."
category: automation
version: 1.0.0
author: 薪人薪事
---

# 离职待办巡检

帮助 HR 或管理员按条件找出预计离职员工，并下钻检查每名员工的离职待处理事项。只编排以下 3 个工具：

- `mcp__xrxs_base_getEmployeeFilterFields`
- `mcp__xrxs_employee_searchDismissRecord`
- `mcp__xrxs_employee_getDismissPendingIssueTotal`

## 离职记录状态（必读）

`searchDismissRecord` 默认返回**全部状态**的离职记录，会混入已离职、已取消的员工。本技能聚焦「预计/待离职」人群，因此查询**离职待办相关名单**时，必须先通过 `getEmployeeFilterFields` 取「离职记录状态」字段，并默认过滤掉离职已完成与已取消的记录。状态枚举（码值即候选项 key）：

- `1` = 待离职（员工仍在职，离职流程办理中）
- `2` = 已离职（已真正离职，不再参与离职待办巡检）
- `3` = 已超期（仍待办，与待离职同属待巡检对象）
- `4` = 已取消（撤销离职，不属于巡检对象）

组装 `filters` 时对「离职记录状态」这一字段，`values` 固定填待巡检的两个 key：`["1","3"]`（待离职 + 已超期），从而排除 `2`（已离职）与 `4`（已取消）。这是本技能的**默认行为**：即使用户没提离职状态，也要带上该过滤；不允许在无状态过滤下把全部离职记录当作「预计离职名单」返回。

## 选择工具

- 问「最近有哪些员工要离职」「帮我搜一下预计离职名单」「列出本月准备离职的人」——`mcp__xrxs_employee_searchDismissRecord`，但必须先用 `mcp__xrxs_base_getEmployeeFilterFields` 取「离职记录状态」字段并按要求过滤（见上文「离职记录状态」节），再按需叠加预计离职日期、部门等条件；不可无过滤地直接按页查询。
- 问「帮我看看 3 月 1 日到 3 月 31 日要离职的员工」「某部门最近离职的人有哪些」「按离职日期或部门筛选」——`mcp__xrxs_base_getEmployeeFilterFields` 配合 `mcp__xrxs_employee_searchDismissRecord` 两段式。先以 `filterBizType=5`、keyword 填字段名（如「预计离职日期」「部门」「离职记录状态」）获取字段 ID 与候选项，再按规则构造 `filters` 传给搜索接口。其中「离职记录状态」默认填 `["1","3"]`。
- 问「张三的离职手续还差哪些」「某员工的离职待办有哪些」「他离职前还有哪些事没处理」——`mcp__xrxs_employee_getDismissPendingIssueTotal`，需传入上一步 `searchDismissRecord` 返回的 `employeeId`；若用户给了具体离职日期，可再传 `dismissDate`（yyyy-MM-dd）用于考勤校验。
- 问「查一下这批预计离职人员各自的待处理事项」——先 `mcp__xrxs_employee_searchDismissRecord` 获取员工列表，再逐一下钻 `mcp__xrxs_employee_getDismissPendingIssueTotal`（每人传对应的 `employeeId`）。
- 问「搜索某个姓名/手机号/工号的离职记录」——`mcp__xrxs_employee_searchDismissRecord`，直接传 `keyword`（支持姓名/手机号/工号等），可不组装 filters。

易混概念先分清再回答：

- **筛选字段配置 vs 筛选字段值**：`mcp__xrxs_base_getEmployeeFilterFields` 只返回筛选项的配置和候选项（如 fieldId、dataSource），不返回员工数据；真正的搜索要把选中的值按规则组装成 `filters` 传给 `mcp__xrxs_employee_searchDismissRecord`。
- **离职记录 vs 离职待办**：`mcp__xrxs_employee_searchDismissRecord` 返回的是离职人员名单/记录；`mcp__xrxs_employee_getDismissPendingIssueTotal` 返回单个员工的待处理事项（如考勤、交接等）。不要拿离职记录直接当待办清单。
- **员工 ID vs 搜索关键字**：按姓名等模糊找人用 `searchDismissRecord` 的 `keyword`；查某人的待办必须用它返回的 `employeeId` 调 `getDismissPendingIssueTotal`，不要凭空构造 ID。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展查询范围，也不替用户补全未提及的筛选条件。**唯一例外**：「离职记录状态」默认过滤（见「离职记录状态」节）属于本技能的固定行为，即使处理的是“查预计离职名单”口径，也必须带上 `["1","3"]` 过滤，即使未提供任何状态条件也须带上。
3. 相对日期（「最近」「本月」「本季度」「未来 7 天」）须换算成绝对日期区间再调用，并在回答中说明实际查询区间。
4. `mcp__xrxs_base_getEmployeeFilterFields` 为 GET 接口，`filterBizType` 固定传 `5`（离职记录），`keyword` 必填，应填所需字段的中文名或标识，用于获取该字段的 ID 与候选项。
5. 组装 `filters` 时，按 `getEmployeeFilterFields` 返回的 `fieldFilterType` 填值：日期型用 `dateValues`（开始、结束，yyyy/MM/dd，单边留空传空串），选项/员工/部门等用 `values`（key 取候选项的 key），文本型用 `values` 传关键词。
6. `mcp__xrxs_employee_searchDismissRecord` 默认 `pageNo=1`、`pageSize=20`；若结果可能跨页，应分页拉取或提示用户总页数。每页上限 100，不要自行突破。
7. `mcp__xrxs_employee_getDismissPendingIssueTotal` 是下钻工具，必须依赖 `searchDismissRecord` 返回的 `employeeId`；不要凭空构造员工 ID。`dismissDate` 可选，用户未提供时不传。
8. `keyword`（按姓名/手机号/工号搜索）与 `filters` 可同时使用。仅在用户明确要“查某人的离职记录/历史”（无论是否已离职）时，才可不带「离职记录状态」过滤；只要语义是「预计/待离职名单」，即使不传其他条件，也必须在 `filters` 中带上「离职记录状态」为 `["1","3"]`。

## 结果与权限

- 空结果一律按「未返回数据」处理，不得反推为「没有离职员工」或「权限不足」。
- 工具非成功时必有面向用户的 `message`，如实转述，不猜测技术根因。
- `getEmployeeFilterFields` 返回的字段配置不含实际数据，仅用于构造筛选；若某字段未返回，说明该筛选维度未启用或不在当前权限范围内。
- `searchDismissRecord` 返回的列表字段由后端决定，某字段缺失或 null 表示该信息无值或未配置，不解读为异常。
- `getDismissPendingIssueTotal` 的待办项、数量与口径以企业配置为准；若返回 null/缺失，表示未启用该待办类型或无数据，不等于「已完成」。
- 权限不足时，工具会返回明确提示；向用户转述时只说明「当前权限无法查看」，不展示原始错误码或内部标识。

## 安全边界

- 数据范围以系统授权可见的离职记录为界，不查询在职员工、不越权查看他人隐私。
- 不虚构工具未返回的员工、待办项、审批状态或统计数据。
- 不向用户展示访问令牌、内部接口路径、原始字段枚举值或技术响应。
- 面向用户只用业务语言：没查到说「没有查到相关离职记录/待办」，不说「返回为空 / 字段缺失」。
- 不用缓存结果冒充实时数据；用户每次问的时间范围、筛选条件变化时都重新查询。
- 出现未登录或授权失效时，提示用户重新连接连接器后重试，不要求在聊天中粘贴任何登录凭证。