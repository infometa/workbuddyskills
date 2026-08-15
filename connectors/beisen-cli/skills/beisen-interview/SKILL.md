---
name: beisen-interview
version: 1.2.1
description: "北森招聘面试一体化。本 Skill 覆盖招聘进展查询、面试官待办、面试质量分析、竞品情报分析、招聘需求查询与详情。当用户询问招聘进展、面试进展、面试官待办、待面试、待评价、offer审批、面试质量、竞品分析、招聘需求等面试一体化相关问题时触发。职位/候选人/人才库等招聘主流程问题请走 beisen-recruitment。"
category: 人力资源/招聘面试
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 招聘面试一体化

**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**

> CLI 版本要求：beisen-cli >= 0.2.5（低于该版本会提示升级，执行 `beisen-cli update` 更新）

容易混淆的概念，先分清楚再回答：

- **候选人 vs 申请**：候选人是人，申请是这个人投在某个职位下的流程记录。同一个人可以有多条申请，阶段、评分、推荐理由都挂在申请上，不要跨申请混用。
- **职位 vs 招聘需求**：需求（HC）是「要招几个人、招得怎么样了」，职位是对外发布的岗位与要求。问进度查需求，问职责要求查职位；两者可以关联，但不是一回事。
- **招聘通知 vs 审批待办**：候选人推荐、面试变更这类提醒走招聘通知；员工自己发起或待办的审批与各类待办走审批清单。名字像，来源不同。
- **人才推荐 ≠ 候选人**：人才推荐是按职位算出来的「可能合适的人」，不代表已进入招聘流程。
- **月报 vs 逐日记录**：考勤月报是整月汇总，具体某天的打卡与单据细节要查逐日记录。两者是同一查询能力的两种模式：传 month 看月报，传 beginDate 看逐日。
- **申请时长、打卡时长、结算时长**：加班的三个数字口径不同，以工具返回的说明为准，不要互相替代。

## 路由优先级

本 Skill 处理：招聘面试一体化（招聘进展、面试官待办、面试质量分析、竞品情报、招聘需求）

不归本 Skill 处理：
- 职位搜索 / 职位详情 / 候选人申请详情 / 人才库推荐 → [../beisen-recruitment/SKILL.md](../beisen-recruitment/SKILL.md)
- offer 审批流程 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)
- 员工档案查询 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)

## 命令速查

| 场景 | CLI 命令 | 说明 |
|------|---------|------|
| 查询招聘进展 | `beisen-cli interview recruitmentProgress getRecruitmentProgress` | 按时间范围/职位查询招聘进展 |
| 下钻查询申请明细 | `beisen-cli recruitment apply bs_search_apply_list` | 用招聘进展返回的 `searchBatchId` + `jobId` 下钻查询具体申请列表 |
| 查询面试官待办 | `beisen-cli interview interviewerTodo getInterviewerTodo` | 查询当前用户的面试待办、待评价等 |
| 面试质量分析 | `beisen-cli interview interviewAnalysis analyzeInterviewQuality` | 面试官质量评估报告（异步） |
| 竞品情报分析 | `beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence` | 竞品公司情报分析报告（异步） |
| 查询招聘需求列表 | `beisen-cli interview recruitRequirement bs_search_requirements_list` | 按状态/名称/编号/提出人查询招聘需求 |
| 获取招聘需求详情 | `beisen-cli interview recruitRequirement getRecruitRequirementDetail` | 按 requirementId 获取需求详情 |

## 命令示例

```bash
# 查询招聘进展（默认最近 1 个月）
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{}'

# 查询最近 3 个月招聘进展
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"dateRange":2}'

# 查询指定职位招聘进展
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"jobIds":["<jobId>"]}'

# 自定义日期范围（间隔不能超过半年）
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"startDate":"2026-07-11","endDate":"2026-08-11"}'

# 下钻查询某统计项的具体申请列表（searchBatchId + jobId 来自上一步返回）
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","searchBatchId":"<searchBatchId>","pageIndex":0,"pageSize":30}'

# 查询面试官待办（全部类型）
beisen-cli interview interviewerTodo getInterviewerTodo --data '{}'

# 查询待面试+待评价待办（近3个月）
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"dateRange":2,"todoTypes":[2,3]}'

# 面试质量分析（异步，需轮询）
beisen-cli interview interviewAnalysis analyzeInterviewQuality --data '{"userIdName":"张三"}'

# 竞品情报分析（异步，需轮询）
beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence --data '{"activeDimension":"人才策略","companyNames":["某科技公司"]}'

# 查询招聘需求列表
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{"requirementStatus":40}'

# 获取招聘需求详情
beisen-cli interview recruitRequirement getRecruitRequirementDetail --data '{"requirementId":"<requirementId>"}'
```

