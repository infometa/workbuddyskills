# 交易域 — 运营流程：售后审核、退换货与代客创建

> 售后审核、退货退款、换货、代客创建与线下处置。
> 概念知识见 `references/domains/trade-concepts.md`，状态与枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`aftersale-query.md` / `aftersale-action.md`（审核与处置）、`aftersale-behalf.md`（代客创建）、`return-address-query.md`（退回地址选择）。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。

---

## 审核、退货退款与换货

读取 [售后查询契约](../apis/trade/aftersale-query.md) 与 [售后写操作契约](../apis/trade/aftersale-action.md)。

1. `ops.trade.aftersale.search → ops.trade.aftersale.detail`，取得 `afterSaleNo`、类型、状态、迁移标识、金额、商品及退回方式。迁移只读记录不写。
2. 待审核：拒绝使用 `ops.trade.aftersale.audit` 的 `approved=false` 与用户给定理由；通过则确认金额与实物分支。非仅退款且不是自行送回时，按契约从 `ops.trade.return-address.list-all` 选择真实地址 ID。不要提交已声明不生效的运费调整或审核备注字段。
3. 修改待审核申请：用户要求更正类型/原因/责任/说明/凭证时用 `ops.trade.aftersale.modify`（全量覆盖快照，`modifyReason` ≥10 字）；修改类型会改变后续审核分支，先复述影响。金额与商品行修改不在开放范围。
4. 需要寄回时，在允许阶段用 `ops.trade.aftersale.return-logistics.input` 记录真实退回物流；允许状态包括待买家退回和待商家收货，不能把录单视为已收到实物。
5. 待商家收货：确有收货事实才 `ops.trade.aftersale.receive.confirm`；用户明确拒收结论才 `ops.trade.aftersale.receive.reject`。待审核拒绝与收货拒收不可互换。自行退回自提点且待买家退回阶段的线下拒绝走 `ops.trade.aftersale.reject-complete-offline`——与线下完结是同一阶段的两个互斥处置出口，执行其一即终态。
6. 换货待发出：`ops.trade.aftersale.merchant-ship` 按物流或自行配送分支构造；回读到待买家收货只能说已发出，不说换货闭环完成。审核换货前可用 `ops.trade.aftersale.exchangeable-skus` 核对订单商品行的可换规格，不凭名称猜规格。
7. 每次写入后 detail 回读；涉及退款时按下方字段链核对全部关联退款单。审核通过、售后完成与资金到账分开报告。

退款关联链：`aftersale.detail.orderNo → ops.trade.order.detail → payment.transactionNo / finalPayment.transactionNo → ops.trade.payment.refund.search.input.payOrderNo`。分别查询存在的支付阶段，跨页只保留 `records[].bizRefundNo === 原 afterSaleNo` 的记录；逐笔检查 `status/refundAmount/refundPoints`，不能取首笔代表全部。不要向退款检索传入不支持的 `afterSaleNo/orderNo`。支付记录缺失或不能核实关联时报告待核验。零现金金额且无积分的售后可能不生成退款单，零现金但有积分可能产生纯积分退款记录；空列表不直接等于失败，也不能描述为现金到账。来源：`AbstractAfterSaleService.triggerRefund` 的分阶段分配和零金额分支。

## 代客创建与线下完结

读取 [代客创建契约](../apis/trade/aftersale-behalf.md)。

1. 创建前读取订单详情、已有售后和 `ops.trade.aftersale.reasons-detail`；由真实订单行取得 `orderItemId/skuId`，按原因分组选择 `reasonId`，不可使用售后行 ID。
2. 确认类型、商品数、收到/发出事实、退款金额及运费/包装费；按类型检查总额和行金额关系。金额上限用 `ops.trade.aftersale.refunded-summary` 核对剩余可退余额，不凭印象报价；换货目标规格用 `ops.trade.aftersale.exchangeable-skus` 核对可换性与库存资格，缺少可靠证据时停止，不编造可用值。
3. 自提退货退款/换货必须明确用户选择的 `returnMethod`；仅退款不强加退货方式。凭证按契约构造媒体序列化文本，不能把上传组件整对象直接塞入。
4. `ops.trade.aftersale.create-on-behalf` 返回新售后号，用该号 detail 确认，不自动连做审核。创建结果不确定时先查订单已有售后，避免重复申请。
5. `ops.trade.aftersale.complete-offline` 仅适用契约明确的自行退回分支；确认实际线下处置事实与记录金额。它不是任意售后的强制关闭，也不接受自填退款金额。对应的线下拒绝用 `ops.trade.aftersale.reject-complete-offline`（仅自行退回且待买家退回）——两者是同一阶段的互斥处置选择，执行其一即终态。
