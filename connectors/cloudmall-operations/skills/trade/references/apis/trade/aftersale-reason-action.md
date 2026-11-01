# 交易域 — 售后原因库契约（写操作）

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-aftersale-config.md`
> **先读现值**：写入前用 `aftersale-reason-query.md` 的 reason.list 读原值、从 reason.group-list 取真实大类名；原因库是租户级共享配置，写入前向用户确认目标原因与影响面，不在用户只问查询时执行写操作。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 aftersale.reason.create 🟡 · aftersale.reason.update 🟡 · aftersale.reason.toggle 🟡 · aftersale.reason.delete 🔴 · aftersale.reason.reorder 🟡

---

## ✅ 新增售后原因 — ops.trade.aftersale.reason.create

用途：新增一个售后原因（🟡）。

> **两条硬约束（2026-10-12 评测 badcase 71/73 整改）**：
> 1. **不得以修改预置原因（`isPreset=true`）作为任何替代/推荐方案**——改名冲突、复用、扩展适用类型等场景，宁可新增自定义原因或请用户决策，预置数据只读；
> 2. **目标原因不存在时，说明并列出现有原因请用户确认，不得自行创建后再执行**（排序/编辑/停用等指令同样适用）——创建原因必须来自用户的明确指令。返回新原因 ID 字符串；不改变既有原因；创建后用 reason.list 回读。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| reasonName | 字符串 | 是，≤128 字符 | 原因名称，运营可读 |
| applicableTypes | 字符串数组 | 是，非空 | 适用售后类型，元素限 `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE`（合法取值约定；服务端仅做非空校验，不校验元素值，错误值会静默导致原因不进对应子 Tab） |
| groupName | 字符串 | 是，≤64 字符 | 大类名称；优先从 group-list 取真实大类名 |
| responsibility | 字符串 | 是 | 责任归属：`USER` / `MERCHANT` / `SHARED` |
| needEvidence | 布尔值 | 是 | 是否需要凭证 |
| allowVideo | 布尔值 | 是 | 是否允许视频凭证 |
| sortWeight | 整数 | 否，默认 0，≥0 | 同大类内排序权重，数值越大越靠前 |

来源：`CreateAfterSaleReasonRequest`。创建后用 `ops.trade.aftersale.reason.list` 按对应 subTab 回读新原因。

```json
{
  "capability": "ops.trade.aftersale.reason.create",
  "input": {
    "reasonName": "七天无理由退货",
    "applicableTypes": ["REFUND_ONLY", "RETURN_REFUND"],
    "groupName": "用户原因",
    "responsibility": "USER",
    "needEvidence": false,
    "allowVideo": false,
    "sortWeight": 0
  },
  "summary": "新增售后原因"
}
```

---

## ✅ 编辑售后原因 — ops.trade.aftersale.reason.update

用途：编辑既有售后原因（🟡）。全量覆盖：所有必填字段都要提交，不只提交变化字段。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | reason.list 返回的原因 id |
| 其余字段 | 同 reason.create | 是 | reasonName/applicableTypes/groupName/responsibility/needEvidence/allowVideo 必填；sortWeight 可选 |

来源：`UpdateAfterSaleReasonRequest`（字段与 create 完全一致）。**`sortWeight` 不传保留原值**（服务端仅非 null 时更新），清零需显式传 `0`——这是与 create（默认 0）的差异点。先 reason.list 读原值，向用户复述变更点后提交；回读确认。`applicableTypes` 决定原因出现在哪个子 Tab 与 C 端可选范围，修改它等于改变原因的适用面，需向用户确认。

```json
{
  "capability": "ops.trade.aftersale.reason.update",
  "input": {
    "id": "7200000000000000001",
    "reasonName": "七天无理由退货",
    "applicableTypes": ["REFUND_ONLY", "RETURN_REFUND", "EXCHANGE"],
    "groupName": "用户原因",
    "responsibility": "USER",
    "needEvidence": true,
    "allowVideo": false,
    "sortWeight": 10
  },
  "summary": "编辑售后原因"
}
```

---

## ✅ 启停售后原因 — ops.trade.aftersale.reason.toggle

用途：启用或停用一个售后原因（🟡 可逆）。无请求体，仅路径 `id`；当前状态在 reason.list 的 `enabled` 字段。

停用后 C 端新建售后不可再选该原因；已创建售后的 `reasonId`/`applyReason` 快照不受影响（原因库与售后单是快照式关联，词库修改不回写历史售后）。回读 reason.list 确认 `enabled` 翻转。

```json
{
  "capability": "ops.trade.aftersale.reason.toggle",
  "input": { "id": "7200000000000000001" },
  "summary": "启停售后原因"
}
```

---

## ✅ 删除售后原因 — ops.trade.aftersale.reason.delete

用途：删除一个售后原因（🔴 不可逆）。仅路径 `id`。**预置原因（reason.list 的 `isPreset=true`）服务端直接拒绝删除。**

删除前：用 reason.list 确认目标且 `isPreset=false`；用 `ops.trade.aftersale.search` 按状态过滤进行中售后，向用户说明系统不阻止被引用原因的删除、历史售后保留原因名快照不受影响；确认不再使用后执行。删除后回读 reason.list 确认消失。

```json
{
  "capability": "ops.trade.aftersale.reason.delete",
  "input": { "id": "7200000000000000001" },
  "summary": "删除售后原因"
}
```

---

## ✅ 原因排序 — ops.trade.aftersale.reason.reorder

用途：大类内原因排序（🟡）。提交该大类下**全部**原因 ID 的新顺序（拖拽后顺序），不是增量调整。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| groupName | 字符串 | 是，非空 | 目标大类名 |
| reasonIds | ID字符串数组 | 是，非空 | 按新顺序排列的全部原因 ID |

来源：`ReasonReorderRequest`。数组顺序即最终顺序（影响同类内展示优先级）。提交前先 reason.list 核对该大类当前全部原因 ID；提交后回读 list 核对新顺序。

```json
{
  "capability": "ops.trade.aftersale.reason.reorder",
  "input": {
    "groupName": "用户原因",
    "reasonIds": ["7200000000000000002", "7200000000000000001"]
  },
  "summary": "排序售后原因"
}
```
