---
name: moka-my-attendance
display_name: Moka 我的出勤
display_name_en: Moka My Attendance
description: 员工本人的假期余额与考勤自助查询。查每种假期的可用余额、请假单位与过期提醒；按天看打卡明细与请假/补卡等单据状态，按月看出勤月报统计，查本人加班记录与结算说明。当用户问「我还有几天年假」「我今天打卡了吗」「我这个月迟到了几次」「我的加班怎么结算」时使用。
description_zh: 面向全体员工的本人假勤自助查询。查每种假期的可用余额、请假单位与过期提醒；按天看打卡明细与请假/加班/出差/补卡等单据状态，按月看出勤月报统计，查本人加班记录与结算说明。仅覆盖本人数据，不回答团队或他人考勤。当用户问「我还有几天年假」「我今天打卡了吗」「我这个月考勤怎么样」「我的加班怎么结算」时使用。
description_en: Personal leave and attendance self-service for all employees. Check each leave type's balance, unit and expiry notice; view daily clock-in details with request status, monthly attendance reports, and personal overtime records with settlement notes. Covers only the current user's own data, never team or other people's attendance. Use for questions like "how many annual leave days do I have left", "did I clock in today", or "how is my attendance this month".
category: productivity
version: 1.0.0
author: Moka
---

# 我的假勤

帮员工查清自己的假期余额与出勤情况。只编排以下两个工具：

- `mcp__moka__get_my_leave_balance`
- `mcp__moka__get_my_attendance`

## 选择工具

- 问假期余额：还剩几天年假、调休还有多少、假期什么时候过期、某种假怎么用——`mcp__moka__get_my_leave_balance`，无需入参，单步直达。
- 问某一天或某几天的情况：打卡时间与结果、班次名称——`mcp__moka__get_my_attendance` 按天明细（传 beginDate，可选 endDate）。
- 问单据状态：「我上周三的请假审批通过了吗」「补卡单批了没」——同样查按天明细，请假/加班/出差/外出/补卡单据带审批中/已通过/已驳回/已撤回状态，以单据状态回答。
- 问整月情况：出勤天数、迟到/早退/旷工/缺卡等异常统计、加班/请假/出差时长汇总、月报——`mcp__moka__get_my_attendance` 月报（传 month，或全部缺省 = 当前月）。
- 问加班：这个月加了几次班、加班时长——`mcp__moka__get_my_attendance` 加班视角（view="overtime"）查记录列表。
- 问某条加班怎么结算（调休还是加班费、按什么规则算）——把加班列表返回项的 overtimeRecordId 回传同一工具，取该条的结算说明。
- 问「我这周出勤怎么样」——按天明细传 beginDate 与 endDate（一周恰好在 7 天跨度内），逐日汇报。

易混概念先分清再回答：

- **月报 vs 逐日记录**：月报是整月汇总，具体某天的打卡与单据细节要查按天明细。两者是同一工具的两种视角：传 month 看月报，传 beginDate 看逐日。
- **本人考勤 vs 团队考勤**：本技能只回答「我」的假勤。问「团队 / 我下属 / 某个部门」的出勤，这些问题应由当前可用的其他 Moka 工具处理，不要用本人数据代答。
- **余额 vs 单据**：`mcp__moka__get_my_leave_balance` 只给假期账户余额与使用说明，不含请假单及其审批状态；请假单据在 `mcp__moka__get_my_attendance` 的按天明细里。
- **加班记录 vs 月报里的加班汇总**：月报只给整月加班时长的汇总数，逐条加班记录与单条结算说明在加班视角里，问「加了哪几次班」不要拿月报汇总凑数。
- **申请时长、打卡时长、结算时长**：加班的三个数字口径不同，以工具返回的说明为准，不要互相替代。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展查询范围，也不替用户补时间条件。
3. 相对日期（「今天」「上周三」「这个月」）按 Asia/Shanghai 换算成绝对日期或月份再调用，回答里说明实际查询的日期或区间。
4. 视角明确时显式传 view（daily / monthly / overtime）；缺省时按入参推断——传 beginDate 走按天明细，传 month 或全部缺省走月报。
5. 单日查询只传 beginDate；endDate 缺省 = 仅查当天。按天明细是闭区间且跨度最多 7 天，更长的区间分段查询，或先用月报定位异常日期再按天下钻。
6. beginDate/endDate 与 month 互斥，不要同时传入。
7. 加班结算两段式：先用 view="overtime" 查加班记录列表，再把列表返回项的 overtimeRecordId 回传同一工具；overtimeRecordId 不与日期范围同传。
8. 加班列表支持分页：回答「加了几次班」以返回的总条数为准，需要更多记录就翻页，只汇报实际取到的范围。
9. 典型链路——考勤异常排查：先查月报（传 month 或缺省）定位有异常的日期，再改传 beginDate 看该天的打卡与单据明细，一次把「哪天异常、当天发生了什么」答完整。

## 结果与权限

- 空结果一律按「未返回数据」处理，不得反推为无权限，也不要断言「没有请假 / 没有加班」。
- 结果自带的 notices 是数据解读须知（联合假口径、null 余额语义、单位差异、账期与封存口径等），组织回答前先读，与结论相关的提醒如实转达。
- 假期余额列表中可能混入「联合假」聚合行（若干成员假期余额之和）：合计假期总数时不可把联合假与其成员假期相加，否则重复计算。
- 余额为 null 或缺失不等于余额为 0：可能是该假期不限额，或未向本人开放余额查看。
- 请假单位（天/小时/分钟）因假期类型而异，跨类型的时长不可直接相加或比较，单位以返回的文本为准。
- 月报的统计项由企业配置决定：某一项没出现在返回里，是企业没启用这项统计，不代表该项为 0。
- 月报带考勤账期与封存状态：账期口径以返回说明为准，不要按自然月自行换算；已封存表示该月数据已定稿。
- 按天明细里某字段为 null 或缺失表示该项无数据或企业未启用，不要解读为考勤异常。
- 查询过早的历史日期或月份可能超出企业允许员工查看的账期范围，工具会明确提示，如实转达。
- 企业未向员工开放出勤查询或假期账户时，工具会返回明确提示，如实转达其 message，不自行改写归因。
- 工具结果非成功时必有面向用户的 message，如实转述，不根据公开文案猜测技术根因。

## 安全边界

- 数据面仅限本人：两个工具都只返回当前用户自己的数据，不能用来查询他人或团队的假勤。
- 不向用户展示访问令牌、内部标识符或原始技术响应。
- 不虚构工具未返回的字段、单据或统计项；工具没给的口径不用常识补全。
- 面向用户只用业务语言：没数据说「没有查到」，不说「返回为空 / 字段缺失」，不引用参数名、枚举值或状态码。
- 不用缓存结果冒充实时数据；每次问的日期或月份变了就重新查询。
- 出现未登录或授权失效时，提示用户重新连接 Moka 连接器后重试，不要求用户在聊天中粘贴任何登录凭证。
