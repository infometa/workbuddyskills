# 交易域 — 支付退款查询契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；支付同步/关闭/退款重试/渠道启停写操作见 `payment-action.md`，微信发货补报见 `wx-shipping.md`；运营流程：`references/flows/trade-finance.md`
> 所有 ID 均为十进制字符串；查询只取事实，敏感渠道字段（渠道交易单号、openid 等）不得向用户复述。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 payment.pay-order.search · payment.pay-order.detail · payment.refund.search · payment.channel-config.list · payment.pay-order.child-orders

---

## ✅ 支付单搜索 — ops.trade.payment.pay-order.search

用途：按支付单或订单定位资金记录，供同步、关闭前核验。可选筛选为 `payOrderNo`（模糊）、`bizOrderNo`（精确）、`channelCode`、`status`、`payType`（`CASH`、`POINTS_AND_CASH`、`POINTS_ONLY`）、`payTimeStart`、`payTimeEnd`。时间必须使用空格分隔的 `yyyy-MM-dd HH:mm:ss`，不能使用带 `T` 的 ISO 值。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| pageNum | integer | 可选，默认 1，最小 1 | 页码 |
| pageSize | integer | 可选，默认 20，1～100 | 每页条数 |
| payOrderNo | string | 可选，最多 32 字符 | 支付单号模糊匹配 |
| bizOrderNo | string | 可选，最多 32 字符 | 业务订单号精确匹配；取值是支付单关联的**父订单号**（订单检索/详情返回的 `parentOrderNo`），不是子订单号 `orderNo`。用户给子订单号时，先用 `ops.trade.order.search` 或 `ops.trade.order.detail` 取 `parentOrderNo`，或直接取详情 `payment.transactionNo` 作为 `payOrderNo` 查询 |
| channelCode | string | 可选，最多 32 字符 | 沿用当前记录的渠道编码，不猜值 |
| status | integer | 可选；0 待支付、1 成功、2 关闭、3 退款中、4 已退款（见 `trade-enums.md` 支付状态） | 支付状态；不是订单状态 |
| payType | string | 可选，最多 20 字符；CASH / POINTS_AND_CASH / POINTS_ONLY | 纯现金 / 积分加现金 / 纯积分 |
| payTimeStart | string | 可选，yyyy-MM-dd HH:mm:ss | 支付时间下界 |
| payTimeEnd | string | 可选，同上；不早于起始时间 | 支付时间上界 |

分页记录来自 `PayOrderVO`：`payOrderNo` 是详情/同步/关闭的输入来源；`bizOrderNo` 关联业务订单；`status/statusDesc` 表达支付阶段；`totalAmount/refundedAmount/cashAmount/pointsDeductAmount` 为金额，`pointsAmount/refundedPoints` 为积分数量；`payTime/expireTime/createdTime` 表达支付、到期、创建时间。`orderStatus` 属订单状态，不可与 `status` 混用。来源：`PayOrderPageQuery`、`PayOrderServiceImpl.page`、运营支付列表类型。不得复述 `channelOrderNo/transactionId` 等渠道标识。

```json
{
  "capability": "ops.trade.payment.pay-order.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20
  },
  "summary": "查询支付单"
}
```

---

## ✅ 支付单详情 — ops.trade.payment.pay-order.detail

用途：读取一张支付单的当前状态和关联业务订单。`payOrderNo` 是唯一输入，必须从列表或用户明确指令获得；详情用于确认是否仍可同步或关闭；敏感渠道字段不对用户复述。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| payOrderNo | string | 必填；保持原业务编号 | 支付检索记录的 payOrderNo，不是 id 或 bizOrderNo |

`PayOrderDetailVO` 提供 `payOrderNo/bizOrderNo/status/statusDesc/totalAmount/refundedAmount/payType/cashAmount/pointsAmount/pointsDeductAmount/pointsStatus/payTime/expireTime/closeTime/retryCount/createdTime/updatedTime`；详情另含 `openid`（微信用户标识）与 `channelOrderNo`（渠道交易单号）——均为敏感渠道字段，**不向用户复述**。`historyPayOrders[]` 是同业务历史支付摘要，`refundOrders[]` 是退款记录，不能把历史成功支付当成本次支付成功。`operationLogs[]` 仅作为操作证据，禁止将日志或身份字段整段输出。来源：`PayOrderServiceImpl.detail` 和 `PayOrderDetailVO`。

