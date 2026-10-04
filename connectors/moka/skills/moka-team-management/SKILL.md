---
name: moka-team-management
display_name: Moka 团队管理
display_name_en: Moka Team Management
description: 管理者的团队信息与团队考勤查询。查自己管理范围内的部门层级与成员名单、某位成员的档案（任职、履历、合同、绩效等按权限开放的信息域），以及团队出勤概况、某天具体谁迟到/请假/未排班、按月逐个成员的考勤统计。当部门负责人问「我团队有哪些人」「张三的档案」「今天团队谁迟到了」「这个月谁加班最多」时使用。
description_zh: 面向部门负责人与有汇报下属的管理者（非人事角色）的团队查询。查自己管理范围内的部门层级与成员名单、某位成员的档案（任职、个人信息、履历、合同、绩效结果等按权限开放的信息域），以及团队出勤三视角——出勤概况（按日或按月）、某天某一类的具体名单（谁迟到、谁请假、谁未排班）、按月逐个成员的考勤指标对比。可见范围恒为「所选部门及其子部门 ∩ 本人管理范围」，全部只读。当用户问「我管的部门有哪些」「销售部有哪些人」「今天谁没来」「这个月谁迟到最多」时使用。
description_en: "Team queries for department managers and leaders with direct reports (not an HR role). Browse the departments under the user's management scope and member rosters, read a member's profile (employment, resume, contract, performance results — whatever the account may see), and check team attendance in three views: daily or monthly overview, the exact list of who was late / on leave / unscheduled on a given day, and per-member monthly statistics. Visibility is always the selected department subtree intersected with the user's authorized scope; everything is read-only. Use for questions like \"which departments do I manage\", \"who is on my team\", \"who was late today\", or \"who worked the most overtime this month\"."
category: productivity
version: 1.0.0
author: Moka
---

# 团队管理

帮管理者看清自己管理范围内的组织、成员与出勤。只编排以下三个工具：

- `mcp__moka__list_team_members`
- `mcp__moka__get_team_member_profile`
- `mcp__moka__get_team_attendance`

## 选择工具

- 问「我管哪些部门」或需要部门 ID：`mcp__moka__list_team_members` 的 view="departments"——列出有管理范围的部门层级，可用 parentDeptId 逐层展开或用 keyword 按名称搜索。所有团队查询的 deptId 都只能来自这里，不能凭部门名猜。
- 问「某部门有哪些人 / 团队里有没有叫某某的」：`mcp__moka__list_team_members` 的 view="members"（deptId 必填），返回姓名、工号、部门与在职状态，可按姓名或工号搜索。
- 问某位成员的具体信息（任职、职级、入职日期、履历、合同、绩效结果、目标等）：`mcp__moka__get_team_member_profile`。
- 问团队某天或某月的整体出勤（应到实到、各类异常人数、环比）：`mcp__moka__get_team_attendance` 的 view="summary"——传 day 看当天，传 month 看整月总览，都不传 = 今天。
- 问某天具体是谁（谁请假、谁迟到、谁没排班）：view="records"，必传 day 与 recordType。
- 问按月逐人对比（谁加班最多、谁的假快用完了）：view="member_stats"，可按指标排序、筛选并分页。

易混概念先分清再回答：

