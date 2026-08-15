# 招聘面试 - 面试质量与竞品情报分析命令参考

> CLI 版本要求：beisen-cli >= 0.2.5
> 两个分析接口均为**异步任务**模式，返回 `taskId`，需按 [async-tasks.md](async-tasks.md) 的轮询协议获取最终报告。分析类任务耗时较长，执行前提醒用户耐心等待。

## analyzeInterviewQuality — 面试官质量评估报告

```bash
beisen-cli interview interviewAnalysis analyzeInterviewQuality --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `userIdName` | string | ❌ | 面试官 UserId 或姓名；有值时优先走该面试官的所有面试分析 |
| `jobIdCode` | string | ❌ | 职位 ID 或编码或名称；与 `interviewType` 必须同时有值 |
| `interviewType` | string | ❌ | 面试轮次名称或编码；与 `jobIdCode` 必须同时有值 |
| `assessmentFocus` | string | ❌ | 考察重心：面试是 HR 初筛，还是业务技术面试 |
| `reviewDimensions` | array | ❌ | 自定义维度：用户关注的自定义分析维度 |

### 参数示例

```bash
# 分析某面试官的所有面试质量
beisen-cli interview interviewAnalysis analyzeInterviewQuality --data '{"userIdName":"张三"}'

# 分析某职位的初试质量
beisen-cli interview interviewAnalysis analyzeInterviewQuality --data '{"jobIdCode":"职位ID或编码","interviewType":"初试","assessmentFocus":"业务技术面试"}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "taskId": "异步任务Id"
  },
  "message": null
}
```

### 轮询结果

用返回的 `taskId` 调用 `beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'`，直到 `isFinished == true`，从 `resultJson` 解析面试质量评估报告。

## analyzeCompetitorIntelligence — 竞品情报分析报告

```bash
beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `activeDimension` | string | ✅ | 竞品公司分析维度，根据客户需求总结分析维度 |
| `companyNames` | array | ✅ | 竞品公司名称列表 |

### 参数示例

```bash
beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence --data '{"activeDimension":"人才策略与招聘动向","companyNames":["某科技公司"]}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "taskId": "异步任务Id"
  },
  "message": null
}
```

### 轮询结果

用返回的 `taskId` 调用 `beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'`，直到 `isFinished == true`，从 `resultJson` 解析竞品情报分析报告。

### 注意事项

- `activeDimension` 和 `companyNames` 为必填，缺一不可
- `taskId` 必须从返回中提取，严禁编造
- 报告内容可能包含竞品公司公开信息，展示时以分析结论为主，注意不涉及机密数据
