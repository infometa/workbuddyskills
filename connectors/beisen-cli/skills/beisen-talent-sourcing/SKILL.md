---
name: beisen-talent-sourcing
description: 北森人才搜寻。用于按岗位要求搜索人才库简历、为职位查询 AI 推荐人才、按职位批量获取推荐候选人、轮询或取消人才搜寻异步任务，并承接应聘者画像类分析线索。当用户要求找简历、搜人才库、推荐候选人、按岗位要求寻访、为职位推荐简历或查看人才搜寻任务进度时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森人才搜寻

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

处理尚未明确进入跟进动作的人才发现与推荐：

- 按岗位要求在人才库中搜索推荐候选人。
- 为一个或多个职位查询 AI 推荐人才。
- 轮询或取消人才搜寻异步任务。
- 围绕推荐结果做来源公司、候选人公司分布等应聘者画像归纳；仅基于工具返回内容归纳，不补写事实。

不处理职位详情本身，职位定位需要 `jobId` 时先使用 `beisen-job-management`。不处理已进入流程候选人的阶段/Offer/入职跟进，走 `beisen-applicant-follow-up`。

## 命令

### 为职位查询 AI 推荐人才

```bash
beisen-cli recruitment_ai job bs_recommend_candidates_by_job --data '<json>'
```

入参：

- `jobIds`：职位 ID 列表，必须来自职位查询结果。
- `pageIndex`、`pageSize`：分页参数，页码从 0 开始。

示例：

```bash
beisen-cli recruitment_ai job bs_recommend_candidates_by_job --data '{"jobIds":["<jobId>"],"pageIndex":0,"pageSize":30}'
```

返回读取：

- `data.items`：AI 推荐候选人列表。
- `data.totalCount`：推荐候选人总数。
- 展示推荐候选人摘要：姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、匹配度星级、推荐亮点；字段为空也保留中文列。

### 按岗位要求搜索人才库候选人

```bash
beisen-cli recruitment_ai talentPool bs_search_candidates_in_talentpool --data '<json>'
```

入参：

- `jobRequirements`：职位要求或用户给出的搜索条件。
- `pageIndex`、`pageSize`：分页参数。

示例：

```bash
beisen-cli recruitment_ai talentPool bs_search_candidates_in_talentpool --data '{"jobRequirements":"3-5年Java开发经验，本科及以上","pageIndex":0,"pageSize":10}'
```

该命令返回异步任务，必须提取 `taskId` 后轮询。

### 查询异步任务结果

```bash
beisen-cli recruitment_ai async_task bs_get_async_task_status --data '{"taskId":"<taskId>"}'
```

轮询规则：

- 轮询间隔 2-5 秒，最长等待不超过 5 分钟。
- `isFinished == false` 时继续轮询。
- `status == "Succeeded"` 时解析 `resultJson`。
- `status == "Failed"` 时读取 `errorMessage` 向用户说明。
- `status == "Cancelled"` 时告知任务已取消。

### 取消异步任务

```bash
beisen-cli recruitment_ai async_task bs_cancel_async_task --data '{"taskId":"<taskId>"}'
```

只有用户明确要求停止或确认取消后才调用。`taskId` 必须来自发起任务或进度查询结果。

## 输出要求

- 候选人信息属于 L2 敏感数据，只展示摘要和推荐理由，不回显原始 JSON。
- 推荐不等于已进入招聘流程，不要把推荐名单说成“应聘者列表”或计入流程阶段人数。
- `jobId`、`taskId` 只用于串联命令，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
