---
name: beisen-applicant-follow-up
description: 北森应聘者跟进。用于查看应聘者当前进展、查询某职位下的申请列表、筛出待处理简历、查看面试中应聘者、跟进待发 Offer 应聘者、核对待入职应聘者、查看候选人申请详情。当用户询问候选人、应聘者、申请、简历筛选状态、面试阶段名单、Offer/入职状态或某个应聘者详情时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森应聘者跟进

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

处理进入招聘流程后的应聘者与申请记录：

- 查看应聘者当前进展、所在阶段与状态。
- 筛出某职位下待处理/未筛选简历。
- 查看面试中、待发 Offer、待入职的应聘者。
- 查看某个应聘者的申请详情。
- 从招聘进展统计项下钻到具体申请明细。

不处理职位 JD 与职位详情；职位定位需要 `jobId` 时先使用 `beisen-job-management`。不处理人才库主动搜寻与职位 AI 推荐，走 `beisen-talent-sourcing`。不处理我的招聘待办总览，走 `beisen-recruiting-todo`。

## 命令

### 查询应聘者申请列表

```bash
beisen-cli recruitment apply bs_search_apply_list --data '<json>'
```

常用入参：

- `jobId`：职位 ID，必填，必须来自职位查询或招聘进展返回。
- `pageIndex`、`pageSize`：分页参数，必填，页码从 0 开始。
- `name`：按应聘者姓名搜索。
- `phaseName`、`statusName`：按流程阶段/状态筛选，如“面试”“Offer环节”“面试中”。
- `filterResults`：筛选结果，`4` 表示未筛选/待处理。
- `aiEvaluateResults`：AI 简历评估结果，`3` 非常符合，`5` 基本符合，`4` 不符合。
- `interviewStatuses`：面试状态，`0` 未安排，`1` 已安排。
- `offerStatuses`：Offer 状态，`0` 待发 Offer，`1` 已发 Offer，`2` 已接受 Offer，`3` 已拒 Offer，`5` 已入职 Offer。
- `entryStatuses`：入职状态，`1` 待入职，`2` 已入职。
- `signInStates`：签到状态，`1` 未签到，`2` 已签到，`3` 未到场。
- `searchBatchId`：招聘进展统计项返回的下钻批次 ID，必须与同一职位的 `jobId` 配套使用。

示例：

```bash
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","filterResults":[4],"pageIndex":0,"pageSize":30}'
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","phaseName":"面试","pageIndex":0,"pageSize":30}'
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","offerStatuses":[0],"pageIndex":0,"pageSize":30}'
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","entryStatuses":[1],"pageIndex":0,"pageSize":30}'
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<jobId>","searchBatchId":"<searchBatchId>","pageIndex":0,"pageSize":30}'
```

返回读取：

- `data.items` 是申请列表，通常含 `applyId`、`applicantId`、姓名、学历、学校、专业、最近公司、最近职位、工作年限、投递渠道、阶段状态、AI 评估结果、申请时间。
- `data.totalCount` 是当前筛选条件下申请总数。
- 若已展示条数小于 `totalCount`，提示用户可继续翻页。

### 查询候选人申请详情

```bash
beisen-cli recruitment apply bs_get_apply_detail --data '{"applyIds":["<applyId>"]}'
```

规则：

- `applyId` 必须来自申请列表、待办或招聘进展下钻结果，严禁编造。
- 支持批量传多个 `applyId`。
- 详情只用于回答用户关注的应聘者，不扩散无关候选人信息。

## 输出要求

- 候选人/应聘者信息属于 L2 敏感数据，只展示业务摘要，不回显原始 JSON。
- 列表建议展示：姓名、性别、年龄、工作年限、学历、毕业学校、专业、最近任职公司、最近任职职位、AI 评估结果、AI 评估理由、最初投递渠道、申请创建时间、所在阶段状态。
- 只展示中文语义值，不展示字段名、枚举数字、内部 ID。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
