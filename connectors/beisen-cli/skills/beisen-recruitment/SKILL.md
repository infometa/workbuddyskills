---
name: beisen-recruitment
version: 2.2.0
description: "北森招聘主流程。本 Skill 覆盖职位搜索与详情、AI推荐人才、候选人申请详情与申请列表、人才库推荐候选人搜索、异步任务管理与轮询。当用户询问职位、招聘岗位、候选人、申请、人才库、简历推荐、JD 等招聘主流程问题时触发。面试相关（招聘进展、面试官待办、面试质量分析、竞品情报、招聘需求）请走 beisen-interview。"
category: 人力资源/招聘
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 招聘主流程

**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**

> CLI 版本要求：beisen-cli >= 0.2.13（低于该版本会提示升级，执行 `beisen-cli update` 更新）

容易混淆的概念，先分清楚再回答：

- **候选人 vs 申请**：候选人是人，申请是这个人投在某个职位下的流程记录。同一个人可以有多条申请，阶段、评分、推荐理由都挂在申请上，不要跨申请混用。
- **职位 vs 招聘需求**：需求（HC）是「要招几个人、招得怎么样了」，职位是对外发布的岗位与要求。问进度查需求，问职责要求查职位；两者可以关联，但不是一回事。
- **招聘通知 vs 审批待办**：候选人推荐、面试变更这类提醒走招聘通知；员工自己发起或待办的审批与各类待办走审批清单。名字像，来源不同。
- **人才推荐 ≠ 候选人**：人才推荐是按职位算出来的「可能合适的人」，不代表已进入招聘流程。
- **月报 vs 逐日记录**：考勤月报是整月汇总，具体某天的打卡与单据细节要查逐日记录。两者是同一查询能力的两种模式：传 month 看月报，传 beginDate 看逐日。
- **申请时长、打卡时长、结算时长**：加班的三个数字口径不同，以工具返回的说明为准，不要互相替代。

## 路由优先级

本 Skill 处理：招聘主流程（职位搜索与详情、AI推荐人才、候选人申请详情与申请列表、人才库推荐候选人搜索、异步任务）

不归本 Skill 处理：
- 招聘进展 / 面试官待办 / 面试质量分析 / 竞品情报 / 招聘需求 → [../beisen-interview/SKILL.md](../beisen-interview/SKILL.md)
- offer 审批流程 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)
- 员工档案查询 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)

## 命令速查

| 场景 | CLI 命令 | 说明 |
|------|---------|------|
| 搜索职位 | `beisen-cli recruitment job searchJobs` | 按职位名称/编码/状态/招聘分类分页查询 |
| 查询职位详情 | `beisen-cli recruitment job getJobDetail` | 按 jobId 获取职位完整信息 |
| AI 推荐人才 | `beisen-cli recruitment job bs_recommend_candidates_by_job` | 按职位批量查询 AI 推荐候选人 |
| 查询应聘者申请列表 | `beisen-cli recruitment apply bs_search_apply_list` | 按职位/姓名/状态/筛选结果等查询申请列表 |
| 查询候选人申请详情 | `beisen-cli recruitment apply bs_get_apply_detail` | 按 applyId 批量查询申请详情 |
| 搜索人才库候选人 | `beisen-cli recruitment talentPool bs_search_candidates_in_talentpool` | 按职位要求搜索推荐候选人（异步） |
| 查询异步任务结果 | `beisen-cli recruitment async_task bs_get_async_task_status` | 轮询异步任务执行结果 |
| 取消异步任务 | `beisen-cli recruitment async_task bs_cancel_async_task` | 取消进行中的异步任务 |

## 命令示例

