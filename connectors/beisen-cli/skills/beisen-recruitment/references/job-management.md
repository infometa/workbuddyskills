# 招聘主流程 - 职位管理命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

## searchJobs — 查询职位

```bash
beisen-cli recruitment job searchJobs --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `jobCode` | string | ✅ | 职位编码 |
| `jobTitle` | string | ✅ | 职位名称 |
| `page` | integer | ✅ | 页数，默认从 0 开始，最小值 0 |
| `pageSize` | integer | ✅ | 每页大小，默认 10，最小值 1，最大值 100 |
| `jobStatus` | integer | ❌ | 职位状态：0=已暂停 1=招聘中 2=已结束 3=已取消 6=待处理 7=处理中 |
| `recruitType` | integer | ❌ | 招聘分类：1=社会招聘 2=校园招聘 3=实习生招聘 |

> 注意：schema 中 `jobCode`、`jobTitle`、`page`、`pageSize` 标记为 required，但实际查询可按需填空值。例如按职位名称搜索：`--data '{"jobTitle":"Java开发","page":0,"pageSize":10}'`。

### 返回结构

```json
{
  "code": 200,
  "data": {
    "jobs": [ { "jobId": "职位ID", "jobTitle": "职位名称" } ],
    "page": 0,
    "total": 8
  },
  "message": null
}
```

- `data.total`：职位总数
- `data.jobs`：职位列表，含 `jobId`、`jobTitle`、`jobCode` 等字段
- 分页判断：若 `page < total / pageSize` 则还有更多结果，需提醒用户

## getJobDetail — 获取职位详情

```bash
beisen-cli recruitment job getJobDetail --data '{"jobId":"<id>"}'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `jobId` | string | ✅ | 职位 ID（从 searchJobs 返回的 `jobId` 获取） |

### 返回结构（data 字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `jobId` | string | 职位 ID |
| `jobCode` | string | 职位编号 |
| `jobTitle` | string | 职位名称 |
| `jobStatus` | string | 职位状态 |
| `department` | string | 需求部门 |
| `headCount` | string | 招聘人数 |
| `salaryRange` | string | 薪资范围 |
| `workLocation` | string | 工作地点 |
| `workYears` | string | 工作年限 |
| `education` | string | 学历要求 |
| `recruitType` | string | 招聘类别 |
| `recruitProcess` | string | 招聘流程 |
| `duty` | string | 工作职责 |
| `require` | string | 任职资格 |
| `dutyUser` | string | 职位负责人 |
| `createdDate` | string | 创建时间 |
| `newApplications` | integer | 新增申请数 |
| `totalApplications` | integer | 申请总数 |

### 注意事项

- `jobId` 必须从 `searchJobs` 返回中提取，严禁编造
- 职位信息属于 L1 内部数据，正常展示

## bs_recommend_candidates_by_job — 批量查询职位的 AI 推荐人才

```bash
beisen-cli recruitment job bs_recommend_candidates_by_job --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `jobIds` | array | ✅ | 职位 ID 列表（可由 searchJobs 获得，支持批量查询） |
| `pageIndex` | integer | ✅ | 页码，从 0 开始，默认 0 |
| `pageSize` | integer | ✅ | 分页大小，默认 30，最大 100 |

示例：

```bash
beisen-cli recruitment job bs_recommend_candidates_by_job --data '{"jobIds":["职位ID1","职位ID2"],"pageIndex":0,"pageSize":30}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "items": [ { "推荐候选人字段" } ],
    "totalCount": 15
  },
  "message": null
}
```

- `data.items`：AI 推荐候选人列表
- `data.totalCount`：推荐候选人总数

### 注意事项

- `jobIds` 必须从 `searchJobs` 返回的 `jobId` 中提取，严禁编造
- 候选人信息属于 **L2 敏感数据**，仅展示摘要（姓名、当前职位、推荐理由等），不回显原始 JSON
