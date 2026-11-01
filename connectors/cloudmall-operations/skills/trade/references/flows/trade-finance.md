# 交易域 — 运营流程：支付、退款、发票与对账

> 支付单处置、退款跟进、渠道与微信发货、发票全生命周期、对账差异与节点任务。
> 概念知识见 `references/domains/trade-concepts.md`，状态与枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`payment-query.md` / `payment-action.md`、`wx-shipping.md`、`invoice-query.md` / `invoice-action.md`、`invoice-config-query.md` / `invoice-config-action.md`、`reconcile-query.md` / `reconcile-action.md`、`order-cps.md`（CPS 视角）。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。

---

## 支付与退款

- 支付：`ops.trade.payment.pay-order.search → ops.trade.payment.pay-order.detail`，用支付单号同步或关闭。关闭后回读，渠道已支付时可能转成功；不能预先承诺“将关闭订单”。合并支付反查子单用 `ops.trade.payment.pay-order.child-orders`。
- 渠道与微信发货：渠道启停/微信发货回传开关先 `ops.trade.payment.channel-config.list` 读现值，复述渠道名与影响后切换并回读；渠道密钥配置不开放，需求命中时说明走管理后台。自动回传失败的补报用 `ops.trade.payment.wx-shipping.report`（支付单雪花 ID，见 [微信发货契约](../apis/trade/wx-shipping.md)）。CPS 推广视角查订单用 `ops.trade.order-cps.search`（只读投影，佣金与导购归属见 [CPS 契约](../apis/trade/order-cps.md)）。
- 退款：`ops.trade.payment.refund.search` 取得退款单号与当前状态；只有契约允许才 `ops.trade.payment.refund.retry`。回读处理状态，处理中不是到账。详见 [支付退款查询契约](../apis/trade/payment-query.md) 与 [支付退款写契约](../apis/trade/payment-action.md)。

## 发票与发票配置

- 发票：`ops.trade.invoice.search` 唯一定位 ID；待开具、失败重试、蓝票红冲分别选 trigger/retry/red-flush，不能互相替代。重试返回固定结果对象，需检查 `ok/status` 并再查列表。红冲用返回的新红票 ID 与 `redOriginInvoiceId` 关联核验，不以原票一条记录代替两票结果。红字确认单待确认（红票 ISSUING + PENDING）用 `red-confirm-operate`；取消开票用 `cancel`；代客录入抬头用 `apply-on-behalf`（已签收立即开票、未签收打标）。认证阻塞：`auth-status` 见 blocked=true → 用户完成电子税务局认证 → `auth-clear` 清标记。排查工具：`query-platform`（平台侧最新状态）、`retry-file-transfer`（文件转存幂等补跑）。见 [发票查询契约](../apis/trade/invoice-query.md) 与 [发票写契约](../apis/trade/invoice-action.md)。
- 发票配置：销方/税收分类/商品税收映射按 [发票配置契约](../apis/trade/invoice-config-query.md) 先读现值再改（税率是小数）；平台启停/默认切换影响全链路开票目标，平台凭据配置走管理后台。

## 对账

`ops.trade.reconcile.diff.search → detail → handle-logs` 核对差异依据。待处理可标错或升级；确认只适用已升级记录。确认不会自动退款/补收。回读详情状态及新增日志，备注只记录说明。节点配置/告警通知/看板/手动触发见 [对账查询契约](../apis/trade/reconcile-query.md) 与 [对账写契约](../apis/trade/reconcile-action.md)：手动触发异步返回任务 ID，用 task.search 跟进，不重复触发。
