# 交易域 — 售后原因库契约（查询侧）

> 概念知识：`references/domains/trade-concepts.md`；原因维护写操作见 `aftersale-reason-action.md`；运营流程：`references/flows/trade-aftersale-config.md`
> `subTab` 取值与售后类型一致：`REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE`（前端子 Tab 映射与后端应用层过滤一致）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 aftersale.reason.list · aftersale.reason.group-list

---

## ✅ 原因库查询 — ops.trade.aftersale.reason.list

用途：按售后类型读取原因库全量（含停用项），按大类分组返回。是维护原因、为代客创建/修改选择 `reasonId` 的事实来源。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| subTab | 字符串 | 是 | `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE` |

结果来源：`AfterSaleReasonGroupVO` 数组，每个元素含 `groupName`（大类名）与 `reasons[]`。每个原因项的关键字段：`id`（后续写操作定位）、`reasonName`、`groupName`、`responsibility`（`USER` / `MERCHANT` / `SHARED`）、`applicableTypes`（适用售后类型数组）、`isPreset`（布尔值，预置原因不可删除）、`enabled`（启用状态）、`needEvidence`、`allowVideo`、`sortWeight`。排序按大类升序、同类内 `sortWeight` 降序。

```json
{
  "capability": "ops.trade.aftersale.reason.list",
  "input": { "subTab": "REFUND_ONLY" },
  "summary": "查询仅退款原因库"
}
```

---

## ✅ 原因大类查询 — ops.trade.aftersale.reason.group-list

用途：读取某售后类型下已存在的大类名列表，用于新增/编辑原因时选择真实 `groupName`，不自行发明大类名。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| subTab | 字符串 | 是 | `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE` |

结果来源：`List<String>`（大类名字符串数组）。

```json
{
  "capability": "ops.trade.aftersale.reason.group-list",
  "input": { "subTab": "REFUND_ONLY" },
  "summary": "查询仅退款原因大类"
}
```