## 工作流程

1. **招聘进展**：用户问"招聘进展/最新招聘情况"时，执行 `beisen-cli interview recruitmentProgress getRecruitmentProgress`。默认查询最近 1 个月，可用 `dateRange`（1=近1月、2=近3月、3=近半年）或自定义 `startDate`/`endDate`（间隔不能超过半年）控制范围；`jobIds` 可指定职位。返回 `data.items` 数组，每个元素对应一个职位，包含职位基本信息和 10 个统计项（每个统计项含 `count` 和 `searchBatchId`），按职位/统计项以表格展示各环节数量。

   **下钻查询**：当用户想看某个统计项的具体候选人明细时，取该统计项的 `searchBatchId`（不为空）和该职位的 `jobId`，调用 `beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","searchBatchId":"<searchBatchId>","pageIndex":0,"pageSize":30}'` 获取申请列表。`searchBatchId` 为空表示不支持下钻，需告知用户。下钻返回的 `applyId` 可继续传给 `bs_get_apply_detail` 查看单条申请详情。

2. **面试官待办**：用户问"我有什么面试待办/待面试/待评价/待处理简历"时，执行 `beisen-cli interview interviewerTodo getInterviewerTodo`。`todoTypes` 过滤待办类型：1=待筛选简历、2=待评价面试、3=待参加面试`dateRange`/`startDate`/`endDate` 控制统计范围。返回 `pendingInterviews` 列表及各类待办数量。

3. **面试质量分析**：用户需要面试官质量评估报告时，执行 `beisen-cli interview interviewAnalysis analyzeInterviewQuality`。可用 `userIdName`（面试官 UserId 或姓名，有值时优先分析该面试官所有面试）、`jobIdCode`+`interviewType`（指定职位与面试轮次，必须同时有值）、`assessmentFocus`（考察重心）、`reviewDimensions`（自定义维度）。该接口为**异步任务**，返回 `taskId`，需轮询 `bs_get_async_task_status` 获取报告。

4. **竞品情报分析**：用户需要竞品公司分析时，执行 `beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence --data '{"activeDimension":"<分析维度>","companyNames":["<公司名>"]}'`。`activeDimension` 和 `companyNames` 为必填。该接口为**异步任务**，返回 `taskId`，需轮询获取报告。

5. **招聘需求**：用户问"有哪些招聘需求/需求进展"时，执行 `beisen-cli interview recruitRequirement bs_search_requirements_list`，可按 `requirementStatus`（20=审批中、30=审批未通过、40=进行中、50=已关闭、60=已完成、70=已暂停、80=审批已终止）、`requirementName`、`requirementCode`、`createBy` 筛选。查看详情用 `getRecruitRequirementDetail --data '{"requirementId":"<id>"}'`。

## 输出格式约束

- **禁止生成 JSON 文件**：不得将查询结果以 JSON 文件形式输出给用户
- **CSV 表头必须使用中文**：生成 CSV 文件时，表头禁止使用英文字段名（如 name、educationLevel、phaseStatus），必须使用中文（如"姓名""学历""阶段状态"）

## 执行原则