```bash
# 搜索职位（按职位名称，第 1 页）
beisen-cli recruitment job searchJobs --data '{"jobTitle":"Java开发","page":0,"pageSize":10}'

# 搜索招聘中职位（按状态筛选）
beisen-cli recruitment job searchJobs --data '{"jobStatus":1,"page":0,"pageSize":20}'

# 查询职位详情
beisen-cli recruitment job getJobDetail --data '{"jobId":"<jobId>"}'

# AI 推荐人才（支持批量职位）
beisen-cli recruitment job bs_recommend_candidates_by_job --data '{"jobIds":["<jobId>"],"pageIndex":0,"pageSize":30}'

# 查询应聘者申请列表（某职位）
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","pageIndex":0,"pageSize":30}'

# 查询应聘者申请列表（按姓名/AI评估/筛选结果过滤）
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","aiEvaluateResults":[3],"filterResults":[4],"pageIndex":0,"pageSize":30}'

# 查询候选人申请详情（支持批量）
beisen-cli recruitment apply bs_get_apply_detail --data '{"applyIds":["<applyId>"]}'

# 搜索人才库推荐候选人（异步任务，需轮询结果）
beisen-cli recruitment talentPool bs_search_candidates_in_talentpool --data '{"jobRequirements":"3-5年Java开发经验，本科及以上","pageIndex":0,"pageSize":10}'

# 查询异步任务结果
beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<taskId>"}'
```

## 工作流程

1. **搜索职位**：用户要找工作/职位时，执行 `beisen-cli recruitment job searchJobs`，通过 `--data` 传入职位名称（`jobTitle`）、状态（`jobStatus`）、招聘分类（`recruitType`）、分页参数。展示职位名称、职位编号、部门、状态、申请数等关键字段。

2. **职位详情**：用户需要查看某个职位的完整信息时，先通过 `searchJobs` 获取 `jobId`，再执行 `beisen-cli recruitment job getJobDetail --data '{"jobId":"<id>"}'`。展示职位名称、部门、招聘人数、薪资范围、工作地点、工作年限、学历要求、工作职责、任职资格、负责人、招聘流程、申请情况等。

3. **AI 推荐人才**：用户需要某职位的 AI 推荐候选人时，执行 `beisen-cli recruitment job bs_recommend_candidates_by_job --data '{"jobIds":["<jobId>"],"pageIndex":0,"pageSize":30}'`。展示推荐候选人摘要（应聘者姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、匹配度星级、推荐亮点），以上列出的字段必须全部展示，即使值为空也不省略。候选人属于 **L2 敏感数据**，不回显原始 JSON。

4. **应聘者申请列表**：用户需要查某职位下候选人申请列表（如待筛选简历、按阶段/状态/筛选结果过滤）时，执行 `beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>",...}'`。常用过滤条件：`searchType`（0=全部, 1=待处理/未处理，用户说"待处理""未处理""待处理的简历"时设为 1）、`phaseName`（阶段名称，如"简历初筛""面试""Offer环节"等）、`statusName`（状态名称，如"未处理""进行中""本轮通过""本轮淘汰"等）、`filterResults`（筛选结果：1=通过,2=待定,3=淘汰,4=未筛选）、`aiEvaluateResults`（AI 评估：0=未发起,1=评估中,2=评估失败,3=非常符合,4=不符合,5=基本符合,6=信息不足）、`interviewStatuses`（面试状态：0=未安排,1=已安排）、`offerStatuses`（Offer 状态）、`entryStatuses`（入职状态）、`signInStates`（签到状态：1=未签到,2=已签到,3=未到场）。候选人信息属于 **L2 敏感数据**，仅展示摘要（姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、AI评估简历结果、AI评估简历理由、最初投递渠道、申请创建时间、所在阶段状态），以上列出的字段必须全部展示，即使值为空也不省略。

5. **候选人申请详情**：用户需要查看某位候选人的申请详情时，先通过 `bs_search_apply_list` 获取 `applyId`，再执行 `beisen-cli recruitment apply bs_get_apply_detail --data '{"applyIds":[...]}'`。

6. **人才库搜索**：用户需要按职位要求推荐人才库候选人时，执行 `beisen-cli recruitment talentPool bs_search_candidates_in_talentpool --data '{"jobRequirements":"<职位要求>","pageIndex":0,"pageSize":10}'`。该接口为**异步任务**，需按 [references/recruitment-demand.md](references/recruitment-demand.md) 的轮询流程处理。

7. **异步任务**：当人才库搜索、面试质量分析、竞品情报等返回 `taskId` 时，用 `bs_get_async_task_status` 轮询直到 `isFinished == true`，从 `resultJson` 解析结果。

## 输出格式约束

