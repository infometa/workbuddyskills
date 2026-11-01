---
name: beisen-applicant-follow-up
version: 3.2.1
description: "北森应聘者跟进。用于查看应聘者当前进展、查询某职位下的申请列表、筛出待处理简历、查看面试中应聘者、跟进待发 Offer 应聘者、核对待入职应聘者、查看候选人申请详情。当用户询问候选人、应聘者、申请、简历筛选状态、面试阶段名单、Offer/入职状态或某个应聘者详情时使用。"
author: beisen
display_name: "北森应聘者跟进"
display_name_en: "Beisen Applicant Follow-up"
description_zh: "北森应聘者跟进。用于查看应聘者当前进展、查询某职位下的申请列表、筛出待处理简历、查看面试中应聘者、跟进待发 Offer 应聘者、核对待入职应聘者、查看候选人申请详情。当用户询问候选人、应聘者、申请、简历筛选状态、面试阶段名单、Offer/入职状态或某个应聘者详情时使用。"
description_en: "Beisen applicant follow-up. Use to view an applicant's current progress, query the application list under a job, filter out resumes pending action, view candidates currently interviewing, follow up on applicants awaiting an Offer, verify applicants pending onboarding, and view a candidate's application details. Trigger when the user asks about candidates, applicants, applications, resume-screening status, interview-stage lists, Offer/onboarding status, or the details of a specific applicant."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森应聘者跟进

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 绝对禁止
- 禁止执行额外输出，严格按照skill要求输出内容
- 查询结果请严格检查应聘者姓名等信息，不要出现串行等展示问题

## 严格要求
- 若当前智能体支持StructuredContent前端扩展展示，智能体不需要根据data.items做分析&展示，只输出StructuredContent扩展的前端组件即可，不做具体解读。

## 业务边界
处理进入招聘流程后的应聘者与申请记录：
- 查看应聘者当前进展、所在阶段与状态。
- 筛出某职位下待处理/未筛选简历。
- 查看面试中、待发 Offer、待入职的应聘者。
- 查看某个应聘者的申请详情。
- 从招聘进展统计项下钻到具体申请明细。

不处理职位 JD 与职位详情；职位定位需要职位标识时先使用 [beisen-job-management](../beisen-job-management/SKILL.md)。不处理人才库主动搜寻与职位 AI 推荐，走 [beisen-talent-sourcing](../beisen-talent-sourcing/SKILL.md)。不处理我的招聘待办总览，走 [beisen-recruiting-todo](../beisen-recruiting-todo/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配"查询应聘者申请列表"，"查询候选人申请详情"，"获取申请列表可筛选字段数据源"，"获取可用流程"类工具。
- **参数构造（查询应聘者申请列表）**：完全依赖该工具自身的 inputSchema。业务上支持的筛选维度：
  - **职位标识**（必填）：必须来自职位查询或招聘进展返回，严禁编造。
  - 应聘者姓名搜索。
  - 流程阶段/阶段状态筛选（如"面试""Offer环节""面试中"）。
  - 流程筛选，由"获取可用流程"筛选获得
  - 筛选结果（如未筛选/待处理）、AI 简历评估结果（如非常符合/基本符合/不符合）。
  - 面试状态（未安排/已安排）、Offer 状态（待发/已发/已接受/已拒/已入职）、入职状态（待入职/已入职）、签到状态（未签到/已签到/未到场）。
  - 进展统计下钻批次标识：来自招聘进展统计项返回，**必须与同一职位的职位标识配套使用**。
  - 学校：按学校名称直接传文本。
  - 标识从"获取申请列表可筛选字段数据源"，请先调用此工具获取数据源后进行转换
  - 分页参数（页码起始值以 schema 为准）。
  - 以上维度的具体字段名与枚举取值一律以 inputSchema 说明为准。
- **参数构造（查询候选人申请详情）**：申请标识必须来自申请列表、待办或招聘进展下钻的返回，严禁编造；支持批量传多个申请标识。
- **结果展示**：
  第一优先级：若当前智能体支持StructuredContent前端扩展展示，智能体不需要根据data.items做分析&展示，只输出StructuredContent扩展的前端组件即可，不做具体解读。
  按工具 outputSchema 与返回说明解读。
  - 返回读取（查询应聘者申请列表）：
    - `data.items` 是申请列表，通常含 `applyId`、`applicantId`、姓名、学历、学校、专业、最近公司、最近职位、工作年限、投递渠道、阶段状态、AI 评估结果、申请时间。
    - `data.totalCount` 是当前筛选条件下申请总数。
    - 若已展示条数小于 `totalCount`，提示用户可继续翻页。
    - `data.StructuredContent` 是用于扩展展示信息，
  - 返回读取（查询候选人申请详情）：只用于回答用户关注的应聘者，不扩散无关候选人信息。

## 工作流程

1. 用户问某职位下的候选人/申请时：先确认职位标识（必要时经 beisen-job-management 搜索定位），再按筛选维度查询列表。
2. 用户按学历、性别、毕业学校类型、测评结果、最近 AI 面试结果、求职意向、面试站点或自定义字段筛选时：先调用获取申请列表可筛选字段数据源工具，取得字段编码与 DsValue 可选项后再构造筛选参数。
3. 已展示条数小于返回总数时，提示用户可继续翻页。
4. 用户关注某个候选人时，用列表/待办/下钻返回的申请标识查询详情。

## 输出要求

- 候选人/应聘者信息属于 L2 敏感数据，只展示业务摘要，不回显原始返回。
- 列表建议展示：姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、AI 评估结果、AI 评估理由、最初投递渠道、申请创建时间、所在阶段状态。
- 只展示中文语义值，不展示字段名、枚举数字、内部 ID。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