- 所有入参通过 `--data` 以 JSON 字符串传递，不使用 `--query`/`--page`/`--size` 等分散标志
- `jobId`、`requirementId`、`taskId` 必须从 CLI 返回中提取，严禁编造
- 候选人/求职者信息属于 **L2 敏感数据**，仅展示摘要，不回显原始 JSON
- 异步任务（面试质量分析、竞品情报）返回 `taskId` 后，按 [references/async-tasks.md](references/async-tasks.md) 的轮询协议处理；分析类任务耗时较长，执行前提醒用户耐心等待
- 招聘进展按职位/统计项汇总后以表格展示，突出待办快照（待筛简历、待安排面试、待面试、待发Offer、待入职）和完成量（已筛简历、已完成面试、已发Offer、已拒绝Offer、已入职）
- 用户追问某统计项明细时，用 `searchBatchId` + `jobId` 下钻到 `bs_search_apply_list` 获取申请列表；`searchBatchId` 为空时告知用户该统计项暂不支持下钻
- 面试官待办直接展示各类待办数量，即将到来的面试列表用表格呈现（候选人、职位、面试类型、方式、时间）

## 命令分组与参考

| 分组 | 参考文件 | 覆盖命令 |
|------|---------|---------|
| 招聘进展 | [references/recruitment-progress.md](references/recruitment-progress.md) | getRecruitmentProgress |
| 面试官待办 | [references/interviewer-todo.md](references/interviewer-todo.md) | getInterviewerTodo |
| 质量/情报分析 | [references/analytics.md](references/analytics.md) | analyzeInterviewQuality, analyzeCompetitorIntelligence |
| 招聘需求 | [references/recruit-requirement.md](references/recruit-requirement.md) | bs_search_requirements_list, getRecruitRequirementDetail |
| 异步任务 | [references/async-tasks.md](references/async-tasks.md) | 异步结果轮询（调用 beisen-recruitment async_task） |

## Playbook 案例

### 案例 1：查询招聘进展

用户问："帮我看看最新招聘进展"

执行步骤：
1. 前置检查（beisen-shared 的 Step 1-3）
2. 执行 `beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{}'`（默认近 1 个月）
3. 若用户要求更长周期，改用 `--data '{"dateRange":2}'` 或自定义日期
4. 解析 `data.items` 数组，按职位/统计项以表格展示待办快照与完成量

### 案例 1.1：招聘进展下钻查询具体申请

用户追问："帮我看看 XX 职位待面试的候选人有哪些"

执行步骤：
1. 先执行 `getRecruitmentProgress` 获取招聘进展，找到该职位的 `pendingInterview` 统计项
2. 检查 `pendingInterview.searchBatchId` 是否非空；若为空则告知用户该统计项暂不支持下钻
3. 执行 `beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<该职位jobId>","searchBatchId":"<pendingInterview.searchBatchId>","pageIndex":0,"pageSize":30}'`
4. 以表格展示申请列表（姓名、学历、工作年限、最近公司、阶段状态、投递渠道等）
5. 若用户需要某候选人更多详情，用返回的 `applyId` 调用 `bs_get_apply_detail` 查看

### 案例 2：查询面试官待办

用户问："我最近有什么面试要参加？"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli interview interviewerTodo getInterviewerTodo --data '{}'`
3. 展示各类待办数量（待面试、待评价、待处理简历）
4. 用表格展示即将到来的面试列表（候选人、职位、面试类型、方式、时间）

### 案例 3：竞品情报分析

用户问："帮我分析一下 XX 公司的招聘情况"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence --data '{"activeDimension":"人才策略","companyNames":["XX公司"]}'`
3. 提取 `taskId`，轮询 `bs_get_async_task_status` 直到 `isFinished == true`
4. 从 `resultJson` 解析报告内容，向用户展示分析结论

## 详细参考

- [references/recruitment-progress.md](references/recruitment-progress.md)：招聘进展查询参数、返回结构与下钻查询说明
- [references/interviewer-todo.md](references/interviewer-todo.md)：面试官待办查询参数与返回
- [references/analytics.md](references/analytics.md)：面试质量与竞品情报分析
- [references/recruit-requirement.md](references/recruit-requirement.md)：招聘需求列表与详情
- [references/async-tasks.md](references/async-tasks.md)：异步任务轮询协议

## 不在本 Skill 范围

- 职位搜索 / 职位详情 / 候选人申请详情 / 人才库推荐 → [../beisen-recruitment/SKILL.md](../beisen-recruitment/SKILL.md)
- offer 审批流程 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)
- 员工入职后的档案管理 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
