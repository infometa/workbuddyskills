---
name: beisen-recruiting-todo
version: 3.2.1
description: "北森招聘待办。用于汇总我的招聘事项、查看待筛选简历数量、待评价面试、待参加面试、确认近期面试日程，以及展示当前用户招聘待办清单。当用户问我有什么招聘待办、待处理简历、待评价面试、今天或近期有没有面试、面试日程时使用。"
author: beisen
display_name: "北森招聘待办"
display_name_en: "Beisen Recruiting To-Do"
description_zh: "北森招聘待办。用于汇总我的招聘事项、查看待筛选简历数量、待评价面试、待参加面试、确认近期面试日程，以及展示当前用户招聘待办清单。当用户问我有什么招聘待办、待处理简历、待评价面试、今天或近期有没有面试、面试日程时使用。"
description_en: "Beisen recruiting to-do. Use to summarize my recruitment items, view the count of resumes pending screening, interviews pending evaluation, and interviews I must attend, confirm upcoming interview schedules, and display the current user's recruiting to-do list. Trigger when the user asks what recruiting to-dos they have, about resumes pending action, interviews pending evaluation, whether there are interviews today or soon, or about the interview schedule."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森招聘待办

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 业务边界

处理当前用户自己的招聘事项：

- 汇总我的招聘待办。
- 查看待筛选简历、待评价面试、待参加面试数量。
- 确认近期面试日程、面试方式、时间、地点和会议链接。

不处理候选人完整申请详情；需要详情时用工具返回的申请标识转到 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md)。不处理团队/整体招聘进展，走 [beisen-recruiting-insights](../beisen-recruiting-insights/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配"面试官待办/我的招聘待办"类工具。
- **参数构造**：完全依赖该工具自身的 inputSchema。业务上支持的筛选维度：
  - **统计周期**：预设周期（如最近 1 个月 / 3 个月 / 近半年）或自定义起止日期（成对使用，自定义优先于预设）；不传时各待办类型按工具说明的默认范围返回（如待筛选简历/待评价面试默认过去 3 个月，待参加面试默认未来 7 天）。
  - **待办类型**：待筛选简历 / 待评价面试 / 待参加面试；不传则查询全部。
  - 具体参数字段、枚举取值与日期格式一律以 inputSchema 说明为准。
- **结果解读**：按工具 outputSchema 与返回说明解读，通常含各类待办数量与待参加面试列表（候选人、职位、面试轮次、方式、开始/结束时间、地点、会议链接等）。

## 输出要求

- 先给待办数量总览，再用表格列出近期面试。
- 面试列表建议展示：候选人、职位、面试轮次、方式、开始时间、结束时间、地点、会议链接（链接必须来自工具返回）。
- 候选人信息属于 L2 敏感数据，仅展示待办所需摘要，不回显原始返回。
- 不要把"我安排的面试"与"我需要参加/评价的面试"混成同一种责任；按工具返回口径说明。
- 申请标识、任务标识等内部 ID 只用于串联查询，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
