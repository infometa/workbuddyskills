# 交易域 — 售后写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-aftersale.md`
> **先读现值**：全部写入先读 `aftersale-query.md` 的 detail（类型、现态、金额、商品行、退回方式），确认业务单号与操作结论；代客创建（create-on-behalf）见 `aftersale-behalf.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。除代客创建返回新售后号外，写能力没有业务详情返回，成功受理后使用 detail 回读。超时或不确定结果先回读，禁止自动重复审核、退款、创建、追加备注或发货。退款状态必须进一步核对退款单，`REFUNDING` 不等于资金到账。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 aftersale.audit 🔴 · aftersale.return-logistics.input 🔴 · aftersale.merchant-ship 🔴 · aftersale.receive.confirm 🔴 · aftersale.receive.reject 🔴 · aftersale.remark.update 🟡 · aftersale.remark.add 🟡 · aftersale.complete-offline 🔴 · aftersale.modify 🔴 · aftersale.reject-complete-offline 🔴

---

## ✅ 售后审核 — ops.trade.aftersale.audit

用途：对 `PENDING_AUDIT` 售后给出同意或拒绝结论（🔴）。同意仅退款会直接发起退款；同意退货退款或换货进入 `PENDING_BUYER_RETURN`。已审核单不可重复审核；通过可能触发退款，先确认金额和影响。

| 参数 | 类型 | 必填与来源 |
|---|---|---|
| afterSaleNo | 字符串 | 是，已核对的详情单号 |
| approved | 布尔值 | 是，用户明确审核结论，不能传字符串或操作名 |
| rejectReason | 字符串 | 拒绝时条件必填且非空，最多 500 字符 |
| returnAddressId | ID字符串 | 同意且类型非 REFUND_ONLY 且 returnMethod 非 SELF_DELIVERY 时必填；从 `ops.trade.return-address.list-all` 取得。SELF_DELIVERY 使用自提点地址，省略此字段 |
| freightRefundAmount | 金额 | 当前不可用：DTO 有字段，但审核实现未读取，不能通过审核修改运费 |
| operatorRemark | 字符串，最多500字符 | 当前不可用：审核未读取；需备注时单独调用明确的备注能力 |
| rejectReasonCode | 字符串，最多64字符 | 当前不可用：审核未读取 |
| rejectDetail | 字符串，最多2000字符 | 当前不可用：审核未读取；注释的最少20字也未实现 |

来源：`AfterSaleAuditRequest`、`AbstractAfterSaleService.audit` 及三种售后策略；前端审核弹窗传入字段不能证明运行时已生效。只提交契约确认实际生效的字段；DTO 中存在不代表实现会消费，不可用的运费调整、审核备注等不能承诺生效。回读 `afterSaleStatus`、`auditResult`、`rejectReason`、地址快照；仅退款还要跟进 `refund` 与支付域退款单。需要改退款金额时停止审核并交由运营处理，禁止传未消费字段后声称改款成功。

```json
{
  "capability": "ops.trade.aftersale.audit",
  "input": {
    "afterSaleNo": "AS20260905000001",
  "approved": true,
    "returnAddressId": "7000000000000000001"
  },
  "summary": "审核售后"
}
```

---

## ✅ 录入退货物流 — ops.trade.aftersale.return-logistics.input

用途：登记客户寄回物流（🔴），适用于退货退款/换货的 `PENDING_BUYER_RETURN` 或 `PENDING_MERCHANT_RECEIVE`；`returnMethod=SELF_DELIVERY` 禁用。前一状态录入后进入待商家收货，后一状态允许补录，不代表已收货；不能把录单视为已收到实物。

| 参数 | 类型 | 必填 / 约束 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |
| expressCompanyCode | 字符串 | 是，非空，最多32字符，真实承运商编码 |
| trackingNumber | 字符串 | 是，非空，最多64字符，真实退回运单号 |

来源：`ReturnLogisticsInputRequest` 与 `AbstractAfterSaleService.inputReturnLogistics`。无业务详情返回；回读 `logistics` 中的承运商/运单及 `afterSaleStatus`，失败后不自动换号重试。

```json
{
  "capability": "ops.trade.aftersale.return-logistics.input",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "expressCompanyCode": "shunfeng",
    "trackingNumber": "SF1234567890"
  },
  "summary": "录入退货物流"
}
```

---

## ✅ 换货商家发货 — ops.trade.aftersale.merchant-ship

用途：登记换货商品的商家寄出方式（🔴）。`deliveryMethod` 必填且只可为 `LOGISTICS` 或 `SELF_DELIVERY`；前者额外要求承运商编码和运单号，后者不得伪造物流信息。

前置：`afterSaleType=EXCHANGE` 且 `afterSaleStatus=PENDING_MERCHANT_SHIP`，已实际交付换货商品；不能用于原订单发货。

| 参数 | 类型 | 必填 / 约束 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |
| deliveryMethod | 字符串 | 是，严格 LOGISTICS 或 SELF_DELIVERY |
| expressCompanyCode / trackingNumber | 字符串 | LOGISTICS 时条件必填且非空；SELF_DELIVERY 省略 |

来源：`MerchantShipRequest`、`AbstractAfterSaleService.inputMerchantShipLogistics`。无业务详情返回；回读状态应进入 `PENDING_BUYER_RECEIVE`，物流方式还需核对运单；回读到待买家收货只能说已发出，不说换货闭环完成。这里的 SELF_DELIVERY 是商家换货配送方式，不自动等于客户退回方式。

```json
{
  "capability": "ops.trade.aftersale.merchant-ship",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "deliveryMethod": "LOGISTICS",
    "expressCompanyCode": "shunfeng",
    "trackingNumber": "SF1234567890"
  },
  "summary": "录入换货物流"
}
```

---

## ✅ 确认收到退货 — ops.trade.aftersale.receive.confirm

用途：登记商家已经实际收到退回商品（🔴）。仅输入 `afterSaleNo`；只在待商家收货阶段、且已核验实物后调用；不能用本能力表示“物流看上去已签收”。

| 参数 | 类型 | 必填 / 来源 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |

仅 `PENDING_MERCHANT_RECEIVE` 的退货退款/换货可用。来源：`AbstractAfterSaleService.confirmReceive`、`ReturnRefundAfterSaleService`、`ExchangeAfterSaleService`。返回无业务详情；退货退款会触发资金退款，回读退款进度；换货应进入 `PENDING_MERCHANT_SHIP`。

```json
{
  "capability": "ops.trade.aftersale.receive.confirm",
  "input": {
    "afterSaleNo": "AS20260905000001"
  },
  "summary": "确认收到退货"
}
```

---

## ✅ 拒收退货 — ops.trade.aftersale.receive.reject

用途：在实际验收后拒收退回商品（🔴）。`rejectReason` 必填、非空且最多 500 字符；仅待商家收货阶段可用。

| 参数 | 类型 | 必填 / 约束 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |
| rejectReason | 字符串 | 是，非空，最多500字符，用户给出的验收结论 |

仅 `PENDING_MERCHANT_RECEIVE`；与待审核阶段的拒绝审核不同，两者不可互换。来源：`AfterSaleRejectReceiveRequest`、`AbstractAfterSaleService.rejectReceive`。返回无业务详情；回读 `auditResult=RECEIVE_REJECTED`、`rejectReason` 与流转后的售后状态。不能用拒收替代其他阶段未开放的拒绝操作。

```json
{
  "capability": "ops.trade.aftersale.receive.reject",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "rejectReason": "商品已影响二次销售"
  },
  "summary": "驳回售后"
}
```

---

## ✅ 覆盖售后备注 — ops.trade.aftersale.remark.update

用途：覆盖售后单的单条运营备注，对齐运营端编辑页（🟡）。`remark` 必须非 null 且最多 200 字符；它会替换旧值，不能误传为追加流水的 `content`；先读原备注并确认覆盖内容，避免无意覆盖。

| 参数 | 类型 | 必填 / 约束 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |
| remark | 字符串 | 是，最多200字符；允许空字符串，表示清空，须用户明确要求 |

不改变售后状态。来源：`UpdateRemarkRequest`、`AbstractAfterSaleService.updateRemark`。返回无业务详情；回读详情 `remark` 与提交值一致。

```json
{
  "capability": "ops.trade.aftersale.remark.update",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "remark": "已与客户电话确认退货原因"
  },
  "summary": "修改售后备注"
}
```

---

## ✅ 追加售后备注 — ops.trade.aftersale.remark.add

用途：追加一条可追溯的运营操作备注（🟡）。`content` 必填、非空且最多 2000 字符；与前端使用的 `remark` 覆盖字段是两个不同能力，禁止混传；追加记录不改变售后或资金状态。

| 参数 | 类型 | 必填 / 约束 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号 |
| content | 字符串 | 是，非空，最多2000字符 |

来源：`AddRemarkRequest`、`AfterSaleOperationRemarkService`。返回无业务详情；回读 `operationRemarks` 最近记录的内容/时间，重复提交会追加重复记录。不承诺修改详情的单条 `remark`；追加后可用备注流水查询核对。

```json
{
  "capability": "ops.trade.aftersale.remark.add",
  "input": {
    "afterSaleNo": "AS20260905000001",
  "content": "已与客户电话确认退货原因"
  },
  "summary": "添加售后备注"
}
```

---

## ✅ 线下完结售后 — ops.trade.aftersale.complete-offline

用途：完成自行退回自提点的售后线下流转（🔴）。仅输入 `afterSaleNo`；必须先确认 `returnMethod=SELF_DELIVERY`、售后类型和当前阶段均满足规则，且不得附带或伪造退款金额。

| 参数 | 类型 | 必填 / 来源 |
|---|---|---|
| afterSaleNo | 字符串 | 是，详情单号；没有其他输入字段 |

退货退款只允许 `PENDING_BUYER_RETURN` / `PENDING_MERCHANT_RECEIVE`；换货还允许 `PENDING_MERCHANT_SHIP` / `PENDING_BUYER_RECEIVE`。必须核实线下退回验收，以及换货的交付已全部完成，才能执行一次性推进。金额取现有售后记录，先确认现态。来源：`AbstractAfterSaleService.completeAfterSaleOffline`。返回无业务详情；退货退款推进并触发退款，应继续跟进资金状态；换货推进至完成。不能把“客户打算到店”当线下已完成事实，也不能用于 LOGISTICS 退回；它不是任意售后的强制关闭，也不接受自填退款金额。

```json
{
  "capability": "ops.trade.aftersale.complete-offline",
  "input": {
  "afterSaleNo": "AS20260905000001"
  },
  "summary": "线下完结售后"
}
```

---

## ✅ 修改待审核售后 — ops.trade.aftersale.modify

用途：修改**待审核**售后的类型、原因、责任归属、申请说明与凭证（🔴）。全量覆盖申请快照，且必须提供 ≥10 字的修改说明（自动记录到运营流水）。

前置：仅 `PENDING_AUDIT` 状态允许修改（`AbstractAfterSaleService.modifyAfterSale` 状态校验）；原因必须存在且启用。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| afterSaleNo | 字符串 | 是，路径参数 | 售后单号 |
| afterSaleType | 字符串 | 是 | `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE` |
| reasonId | ID字符串 | 是 | 原因 ID，从 reason.list / reasons-detail 取真实启用原因 |
| responsibility | 字符串 | 是 | `USER` / `MERCHANT` / `SHARED`（可手动覆写原因默认责任） |
| applyDescription | 字符串 | 否，≤500 字 | 申请说明 |
| mediaJson | 字符串 | 否 | 凭证 JSON 序列化字符串，结构同 `aftersale-behalf.md` 的 create-on-behalf |
| modifyReason | 字符串 | 是，非空且 ≥10 字 | 修改说明，记录到运营流水供追溯 |

修改类型可能改变后续审核分支（如仅退款改退货退款），须向用户确认影响；提交后 detail 回读类型、原因、责任与说明。注意本能力不修改商品行与金额（金额修改不在开放范围）。

```json
{
  "capability": "ops.trade.aftersale.modify",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "afterSaleType": "REFUND_ONLY",
    "reasonId": "7100000000000000001",
    "responsibility": "USER",
    "modifyReason": "客户来电要求更正售后原因"
  },
  "summary": "修改待审核售后"
}
```

---

## ✅ 线下拒绝售后 — ops.trade.aftersale.reject-complete-offline

用途：线下拒绝“自行退回自提点”的售后（🔴）。与线下完结（complete-offline）是同一阶段（自行退回+待买家退回）的两个互斥处置出口：一个完成线下流转，一个拒绝，执行其一即终态。

前置（`AbstractAfterSaleService.rejectCompleteOffline` 双重校验）：`returnMethod=SELF_DELIVERY`（仅自行退回自提点）且 `afterSaleStatus=PENDING_BUYER_RETURN`（仅待买家退回；待商家收货阶段应使用 receive.reject）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| afterSaleNo | 字符串 | 是，路径参数 | 售后单号 |
| rejectReason | 字符串 | 是，非空且 ≤500 字 | 拒绝原因（用户给出的线下核实结论） |

执行后售后转为 `REJECTED`（审核结果 `RETURN_REJECTED`）；回读 detail 核对状态、`auditResult` 与 `rejectReason`。不触发退款。

```json
{
  "capability": "ops.trade.aftersale.reject-complete-offline",
  "input": {
    "afterSaleNo": "AS20260905000001",
    "rejectReason": "线下核实商品不符合退换条件"
  },
  "summary": "线下拒绝售后"
}
```