- **成员名单 vs 成员档案**：名单回答「这个部门有哪些人」，档案回答「这个人的任职、履历、合同等具体信息」。查某个人先从名单拿到姓名或工号。
- **本人 vs 团队**：问用户「我自己」的考勤、档案、假期，这些问题应由当前可用的其他 Moka 工具处理，不要用团队能力查本人。
- **没有团队管理范围 ≠ 团队没有异常**：用户没有管理范围时工具会明确报出来，如实转述；绝不能因为拿不到数据就回答「今天没有人迟到」。
- **统计项由企业配置决定**：异常类型与成员统计指标不是固定全集，某一项没出现在返回里是企业没启用，不代表该项为 0；成员统计启用了哪些指标以返回的 availableFields 为准。
- **在职状态**：成员名单带在职/试用期/待入职/已离职状态，回答「团队有多少人」时说明统计口径，不要把待入职或已离职混进在职人数。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展关键词、日期或筛选指标。
3. 相对日期（「今天」「这个月」）按 Asia/Shanghai 换算成绝对日期或月份再调用，回答里说明实际查询的日期或区间。
4. 团队考勤的 deptId 可缺省，缺省即「我管理的全部人」——用户没指定部门时不必先查部门层级。
5. 成员名单与成员档案的 deptId **必填**，先用 view="departments" 取得；要按具体部门看考勤时同样从这里取 deptId。
6. 成员档案按「部门 + 姓名或工号」定位（deptId + keyword），工具就是这样设计的，不接受员工 ID；工号更精确。命中多人时让用户确认，再用工号重查。
7. 要看成员的履历、合同、培训等具体信息域：先按缺省域拿到档案，再用返回的 availableScopes 里的域名作为 dataScopes 重查。某个域提示需改用其他能力时按提示走，不要硬要本工具给数据。
8. 考勤最常用链路：view="summary" 传 day 看各类人数 →（同一个 day + 对应 recordType）→ view="records" 看具体是谁。问「有几个人迟到、都是谁」要一次走完。
9. 月度链路：view="summary" 传 month 看整月各项与环比 → view="member_stats" 按指标排序或筛选逐个成员对比。
10. 视角专属参数不要串用：recordType 仅 view="records"，排序与指标筛选仅 view="member_stats"；records 按天查、member_stats 按月查。
11. 成员名单单次最多 50 人且不支持翻页：总数大于返回条数时用 keyword 收窄或按子部门查询，不要把已列出的人数说成总人数。

## 结果与权限

- 数据面恒为「所选部门及其子部门 ∩ 本人管理范围」：同一个部门，不同管理者看到的人不同；名单人数可能少于部门实际规模，名单也不含用户本人。这不是故障，如实按返回口径汇报。
- 没有团队管理范围时，工具会明确拒绝并给出面向用户的说明，如实转述，不要换其他能力绕行；该功能面向部门负责人与有汇报下属的管理者。
- 空结果一律按「未返回数据」处理，不得反推为无权限，也不得反过来把无权限说成没有数据。
- 团队考勤结果会回显本次实际统计的部门：deptId 缺省时即管理范围的顶层，按返回口径说明统计覆盖了谁。
- 传入不在管理范围内的部门不会看到范围外的数据：结果只会是该部门与本人管理范围的交集，可能为空，如实按返回汇报。
- 只有汇报下属、没有部门负责人身份的管理者可能无法按部门查名单；这种情况按工具提示直接用团队考勤视角看下属数据。
- 成员档案字段为空表示「未开放查看或未录入」两种可能，不要断言该员工没有这项信息；某个信息域不在 availableScopes 里是没对当前账号开放，不是不存在。
- 绩效结果最多返回最近几次已归档记录，员工目标按当前账号可见范围过滤，如实呈现可见部分。
- 结果自带的 notices 说明各视角的统计口径与空态语义，组织回答前先读，与结论相关的提醒如实转达。

## 安全边界

- 团队数据是管理者视角的同事数据，只在用户为了管理团队而提问时使用：如实呈现名单、任职与统计，不做绩效评判或人员比较的引申结论，不把某位成员的情况转述给无关的人。
- 成员不在可见范围时工具会明确拒绝，如实转述，不尝试构造或猜测标识去绕行。
- 全部只读：不能审批、修改考勤或变更组织与成员信息。
- 不向用户展示访问令牌、内部标识符或原始技术响应；不虚构工具未返回的字段。
- 面向用户只用业务语言，不引用参数名、枚举值或状态码；出现未登录或授权失效时，提示重新连接 Moka 连接器后重试。
