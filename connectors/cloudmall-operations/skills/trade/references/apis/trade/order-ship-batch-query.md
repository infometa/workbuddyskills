# 交易域 — 批量发货与物流导入契约（查询侧）

> 运营流程：`references/flows/trade-fulfillment.md`；批量发货/导入的写操作见 `order-ship-batch-action.md`
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 order.import-multi-package-ship.task

---

## ✅ 多包裹导入任务查询 — ops.trade.order.import-multi-package-ship.task

用途：查询多包裹发货导入任务的执行结果。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| taskId | 字符串 | 是，路径参数 | import-multi-package-ship 返回的任务 ID |

结果为 `ShipImportResultVO`；**任务未完成时 `data` 为 null**（不是失败），等待后重查。任务级失败看 `errorMessage`。

```json
{
  "capability": "ops.trade.order.import-multi-package-ship.task",
  "input": { "taskId": "IMP202609180001" },
  "summary": "查询多包裹导入任务结果"
}
```
