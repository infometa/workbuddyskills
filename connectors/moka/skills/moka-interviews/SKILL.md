---
name: moka-interviews
display_name: Moka 面试
display_name_en: Moka Interviews
description: Moka 面试查询。查与我相关的面试安排、某位候选人的面试记录与面试官评价、某场面试的纪要与转写，看招聘团队的面试总览（今天/明天及以后/昨天及以前），以及企业的面试轮次与评价表配置。当用户问自己的面试安排、候选人面试履历、面试纪要、团队面试总览或面试准备时使用。
description_zh: 面向面试官与招聘负责人的面试查询。查与我相关的面试安排（我要参加的、我安排的）、某位候选人的全部面试记录与面试官评价、某一场面试的纪要与转写原文；看招聘团队的面试安排总览（按今天/明天及以后/昨天及以前分组）；查企业的面试配置（分几轮、每轮评价表考察什么）。当用户问「我今天有没有面试」「这个候选人面到第几轮了、评价怎么样」「那场面试聊了什么」「今天公司有哪些面试」「二面要考察什么」时使用。
description_en: Interview lookup for interviewers and recruiting owners. Checks the interviews related to me (ones I attend or arrange), a candidate's full interview records with interviewer evaluations, and the meeting summary and transcript of a specific interview; shows the recruiting team's interview overview grouped by today / tomorrow-and-later / yesterday-and-earlier; and reads the company's interview setup (rounds and feedback templates). Use it for questions like "do I have interviews today", "which round is this candidate at and how were the evaluations", "what was discussed in that interview", "what interviews does the company have today", or "what should round two assess".
category: productivity
version: 1.0.0
author: Moka
---

# 面试查询与准备

查面试安排、候选人面试履历、面试纪要，看团队面试总览与企业面试配置。只编排以下三个工具：

- `mcp__moka__get_interview_records`
- `mcp__moka__list_interview_overview`
- `mcp__moka__get_interview_setup`

## 选择工具

`mcp__moka__get_interview_records` 按 view 分三个视角，选择规则：

- `view="my_list"`（缺省）：**与我相关**的面试安排——「我今天有没有面试」「我还有几场没写反馈」。按分组（即将开始/未反馈/已反馈/已失效）返回各分组数量与面试列表，只给反馈状态、不含评语正文。
- `view="by_candidate"`：**某位候选人**的面试履历——「他面到第几轮了」「面试官对他评价怎么样」。返回每轮面试与各面试官的反馈状态、评价结论与评语；需要评价表逐题作答明细时再开启对应的明细开关（内容会明显变长）。
- `view="summary"`：**某一场面试**的纪要与转写——「那场面试聊了什么」「纪要发我看看」。默认只返回纪要正文，仅在用户明确要看原话、要核对细节时才开启转写开关。

另外两个工具：

- 「今天**公司/团队**有哪些面试」「明天还有多少场」「昨天的面试都反馈了吗」：用 `mcp__moka__list_interview_overview`（HR 视角总览）。按「今天/明天及以后/昨天及以前」三档分组返回数量与列表，支持按职位归属筛选。只问「我自己」的面试用 `mcp__moka__get_interview_records` 的 my_list，不要用总览。
- 「我们面试分几轮」「二面要考察什么」「面试该问些什么」：用 `mcp__moka__get_interview_setup`。这是**企业配置**——view=rounds 看轮次清单，view=feedback_template 按「职位+第几轮」看评价表模板（评价维度、题目与面试参考问题）。它不是某位候选人的面试情况，别与面试记录混答。

概念辨析：

- **面试记录 vs 面试纪要**：记录是「面了几轮、谁面的、评价结论与评语」，来自面试官填写；纪要是会议的自动整理稿与逐句转写，由语音识别产生，可能有错漏、不等于面试结论。问评价看记录（by_candidate），问「聊了什么」看纪要（summary）。
- **我的面试的两种归属**：「我要参加的」（本人是面试官）和「我安排的」（本人是负责人，自己不一定上场）是 my_list 的两个口径，用户没明确区分时两者都查，明确说了再收窄。

