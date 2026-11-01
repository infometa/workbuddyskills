# 交易域 — 支付退款写操作契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；运营流程：`references/flows/trade-finance.md`
> **先读现值**：全部写入先用 `payment-query.md` 的 pay-order.detail / refund.search / channel-config.list 精确读取单号、金额、现态；微信发货手动补报见 `wx-shipping.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。超时或不确定结果先回读，禁止盲目重试。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 payment.pay-order.sync 🔴 · payment.pay-order.close 🔴 · payment.refund.retry 🔴 · payment.channel-config.update-status 🔴 · payment.channel-config.wx-shipping-switch 🔴

---

## ✅ 同步支付状态 — ops.trade.payment.pay-order.sync

用途：主动拉取并更新一张支付单的最新处理结果（🔴）。仅输入 `payOrderNo`；超时后先重新读取，绝不重复提交；同步可能推进支付成功或关闭订单，先复述当前状态、金额、关联订单并确认。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| payOrderNo | string | 必填；保持原业务编号 | 详情中的 payOrderNo |

先读详情，明确确认单号、金额和订单。返回 `PayOrderVO`，字段含义同支付检索；运行时同步可能调用支付成功处理并推进关联订单。若无变化只能报告当前状态，不能声称补单成功。超时先用支付详情回读；不得立即再次同步。来源：`PayOrderController.sync`、`PayOrderServiceImpl.queryPayOrder`。

```json
{
  "capability": "ops.trade.payment.pay-order.sync",
  "input": {
    "payOrderNo": "PO20260905000001"
  },
  "summary": "同步支付状态"
}
```

---

## ✅ 关闭支付单 — ops.trade.payment.pay-order.close

用途：关闭仍未完成的支付单（🔴）。仅输入 `payOrderNo`；关闭的是支付机会，不能逆转已成功支付。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| payOrderNo | string | 必填；保持原业务编号 | 详情中的 payOrderNo |

仅 `status=0` 可关闭，先确认单号、金额、业务订单。返回无业务数据；**成功应答不证明已关闭**：运行时关闭前发现渠道已支付，会改走支付成功流程，且上层不返回该分支标识。必须回读详情：`status=2` 才是已关闭，`status=1` 应报告已支付并停止关闭流程，其他状态报告未确认；不能预先承诺“将关闭订单”。来源：`PayOrderServiceImpl.closePayOrder` 的 PENDING 检查和渠道成功分支。

```json
{
  "capability": "ops.trade.payment.pay-order.close",
  "input": {
    "payOrderNo": "PO20260905000001"
  },
  "summary": "关闭支付单"
}
```

---

## ✅ 退款重试 — ops.trade.payment.refund.retry

用途：重试一张失败或满足重试条件的退款（🔴 资金高危）。仅输入 `refundOrderNo`；必须先从退款检索精确定位，超时或未知结果不得重复调用。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| refundOrderNo | string | 必填；保持原业务编号 | 退款检索记录的 refundOrderNo |

先核对退款单号、支付单号、退款金额与现态并确认。运行时允许 `status=2`；或 `status=0` 且创建已超过 5 分钟、`channelRefundNo` 为空。后者缺时间或渠道受理证据时停止，不推测可重试。`status=1` 禁止重试。返回无业务数据，必须按退款编号重新检索并逐字匹配；仅 `status=1` 表示退款成功。超时后先查状态，禁止盲目重试。来源：`RefundOrderServiceImpl.retryRefund`、`RefundStatusEnum`。

```json
{
  "capability": "ops.trade.payment.refund.retry",
  "input": {
    "refundOrderNo": "RO20260905000001"
  },
  "summary": "重试退款"
}
```

---

## ✅ 支付渠道启停 — ops.trade.payment.channel-config.update-status

用途：启用或禁用一个支付渠道（🔴）。禁用后该渠道全部新支付不可用，进行中的支付不受影响；影响全租户该渠道支付可用性。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | channel-config.list 返回的渠道 ID |
| status | 整数 | 是，非 null | `1` 启用、`0` 禁用 |

来源：`ToggleStatusRequest`。执行前复述渠道名、当前状态与目标状态的影响；执行后 channel-config.list 回读 `status`。**这不是渠道密钥配置**——只切换可用性。

```json
{
  "capability": "ops.trade.payment.channel-config.update-status",
  "input": { "id": "8400000000000000001", "status": 1 },
  "summary": "启用支付渠道"
}
```

---

## ✅ 微信发货开关切换 — ops.trade.payment.channel-config.wx-shipping-switch

用途：切换支付渠道的微信发货信息回传开关（🔴）。开=发货信息自动上报微信（小程序发货管理合规要求）；关=不自动上报。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| id | ID字符串 | 是，路径参数 | channel-config.list 返回的渠道 ID |
| wxShippingEnabled | 整数 | 是，仅 `0` 或 `1` | `1` 开、`0` 关；其他值服务端报错 |

来源：`ChannelConfigController.toggleWxShippingSwitch`（body 为 `{"wxShippingEnabled": 0|1}`）。执行前说明开关影响（微信小程序要求上报发货信息，关闭可能影响小程序交易合规）；执行后回读 list 的 `wxShippingEnabled`。与手动补报（`wx-shipping.md`）配合使用。

```json
{
  "capability": "ops.trade.payment.channel-config.wx-shipping-switch",
  "input": { "id": "8400000000000000001", "wxShippingEnabled": 1 },
  "summary": "开启微信发货回传"
}
```
