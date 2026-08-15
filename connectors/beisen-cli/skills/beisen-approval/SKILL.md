---
name: beisen-approval
version: 1.1.20
description: "北森审批中心查询。本 Skill 用于查询审批流程的当前状态、节点、审批人等信息，覆盖本人待办、已办；支持按流程状态（在途/已结束）和时间范围筛选。当用户询问'我有什么待办'、'审批进度'、'已办事项'、'流程到哪了'、'在途流程'、'已结束流程'等审批相关问题时触发。每人仅能查询自己发起或参与过的流程，不支持创建、审批、转交等写操作。"
category: 人力资源/审批
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 审批中心

**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**

## 路由优先级

本 Skill 处理：审批流程状态、节点、审批人查询（本人待办 / 已办 ）

不归本 Skill 处理：
- 招聘 offer 审批 → [../beisen-recruitment/SKILL.md](../beisen-recruitment/SKILL.md)
- 创建审批定义、审批同意/拒绝/转交/撤回 → 走后台管理界面

## 触发场景

当用户表达以下意图时触发：
- 查流程、查审批、流程进度、审批到哪了
- 我的流程状态、XX的审批进度
- 当前节点、审批人是谁
- 在途流程、进行中的流程、审批中的流程
- 已结束流程、已通过/已驳回的流程
- 某段时间内的流程、最近的流程

## 命令速查

| 场景 | CLI 命令 | 说明 |
|------|---------|------|
| 查询自己的待办 | `beisen-cli approval task queryMyPendingTasks` | 返回当前用户待处理的审批列表 |
| 查询自己的已办 | `beisen-cli approval task queryMyCompletedTasks` | 返回当前用户已处理的审批列表（默认近 30 天） |

## 命令示例

```bash
# 查询待办审批（可按 --data 传入日期 / 状态 / 类型筛选）
beisen-cli approval task queryMyPendingTasks
beisen-cli approval task queryMyPendingTasks --data '{"startDate":"2026-08-01","endDate":"2026-08-31"}'
# 查询已办审批（默认近 30 天）
beisen-cli approval task queryMyCompletedTasks
```

## 工作流程

1. **查本人待办**：用户需要查询自己的待办时，执行 `beisen-cli approval task queryMyPendingTasks`，结果按到达时间降序排列，需保证统计的数量与查询到的数量一致

2. **查本人已办**：用户需要查询自己的已办时，执行 `beisen-cli approval task queryMyCompletedTasks`，默认查询近 30 天的已办任务，结果按发起时间降序排列，需保证统计的数量与查询到的数量一致

3. **时间范围提取**：用户提到时间范围时，自行提取查询的开始/结束时间，格式 `YYYY-MM-DD`，作为 `startDate` / `endDate` 传入 `--data`。

4. **流程状态**：流程状态的名称与值见 [references/processstate.md](references/processstate.md)（审批中=1、通过=2、不通过=3、已完成=4、已终止=5、已驳回=6、已撤回=7）。筛选在途/已结束流程时，按对应状态值作为 `approvalStatuses` 传入 `--data`。

5. **结果输出**：根据查询结果先进行总结，再以 Markdown 表格展示详细内容；若结果中返回了 `detailPageUrl` 任务链接，将链接作为流程标题的超链形式展示。

## 处理链

1. **查待办** → `approval task queryMyPendingTasks` 获取待办列表，提取 `processTitle`、`currentNode`、`currentApproverName`、`startTime`、`arrivalTime`、`detailPageUrl` 等关键字段
2. **用户明确需要详情时** → 根据返回的 `approvalObjectId` 或 `taskId` 补查详情（如有对应命令）
3. **查已办** → `approval task queryMyCompletedTasks` 获取已处理记录，提取 `processStatus`/`processStatusName`（审批状态）和 `arrivalTime`（到达时间）
4. 已拿到 `approvalObjectId` 后，不要重复查询列表

## 执行原则

