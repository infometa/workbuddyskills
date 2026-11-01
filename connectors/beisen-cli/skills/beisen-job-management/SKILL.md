---
name: beisen-job-management
version: 3.2.1
description: "北森职位管理。用于搜索招聘职位、按职位名称/编码/状态/招聘分类查询职位列表、查看职位详情、JD、职责、任职资格、招聘人数、薪资范围、工作地点、招聘流程和申请数量。当用户询问职位、招聘岗位、JD、岗位职责、任职要求、职位状态或需要先定位职位标识给其他招聘 Skill 使用时使用。"
author: beisen
display_name: "北森职位管理"
display_name_en: "Beisen Job Management"
description_zh: "北森职位管理。用于搜索招聘职位、按职位名称/编码/状态/招聘分类查询职位列表、查看职位详情、JD、职责、任职资格、招聘人数、薪资范围、工作地点、招聘流程和申请数量。当用户询问职位、招聘岗位、JD、岗位职责、任职要求、职位状态或需要先定位职位标识给其他招聘 Skill 使用时使用。"
description_en: "Beisen job (position) management. Use to search recruitment jobs, query the job list by job name/code/status/recruitment category, and view job details, JD, responsibilities, qualifications, headcount, salary range, work location, recruitment process, and application counts. Trigger when the user asks about jobs, openings, JDs, job responsibilities, job requirements, job status, or when a job identifier must first be located for other recruitment Skills to use."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森职位管理

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 业务边界

处理职位本身：

- 搜索职位、按名称/编码/状态/招聘分类筛选职位。
- 查看职位详情、JD、职责、任职资格、招聘人数、薪资、地点、招聘流程、负责人和申请数量。
- 为其他招聘 Skill 定位职位标识（职位 ID）。

不处理职位下应聘者名单，走 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md)。不处理 AI 推荐人才和人才库搜寻，走 [beisen-talent-sourcing](../beisen-talent-sourcing/SKILL.md)。不处理招聘需求/HC，走 [beisen-recruitment-demand-management](../beisen-recruitment-demand-management/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配"职位搜索/职位列表"与"职位详情"类工具。
- **参数构造（职位搜索）**：完全依赖该工具自身的 inputSchema。业务上支持的筛选维度：
  - 职位名称、职位编码（schema 中标记必填但业务上可按需为空的字段，按其说明处理）
  - 职位状态（业务语义：招聘中、已暂停、已结束、已取消、待处理、处理中等；枚举取值以 schema 为准）
  - 招聘分类（业务语义：社会招聘、校园招聘、实习生招聘，也可能为租户自定义文本）
  - 分页参数（页码起始值、每页条数以 schema 为准）
- **参数构造（职位详情）**：职位标识必须来自职位搜索返回，严禁编造。
- **结果解读**：按工具 outputSchema 与返回说明解读。列表通常含职位标识、职位名称、职位编号、状态与总数；详情通常含职位基础信息、部门、招聘人数、薪资范围、工作地点、年限/学历要求、招聘类别、招聘流程、工作职责、任职资格、职位负责人、创建时间、申请数量等，实际字段以返回为准。

## 工作流程

1. 用户问具体职位的 JD/职责/要求时，**先搜索定位**；命中多个职位时，按部门、状态、招聘分类等信息让用户确认后再查详情。
2. 其他招聘 Skill 需要职位标识时，由本 Skill 搜索定位后原样透传。
3. 列表还有更多页时，提示用户可继续翻页。

## 输出要求

- 职位信息属于 L1 内部数据，可正常展示。
- 面向用户只展示业务语义，不展示职位标识等内部 ID，除非用户明确需要用于系统对接。
- 查看详情时优先呈现：职位名称、编号、状态、部门、招聘人数、地点、学历/年限要求、职责、任职资格、招聘流程、负责人、申请数量。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
