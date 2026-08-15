# 招聘主流程 - 异步任务命令参考

> CLI 版本要求：beisen-cli >= 0.2.5

部分招聘接口（如 `bs_search_candidates_in_talentpool`、面试域的 `analyzeInterviewQuality`、`analyzeCompetitorIntelligence`）为**异步任务**模式：发起后立即返回 `taskId`，需轮询任务状态获取最终结果。

## bs_get_async_task_status — 查询异步任务执行结果

```bash
beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `taskId` | string | ✅ | 异步任务 ID，来自发起异步任务接口的返回值 |

### 返回结构（data 字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `taskId` | string | 异步任务 ID |
| `businessCode` | string | 业务编码，标识该异步任务属于哪个业务 |
| `label` | string | 任务描述，由发起方设置 |
| `status` | string | 任务状态：Running-执行中 / Succeeded-执行成功 / Failed-执行失败 / Cancelling-取消中 / Cancelled-已取消 |
| `statusDescription` | string | 任务状态中文说明 |
| `statusText` | string | 当前执行阶段的文字说明 |
| `isFinished` | boolean | 是否已进入终态（Succeeded/Failed/Cancelled），终态无需再轮询 |
| `progressPercent` | integer | 执行进度百分比 0-100 |
| `processedCount` | integer | 已处理数量 |
| `totalCount` | integer | 需处理总数量，0 表示未提供总量 |
| `resultJson` | string | 执行结果的 JSON 字符串，**仅在 status=Succeeded 时有值** |
| `errorMessage` | string | 失败原因，仅在 status=Failed 时有值 |
| `createTime` | string | 任务创建时间 |
| `updateTime` | string | 任务最后更新时间 |
| `finishTime` | string | 任务进入终态的时间，未结束时为空 |

## bs_cancel_async_task — 取消异步任务

```bash
beisen-cli recruitment async_task bs_cancel_async_task --data '{"taskId":"<id>"}'
```

### 参数（--data JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `taskId` | string | ✅ | 异步任务 ID，来自发起异步任务接口的返回值 |

### 返回结构（data 字段）

| 字段 | 类型 | 说明 |
|------|------|------|
| `taskId` | string | 异步任务 ID |
| `status` | string | 任务当前状态（同状态枚举） |
| `accepted` | boolean | 取消指令是否已被接受。已进入终态的任务无法取消，返回 false |

## 轮询流程

1. 发起异步任务 → 提取 `taskId`
2. 调用 `bs_get_async_task_status` 轮询（间隔 2-5 秒，最长等待不超过 5 分钟）
3. `isFinished == true` 后：
   - `Succeeded` → 解析 `resultJson` 得到最终结果
   - `Failed` → 读取 `errorMessage` 向用户说明失败原因
   - `Cancelled` → 告知用户任务已取消
4. 若任务执行时间过长或用户放弃等待，可调用 `bs_cancel_async_task` 取消

### 注意事项

- `taskId` 必须从发起接口返回值中提取，严禁编造
- `resultJson` 是 JSON **字符串**，需要先 `JSON.parse` 再展示
- 轮询避免高频请求，控制在 2-5 秒间隔