- **禁止生成 JSON 文件**：不得将查询结果以 JSON 文件形式输出给用户
- **CSV 表头必须使用中文**：生成 CSV 文件时，表头禁止使用英文字段名（如 name、educationLevel、phaseStatus），必须使用中文（如"姓名""学历""阶段状态"）

## 执行原则

- 所有入参通过 `--data` 以 JSON 字符串传递，不使用 `--query`/`--page`/`--size` 等分散标志
- `jobId`、`applyId`、`taskId` 必须从 CLI 返回中提取，严禁编造
- `searchJobs` 的 `jobCode`/`jobTitle` 按需填写，分页参数 `page`/`pageSize` 必须提供
- 职位信息属于 L1 内部数据，正常展示；候选人信息属于 L2 敏感数据，仅展示摘要
- **展示约束**：向用户展示数据时，只展示中文语义值（如"面试中""非常符合"），不展示原始编码名或字段名（如 `phaseName`、`statusName`、`aiEvaluateResults` 等），不展示枚举数字（如 0、1、3 等）
- 分页处理：`searchJobs` 返回 `total` 字段，若 `page` 未到最后页，提醒用户存在更多结果
- 异步任务轮询间隔 2-5 秒，最长等待不超过 5 分钟；失败时读取 `errorMessage` 向用户说明

## 命令分组与参考

| 分组 | 参考文件 | 覆盖命令 |
|------|---------|---------|
| 职位管理 | [references/job-management.md](references/job-management.md) | searchJobs, getJobDetail, bs_recommend_candidates_by_job |
| 候选人/申请/人才库 | [references/candidate-search.md](references/candidate-search.md) | bs_search_apply_list, bs_get_apply_detail, bs_search_candidates_in_talentpool |
| 异步任务 | [references/recruitment-demand.md](references/recruitment-demand.md) | bs_get_async_task_status, bs_cancel_async_task |

## Playbook 案例

### 案例 1：搜索职位并查看详情

用户问："有没有 Java 开发的职位？"

执行步骤：
1. 前置检查（beisen-shared 的 Step 1-3）
2. 执行 `beisen-cli recruitment job searchJobs --data '{"jobTitle":"Java开发","page":0,"pageSize":10}'`
3. 展示匹配职位列表（职位名称、部门、招聘状态）
4. 用户选择某个职位后，用返回的 `jobId` 执行 `getJobDetail` 查看详情

### 案例 2：查看某职位的待处理简历

用户问："查一下软件测试工程师职位的待处理简历"

执行步骤：
1. 前置检查
2. 用 `searchJobs` 或已知 `jobId` 定位职位
3. 执行 `beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","filterResults":[4],"pageIndex":0,"pageSize":30}'`（filterResults=4 表示未筛选/待处理）
4. 展示申请列表摘要（姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、AI评估简历结果、AI评估简历理由、最初投递渠道、申请创建时间、所在阶段状态），候选人属于 L2 敏感数据，仅展示摘要

### 案例 3：人才库推荐候选人

用户问："帮我从人才库推荐几个符合岗位要求的候选人"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli recruitment talentPool bs_search_candidates_in_talentpool --data '{"jobRequirements":"<用户描述的职位要求>","pageIndex":0,"pageSize":10}'`
3. 提取返回的 `taskId`，轮询 `bs_get_async_task_status` 直到 `isFinished == true`
4. 从 `resultJson` 解析候选人列表，展示摘要（姓名、当前职位、匹配度等 L2 摘要信息）

## 详细参考

- [references/job-management.md](references/job-management.md)：职位管理命令详细参数与返回格式
- [references/candidate-search.md](references/candidate-search.md)：候选人申请与人才库搜索命令
- [references/recruitment-demand.md](references/recruitment-demand.md)：异步任务管理与轮询协议

## 不在本 Skill 范围

- 招聘进展 / 面试官待办 / 面试质量分析 / 竞品情报 / 招聘需求 → [../beisen-interview/SKILL.md](../beisen-interview/SKILL.md)
- offer 审批流程 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)
- 员工入职后的档案管理 → [../beisen-employee-profile/SKILL.md](../beisen-employee-profile/SKILL.md)
