# 交易域 — 订单详情与单笔事实读取契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；检索/计数见 `order-query.md`；发货等写操作见 `order-action.md`；运营流程：`references/flows/trade-fulfillment.md`
> 所有 ID 均为十进制字符串；单笔事实是写前校验的唯一来源，敏感详情（手机号、脱敏地址、身份标识）不得向用户复述。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 order.detail · order.logistics · order.urge-records · order.pickup-verify.preview · order.mark.get

---

## ✅ 订单详情 — ops.trade.order.detail

用途：读取单订单的状态、商品行、履约和售后关联，用作发货、改址、完结前的唯一事实来源。`orderNo` 必须来自列表或用户明确提供的订单号；敏感详情不得向用户复述。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；真实业务订单号，不能用订单主键 id 替代 |

| 返回关键字段 | 类型 | 来源及下一步用途 |
|---|---|---|
| orderNo/orderStatus/orderStatusDesc/dataSource | 字符串 | OrderDetailVO；核对目标、现态、是否迁移数据 |
| orderRole/subOrders/hierarchySummary | 字符串/结构对象 | OrderDetailVO；识别购买单和履约子单，取具体子单号后再次 detail |
| fulfillmentMode/deliveryMethod | 字符串 | 区分自提、快递、同城履约 |
| items[].id/orderLineNo/skuId/spuId | 字符串 | OrderItemVO；仅 id 用于发货 bizItemId，skuId 用于售后商品匹配 |
| items[].quantity/itemType | 整数/字符串 | 原订购数、商品行性质；不发换入商品 EXCHANGE_IN |
| items[].quantityStats | 固定对象 | OrderItemQuantityStats：shippedQuantity/receivedQuantity/afterSaleQuantity/cancelledQuantity/shippableQuantity（整数）、refundedAmount（金额）；Service.detail 合成实时数量；缺失则不能计划发货 |
| packages[].packageNo/trackingNumber/items | 字符串/数组 | OrderPackageVO；已有包裹和商品分配，修改发货必须完整保留数量 |
| packages[].items[].orderItemId/quantity | ID字符串/整数 | OrderPackageItemVO；复原完整发货方案时，orderItemId 映射为 newPackages[].items[].bizItemId，quantity 为该包裹已有数量。这里不是 items[].id，也不是 SKU ID；来源 ModifyShipModal 的已有包裹转换逻辑 |
| logistics[] | 对象数组 | OrderLogisticsVO，见 logistics 能力；按 trackingNumber 与 packages 对齐承运商 |
| receiverName/receiverPhone/receiverProvince/receiverCity/receiverDistrict/receiverDetailAddress | 字符串 | 改地址字段来源；号码若已脱敏必须重新向用户取得原值 |
| receiverLng/receiverLat | 经纬度数字 | 改地址映射到 longitude/latitude；仅地址未变化时才可复用旧坐标 |
| payment.transactionNo / finalPayment.transactionNo | 字符串 | OrderPaymentVO；分别为支付记录及存在时的尾款支付单号，用作 payment.refund.search 的 payOrderNo；不是 orderNo。多笔支付须分别核对，不能只检查首笔 |
| remark/afterSaleList/statusLogs | 文本/数组/数组 | 原备注、售后摘要、状态记录；售后状态还须查询售后详情确认 |

`promotionInfo/couponInfo/fulfillmentInfo/items[].specInfo/spuInfo/skuInfo/stockInfo` 是**JSON 文本字符串**（序列化展示快照），不能作为任意可写对象，也不能把快照内字段凭空变为输入。值形态：`fulfillmentInfo` 为自提扩展信息对象（含 `pickupTime/pickupContactName/pickupContactPhone`，仅 SELF_PICKUP 订单有值）；`items[].stockInfo` 为仓库分配数组 `[{"warehouseId":...,"warehouseName":"...","allocatedQuantity":...}]`；`items[].specInfo` 为规格映射对象（如 `{"颜色":"红"}`）；`items[].categoryIdPath` 为分类 ID JSON 数组（如 `"[1,5,23]"`）；`promotionInfo/couponInfo/spuInfo/skuInfo` 为活动/券/商品扩展映射文本，键随营销形态变化，仅作展示转述。另有三个结构化业务信息对象（非字符串）：`giftInfo`（送礼购买单：giftMode/giftCount/claimedGiftCount/remainingGiftCount/blessing/expireAt 等，非送礼订单为空）、`periodInfo`（周期购购买单：totalPeriods/deliveredPeriods/undeliveredPeriods/intervalWeeks 等周期进度，非周期购为空）、`groupBuyInfo`（拼团：groupId/groupRole/groupStatus/groupExpireTime 等，仅 GROUP_BUY 订单有值）——用于向用户解释业务进度，不作为写输入。来源 `OrderDetailVO/OrderItemVO/OrderItemQuantityStats/GiftOrderDetailInfoVO/PeriodOrderDetailInfoVO/GroupBuyInfoVO` 与 `OrderServiceImpl.detail`；前端 `ShipModal/GoodsSelectTable/ModifyShipModal` 以 items[].id 和 quantityStats 构造商品行。

