---
name: beisen-talent-sourcing
version: 3.2.1
description: "北森人才搜寻。用于按岗位要求搜索人才库简历、为职位查询 AI 推荐人才、按职位批量获取推荐候选人、轮询或取消人才搜寻异步任务，并承接应聘者画像类分析线索。当用户要求找简历、搜人才库、推荐候选人、按岗位要求寻访、为职位推荐简历或查看人才搜寻任务进度时使用。"
author: beisen
display_name: "北森人才搜寻"
display_name_en: "Beisen Talent Sourcing"
description_zh: "北森人才搜寻。用于按岗位要求搜索人才库简历、为职位查询 AI 推荐人才、按职位批量获取推荐候选人、轮询或取消人才搜寻异步任务，并承接应聘者画像类分析线索。当用户要求找简历、搜人才库、推荐候选人、按岗位要求寻访、为职位推荐简历或查看人才搜寻任务进度时使用。"
description_en: "Beisen talent sourcing. Use to search talent-pool resumes against job requirements, query AI-recommended talent for a job, batch-fetch recommended candidates by job, poll or cancel talent-sourcing async tasks, and pick up applicant-profile analysis leads. Trigger when the user asks to find resumes, search the talent pool, recommend candidates, source by job requirements, recommend resumes for a job, or view the progress of a talent-sourcing task."
category: productivity
requires-skills:
  - beisen-shared
---

# 北森人才搜寻

**CRITICAL — 开始前 MUST 读取 [references/beisen-shared.md](references/beisen-shared.md)**

## 业务边界

处理尚未明确进入跟进动作的人才发现与推荐：

- 按岗位要求在人才库中搜索推荐候选人。
- 为一个或多个职位查询 AI 推荐人才。
- 轮询或取消人才搜寻异步任务。
- 围绕推荐结果做来源公司、候选人公司分布等应聘者画像归纳；仅基于工具返回内容归纳，不补写事实。

不处理职位详情本身，职位定位需要职位标识时先使用 [beisen-job-management](../beisen-job-management/SKILL.md)。不处理已进入流程候选人的阶段/Offer/入职跟进，走 [beisen-applicant-follow-up](../beisen-applicant-follow-up/SKILL.md)。

## 工具的读取与加载

- **工具发现**：在北森连接器当前已注册的工具清单中，按名称与描述匹配三类工具："按职位推荐候选人（AI 推荐）"、"人才库搜索候选人"、"异步任务状态查询 / 取消"。
- **参数构造**：完全依赖各工具自身的 inputSchema。业务输入语义：
  - **AI 推荐人才**：职位标识列表（必须来自职位查询结果，严禁编造）+ 分页参数。
  - **人才库搜索**：职位要求或用户给出的搜索条件（如"3-5年Java开发经验，本科及以上"）+ 分页参数。该能力为**异步任务**：发起后从返回中提取任务标识，再轮询结果。
  - **任务轮询/取消**：任务标识必须来自发起任务或进度查询的返回。
- **结果解读**：按各工具 outputSchema 与返回说明解读。推荐结果通常含候选人摘要（姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司/职位、匹配度、推荐亮点）与总数。

## 异步任务轮询与取消

- 轮询间隔 2-5 秒，最长等待不超过 5 分钟。
- 任务未完成 → 继续轮询；成功 → 解析任务结果并展示；失败 → 读取失败原因向用户说明；已取消 → 告知任务已取消。
- 超时未完成 → 告知用户任务仍在进行，可稍后再查进度，不无限轮询。
- **只有用户明确要求停止或确认取消后**才调用取消工具。

## 输出要求

- 候选人信息属于 L2 敏感数据，只展示摘要和推荐理由，不回显原始返回；推荐列表字段为空也保留中文列。
- 推荐不等于已进入招聘流程，不要把推荐名单说成"应聘者列表"或计入流程阶段人数。
- 职位标识、任务标识只用于串联工具调用，不展示给用户。
- 分页结果多于已展示条数时，提示可继续翻页。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
