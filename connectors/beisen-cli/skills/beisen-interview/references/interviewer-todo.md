# 招聘面试 - 面试官待办查询命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

## getInterviewerTodo — 查询面试官待办

```bash
beisen-cli interview interviewerTodo getInterviewerTodo --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `dateRange` | integer | ❌ | 预设统计周期：1=最近1个月、2=最近3个月、3=近半年；不传时各待办类型使用各自默认时间范围（待筛选简历/待评价面试默认过去3个月，待参加面试默认未来7天） |
| `startDate` | string | ❌ | 自定义统计起始日期（YYYY-MM-DD），与 `endDate` 成对使用，优先于 `dateRange` |
| `endDate` | string | ❌ | 自定义统计截止日期（YYYY-MM-DD），与 `startDate` 成对使用 |
| `todoTypes` | array | ❌ | 待办类型列表：1=待筛选简历、2=待评价面试、3=待参加面试；不传则查询全部类型 |

### 参数示例

```bash
# 查询全部类型待办（各类型使用各自默认时间范围）
beisen-cli interview interviewerTodo getInterviewerTodo --data '{}'

# 查询近3个月全部待办
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"dateRange":2}'

# 只查待参加面试和待评价面试
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"todoTypes":[2,3]}'

# 自定义日期范围
beisen-cli interview interviewerTodo getInterviewerTodo --data '{"startDate":"2026-07-11","endDate":"2026-08-11"}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "pendingResumeCount": 0,
    "pendingInterviewEvaluationCount": 13,
    "pendingInterviewCount": 1,
    "pendingInterviews": [
      {
        "applicantName": "候选人姓名",
        "applyId": "申请ID",
        "endTime": "2026-08-12 08:20",
        "interviewLocation": "面试地点",
        "interviewType": "初试",
        "interviewWay": "视频",
        "jobName": "职位名称",
        "meetingUrl": "会议链接",
        "startTime": "2026-08-12 08:00"
      }
    ]
  },
  "message": null
}
```

### data 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `pendingResumeCount` | integer | 待筛选简历数量（不包含已取消已过期的） |
| `pendingInterviewEvaluationCount` | integer | 待评价面试数量（不包含未评价但已完成的） |
| `pendingInterviewCount` | integer | 待参加面试数量（不包含面试官已拒绝的） |
| `pendingInterviews` | array | 待参加面试列表 |

### pendingInterviews 元素字段

| 字段 | 说明 |
|------|------|
| `applicantName` | 候选人姓名 |
| `applyId` | 申请 ID |
| `jobName` | 应聘职位名称 |
| `interviewType` | 面试轮次（初试/复试/终试等） |
| `interviewWay` | 面试方式（视频/现场等） |
| `startTime` | 开始时间（YYYY-MM-DD HH:mm） |
| `endTime` | 结束时间（YYYY-MM-DD HH:mm） |
| `interviewLocation` | 面试地点（可能为 null） |
| `meetingUrl` | 会议链接（可能为 null） |

### 注意事项

- 候选人/求职者信息属于 **L2 敏感数据**，展示候选人姓名、职位、时间等摘要信息即可，不回显原始 JSON
- 待办数量字段优先展示，面试列表用表格呈现
- `todoTypes` 传空或省略时查询全部类型；数量字段不包含面试官已拒绝/已取消的待办
