---
name: xrxs-employee-pending-entry
display_name: 检查待入职员工必填信息
display_name_en: Check Pending Employee Entry Required Information
description: 帮助 HR 检索待入职员工的入职记录，并查看可用于入职搜索的过滤字段，从而按姓名、手机号、工号或自定义筛选条件定位待入职人员并检查其信息填写情况。仅覆盖员工入职记录与入职搜索条件配置，不处理转正、调岗、离职等其他人事流程。当用户问「帮我查待入职员工」「入职记录能按哪些条件筛选」「张三的入职记录」「哪些待入职人员还没填某信息」时使用。
description_zh: 帮助 HR 检索待入职员工的入职记录，并查看可用于入职搜索的过滤字段。支持按姓名/手机号/工号等关键字搜索，也支持按入职日期、部门、岗位等自定义筛选条件定位待入职人员，进而检查其信息填写情况。数据边界为“员工入职记录”与“入职记录搜索过滤条件配置”，不覆盖转正、调岗、离职等其他人事流程，也不直接给出“必填项是否缺失”的系统校验结论。典型问句：「帮我查待入职员工」「入职记录能按哪些条件筛选」「张三的入职记录」「哪些待入职人员还没填某信息」。
description_en: Helps HR retrieve pending employee entry records and view available search/filter fields. Supports keyword search by name/mobile/employee number, as well as custom filters such as entry date, department, or position to locate pending hires and check their information completeness. Limited to employee entry records and entry-record filter configuration; does not cover confirmation, transfer, resignation, or other HR workflows, nor does it directly return system validation of missing required fields. Use for questions like 'look up pending employees', 'what filters are available for entry records', 'Zhang San's entry record', or 'which pending employees have not filled in certain information'.
category: data
version: 1.0.0
author: 薪人薪事
---

# 检查待入职员工必填信息

帮 HR 检索待入职员工的入职记录，并获取入职搜索可用的过滤字段。只编排以下 2 个工具：

- `mcp__xrxs_base_getEmployeeFilterFields`
- `mcp__xrxs_employee_searchEntryRecord`

## 选择工具

- 问「帮我查一下待入职员工」「入职记录里有哪些人」「搜索待入职名单」——`mcp__xrxs_employee_searchEntryRecord`，可直接用 `keyword`（姓名/手机号/工号等）搜索，也可配合 `pageNo`/`pageSize` 分页；没有额外条件时无需传入 `filters`，默认按第 1 页返回。
- 问「能按哪些字段筛选入职记录」「入职搜索有哪些过滤条件」——`mcp__xrxs_base_getEmployeeFilterFields`，必须传 `filterBizType=2`（入职记录业务）和 `keyword`（筛选项关键字），返回的字段配置用于后续构造 `searchEntryRecord` 的 `filters`。
- 问「按入职日期、部门、岗位等条件查待入职员工」「待入职人员中符合某条件的有谁」——`mcp__xrxs_base_getEmployeeFilterFields` / `mcp__xrxs_employee_searchEntryRecord` 两段式：先以 `filterBizType=2` 取字段配置，再按字段类型把用户选中值填入 `values` 或 `dateValues`，最后调用 `searchEntryRecord` 的 `filters` 查询。
- 问「张三的入职记录」「查某个人的待入职信息」——`mcp__xrxs_employee_searchEntryRecord`，把姓名、手机号或工号等放入 `keyword` 即可单步直达搜索。
- 问「下一页」「每页显示多少条」「入职记录总共有几页」——`mcp__xrxs_employee_searchEntryRecord`，通过 `pageNo` 翻页，`pageSize` 默认 20、最大 100。

易混概念先分清再回答：

