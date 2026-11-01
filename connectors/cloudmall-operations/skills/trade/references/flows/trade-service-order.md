# 交易域 — 运营流程：服务订单履约

> 服务类商品（上门/取送）履约：协助预约、派单/改派、核销。
> 概念知识见 `references/domains/trade-concepts.md`，状态与枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`service-order-query.md` / `service-order-action.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。

---

读取 [服务订单查询契约](../apis/trade/service-order-query.md) 与 [服务订单写契约](../apis/trade/service-order-action.md)。

1. `ops.trade.service-order.search`（或 tab-count 排队）定位购买单 `purchaseOrderNo`，再 `ops.trade.service-order.detail` 读取全部履约子单与次数序号；三层标识（购买单/履约子单/次数序号）不能互换。
2. 协助预约：先 `ops.trade.service-order.time-slots` 查目标日期可约时段与容量，向用户确认时段后 `assist-appointment`（sequenceNo 从 1 开始，重试保持同序号）；改已预约的子单用 `reschedule`（`rescheduleCount` 计数递增展示，服务端当前不限制改约次数）。
3. 派单/改派：`dispatch` 首次指派真实服务人员（staffId+staffName 来自用户或门店信息，不猜测）；改派 `redispatch` 附原因；执行后 detail 回核对服务人员。
4. 核销：客户提供的 4 位核销码 + 核销节点（`PICKUP` 取件 / `COMPLETION` 完成）执行 `verify`；码错不重试猜测，执行后回读状态。
5. 导出用 `service-order.export`（URL 型）。会员手机号是敏感面，只用于对象核对，不复述明文。
