---
name: beisen-recruiting-insights
version: 3.2.1
description: "北森招聘洞察。用于查看整体招聘进展、定位流程卡点、查看重点岗位进展、复盘阶段完成量、追踪 Offer 到岗转化，以及发起面试质量分析、竞品情报分析、查看或取消分析异步任务。当用户询问招聘进展、面试进展、阶段完成量、流程瓶颈、重点岗位进展、Offer 到岗转化、面试官提问质量、同职位面试官对比、优秀提问案例、低效面试问题、竞品情报或停止分析任务时使用。"
author: beisen
display_name: "北森招聘洞察" 
display_name_en: "Beisen Recruiting Insights"
description_zh: "北森招聘洞察。用于查看整体招聘进展、定位流程卡点、查看重点岗位进展、复盘阶段完成量、追踪 Offer 到岗转化，以及发起面试质量分析、竞品情报分析、查看或取消分析异步任务。当用户询问招聘进展、面试进展、阶段完成量、流程瓶颈、重点岗位进展、Offer 到岗转化、面试官提问质量、同职位面试官对比、优秀提问案例、低效面试问题、竞品情报或停止分析任务时使用。"
description_en: "Beisen recruiting insights. Use to review overall recruitment progress, locate process bottlenecks, view progress on key positions, review stage completion volumes, and track Offer-to-onboarding conversion, as well as launch interview-quality analysis and competitor-intelligence analysis, and view or cancel async analysis tasks. Trigger when the user asks about recruitment progress, interview progress, stage completion volumes, process bottlenecks, key-position progress, Offer-to-onboarding conversion, interviewer question quality, interviewer comparison within the same job, exemplary questioning cases, inefficient-interview issues, competitor intelligence, or stopping analysis tasks."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森招聘洞察

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 业务边界

处理招聘管理与分析视角的洞察问题：

- 看整体招聘进展、重点岗位进展、阶段完成量。
- 定位流程卡点：待筛简历、待安排面试、待面试、待发 Offer、待入职等积压。
- 追踪 Offer 到岗转化：已发 Offer、已拒绝 Offer、待入职、已入职。
- 发起面试质量分析：看面试官提问质量、对比同职位面试官、沉淀优秀提问案例、识别低效面试问题。
- 发起竞品情报分析：分析应聘者提到的竞品、查看某个维度的竞品信号、提炼人才流动线索。
- 轮询或取消分析异步任务。

不处理招聘需求列表与需求详情，走 [beisen-recruitment-demand-management](../beisen-recruitment-demand-management/SKILL.md)。不处理我的个人招聘待办，走 [beisen-recruiting-todo](../beisen-recruiting-todo/SKILL.md)。不处理单个应聘者详情，走 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md)。不处理职位 JD，走 [beisen-job-management](../beisen-job-management/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配四类工具："招聘进展查询"、"面试质量分析（异步）"、"竞品情报分析（异步）"、"异步任务状态查询 / 取消"。
- **参数构造**：完全依赖各工具自身的 inputSchema。业务输入语义：
  - **招聘进展**：统计周期（预设周期如最近 1 个月 / 3 个月 / 近半年，或自定义起止日期——成对使用、优先于预设、跨度上限以 schema 说明为准；均未传时默认口径以工具说明为准）；职位范围（职位标识列表，必须来自职位查询或上下文返回，未传时按当前用户权限返回可见在招职位，数量上限以工具说明为准）。
  - **面试质量分析**：面试官（标识或姓名）；指定职位与面试轮次时两者必须同时传；考察重心（如 HR 初筛、业务技术面试）；用户关注的自定义分析维度。
  - **竞品情报分析**：分析维度与竞品公司名称列表（均必填，来自用户明确表达）。
  - **任务轮询/取消**：任务标识必须来自发起异步任务的返回，严禁编造。
- **结果解读**：按各工具 outputSchema 与返回说明解读。招聘进展通常按职位返回：职位信息（名称、编号、部门、招聘周期、招聘类别）、待办快照（待处理新简历、待安排面试、待进行面试、待发 Offer、待入职）、完成量（已筛简历、已完成面试、已发 Offer、已拒绝 Offer、已入职）；统计项可能附带下钻批次标识（空值表示不支持下钻）。

## 下钻规则

- 招聘进展统计项附带下钻批次标识时，可用其查询具体申请明细：**下钻标识必须与该统计项所属职位的职位标识配套使用**，转 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md) 的申请列表查询。
- 下钻返回的申请标识可继续查看申请详情。
- 下钻结果属于候选人 L2 数据，只展示摘要。

## 异步任务轮询与取消

- 面试质量分析与竞品情报分析均为异步任务：发起后从返回中提取任务标识，再轮询结果。
- 轮询间隔 2-5 秒，最长等待不超过 5 分钟；超时未完成时告知用户任务仍在进行、可稍后查看进度，不无限轮询。
- 任务成功 → 解析任务结果展示最终报告；失败 → 读取失败原因向用户说明；已取消 → 告知任务已取消。
- **只有用户明确要求停止或确认取消后**，才调用取消工具。

## 输出要求

- 招聘进展按职位/统计项表格展示，突出待办快照、完成量、明显卡点和 Offer 到岗转化；数字逐字取自返回，不做聚合计算。
- 面试质量与竞品情报只基于分析报告输出，不补写报告外事实。
- 候选人下钻数据属于 L2 敏感数据，只展示摘要，不回显原始返回。
- 职位标识、下钻批次标识、任务标识只用于串联工具调用，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
