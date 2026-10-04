---
name: beisen-job-management
description: 北森职位管理。用于搜索招聘职位、按职位名称/编码/状态/招聘分类查询职位列表、查看职位详情、JD、职责、任职资格、招聘人数、薪资范围、工作地点、招聘流程和申请数量。当用户询问职位、招聘岗位、JD、岗位职责、任职要求、职位状态或需要先定位 jobId 给其他招聘 skill 使用时使用。
version: 1.2.13
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# 北森职位管理

开始前读取 `../beisen-shared/SKILL.md` 并完成共享前置检查。

## 业务边界

处理职位本身：

- 搜索职位、按名称/编码/状态/招聘分类筛选职位。
- 查看职位详情、JD、职责、任职资格、招聘人数、薪资、地点、招聘流程、负责人和申请数量。
- 为其他招聘 skill 定位 `jobId`。

不处理职位下应聘者名单，走 `beisen-applicant-follow-up`。不处理 AI 推荐人才和人才库搜寻，走 `beisen-talent-sourcing`。不处理招聘需求/HC，走 `beisen-recruitment-demand-management`。

## 命令

### 搜索职位

```bash
beisen-cli recruitment job searchJobs --data '<json>'
```

入参：

- `jobCode`：职位编码。Schema 可能标记必填，但实际可按需为空或省略。
- `jobTitle`：职位名称。Schema 可能标记必填，但实际可按需为空或省略。
- `page`、`pageSize`：分页参数，页码从 0 开始。
- `jobStatus`：职位状态，`0` 已暂停，`1` 招聘中，`2` 已结束，`3` 已取消，`6` 待处理，`7` 处理中。
- `recruitType`：招聘分类，`1` 社会招聘，`2` 校园招聘，`3` 实习生招聘，也可能为自定义文本。

示例：

```bash
beisen-cli recruitment job searchJobs --data '{"jobTitle":"Java开发","page":0,"pageSize":10}'
beisen-cli recruitment job searchJobs --data '{"jobStatus":1,"page":0,"pageSize":20}'
```

返回读取：

- `data.jobs`：职位列表，含 `jobId`、职位名称、职位编号、状态等。
- `data.total`：职位总数。
- 若还有更多页，提示用户可继续翻页。

### 查询职位详情

```bash
beisen-cli recruitment job getJobDetail --data '{"jobId":"<jobId>"}'
```

规则：

- `jobId` 必须来自 `searchJobs` 返回，严禁编造。
- 用户问具体职位的 JD/职责/要求时，先搜索定位；若命中多个职位，按部门、状态、招聘分类等信息让用户确认。

详情字段通常包括职位 ID、职位编号、职位名称、状态、部门、招聘人数、薪资范围、工作地点、工作年限、学历要求、招聘类别、招聘流程、工作职责、任职资格、职位负责人、创建时间、新增申请数、申请总数。

## 输出要求

- 职位信息属于 L1 内部数据，可正常展示。
- 面向用户只展示业务语义，不展示 `jobId` 等内部 ID，除非用户明确需要用于系统对接。
- 查看详情时优先呈现：职位名称、编号、状态、部门、招聘人数、地点、学历/年限要求、职责、任职资格、招聘流程、负责人、申请数量。
- 禁止生成 JSON 文件；若生成 CSV，表头必须使用中文。