- **过滤条件配置 vs 入职记录数据**：`mcp__xrxs_base_getEmployeeFilterFields` 返回的是筛选项“配置”，不是员工数据；真正的入职记录列表由 `mcp__xrxs_employee_searchEntryRecord` 返回。
- **两个 keyword 含义不同**：`getEmployeeFilterFields` 的 `keyword` 用于匹配筛选项名称；`searchEntryRecord` 的 `keyword` 用于匹配员工姓名/手机号/工号等。
- **`filterBizType` 必须选对**：只有 `filterBizType=2` 才对应入职记录筛选字段；使用 `1` 拿到的是员工搜索字段配置，不能直接用于入职记录搜索。
- **筛选值构造依赖字段类型**：`filters` 中的 `values`/`dateValues` 必须按返回的 `fieldFilterType` 规则填写，不是任意文本；`dateValues` 用于日期类型，`values` 用于选项/数字/文本/部门/岗位/员工等类型。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展查询范围，也不替用户补齐未提及的筛选条件。
3. 相对日期（「今天」「本月」「最近 7 天」）需换算成绝对日期后再调用；日期类型筛选使用 `dateValues`，格式为 `yyyy/MM/dd` 时间戳，区间用 2 个元素 `[开始, 结束]`，单边留空传空串。
4. `mcp__xrxs_base_getEmployeeFilterFields` 的 `filterBizType` 必须传 `2`（入职记录），`keyword` 必填，用于命中筛选项名称；返回的字段配置中 `dataSource` 仅在构造筛选值时参考，回传给 `searchEntryRecord` 时不含 `dataSource`。
5. 将 `getEmployeeFilterFields` 返回的字段配置映射为 `searchEntryRecord` 的 `filters`：`fieldFilterType=1` 日期类型用 `dateValues`；其余类型按规则用 `values`，`key` 取对应 ID 或选项 key；只包含用户明确选中的筛选项。
6. `mcp__xrxs_employee_searchEntryRecord` 的 `pageNo` 从 1 开始，默认 1；`pageSize` 默认 20，最大 100；`keyword` 与 `filters` 只传用户已明确提供的条件。
7. 条件筛选必须先走后端认可的两段式：先取字段配置，再构造 `filters` 搜索；没有筛选需求时可直接用 `keyword` 单步搜索。
8. 若用户表达“必填信息缺失/未填写”，本工具无法直接返回系统校验结论，只能通过对应字段是否为空/未填来推断，且前提是该字段本身属于可搜索字段。
9. **入职记录状态过滤**：若查询目标为“待入职员工”，必须先通过 `getEmployeeFilterFields` 取「入职记录状态」字段，并构造 `filters` 仅保留待入职状态（默认排除已入职、已放弃/已取消等状态）；这是本技能的固定行为，即使用户未提及状态也须带上。

## 结果与权限

- 空结果一律按「未查询到符合条件的入职记录」处理，不得反推为“没有待入职员工”或“数据不存在”。
- `searchEntryRecord` 返回的业务数据以实际 `data` 对象为准，不凭空补全总页数、总条数等未返回字段。
- 入职记录中某字段为 null 或缺失，仅表示该字段无值或企业未配置展示，不要直接解读为“必填信息缺失”或“信息异常”。
- `getEmployeeFilterFields` 返回空字段列表，说明 `keyword` 未命中任何筛选项，应提示用户换关键词重试。
- 工具返回非成功状态时，如实转述其 `message`，不根据状态码或技术文案猜测根因。

## 安全边界

- 数据面仅限当前用户权限范围内的入职记录，不越权查询他人或租户外的数据。
- 不虚构工具未返回的字段、记录或“必填项缺失”结论；工具没给的口径不用常识补全。
- 面向用户只用业务语言：没数据说「没有查到」，不说「返回为空/字段缺失」；不主动向用户展示参数名、内部标识符或原始响应。
- 不用缓存结果冒充实时数据；每次查询条件或页码变化都重新调用。
- 出现未登录或授权失效时，提示用户重新连接连接器后重试，不要求用户在聊天中粘贴任何登录凭证。