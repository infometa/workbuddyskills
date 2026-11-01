# 交易域 — 运营流程：发货、履约与订单管理

> 新发货、修改已有包裹、批量发货、Excel 导入、改地址、备货、自提核销、人工完成；订单导出、标记、周期购与 CPS 辅助管理。
> 概念知识见 `references/domains/trade-concepts.md`，状态与枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`order-query.md`（检索）/ `order-detail.md`（单笔事实）/ `order-action.md`（单包裹发货与订单操作）、`order-ship-batch-action.md`（批量与导入/发货计划）、`order-export-query.md` / `order-export-action.md`（导出）、`order-cps.md`（CPS）。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律；示例中的号码只是格式示意。

---

## 新发货与修改已有包裹

读取 [订单检索契约](../apis/trade/order-query.md)、[订单详情契约](../apis/trade/order-detail.md) 与 [订单写操作契约](../apis/trade/order-action.md)。

1. `ops.trade.order.search` 定位 `orderNo`，再 `ops.trade.order.detail` 核对履约子单、状态和商品行；购买单先选择具体子单，不能直接套用普通发货。
2. 新发货：从详情 `items[].id` 取得 `bizItemId`，以 `quantityStats.shippableQuantity` 为本次上限；`ops.trade.order.ship` 的包裹仅表示本次新增发货。承运商和运单来自实际物流事实，不能虚构。
3. 修改已有发货：`ops.trade.order.modify-ship` 接收完整目标方案。用 `packages[].items[].orderItemId → newPackages[].items[].bizItemId`、原包裹数量和物流记录重建全部包裹，再修改明确要求的部分；不能只提交改动包裹。此能力没有门店自配分支，也不支持用 `orderLineNo` 替代。
4. 批量整单：仅当每单整单一套物流且各单均核实可发时使用 `ops.trade.order.batch-full-ship`；需要逐包裹指定商品内容用 `ops.trade.order.batch-ship`（≤50 单）；多订单合并包裹用 `ops.trade.order.merge-ship`（2~3 单，服务端要求同收货人、同一下单账号、同一发货门店、订单创建时间在 3 天窗口内且均处待发货/部分发货）。见 [批量发货与物流导入契约](../apis/trade/order-ship-batch-action.md)。
5. Excel 导入发货：用户已提供真实文件并确认内容时转交 `ops.trade.order.import-ship`（同步）/ `import-multi-package-ship`（异步，轮询任务查询）；批量改物流单号用 `import-modify-logistics`。逐单结果分别报告，失败明细链接转告用户，不自动重试。模板从管理后台获取，Agent 不代造文件内容。
6. 确认订单、商品/数量、承运商及单号后执行；读取详情与 `ops.trade.order.logistics` 核对数量和运单。批量返回逐单结果，分别报告成功、失败与待核验，不把总体受理说成全部成功。

催单只读 `ops.trade.order.urge-records`，记录客户催促不代表已实际发货。

## 改地址、备货、自提与完成

1. 改地址先 detail，取得完整目标省市区、详细地址和未脱敏联系人信息；订单地址省略省市区可能清空，不套用退货地址局部更新规则。地址变化不能沿用旧坐标。
2. 复述新地址与适用订单，按 `ops.trade.order.receiver-address.update` 契约确认后提交并回读。无法验证配送范围时不能宣称校验通过。
3. `ops.trade.order.confirm-pickup` 是备货完成进入待自提，不是客户已经取货。
4. 客户实际取货时先 `ops.trade.order.pickup-verify.preview` 核对核销码关联订单和商品，确认实际交付后调用 `ops.trade.order.pickup-verify.confirm`，再 detail 核对状态。不把服务预约到店当实物核销。前置：订单为自提模式且已支付（PayStatus=1 支付成功）。
5. `ops.trade.order.complete` 是人工完结，不代替发货或收货；先核对已签收及无进行中售后等契约条件（人工完成触发积分发放），确认后执行并回读。

## 订单导出

`ops.trade.order.export` 按筛选提交，按返回 `mode` 分支——`sync` 直接把下载链接（约 60 分钟时效）告知用户；`async` 拿 `taskId` 轮询 `ops.trade.order.export.task.detail` 至 SUCCESS/FAILED，`truncated=true` 必须明示文件不完整。排队中与执行中任务均可取消（`export.task.cancel`），导出文件含收货人敏感信息，链接只给提交人本人。见 [订单导出契约](../apis/trade/order-export-query.md)。

## 订单标记

`mark.set` / `mark.clear` 批量操作，`mark.get` 回读核对；标记是运营便签，不改变订单状态机。标记后可按 `markColor` 在 `ops.trade.order.search` 筛选同色订单。

## 周期购

退订（`period-buy.unsubscribe`）先复述受影响周期与退款金额；退订**直接生成退款单并关闭订单、不创建售后单**——用 `ops.trade.payment.refund.search` 按支付单跟进退款状态，不取 `afterSaleNo`（恒为 null）；改单期发货日期用 `delivery-plan.update`（运营端仅日期 + 操作原因）。定位链路：购买单详情（orderRole=PURCHASE 的购买单号）的 `subOrders` 列表取具体某一期子单号，再对该子单操作。

## CPS 查询

`ops.trade.order-cps.search` 筛选与订单检索一致，典型筛选 `cpsUid`（分销员）、`cpsSettleStatus`（结算状态，见 `trade-enums.md` CpsSettleStatus）、`distributorKeyword`（分销员名称/UID 模糊）；佣金结算以 `totalCommission` 为准。
