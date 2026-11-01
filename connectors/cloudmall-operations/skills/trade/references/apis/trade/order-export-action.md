# 交易域 — 订单导出契约（写操作）

> **先读现值**：取消前用 `order-export-query.md` 的 export.task.detail 核对任务状态；仅 PENDING 与 RUNNING 可取消。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 order.export.task.cancel 🟡

---

## ✅ 取消导出任务 — ops.trade.order.export.task.cancel

用途：取消导出任务（🟡）。`PENDING`（排队中）与 `RUNNING`（执行中）均可取消——RUNNING 任务取消后，正在执行的 Worker 在下一次续租/回写进度时自行中止并清理临时文件；`SUCCESS` / `FAILED` 等终态不可取消。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| taskId | ID字符串 | 是，路径参数 | export 返回的任务 ID |

来源：`OrderExportTaskService.cancel`（任务不存在/终态时报错）。取消后任务状态对外归并为 FAILED（`errorMessage` 含取消说明）。执行后回读任务详情核对。

```json
{
  "capability": "ops.trade.order.export.task.cancel",
  "input": { "taskId": "8300000000000000001" },
  "summary": "取消导出任务"
}
```
