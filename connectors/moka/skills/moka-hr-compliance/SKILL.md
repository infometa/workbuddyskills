---
name: moka-hr-compliance
display_name: Moka 档案合规
display_name_en: Moka HR Compliance
description: 面向人事合规角色的档案与审计查询（含薪酬档案等敏感数据，普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器查询员工的薪资/参保/黑名单专项档案、电子签记录与签署状态、员工信息的操作日志。当用户做档案核查、签署进度跟进或「谁在何时改了什么」的审计追溯时使用。
description_zh: 面向人事合规角色的档案与审计查询（含薪酬档案等敏感数据，普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器查询指定员工的薪资档案、参保档案、黑名单记录三类专项档案，电子签记录与签署状态（按人员汇总、按流程查文件、签署中心列表），以及员工信息的操作日志（谁在何时改了哪些字段）。当用户核查员工档案、跟进文件签署进度或做变更审计时使用。
description_en: Archive and audit queries for HR compliance roles (includes sensitive data such as salary archives; regular employee accounts lack the required permissions). Uses the Moka Connector available on the current platform to query an employee's special archives (salary, social insurance, blacklist), e-signature records and signing status (per-person aggregation, files by flow, signing-center lists), and operation logs of employee data changes (who changed which fields and when). Use it for archive checks, signing progress follow-ups, or change audits.
category: productivity
version: 1.0.0
author: Moka
---

# Moka 档案合规

以人事合规视角核查档案、签署与变更记录，全部只读。只编排以下三个工具：

- `mcp__moka__get_hr_archives`
- `mcp__moka__get_esign_records`
- `mcp__moka__get_operation_logs`

## 选择工具

专项档案用 `mcp__moka__get_hr_archives`，按 `archiveType` 分三类：

- `archiveType="salary"`：薪资档案——薪资明细、方案、生效日期与审批状态摘要，薪酬敏感。
- `archiveType="welfare"`：参保档案——社保与公积金档案摘要、参保状态与事件类型。
- `archiveType="blacklist"`：黑名单记录——字段定义与是否已列入黑名单的状态摘要。

适用于「查看这名员工的薪资档案」「查询参保档案」「确认黑名单状态」等问题。

电子签用 `mcp__moka__get_esign_records`，按查询动作选择：

- 按人员或按业务汇总：文件总数、已签数量与逐文件签署状态，回答「这位员工的文件签完了吗」。
- 签署记录列表：分页查询，可按姓名、签署状态、签署开始/完成时间、法人公司筛选。
- 流程详情：用列表返回的 `flowId` 查单条流程的人员、签署开始时间与文件明细，回答「这条签署记录有哪些文件」。
- 状态统计：对选中的列表记录按签署状态统计数量分布。
- 工作台数量：待发起与待签署的数量。
- 业务文件状态：按业务来源（审批、入职、合同、薪酬、花名册、绩效、试用期、参保档案）查文件状态。
- 签署中心列表：分页浏览签署中心记录，可按部门、时间范围等条件筛选。

审计追溯用 `mcp__moka__get_operation_logs`：分页查询指定员工的操作日志，返回操作时间、操作人、功能模块、操作来源和每次操作的字段变更前后内容，回答「谁在何时改了该员工的哪些信息」。

易混辨析：签署「按人员汇总」回答某个人的整体签署进度，「按流程查文件」回答某条签署记录里有什么，先汇总或列表、再下钻详情；操作日志是员工信息的变更审计，不是签署记录的变更。

员工本人的档案自助查询、假勤薪酬列表盘点、档案与黑名单的修改，不在本技能范围内。这些问题应由当前可用的其他 Moka 工具处理。

## 调用规范

1. 使用 Moka 连接器提供的工具（本技能内的工具名即实际注册名）；连接器未安装或未连接时如实告知用户，不改用其他来源。
2. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源；电子签各查询动作的参数组合以工具实时 description 为准。
3. 只传用户明确给出的条件，不自行扩展时间范围、状态或业务来源；电子签的业务来源仅在用户明确指定时传入，禁止猜测。
4. 句柄先取后用，禁止猜测：
   - 员工标识由业务上下文提供（如花名册等其他查询能力的返回项）。
   - `flowId` 必须来自 `mcp__moka__get_esign_records` 自己的签署记录列表结果。
   - 状态统计的记录标识、法人公司信息同样来自列表返回项。
5. 三个工具都需要目标员工或记录标识才能查询：用户只给了姓名时，先经有权限的查人能力确认唯一身份，再进入本技能的查询；同名时向用户澄清。
6. 列表结果按页返回，只汇报实际取到的范围；操作日志有下一页标记时递增页码继续查询。
7. 批量查询有单次数量上限，超出时分批调用。
8. 相对日期先按用户所在时区换算成绝对日期再调用，回答里说明实际查询的区间。

## 结果与权限

- 空结果一律按「未返回数据」处理：未查到档案记录、日志或签署数据不代表没有权限，也不要断言「确实没有」。
- 工具返回的 notices 与 message 如实转达，先读 notices 再组织回答。
- 三类查询各自要求相应员工数据的管理或查看权限；电子签只返回当前账号可见的数据。
- 签署中心列表的总数口径不可靠时按返回条数与「是否还有下一页」转述，不要编造总数。
- 档案返回中的「是否允许编辑/删除/增减员」等只是状态摘要，描述系统配置而非可执行操作，不要据此承诺可以修改。
- 操作日志按返回内容逐条转述变更前后值，不推断操作动机，不替系统定性「违规」；审计结论由用户自行判断。
- 签署状态按返回的状态与数量如实转述，未完成不等于拒签。

## 安全边界

- 薪资档案、参保档案与黑名单属于高敏数据：只在用户为合规管理目的提问时使用，按问题最小范围呈现，不主动扩散薪酬数值与黑名单信息，不把某位员工的档案转述给无关的人。
- 不向用户展示访问令牌、内部标识符或原始技术响应；员工、流程、记录的标识句柄只用于串联工具，不出现在回答里。
- 不虚构工具未返回的字段；电话、证件、头像等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 全部只读：不支持发起、撤销、下载或修改签署记录，不新增、修改或删除档案与黑名单；用户要操作时引导其在 Moka 页面处理。
