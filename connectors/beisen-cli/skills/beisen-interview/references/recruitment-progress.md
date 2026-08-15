# 招聘面试 - 招聘进展查询命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

## getRecruitmentProgress — 查询招聘进展

```bash
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `dateRange` | integer | ❌ | 预设统计周期：1=最近1个月、2=最近3个月、3=近半年；未传且未指定自定义日期时默认最近1个月 |
| `startDate` | string | ❌ | 自定义统计起始日期（YYYY-MM-DD），与 `endDate` 成对使用，优先于 `dateRange`；与 `endDate` 间隔不能超过半年 |
| `endDate` | string | ❌ | 自定义统计截止日期（YYYY-MM-DD），与 `startDate` 成对使用 |
| `jobIds` | array | ❌ | 职位 ID 列表（GUID 格式），指定查询的职位；未传时按当前用户权限返回可见在招职位（默认前 15 个） |

### 参数示例

```bash
# 默认最近1个月
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{}'

# 最近3个月
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"dateRange":2}'

# 指定职位
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"jobIds":["职位GUID1","职位GUID2"]}'

# 自定义日期（间隔不超过半年）
beisen-cli interview recruitmentProgress getRecruitmentProgress --data '{"startDate":"2026-02-11","endDate":"2026-08-11"}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "jobId": "职位ID",
        "jobName": "职位名称",
        "jobCode": "职位编号",
        "department": "需求部门",
        "recruitmentCycle": "招聘周期",
        "recruitmentType": "招聘类别",
        "pendingResume":       { "count": 5, "searchBatchId": "批次ID" },
        "pendingInterviewSchedule": { "count": 3, "searchBatchId": "批次ID" },
        "pendingInterview":    { "count": 2, "searchBatchId": "批次ID" },
        "pendingOffer":        { "count": 1, "searchBatchId": "批次ID" },
        "pendingOnboard":      { "count": 0, "searchBatchId": "批次ID" },
        "screenedResume":      { "count": 10, "searchBatchId": "批次ID" },
        "completedInterview":  { "count": 8, "searchBatchId": "批次ID" },
        "sentOffer":           { "count": 4, "searchBatchId": "批次ID" },
        "rejectedOffer":       { "count": 1, "searchBatchId": "批次ID" },
        "onboarded":           { "count": 3, "searchBatchId": "批次ID" }
      }
    ]
  },
  "message": null
}
```

#### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | array | 招聘进展列表，每个元素对应一个职位 |
| `items[].jobId` | string | 职位 ID，下钻查询时需传入 `bs_search_apply_list` 的 `jobId` 参数 |
| `items[].jobName` | string | 职位名称 |
| `items[].jobCode` | string | 职位编号 |
| `items[].department` | string | 需求部门 |
| `items[].recruitmentCycle` | string | 招聘周期 |
| `items[].recruitmentType` | string | 招聘类别 |

#### 统计项字段（StatisticItem）

每个统计项（如 `pendingResume`、`completedInterview` 等）结构相同：

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | integer | 该统计项的数量 |
| `searchBatchId` | string/null | 下钻查询 ID，用于配合 `jobId` 调用 `bs_search_apply_list` 查询该统计项对应的具体申请列表；**为空表示该统计项暂不支持下钻** |

统计项清单：

| 统计项 | 含义 | 分类 |
|--------|------|------|
| `pendingResume` | 待处理新简历 | 待办快照 |
| `pendingInterviewSchedule` | 待安排面试 | 待办快照 |
| `pendingInterview` | 待进行面试 | 待办快照 |
| `pendingOffer` | 待发 Offer | 待办快照 |
| `pendingOnboard` | 待入职 | 待办快照 |
| `screenedResume` | 已筛简历 | 完成量 |
| `completedInterview` | 已完成面试 | 完成量 |
| `sentOffer` | 已发 Offer | 完成量 |
| `rejectedOffer` | 已拒绝 Offer | 完成量 |
| `onboarded` | 已入职 | 完成量 |

### 下钻查询：从招聘进展到具体申请列表

当用户需要查看某个统计项的**具体候选人明细**时，使用返回的 `searchBatchId` + `jobId` 调用 `bs_search_apply_list` 进行下钻查询。

**调用方式**（属于 beisen-recruitment 域）：

```bash
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"<上一步返回的jobId>","searchBatchId":"<上一步返回的searchBatchId>","pageIndex":0,"pageSize":30}'
```

**规则**：
- `searchBatchId` 必须与**该统计项所属职位的 `jobId`** 一起传入，二者缺一不可
- `searchBatchId` 为空（null 或空字符串）时，表示该统计项不支持下钻，不要调用 `bs_search_apply_list`
- 下钻返回的申请列表中，`applyId` 可继续传给 `bs_get_apply_detail` 查看单条申请详情
- `bs_search_apply_list` 的完整参数与返回结构参见 [../../beisen-recruitment/references/candidate-search.md](../../beisen-recruitment/references/candidate-search.md)

### 注意事项

- `jobIds` 每个元素必须为 GUID 格式
- `startDate` 与 `endDate` 间隔不能超过半年，否则返回 400 参数错误
- 未传 `jobIds` 时按当前用户权限返回可见在招职位（默认前 15 个）
- 若服务端返回 500 "服务异常，查询招聘进展失败"，为北森后端临时故障，稍后重试；若持续报错建议联系北森技术支持确认接口是否对租户开通
