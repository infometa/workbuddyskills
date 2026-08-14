---
name: "flow-tasks-query"
description: "Used when the user's request involves pending approval flow, pending business flow, pending stage propeller, pending approval, my to-do, and similar scenarios"
apiName: "flow_tasks_query_mcp"
---
# Pending Task Query

当前 MCP 版本只保留审批流待办查询；业务流和阶段推进待办在当前工具集中没有对应 tool，命中时忽略。

## 核心约束

- 只做待办查询，不做写入。
- 不暴露 CLI、SQL 或命令映射。
- “我 / 我的 / me / my to-do” 一律先取当前用户。
- 查询结果为空时直接说明，不改条件重试。

## 处理流程

1. 判断是否是审批流待办。
2. 通过 `get_current_user` 取当前 `employeeId`。
3. 调用 `approval_search` 查询待办。
4. 如需展示关联单据，再补 `approval_runtime_get_task_detail`。
5. 如只有对象 ID，没有名称，再用 `data_record_get_by_id` 补显示名。

## Tool 选择

| 目的 | Tool | 固定 apiName |
|---|---|---|
| 取当前用户 | `get_current_user` | - |
| 查询审批待办 | `approval_search` | `action_zwPNM__c` |
| 获取审批任务详情 | `approval_runtime_get_task_detail` | `ApprovalFeedDetail` |
| 按对象和 ID 取记录 | `data_record_get_by_id` | `GetRecordById` |

## 调用方式

### 审批流待办

```json
{
  "apiName": "action_zwPNM__c",
  "workflow_name": "<用户输入中的流程/待办关键词>",
  "task_name": "<用户输入中的任务关键词>",
  "current_candidate_ids": ["<当前员工ID>"]
}
```

### 详情补全

当待办结果里只有 `taskId`、`todoId` 或 `workflowInstanceId` 时，先调：

```json
{
  "apiName": "ApprovalFeedDetail",
  "taskId": "<taskId>",
  "todoId": "<todoId>",
  "workflowInstanceId": "<workflowInstanceId>"
}
```

若详情里只有对象 ID，再调：

```json
{
  "apiName": "GetRecordById",
  "object_api_name": "<objectApiName>",
  "id": "<recordId>"
}
```

## 输出

- `Record count: N`
- 审批流待办表格
- 业务记录显示名优先；没有就用原始 ID

## 不支持

- 业务流待办
- 阶段推进待办
- 任何写操作