候选人的简历与流程阶段、面试变更类系统通知、多场面试的对比分析——这些问题应由当前可用的其他 Moka 工具处理。

## 常见问题速查

- 「我今天有没有面试」「我还有几场没写反馈」→ `mcp__moka__get_interview_records`（view=my_list）
- 「他面到第几轮了、评价怎么样」→ `mcp__moka__get_interview_records`（view=by_candidate）
- 「那场面试聊了什么」→ `mcp__moka__get_interview_records`（view=by_candidate 拿句柄 → view=summary）
- 「今天公司有哪些面试」→ `mcp__moka__list_interview_overview`
- 「我们面试分几轮」「二面要考察什么」→ `mcp__moka__get_interview_setup`

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件（日期、候选人姓名、分组），不自行扩展；相对日期按用户所在时区换算成绝对日期再传，回答里说明实际查询的日期。
3. my_list 的归属看返回项的 interviewerIsMe / arrangerIsMe，不要拿姓名去猜：interviewerIsMe=true 才是用户本人要出席、要提交反馈的场次；arrangerIsMe=true 是用户安排的，反馈由对应面试官提交、不是用户欠的。
4. 问「我自己」欠的反馈用 `scope="mine"`（或只统计 interviewerIsMe=true 的条目）；问「我安排的」用 `scope="arranged"`；未明确区分时用缺省 all——但直接汇总 all 会把别人欠的反馈说成用户自己的。
5. 纪要走两段式句柄传递：先 `view="by_candidate"`（applicationId 来自候选人清单、招聘通知或 my_list 返回项）查该候选人的面试场次，再把**同一条**返回项的 interviewRecordId 与 applicationId 成对传给 `view="summary"`。
6. 返回项标记没有纪要（hasInterviewSummary=false）的场次不必再查纪要；纪要正文原样引用，不要再做一次总结。
7. my_list 查未反馈/已反馈/已失效分组时，不传日期范围默认只看最近 90 天；要查更早的面试必须显式传日期。
8. 评价表查询先有职位再有轮次：轮次可先用 `mcp__moka__get_interview_setup`（view=rounds）确认企业配置了哪些轮次；职位 ID 来自职位查询结果。
9. 数「几场面试」要去重：同一场面试多位面试官时 my_list 每位面试官一行（按时间+候选人去重）；总览的行粒度是「面试×申请」，集体面试每位候选人一行（按时间+面试官去重）。
10. 轮次名称、评价表题目由企业自行配置，原样引用，不要翻译或改写。

## 结果与权限

- 空结果一律按「未返回数据」如实说明：既可能确实没有面试，也可能当前账号没有可查看的职位数据权限（两者返回形态相同、无法区分），不要断言「今天没有面试」。
- 评价可见范围受招聘角色权限控制：反馈状态显示「已反馈但当前不可见」时，表示当前账号看不到评价详细内容——这不代表评价是负面的，不要推测内容，如实说明即可。
- 只有通过在线会议进行或开启了纪要的场次才有纪要；不能生成或重新生成纪要（需在 Moka 页面操作），生成中的场次如实说明状态、不等待。
- 该职位该轮次未返回评价表模板时如实说明：可能这一轮没有配置固定评价表，也可能轮次序号不存在，可先确认轮次清单。
- 角色门槛：`mcp__moka__get_interview_records` 需要面试官及以上；`mcp__moka__list_interview_overview` 需要 HR 角色；`mcp__moka__get_interview_setup` 仅需登录。被拒绝时如实说明权限边界，不要换身份绕行。
- 工具返回的 notices 与 message 是数据解读须知，先读再组织回答，如实转达；分组数量以返回的 counts 为准。
- 全部只读：不能安排、改期或取消面试，不能代替面试官提交反馈，这些操作需要用户在 Moka 页面完成。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；申请 ID、面试场次 ID、职位 ID 只用于串联工具，不出现在回答里。
- 候选人与面试官的电话、邮箱等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 只使用工具返回的字段组织回答，不虚构评价内容或纪要。
- 他人的评价与面试信息按当前账号可见范围使用，不扩散给无关的人。