- 待办 / 已办命令查询当前登录用户的审批数据；按发起人查询需传入 `ownerId`（员工ID），且仅能查询自己发起或参与过的流程
- 筛选条件通过 `--data` 的 JSON 传入（`approvalStatuses` / `approvalTypes` / `startDate` / `endDate`），均为可选
- `approvalStatuses` 取值见 [references/processstate.md](references/processstate.md)；
- 审批列表属于 L1 内部数据，正常展示；批量结果较多时使用摘要模式
- 返回的 `approvalObjectId`、`taskId`、`currentApproverId` 等 ID 必须从 CLI 返回中提取，严禁编造
- 审批标题和审批人信息直接展示，无需额外转换

## 返回字段说明

### 响应结构

CLI 返回为 JSON，外层为信封，内层为业务数据：

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "data": [ { "...": "审批条目" } ]
  }
}
```

- `ok`：CLI 调用是否成功
- `identity`：身份标识
- `data.code`：状态码（`"200"` 表示成功）
- `data.data`：审批条目数组

### 审批条目字段

以下字段在 `queryMyPendingTasks`、`queryMyCompletedTasks` 返回的每条审批记录中一致出现：

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

## 输入输出实例

### 查询本人的待办信息

约束：基于 `queryMyPendingTasks` 查询出的结果，按到达时间降序排列。

问题实例：帮我查下我还有哪些没审批的待办

回复实例：你有一条李四的晋升审批待审批

**待你处理（1条）**

| 流程标题 | 审批类型 | 当前节点 | 当前审批人 | 发起时间 | 到达时间 |
|--------|---------|--------|--------|------|---------|
| 李四的晋升审批 | 晋升审批 | 部门总监审批 | 李四 | 2026-06-10T09:30:00 | 2026-06-12 14:00 |

### 查询本人的已办信息

约束：基于 `queryMyCompletedTasks` 查询出的结果，按发起时间降序排列。

问题实例：帮我查下我有哪些已办

回复实例：你已处理了以下数据

**你已处理（2条）**

| 序号 | 流程标题 | 审批类型 | 状态 | 当前节点 | 当前审批人 | 发起时间 |
|--------|--------|---------|------|---------|-----------|---------|
| 1 | 张三的请假审批 | 请假 | 审批中 | 部门总监审批 | 李四 | 2026-06-10T09:30:00 |
| 2 | 张三的请假审批 | 请假 | 已通过 | -- | -- | 2026-06-12T10:00:00 |

## 边界情况

- 查询结果为空时，说明"该员工暂无相关审批流程"
- 时间范围参数只传了开始时间或结束时间时，按单边筛选处理

## Playbook 案例

### 案例 1：查询待办审批

用户问："我有什么待办审批？"

执行步骤：
1. 前置检查（beisen-shared 的 Step 1-3）
2. 执行 `beisen-cli approval task queryMyPendingTasks`
3. 解析返回的 `data.data` 数组，按 `arrivalTime` 降序展示流程标题（`processTitle`）、当前节点（`currentNode`）、当前审批人（`currentApproverName`）、发起时间（`startTime`）、到达时间（`arrivalTime`）
4. 如返回结果较多，提示"还有更多待办，是否继续查看？"

### 案例 2：查询已办审批

用户问："我最近处理了哪些审批？"

执行步骤：
1. 前置检查
2. 执行 `beisen-cli approval task queryMyCompletedTasks`（默认近 30 天）
3. 按发起时间（`startTime`）降序展示流程标题（`processTitle`）、状态（`processStatusName`）、当前节点（`currentNode`）、当前审批人（`currentApproverName`）、发起时间（`startTime`）
4. 如返回结果较多，提示存在更多记录


## 详细参考

- [references/pending-list.md](references/pending-list.md)：待办命令详细参数与返回格式
- [references/done-list.md](references/done-list.md)：已办命令详细参数与返回格式
- [references/processstate.md](references/processstate.md)：审批流程状态名称与值

## 不在本 Skill 范围

- 创建审批定义（走后台管理）
- 非审批类待办（如招聘待办 → beisen-recruitment）
- 审批操作（同意/拒绝/转交/撤回）— 当前版本不支持
