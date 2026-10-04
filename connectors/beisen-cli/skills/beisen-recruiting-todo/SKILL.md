---
name: beisen-recruiting-todo
description: 北森招聘待办。用于汇总我的招聘事项、查看待筛选简历数量、待评价面试、待参加面试、确认近期面试日程，以及展示当前用户招聘待办清单。当用户问我有什么招聘待办、待处理简历、待评价面试、今天或近期有没有面试、面试日程时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森招聘待办

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

处理当前用户自己的招聘事项：

- 汇总我的招聘待办。
- 查看待筛选简历、待评价面试、待参加面试数量。
- 确认近期面试日程、面试方式、时间、地点和会议链接。

不处理候选人完整申请详情；需要详情时用 `applyId` 转到 `beisen-applicant-follow-up`。不处理团队/整体招聘进展，走 `beisen-recruitment-demand-management`。

## 命令

```bash
beisen-cli interview interviewerTodo getInterviewerTodo --data '<json>'
```

入参：

- `dateRange`：预设周期，`1` 最近 1 个月，`2` 最近 3 个月，`3` 近半年。不传时各待办类型使用默认范围：待筛选简历/待评价面试默认过去 3 个月，待参加面试默认未来 7 天。
- `startDate`、`endDate`：自定义日期，必须成对使用，优先于 `dateRange`。
- `todoTypes`：待办类型列表，`1` 待筛选简历，`2` 待评价面试，`3` 待参加面试。不传则查询全部。

示例：

```bash
beisen-cli interview interviewerTodo getInterviewerTodo --data '{}'
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"todoTypes":[2,3]}'
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"dateRange":2}'
```

返回读取：

- `pendingResumeCount`：待筛选简历数量。
- `pendingInterviewEvaluationCount`：待评价面试数量。
- `pendingInterviewCount`：待参加面试数量。
- `pendingInterviews`：待参加面试列表，含候选人、申请 ID、职位、面试轮次、方式、开始/结束时间、地点、会议链接。

## 输出要求

- 先给待办数量总览，再用表格列出近期面试。
- 面试列表建议展示：候选人、职位、面试轮次、方式、开始时间、结束时间、地点、会议链接。
- 候选人信息属于 L2 敏感数据，仅展示待办所需摘要，不回显原始 JSON。
- 不要把“我安排的面试”与“我需要参加/评价的面试”混成同一种责任；按工具返回口径说明。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
