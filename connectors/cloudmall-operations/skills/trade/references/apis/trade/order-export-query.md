# 交易域 — 订单导出契约（查询侧）

> 运营流程：`references/flows/trade-fulfillment.md`；导出任务取消（写操作）见 `order-export-action.md`
> 导出是只读查询面（🟢）。所有 ID 为十进制字符串。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 order.export · order.export.task.detail · order.export.task.list

---

## ✅ 订单导出 — ops.trade.order.export

用途：导出订单清单，返回 COS 预签名下载链接（🟢 URL 型导出）。**双模式**：小数据量同步完成（`mode=sync` 直接拿 `downloadUrl`）；大数据量自动转异步任务（`mode=async` 拿 `taskId` 走任务查询轮询）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| exportType | 字符串 | 是 | 导出维度：`ORDER`（订单维度）/ `ORDER_ITEM`（订单商品详情维度） |
| 其余筛选字段 | 同 order.search | 否 | 继承订单分页查询全部筛选字段（时间/状态/关键词等），导出忽略分页 |

来源：`OrderExportRequest`（继承 `OrderPageQuery`）。结果来源 `ExportResultVO`：`mode`（`sync` / `async`）、`taskId`（仅 async）、`downloadUrl`（仅 sync 或异步完成后）。**必须按 `mode` 分支报告**：sync 直接给下载链接（约 60 分钟时效）；async 报告 taskId 并轮询任务详情。无匹配数据时服务端拒绝提交（不能导出空文件）。

```json
{
  "capability": "ops.trade.order.export",
  "input": { "exportType": "ORDER", "status": "PENDING_SHIPMENT" },
  "summary": "导出待发货订单"
}
```

---

## ✅ 导出任务详情 — ops.trade.order.export.task.detail

用途：查询导出任务的进度与下载地址（🟢）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| taskId | ID字符串 | 是，路径参数 | export 返回的任务 ID |

结果来源 `OrderExportTaskVO`：

| 字段 | 类型 | 含义 |
|---|---|---|
| taskId / status | ID字符串 / 字符串 | 任务 ID 与状态：`PENDING` 排队中、`RUNNING`（对外展示 `PROCESSING`）导出中、`SUCCESS` 已完成、`FAILED` 失败（已取消任务对外也归并为 FAILED，避免轮询不终止） |
| exportType / fileName | 字符串 | 导出维度与文件名 |
| progress / exportedRows | 整数 | 进度百分比 0~100 / 已导出行数 |
| truncated | 布尔值 | true 表示命中行数上限被截断，文件不完整，必须向用户明示 |
| downloadUrl | 字符串 | 仅 SUCCESS 且未过期时有值 |
| message / errorMessage | 字符串 | 截断说明（message）/ 失败与取消原因（errorMessage，取消任务的说明写入此字段） |
| operatorName / createdAt / completedAt | 字符串 / 毫秒时间戳 | 提交人与时间 |

**仅任务提交人本人可见**（导出含收货人、手机号、地址，Service 层强制归属校验）：Agent 以当前身份查询他人任务会失败，属预期。轮询以 SUCCESS/FAILED 为终止态；`downloadUrl` 过期后需重新提交导出。

```json
{
  "capability": "ops.trade.order.export.task.detail",
  "input": { "taskId": "8300000000000000001" },
  "summary": "查询导出任务进度"
}
```

---

## ✅ 导出任务列表 — ops.trade.order.export.task.list

用途：分页查询**当前操作人本人提交**的订单导出任务列表（服务端按创建人过滤，非租户维度；同 task.detail 的归属规则）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| pageNum | 整数 | 否，默认 1 | 页码 |
| pageSize | 整数 | 否，默认 10 | 每页条数 |

```json
{
  "capability": "ops.trade.order.export.task.list",
  "input": { "pageNum": 1, "pageSize": 10 },
  "summary": "查询导出任务列表"
}
```
