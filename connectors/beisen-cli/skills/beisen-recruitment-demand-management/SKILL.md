---
name: beisen-recruitment-demand-management
description: 北森招聘需求管理。用于查询招聘需求列表与详情、按需求状态/名称/编号/提出人筛选招聘需求、查看 HC/招聘人数、需求负责人、期望到岗时间、关联职位、Offer/待入职/已到岗等需求级进展。当用户询问招聘需求、HC、需求详情、需求状态、需求负责人、需求还差几人、需求到岗情况时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森招聘需求管理

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

只处理招聘需求本身：

- 查询招聘需求列表。
- 按状态、名称、编号、提出人筛选需求。
- 查看单个招聘需求详情。
- 读取需求人数、负责人、期望到岗、关联职位、已发 Offer、已接受 Offer、待入职、已到岗等需求级字段。

不处理整体招聘进展、流程卡点、阶段完成量、Offer 到岗转化分析、面试质量分析、竞品情报分析，这些走 `beisen-recruiting-insights`。不处理职位 JD/任职资格，走 `beisen-job-management`。不处理单个应聘者跟进，走 `beisen-applicant-follow-up`。

## 查询需求列表

```bash
beisen-cli interview recruitRequirement bs_search_requirements_list --data '<json>'
```

入参：

- `requirementStatus`：需求状态，`20` 审批中，`30` 审批未通过，`40` 进行中，`50` 已关闭，`60` 已完成，`70` 已暂停，`80` 审批已终止。
- `requirementName`：需求名称，默认不限。
- `requirementCode`：需求编号，默认不限。
- `createBy`：需求提出人姓名或邮箱，默认不限。

示例：

```bash
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{}'
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{"requirementStatus":40}'
beisen-cli interview recruitRequirement bs_search_requirements_list --data '{"requirementName":"Java"}'
```

返回读取：

- `data.items`：需求列表。
- `data.total`：符合条件的需求总数。
- 条目通常含 `requirementId`、需求编号、需求名称、需求状态、部门、负责人、招聘人数等，以实际返回为准。

## 查询需求详情

```bash
beisen-cli interview recruitRequirement getRecruitRequirementDetail --data '{"requirementId":"<requirementId>"}'
```

规则：

- `requirementId` 必须来自 `bs_search_requirements_list` 返回，严禁编造。
- 用户问某个具体需求时，先查列表定位；命中多个需求时按名称、编号、部门、负责人和状态让用户确认。

详情字段通常包括：

- 需求基础信息：需求 ID、需求编号、需求名称、需求状态、需求部门、需求负责人、招聘人数、提出时间、期望到岗时间。
- 要求信息：工作职责、任职资格。
- 关联信息：已关联职位 ID。
- 进展信息：已发 Offer 数、已接受 Offer 数、待入职人数、已到岗人数。

## 输出要求

- 招聘需求属于 L1 内部数据，可正常展示。
- 回答需求进展时优先使用详情中的 `sentOfferCount`、`acceptedOffers`、`pendingEntryCount`、`accumulateArriveCount` 等字段。
- `requirementId` 只用于串联命令，不展示给用户。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
