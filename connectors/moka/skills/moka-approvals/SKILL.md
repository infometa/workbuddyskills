---
name: moka-approvals
display_name: Moka 审批
display_name_en: Moka Approvals
description: 员工的审批与办事自助。查可发起的流程入口与办事路径、按四个视角看审批待办清单，跟进某个审批的流转进度与驳回意见、查看审批单填写的内容、按流程名找发起链接。当用户问「我要请假去哪里发起」「我有哪些待办」「我的审批到谁了」「审批单填了什么」时使用。
description_zh: 面向全体员工的审批与办事自助。查本人可发起的流程入口（请假、补卡、出差、转正等）与功能页面的操作路径；按「我发起的 / 待我处理 / 我已处理 / 抄送我的」四个视角看待办清单；跟进某个审批的流转进度与驳回意见、查看审批单表单内容、按流程名找发起链接。全部只读，不代替用户发起或审批。当用户问「补卡在哪里申请」「我有哪些待审批事项」「我的请假审批现在到谁了」「这张单子填了什么」时使用。
description_en: Approval and office self-service for all employees. Look up launchable process entries with step-by-step paths, list approval backlogs in four views (initiated, to-do, processed, copied-to-me), follow an approval's progress and rejection comments, read the submitted form content, and find launch links by process name. Read-only; it never submits or approves on the user's behalf. Use when the user asks where to start a request, what is pending on them, where an approval is stuck, or what a form contains.
category: productivity
version: 1.0.0
author: Moka
---

# 审批

帮员工找到办事入口、盯住待办、把审批进度与单据内容查清楚。只编排以下两个工具：

- `mcp__moka__get_my_workspace`
- `mcp__moka__get_my_approvals`

## 选择工具

- 问「请假 / 补卡 / 出差在哪里办」「我能发起哪些流程」：`mcp__moka__get_my_workspace` 的 view="entries"——列出可发起的流程入口与功能页面入口，并给出 PC 与移动端操作路径；只做指引，不代替发起。
- 问「我发起的审批怎么样了」：`mcp__moka__get_my_workspace` 的 view="initiated"，可用 status 筛审批中/已完成/已取消，缺省看审批中。
- 问「我有哪些要处理的」：view="todo"——涵盖审批、绩效、薪酬等各类待办，按类别分组。
- 问「我处理过哪些」：view="processed"。
- 问「抄送给我的」：view="copied"，可用 readStatus 只看未读或已读。
- 问某个审批走到哪了、卡在谁那、为什么被驳回：`mcp__moka__get_my_approvals` 的 action="progress"。
- 问审批单里填了什么（事由、日期、金额等表单内容）：`mcp__moka__get_my_approvals` 的 action="detail"。
- 要发起某个审批的入口链接：`mcp__moka__get_my_approvals` 的 action="launch_link"。

易混概念先分清再回答：

- **四个视角各归各**：「我发起的」是自己提交的申请，「待我处理」是等自己审的，「我已处理」是自己处理过的记录，「抄送我的」只是知会、无需处理。问「我处理过哪些」不要给待处理，问「抄送我的」不要混进待办。抄送条目没有审批状态，要确认结果得再查进度。
- **审批待办 vs 通知**：候选人推荐、面试变更这类招聘提醒不在本技能范围，这些问题应由当前可用的其他 Moka 工具处理。
- **人事审批 vs 招聘审批**：企业开通一体化后，招聘相关审批（如 offer 审批）也会出现在待办清单里，单独归在「招聘审批」类别。这类只能看到标题和时间，没有状态与进度详情——不要拿人事审批的状态去套，也不要说它「没有状态」，而是本能力不提供，需要到 Moka 页面跟进。
- **审批单内容 vs 审批进度**：表单里填了什么是 action="detail"，走到哪个节点、谁在审、为什么被驳回是 action="progress"。按用户实际问的取，别用其中一个回答另一个；既问内容又问进度时两个都调。
- **办事 vs 待办**：「我要办件事」找入口（view="entries"），「有什么事等我办」看待办（view="todo"），两类问题不要串。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展关键词或筛选条件。
3. 进度与详情是两段式：先用 `mcp__moka__get_my_workspace` 待办视角找到目标条目，再把该条目返回的 progressQuery 内容**原样**传给 `mcp__moka__get_my_approvals`（action="progress" 或 "detail"），不要自行构造或改动句柄。
4. progressQuery 为 null 的条目不支持进度与详情查询（招聘审批即属此类），如实说明并提示到 Moka 页面跟进。
5. 视角专属参数不要串用：status 仅 view="initiated"，readStatus 仅 view="copied"，keyword 与分页仅待办四视角；view="entries" 不带参数。
6. action="launch_link" 只按流程名（keyword）或此前返回的候选项（flowDefId）查询，不接受审批实例句柄。
7. 发起入口命中多个流程时先让用户确认再给链接：流程名称是管理员自定义文案，同一业务可能有多个流程，全部列给用户选择，不要替用户挑。
8. 待办条目多时用 keyword 按标题或摘要收窄；分页结果只汇报实际取到的范围，需要完整清单就接着翻页。
9. 用户追问「刚才那条审批」时沿用当前会话已取得的句柄继续查询，不重复检索清单。
10. 典型链路——审批卡在哪：待办清单定位条目 → progressQuery 原样传 action="progress"；审批单填了什么：同一句柄传 action="detail"。一次把「什么单子、到哪了、为什么」答完整。
11. 用户问「我发起的审批都到哪了」这类批量问题：先取清单，再对最相关的前几条逐条查进度，并说明你做了取舍，不要停在清单上。

## 结果与权限

- 空结果一律按「未返回数据」处理，不得反推为无权限，也不要断言「没有待办 / 没有审批」。
- 结果自带的 notices 是数据解读须知（匿名审批、附件占位、链接语义、分组与分页口径等），组织回答前先读，与结论相关的提醒如实转达。
- 待办按类别分组，数量以返回的分组与总数为准，不要自行合并或换算。
- 发起入口视角只列当前员工可见、可发起的流程（已按适用范围过滤）：某流程没出现，说明未向本人开放或企业未配置，如实说明即可。
- 审批单里的附件只有占位信息，内容看不到，不要转述或猜测附件内容。
- 匿名审批节点的处理人按返回的匿名形态如实呈现，不猜测是谁。
- 进度里的驳回意见转达原文，不加工、不替审批人补充理由。
- 工具全部只读：不能代替用户提交申请、通过或驳回审批；用户要操作时给出入口或链接，让本人完成。

## 安全边界

- 数据面仅限本人可见的审批与待办，不能用来查他人的审批。
- 发起链接与操作路径只发给用户本人，不转发到公开渠道。
- 不向用户展示访问令牌、内部标识符、查询句柄内容或原始技术响应。
- 不虚构工具未返回的字段：审批单里没有的内容、无进度详情的条目，都如实说明，不用常识补全。
- 不用缓存结果冒充实时数据：待办与进度随时在变，用户再次询问时重新查询。
- 面向用户只用业务语言，不引用参数名、枚举值或状态码；出现未登录或授权失效时，提示重新连接 Moka 连接器后重试，不要求用户粘贴任何登录凭证。
