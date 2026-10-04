---
name: beisen-recruiting-insights
description: 北森招聘洞察。用于查看整体招聘进展、定位流程卡点、查看重点岗位进展、复盘阶段完成量、追踪 Offer 到岗转化，以及发起面试质量分析、竞品情报分析、查看或取消分析异步任务。当用户询问招聘进展、面试进展、阶段完成量、流程瓶颈、重点岗位进展、Offer 到岗转化、面试官提问质量、同职位面试官对比、优秀提问案例、低效面试问题、竞品情报或停止分析任务时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森招聘洞察

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

处理招聘管理与分析视角的洞察问题：

- 看整体招聘进展、重点岗位进展、阶段完成量。
- 定位流程卡点：待筛简历、待安排面试、待面试、待发 Offer、待入职等积压。
- 追踪 Offer 到岗转化：已发 Offer、已拒绝 Offer、待入职、已入职。
- 发起面试质量分析：看面试官提问质量、对比同职位面试官、沉淀优秀提问案例、识别低效面试问题。
- 发起竞品情报分析：分析应聘者提到的竞品、查看某个维度的竞品信号、提炼人才流动线索。
- 轮询或取消分析异步任务。

不处理招聘需求列表与需求详情，走 `beisen-recruitment-demand-management`。不处理我的个人招聘待办，走 `beisen-recruiting-todo`。不处理单个应聘者详情，走 `beisen-applicant-follow-up`。不处理职位 JD，走 `beisen-job-management`。

## 招聘进展

```bash
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '<json>'
```

入参：

- `dateRange`：预设统计周期，`1` 最近 1 个月，`2` 最近 3 个月，`3` 近半年；未传且未指定自定义日期时默认最近 1 个月。
- `startDate`、`endDate`：自定义日期，必须成对使用，优先于 `dateRange`，间隔不能超过半年。
- `jobIds`：职位 ID 列表；未传时按当前用户权限返回可见在招职位，默认前 15 个。职位 ID 必须来自职位查询或上下文返回。

示例：

```bash
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{}'
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"dateRange":2}'
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"jobIds":["<jobId>"]}'
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"startDate":"2026-07-11","endDate":"2026-08-11"}'
```

返回读取：

- 每个 `data.items[]` 对应一个职位，含职位名称、职位编号、部门、招聘周期、招聘类别。
- 待办快照：`pendingResume` 待处理新简历、`pendingInterviewSchedule` 待安排面试、`pendingInterview` 待进行面试、`pendingOffer` 待发 Offer、`pendingOnboard` 待入职。
- 完成量：`screenedResume` 已筛简历、`completedInterview` 已完成面试、`sentOffer` 已发 Offer、`rejectedOffer` 已拒绝 Offer、`onboarded` 已入职。
- 每个统计项含 `count` 和 `searchBatchId`；`searchBatchId` 可用于下钻具体申请明细，空值表示不支持下钻。

下钻规则：

```bash
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","searchBatchId":"<searchBatchId>","pageIndex":0,"pageSize":30}'
```

- `searchBatchId` 必须与该统计项所属职位的 `jobId` 配套使用。
- 下钻返回的 `applyId` 可继续交给 `beisen-applicant-follow-up` 查看申请详情。
- 下钻结果属于候选人 L2 数据，只展示摘要。

## 面试质量分析

```bash
beisen-cli interview_ai interviewAnalysis analyzeInterviewQuality --data '<json>'
```

入参：

- `userIdName`：面试官 UserId 或姓名；有值时优先分析该面试官所有面试。
- `jobIdCode` 与 `interviewType`：指定职位与面试轮次时必须同时传。
- `assessmentFocus`：考察重心，如 HR 初筛或业务技术面试。
- `reviewDimensions`：用户关注的自定义分析维度。

示例：

```bash
beisen-cli interview_ai interviewAnalysis analyzeInterviewQuality --data '{"userIdName":"张三"}'
beisen-cli interview_ai interviewAnalysis analyzeInterviewQuality --data '{"jobIdCode":"<职位ID或编码>","interviewType":"初试","assessmentFocus":"业务技术面试"}'
```

该命令为异步任务，返回 `taskId` 后必须轮询。

## 竞品情报分析

```bash
beisen-cli interview_ai interviewAnalysis analyzeCompetitorIntelligence --data '<json>'
```

入参：

- `activeDimension`：竞品公司分析维度，必填。
- `companyNames`：竞品公司名称列表，必填。

示例：

```bash
beisen-cli interview_ai interviewAnalysis analyzeCompetitorIntelligence --data '{"activeDimension":"人才策略与招聘动向","companyNames":["某科技公司"]}'
```

该命令为异步任务，返回 `taskId` 后必须轮询。

## 异步任务轮询与取消

```bash
beisen-cli recruitment_ai async_task bs_get_async_task_status --data '{"taskId":"<taskId>"}'
beisen-cli recruitment_ai async_task bs_cancel_async_task --data '{"taskId":"<taskId>"}'
```

轮询规则：

- `taskId` 必须来自发起异步任务接口返回，严禁编造。
- 轮询间隔 2-5 秒，最长等待不超过 5 分钟。
- `isFinished == false` 时继续轮询。
- `status == "Succeeded"` 时解析 `resultJson` 展示最终报告。
- `status == "Failed"` 时读取 `errorMessage` 向用户说明失败原因。
- `status == "Cancelled"` 时告知任务已取消。
- 只有用户明确要求停止或确认取消后，才调用取消命令。

## 输出要求

- 招聘进展按职位/统计项表格展示，突出待办快照、完成量、明显卡点和 Offer 到岗转化。
- 面试质量与竞品情报只基于分析报告输出，不补写报告外事实。
- 候选人下钻数据属于 L2 敏感数据，只展示摘要，不回显原始 JSON。
- `jobId`、`searchBatchId`、`taskId` 只用于串联命令，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
