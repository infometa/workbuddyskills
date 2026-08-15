# 审批中心 - 待办命令参考

## queryMyPendingTasks — 查询我的待办

```bash
beisen-cli approval task queryMyPendingTasks [--data '{...}']
```

### 参数（通过 --data 传入 JSON）

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|:----:|
| `approvalStatuses` | array | 流程状态筛选，不填则返回全部 | 否 |
| `approvalTypes` | array | 审批类型编码，不填则返回该用户所有类型流程 | 否 |
| `startDate` | string | 起始日期 `YYYY-MM-DD`，按流程发起时间筛选 | 否 |
| `endDate` | string | 结束日期 `YYYY-MM-DD`，接口默认查到当日 23:59:59 | 否 |

### 返回结构

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "data": [
      {
        "approvalObjectId": "dffb5040-610f-45a1-bb3f-53f93a2495e7",
        "taskId": "dffb5040-610f-45a1-bb3f-53f93a2495e7",
        "processTitle": "wo de ming zi的审批自由流程",
        "approvalCategory": 10000005,
        "approvalCategoryName": "审批类别AAA开发态",
        "bizAppName": "BeisenCloudStepAAA",
        "processStatus": 1,
        "processStatusName": "审批中",
        "currentNode": "单人审批",
        "currentApproverId": [460088235],
        "currentApproverName": "wo de ming zi",
        "startTime": "2025-05-08T15:30:47.36",
        "arrivalTime": "2025-05-08 15:30",
        "detailPageUrl": "//cloud.italent.link/ItalentTransfer?iTalentFrame=..."
      }
    ]
  }
}
```

- `ok`：CLI 调用是否成功
- `identity`：身份标识
- `data.code`：状态码（`"200"` 表示成功）
- `data.data`：审批条目数组

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `approvalObjectId` | string | 审批对象ID（UUID 格式），审批实例的唯一标识 |
| `taskId` | string | 任务ID（UUID 格式），当前任务实例标识 |
| `processTitle` | string | 流程标题 |
| `approvalCategory` | number | 审批类型编码 |
| `approvalCategoryName` | string\|null | 审批类型名称（可能为 null） |
| `bizAppName` | string | 业务应用名称（如 BeisenCloudStepAAA、BeisenCloudDemo、ServiceCenter） |
| `processStatus` | number | 流程状态值（1=审批中、2=通过、3=不通过、4=已完成、5=已终止、6=已驳回、7=已撤回） |
| `processStatusName` | string | 流程状态名称（如"审批中"） |
| `currentNode` | string | 当前审批节点名称 |
| `currentApproverId` | number[] | 当前审批人ID列表 |
| `currentApproverName` | string | 当前审批人姓名 |
| `startTime` | string | 流程发起时间（ISO 8601 格式，如 `2025-05-08T15:30:47.36`） |
| `arrivalTime` | string | 任务到达时间（格式 `YYYY-MM-DD HH:mm`，如 `2025-05-08 15:30`） |
| `detailPageUrl` | string | 审批详情页URL（用于在流程标题上做超链展示） |

> 所有字段必须从 CLI 返回中提取真实值，严禁编造。

### 注意事项

- 仅返回当前登录用户的待办
- 结果按到达时间（`arrivalTime`）降序排列
- `approvalStatuses` 取值见 [processstate.md](processstate.md)
- `approvalObjectId`、`taskId` 等标识符必须从返回中提取，严禁编造
- `approvalCategoryName` 可能为 null，展示时以 `approvalCategory` 编码代替或省略类型列