```json
{
  "capability": "ops.trade.order.detail",
  "input": {
    "orderNo": "SO20260905000001"
  },
  "summary": "查询订单详情"
}
```

---

## ✅ 订单运单查询 — ops.trade.order.logistics

用途：读取该订单已登记的包裹与运单状态。`orderNo` 为唯一输入；空运单列表不等价于未发货，需结合订单详情的履约状态判断。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；真实订单号 |

返回 `OrderLogisticsVO[]`：`trackingNumber/expressCompanyCode/expressCompanyName/currentStatus`（字符串）、`signedTime`（可空时间）、`deliveryMethod/deliveryPerson/deliveryPhone`（可空字符串）。来源 `OrderServiceImpl.getLogistics` 转换运单结果。`currentStatus=SIGNED` 任一命中即阻止修改发货；当前返回不含完整轨迹节点，不能编造运输轨迹。快递缺失或查询失败时先解释数据缺口，不能据空值推定允许修改。

```json
{
  "capability": "ops.trade.order.logistics",
  "input": {
    "orderNo": "SO20260905000001"
  },
  "summary": "查询订单运单"
}
```

---

## ✅ 催单记录查询 — ops.trade.order.urge-records

用途：核实客户实际催发货时间和来源。`orderNo` 为唯一输入；仅作为排优先级的依据，不改变订单；不是催单发送能力，不能承诺已经通知仓库。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| orderNo | 字符串 | 必填；真实订单号 |

返回 `OrderUrgeRecordVO[]`：`urgedAt`（yyyy-MM-dd HH:mm:ss）、`source`（来源原值）、`uid`（十进制字符串，由 vibe-common 全局 Long→String 序列化保障）。来源 `OrderServiceImpl.getUrgeRecords`；空数组仅表示未查到流水。

```json
{
  "capability": "ops.trade.order.urge-records",
  "input": {
    "orderNo": "SO20260905000001"
  },
  "summary": "查询催单记录"
}
```

---

## ✅ 自提核销预览 — ops.trade.order.pickup-verify.preview

用途：在自提交付前，用六位核销码预览匹配的订单与商品。`pickupCode` 必须是严格六位数字；预览成功也不能视作已经交付。

| 输入 | 类型 | 必填/限制 |
|---|---|---|
| pickupCode | 字符串 | 必填；正则 \d{6}；保留前导零 |
| orderNo | 字符串 | 可选；已明确订单时传入以绑定目标 |
| verifyChannel | 字符串 | DTO 预留字段，Agent 不传；运营核销渠道由执行方固定 |

返回 `PickupVerifyPreviewVO`：`orderNo/orderStatusDesc/createTime/paidAmount`（字符串）、`totalQuantity`（整数）、`items[]` 的 `skuName/skuImage/specDesc/price`（字符串）、`quantity`（整数），以及 `pickupContactName/pickupContactPhone/pickupTime/pickupSiteName/pickupSiteAddress`。来源 `PickupVerifyServiceImpl.preview` 构造，联系电话为脱敏展示。核对目标、提货点、商品件数并取得实际交付确认后才可 confirm；无匹配或已核销不得枚举试码。

```json
{
  "capability": "ops.trade.order.pickup-verify.preview",
  "input": {
    "pickupCode": "123456"
  },
  "summary": "预览自提核销"
}
```

---

## ✅ 订单标记查询 — ops.trade.order.mark.get

用途：查询单笔订单的运营标记（颜色便签）。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| orderNo | 字符串 | 是，路径参数 | 订单检索/详情或用户明确提供 |

结果来源 `OrderMarkVO`：`color`（`RED`/`YELLOW`/`GREEN`/`BLUE`/`PURPLE`，null 表示无标记，不是错误）、`remark`（标记备注）、`markedBy`（标记人）、`markedTime`（标记时间字符串）。

```json
{
  "capability": "ops.trade.order.mark.get",
  "input": { "orderNo": "SO20260905000001" },
  "summary": "查询订单标记"
}
```
