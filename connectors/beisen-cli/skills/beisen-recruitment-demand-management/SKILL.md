---
name: beisen-recruitment-demand-management
version: 3.2.1
description: "北森招聘需求管理。用于查询招聘需求列表与详情、按需求状态/名称/编号/提出人筛选招聘需求、查看 HC/招聘人数、需求负责人、期望到岗时间、关联职位、Offer/待入职/已到岗等需求级进展。当用户询问招聘需求、HC、需求详情、需求状态、需求负责人、需求还差几人、需求到岗情况时使用。"
author: beisen
display_name: "北森招聘需求管理"
display_name_en: "Beisen Recruitment Demand Management"
description_zh: "北森招聘需求管理。用于查询招聘需求列表与详情、按需求状态/名称/编号/提出人筛选招聘需求、查看 HC/招聘人数、需求负责人、期望到岗时间、关联职位、Offer/待入职/已到岗等需求级进展。当用户询问招聘需求、HC、需求详情、需求状态、需求负责人、需求还差几人、需求到岗情况时使用。"
description_en: "Beisen recruitment-demand management. Use to query the recruitment-demand list and details, filter demands by status/name/number/requester, and view HC (hiring headcount), the demand owner, expected fill date, linked jobs, and demand-level progress such as Offer/onboarding-pending/onboarded. Trigger when the user asks about recruitment demands, HC, demand details, demand status, the demand owner, how many people a demand is still short, or a demand's onboarding status."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森招聘需求管理

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 业务边界

只处理招聘需求本身：

- 查询招聘需求列表。
- 按状态、名称、编号、提出人筛选需求。
- 查看单个招聘需求详情。
- 读取需求人数、负责人、期望到岗、关联职位、已发 Offer、已接受 Offer、待入职、已到岗等需求级信息。

不处理整体招聘进展、流程卡点、阶段完成量、Offer 到岗转化分析、面试质量分析、竞品情报分析，这些走 [beisen-recruiting-insights](../beisen-recruiting-insights/SKILL.md)。不处理职位 JD/任职资格，走 [beisen-job-management](../beisen-job-management/SKILL.md)。不处理单个应聘者跟进，走 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配"招聘需求列表查询"与"招聘需求详情查询"类工具。
- **参数构造（需求列表）**：完全依赖该工具自身的 inputSchema。业务上支持的筛选维度：
  - 需求状态（业务语义：审批中、审批未通过、进行中、已关闭、已完成、已暂停、审批已终止；枚举取值以 schema 为准）
  - 需求名称、需求编号、需求提出人（姓名或邮箱）；均默认不限
- **参数构造（需求详情）**：需求标识必须来自需求列表返回，严禁编造。
- **结果解读**：按工具 outputSchema 与返回说明解读。列表通常含需求标识、需求编号、名称、状态、部门、负责人、招聘人数与总数；详情通常含：
  - 需求基础信息：编号、名称、状态、部门、负责人、招聘人数、提出时间、期望到岗时间
  - 要求信息：工作职责、任职资格
  - 关联信息：已关联职位
  - 进展信息：已发 Offer 数、已接受 Offer 数、待入职人数、已到岗人数

## 工作流程

1. 用户问某个具体需求时，**先查列表定位**；命中多个需求时按名称、编号、部门、负责人和状态让用户确认后再查详情。
2. 回答需求进展（还差几人、到岗情况）时，优先使用详情中的进展信息，数字逐字取自返回，不做差值计算。

## 输出要求

- 招聘需求属于 L1 内部数据，可正常展示。
- 需求标识只用于串联工具调用，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