```json
{
  "capability": "ops.trade.payment.pay-order.detail",
  "input": {
    "payOrderNo": "PO20260905000001"
  },
  "summary": "查询支付单详情"
}
```

---

## ✅ 退款单搜索 — ops.trade.payment.refund.search

用途：定位退款申请及其处理状态；不能以“已受理”推断“已到账”。可选筛选是 `refundOrderNo`、`payOrderNo`、`status`。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| pageNum | integer | 可选，默认 1，最小 1 | 页码 |
| pageSize | integer | 可选，默认 20，1～100 | 每页条数 |
| refundOrderNo | string | 可选，最多 32 字符 | 退款单号筛选；写前逐字比对返回编号 |
| payOrderNo | string | 可选，最多 32 字符 | 关联支付单号 |
| status | integer | 可选；0 退款中、1 成功、2 失败（见 `trade-enums.md` 退款状态） | 退款阶段；不是售后状态 |

记录来自 `RefundOrderVO`：`refundOrderNo` 供重试；`payOrderNo/bizRefundNo` 关联支付和业务退款；`refundAmount/totalAmount` 为金额，`refundPoints` 为积分数量；`status/statusDesc/successTime/retryCount/createdTime/reason` 供核验。`channelRefundNo` 只检查是否存在，禁止对用户复述其值。来源：`RefundOrderPageQuery`、`RefundOrderServiceImpl.page/retryRefund`；成功必须看 `status=1`，调用被受理不等于退款成功。

从售后追踪退款：取售后详情的 orderNo 读取订单详情，以 payment.transactionNo 及存在时的 finalPayment.transactionNo 分别作为 payOrderNo 查询；跨页逐字匹配 records[].bizRefundNo 与原 afterSaleNo，检查全部分笔，不仅首条。afterSaleNo/orderNo 不是本能力筛选字段。零金额且无积分场景可能无退款单；支付记录不完整时说明待核验，不推断全部到账。来源：AbstractAfterSaleService.triggerRefund 分阶段退款记录创建。

```json
{
  "capability": "ops.trade.payment.refund.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20
  },
  "summary": "查询退款单"
}
```

---

## ✅ 支付渠道配置列表 — ops.trade.payment.channel-config.list

用途：读取支付渠道配置列表。**出参已脱敏**：`appId`、`mchId`、`certificateSerialNo` 均为脱敏展示，不含任何密钥/证书原文；不能作为写操作入参回传。

入参：无，传 `{}`。结果来源 `ChannelConfigVO` 数组：

| 字段 | 类型 | 含义 |
|---|---|---|
| id | ID字符串 | 渠道配置 ID（启停/开关操作的定位） |
| channelCode / channelName | 字符串 | 渠道编码与名称 |
| status | 整数 | 渠道状态：`1` 启用、`0` 禁用 |
| apiVersion | 字符串 | API 版本：`V2` / `V3` |
| appId / mchId / certificateSerialNo | 字符串 | **脱敏展示**，不能作为写操作入参回传 |
| wxShippingEnabled | 整数 | 微信发货回传开关：`1` 开、`0` 关 |
| createdTime / updatedTime | 时间字符串 | `yyyy-MM-dd HH:mm:ss` |

注意：渠道的**创建与更新（含密钥证书配置）不在开放范围**（敏感凭据面，走管理后台）；本能力只读，状态/开关切换见 `payment-action.md`。

```json
{
  "capability": "ops.trade.payment.channel-config.list",
  "input": {},
  "summary": "查询支付渠道配置"
}
```

---

## ✅ 支付单子单查询 — ops.trade.payment.pay-order.child-orders

用途：查询一笔支付单关联的全部子单号（合并支付/父子单场景：一个支付单对应多个子订单）。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| payOrderNo | 字符串 | 是，路径参数 | 支付单检索/详情 |

结果来源 `List<String>`（子订单号列表）。用于从支付单反查业务子单：拿到子单号后用 `ops.trade.order.detail` 逐单读取；不能把支付单号当订单号使用。

```json
{
  "capability": "ops.trade.payment.pay-order.child-orders",
  "input": { "payOrderNo": "PO20260905000001" },
  "summary": "查询支付单子单号"
}
```
