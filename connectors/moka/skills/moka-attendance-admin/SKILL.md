---
name: moka-attendance-admin
display_name: Moka 假勤管理
display_name_en: Moka Attendance Admin
description: 面向考勤负责人与人事管理角色的假勤管理查询（普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器查询员工出勤报表（日历/月报/日报/补卡）、假期账户与请假辅助、加班详情与试算、已发布排班、出差与外出记录。当用户以管理视角查询或核对员工假勤数据时使用。
description_zh: 面向考勤负责人与人事管理角色的假勤管理查询（普通员工账号无相应权限）。使用当前平台提供的 Moka 连接器查询员工出勤报表（日历/月报/日报/补卡）、假期账户与请假辅助、加班详情与试算、已发布排班、出差与外出记录。当用户以管理视角查询员工出勤明细、假期余额与离职清算、加班结算原因、排班与换班、出差行程重叠预检等问题时使用。
description_en: Attendance administration queries for attendance owners and HR admin roles (regular employee accounts lack the required permissions). Uses the Moka Connector available on the current platform to query employee attendance reports (calendar, monthly, daily, patch clock-in), leave accounts and leave-request assistance, overtime details and trial calculations, published shift schedules, and business travel or out-of-office records. Use it when the user asks admin-view questions about attendance details, leave balances and settlement, overtime settlement reasons, shift schedules, or travel overlap pre-checks.
category: productivity
version: 1.0.0
author: Moka
---

# Moka 假勤管理

以考勤负责人视角查询员工假勤数据，全部只读。只编排以下五个工具：

- `mcp__moka__get_attendance_reports`
- `mcp__moka__get_leave_account_details`
- `mcp__moka__get_overtime_details`
- `mcp__moka__get_shift_schedules`
- `mcp__moka__get_business_travel_records`

## 选择工具

出勤报表用 `mcp__moka__get_attendance_reports`，按视图选能力：

- 出勤日历：按月概览、按天反查账期、单日考勤明细（打卡、单据、补卡逐段展开）。
- 考勤月报：先解析月报配置，再查单人月报详情、当前可变更字段、确认详情、封存状态与封存差异。
- 考勤日报：先解析日报配置，再查单日明细，或从月报的某个字段穿透到日报。
- 补卡：补卡记录、补卡月历、某天可补卡时段、当天补卡规则。

假期账户与请假辅助用 `mcp__moka__get_leave_account_details`，分两个视图：

- 账户视图查假期账户，链路是：先按名称消歧假种 → 按人聚合的余额列表 → 单员工单假种的账户明细 → 用假记录；离职场景另有离职清算明细。
- 辅助视图做请假前的只读辅助：某员工的可用假种与余额、请假时长试算、某日可用时间范围、假种时长上限、假种优先级校验。

加班用 `mcp__moka__get_overtime_details`：

- 单条记录：加班记录详情（仅支持按打卡时长结算的记录）、结算说明（结算方式、休息扣除、取整规则、单日上限等完整链路，用来解释「为什么少算/没算」）。
- 申请前辅助：按时段与打卡试算加班时长、员工某日的加班单位与补偿方式、可申请加班时段。
- 集体加班：每人时长试算（含告警与阻断）、审批风险检查、规则配置、申请表单字段标识。

排班用 `mcp__moka__get_shift_schedules`，仅覆盖已发布的排班数据：

- 先按排班组名称消歧换取 `ruleId`，再按员工视角（每人每天排了哪个班次）或班次视角（每个班次每天排了哪些员工）查看某月排班。
- 排班变更记录（谁在何时把谁的班次改成了什么）与换班申请记录（谁和谁换班、审批到哪一步）分页查询。

出差与外出用 `mcp__moka__get_business_travel_records`：

- 出差视图：出差记录分页列表、某员工一段出差时间与已有行程是否重叠的预检、出差城市搜索与地点逐层下钻、员工考勤规则确认。
- 外出视图：外出记录分页列表、按部门查某一天团队外出与出差的合并记录、一段外出的时长试算。

易混辨析：加班的「记录详情/结算说明」只针对已存在的单条记录，需要先有记录标识；「试算」类能力面向尚未提交的时段，两者不要混用。排班查询不含未发布的草稿排班。

员工询问自己本人的考勤、假期余额、加班记录或工资等自助事务，或需要浏览请假/加班/打卡等记录的全量列表、花名册名单时，不要用本技能的工具。这些问题应由当前可用的其他 Moka 工具处理。

## 调用规范

1. 使用 Moka 连接器提供的工具（本技能内的工具名即实际注册名）；连接器未安装或未连接时如实告知用户，不改用其他来源。
2. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
3. 只传用户明确给出的条件，不自行扩展员工、部门、日期或筛选范围。
4. 句柄先取后用，禁止手写或猜测：
   - 员工与部门标识必须来自本技能工具的返回项，或来自花名册、组织查询等能力的查询结果。
   - 月报配置标识与日报配置标识分别来自 `mcp__moka__get_attendance_reports` 对应视图的解析操作，两者语义不同，不可混用。
   - 假种标识来自 `mcp__moka__get_leave_account_details` 的假种消歧或可用假种返回项。
   - 排班组 `ruleId` 来自 `mcp__moka__get_shift_schedules` 的排班组消歧操作，必须原样传递。
   - 加班记录标识来自加班记录列表的查询结果。
5. 消歧结果不唯一时（月报/日报配置、假种、排班组匹配到多个候选），必须让用户从候选中选择，禁止替用户猜测。
6. 日期用 YYYY-MM-DD、月份用 YYYY-MM；相对日期先按用户所在时区换算成绝对日期再调用，回答里说明实际查询的日期或区间。月报账期以配置为准，可能不是自然月。
7. 补卡记录查询必须使用用户明确给出或确认的起止日期，禁止默认查全年。
8. 出差行程重叠预检的起止时间必须使用相同表示法：都用具体时刻，或都用上午/下午，不能混用。
9. 时长试算需要的假种计时单位等伴随参数，从可用假种返回项中原样透传，不要改写。

## 结果与权限

- 空结果一律按「未返回数据」处理：可能是条件过严或范围内确实没有记录，不得反推为无权限，也不要断言「确实没有」。
- 工具返回的 notices 与 message 如实转达，先读 notices、状态与单位再组织回答。
- 本技能需要假勤相关的管理权限，普通员工账号无相应权限；无权限时工具会明确提示，如实转述，不要绕行。
- 试算、预检、校验类结果都是只读辅助：不评估提交资格、不代表可申请成功、不发生任何写入，不要把试算结果说成已生效。
- 加班集体试算里的告警仍可提交、阻断表示超限不可提交，两者语义不同，按返回内容区分转述。
- 余额、时长等字段为 null 表示后端未返回该口径，不要按 0 转述；系统状态标识若无中文映射，只说「状态标识为 X」，不要编造含义。
- 排班员工视角与班次名单有单次人数上限，被截断时按返回的总数说明，不把已列出的人数说成全部。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；员工 ID、配置标识等句柄只用于串联工具，不出现在回答里。
- 不虚构工具未返回的字段；电话、证件、头像等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 本技能是管理视角的他人假勤数据，只在用户为管理目的提问时使用；如实呈现工具返回的记录与统计，不做考勤表现评判的引申结论，不把某位员工的情况转述给无关的人。
- 全部工具只读：修改考勤、发起补卡、提交请假或加班申请、调整排班都不在本技能范围内，请引导用户在 Moka 页面操作。
