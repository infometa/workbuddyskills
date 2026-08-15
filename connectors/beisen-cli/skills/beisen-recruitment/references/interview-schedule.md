# 招聘 - 面试日程命令参考

## interview-schedule — 查询面试日程

```bash
beisen-cli recruitment interview-schedule [--start <date>] [--end <date>]
```

### 参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--start` | date | 起始日期（YYYY-MM-DD） | 今天 |
| `--end` | date | 结束日期（YYYY-MM-DD） | 7天后 |

### 返回结构

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "items": [
      {
        "interview_id": "面试ID",
        "candidate_name": "候选人姓名",
        "job_title": "面试职位",
        "interview_time": "2026-08-10T14:00:00Z",
        "interview_type": "初面",
        "interviewer": "面试官",
        "location": "会议室A",
        "status": "待面试"
      }
    ],
    "total": 3,
    "has_more": false
  }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `interview_id` | 面试唯一标识 |
| `candidate_name` | 候选人姓名 |
| `job_title` | 面试职位名称 |
| `interview_time` | 面试时间（ISO 8601） |
| `interview_type` | 面试类型（初面/复面/终面） |
| `interviewer` | 面试官姓名 |
| `location` | 面试地点 |
| `status` | 面试状态（待面试/已完成/已取消） |

### 注意事项

- 返回当前登录用户相关的面试日程
- 不指定日期范围时默认查询未来 7 天
- 候选人姓名属于 L2 敏感数据，展示时注意隐私
