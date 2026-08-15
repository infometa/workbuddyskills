# 招聘主流程 - 候选人/申请/人才库命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

## bs_get_apply_detail — 按申请 ID 查询候选人申请详情

```bash
beisen-cli recruitment apply bs_get_apply_detail --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `applyIds` | array | ❌ | 申请 ID 列表（支持批量查询，一个或多个） |

示例：

```bash
beisen-cli recruitment apply bs_get_apply_detail --data '{"applyIds":["申请ID1","申请ID2"]}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "items": [ { "候选人申请详情字段" } ]
  },
  "message": null
}
```

- `data.items`：候选人申请详情列表
- 候选人信息属于 **L2 敏感数据**，仅展示摘要（姓名、应聘职位、进度），不回显原始 JSON

## bs_search_apply_list — 查询应聘者申请列表

```bash
beisen-cli recruitment apply bs_search_apply_list --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `jobId` | string | ✅ | 职位 ID（必填，可由 searchJobs 获得，单个） |
| `pageIndex` | integer | ✅ | 页码，从 0 开始，默认 0 |
| `pageSize` | integer | ✅ | 分页大小，默认 30，最大 100 |
| `name` | string | ❌ | 应聘者姓名搜索 |
| `phaseName` | string | ❌ | 阶段名称（须为该职位流程中的阶段名，如"面试"） |
| `statusName` | string | ❌ | 状态名称（须为该职位流程中的状态名，如"面试中"；多个阶段存在同名状态时需同时指定阶段名称） |
| `aiEvaluateResults` | array | ❌ | AI 评估简历结果：0=未发起,1=评估中,2=评估失败,3=非常符合,5=基本符合,4=不符合,6=信息不足 |
| `filterResults` | array | ❌ | 筛选结果：1=通过,2=待定,3=淘汰,4=未筛选 |
| `interviewStatuses` | array | ❌ | 面试状态：0=未安排,1=已安排 |
| `offerStatuses` | array | ❌ | Offer 状态：-1=未创建,0=待发offer,1=已发offer,2=已接受offer,3=已拒offer,4=失效offer,5=已入职offer |
| `entryStatuses` | array | ❌ | 入职状态：1=待入职,2=已入职,3=已取消入职,4=已转正,5=已离职,6=退休,0=无入职信息 |
| `signInStates` | array | ❌ | 签到状态：2=已签到,3=未到场,1=未签到 |
| `searchBatchId` | string | ❌ | 搜索批次 ID（传入后从用户偏好获取上次搜索条件作为 FilterJson） |

示例：

```bash
# 查询某职位全部应聘者申请
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"职位ID","pageIndex":0,"pageSize":30}'

# 按姓名搜索
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"职位ID","name":"张","pageIndex":0,"pageSize":30}'

# 查询 AI 评估为"非常符合"的申请
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"职位ID","aiEvaluateResults":[3],"pageIndex":0,"pageSize":30}'

# 查询待筛选简历（未筛选）
beisen-cli recruitment apply bs_search_apply_list --data '{"jobId":"职位ID","filterResults":[4],"pageIndex":0,"pageSize":30}'
```

### 返回结构

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "applyId": "申请ID",
        "applicantId": "候选人ID",
        "name": "候选人姓名",
        "gender": "性别",
        "age": "年龄",
        "school": "学校",
        "educationLevel": "学历",
        "major": "专业",
        "lastCompany": "最近公司",
        "lastPosition": "最近职位",
        "yearsOfWork": "工作年限",
        "firstChannel": "投递渠道",
        "phaseStatus": "阶段-状态",
        "aiEvaluateResumeResultDes": "AI评估结果",
        "createdTime": "申请时间"
      }
    ],
    "totalCount": 10
  },
  "message": null
}
```

### 注意事项

- `jobId`、`applyId`、`applicantId` 必须从 CLI 返回中提取，严禁编造
- `phaseName`/`statusName` 须为职位流程中的实际阶段/状态名；返回的 `phaseStatus` 字段即"阶段-状态"格式，可直接参考
- 候选人信息属于 **L2 敏感数据**，仅展示摘要（姓名、学历、最近职位、阶段状态、渠道等），不回显原始 JSON
- 分页：`totalCount` 为筛选条件下的申请总数，若已加载条数 < `totalCount` 需提醒用户可继续翻页

## bs_search_candidates_in_talentpool — 搜索人才库推荐候选人

```bash
beisen-cli recruitment talentPool bs_search_candidates_in_talentpool --data '<json>'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `jobRequirements` | string | ❌ | 职位要求，例如："3–5 年工作经验，本科及以上学历，有 Agent 落地经验" |
| `pageIndex` | integer | ❌ | 页码，从 0 开始 |
| `pageSize` | integer | ❌ | 每页数量，默认 10 |

示例：

```bash
beisen-cli recruitment talentPool bs_search_candidates_in_talentpool --data '{"jobRequirements":"3-5年Java开发经验，本科及以上","pageIndex":0,"pageSize":10}'
```

### 异步任务处理

该接口返回**异步任务**，返回数据为任务状态结构：

```json
{
  "code": 200,
  "data": {
    "taskId": "异步任务Id",
    "status": "Running",
    "statusDescription": "执行中",
    "isFinished": false,
    "progressPercent": 30,
    "label": "任务描述"
  }
}
```

**必须轮询任务结果**：

1. 提取返回的 `taskId`
2. 调用 `beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'` 轮询
3. 直到 `isFinished == true`：
   - `status == "Succeeded"` → 从 `resultJson`（JSON 字符串）解析候选人列表
   - `status == "Failed"` → 读取 `errorMessage` 向用户说明
   - `status == "Cancelled"` → 任务已取消

### 注意事项

- 候选人信息属于 **L2 敏感数据**，仅展示摘要，不回显原始 JSON
- `taskId` 必须从返回中提取，严禁编造
- 轮询间隔建议 2-5 秒，避免高频请求
