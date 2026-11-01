# 交易域 — 订单检索契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；单笔订单事实读取（详情/运单/催单/核销预览/标记）见 `order-detail.md`；发货等写操作见 `order-action.md`；运营流程：`references/flows/trade-fulfillment.md`
> 所有 ID 均为十进制字符串；查询只取事实，搜索手机号等个人信息时不得向用户复述。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 order.search · order.tab-count

---

## ✅ 订单分页搜索 — ops.trade.order.search

用途：用可解释的运营筛选定位候选订单；不用于确认单笔最终状态。常用字段为 `keyword`（订单/商品/收货人/手机号综合搜索）、`status`、`orderNo`、`receiverName`、`receiverPhone`、`productName`、`fulfillmentMode`、`deliveryMethod`、`startTime`、`endTime`、`hasUrge`；金额使用 `minAmount`/`maxAmount`。不要同时用 `status` 与 `statusList`，也不要凭空构造枚举或用户标识。多条命中先让用户选订单，不取第一条。

下表为允许构造的完整字段范围。除分页默认值外全部可选且省略不筛选；多个不同维度通常叠加。前端 `OrderPageQuery extends Record<string, unknown>` 不是任意字段许可。

| 字段 | 类型 | 含义、取值与限制 |
|---|---|---|
| pageNum / pageSize | 整数 | 默认 1 / 20；≥1；pageSize≤100。兼容名称 current/size 不使用 |
| keyword | 字符串 | 综合检索；命中仍须用详情确认 |
| orderNo / parentOrderNo / orderNos / parentOrderNos | 字符串 / 字符串 / 字符串数组 / 字符串数组 | 子单号模糊 / 父单号精确 / 子单批量精确 / 父单批量精确；parentOrderNos 最多50项 |
| noKeyword | 字符串 | 订单号、父订单号任一精确命中 |
| receiverName / receiverPhone / storeName / salesGuideName | 字符串 | 收货人、电话、门店、导购模糊匹配 |
| personKeyword | 字符串 | 人员综合检索；姓名类模糊、电话及用户标识类精确 |
| productName / skuName / goodsKeyword | 字符串 | 商品名称 / SKU名称 / 商品综合检索；不要把商品名与ID混用 |
| uid / liveSessionId / liveRoomId / spuId / groupId | 十进制字符串 | 用户 / 直播场次 / 直播间 / SPU / 分销分组精确标识 |
| categoryIds / couponTemplateIds | 十进制字符串数组 | 任一商品分类 / 任一券模板命中 |
| status / statusList | 字符串 / 字符串数组 | 使用 `trade-enums.md` 订单状态表的精确状态名；数组内为任一；不同时传两个字段 |
| subOrderStatusList | 整数数组 | 履约子单状态代码，见 `trade-enums.md` 订单状态表对应数值；结果仍是购买单 |
| startTime / endTime | 时间字符串 | yyyy-MM-dd HH:mm:ss，按北京时间解释，传入前无需换算 UTC；由 timeType 选择时间维度；起止不倒置 |
| timeType | 字符串 | created（默认，下单）/pay（付款）/finish（完成）/settlement（分销结算）；错值会静默使用下单时间，禁止大写 |
| payStartTime / payEndTime / receiveTimeBefore | 时间字符串 | 同上格式；付款起止、签收时间严格早于上界 |
| expectedShipStart / expectedShipEnd | 时间字符串 | 带时区 ISO-8601，如 2026-09-10T00:00:00+08:00 |
| orderSource / orderChannel / chanId | 字符串 | 来源 / 渠道 / 渠道追踪标识；使用已有记录精确值，不猜渠道码 |
| minAmount / maxAmount | 金额数字 | 实付金额下限/上限，单位元；上下限不倒置 |
| fulfillmentMode | 字符串 | DELIVERY / SELF_PICKUP / SERVICE |
| deliveryMethod | 字符串 | express / city_express / rider_delivery / self_service，使用实际履约值 |
| hasLiveItem / hasUrge | 布尔 | true 才启用含直播 / 有催单筛选；false 不代表反向筛选 |
| sortField | 字符串 | urge_count / created_time；默认下单时间降序，错值回落默认 |
| cpsSettleStatus / cpsUid | 整数 / 字符串 | 分销结算状态 / 分销员标识；状态仅用已查到的真实编码，不猜数字含义 |
| distributorKeyword / groupName | 字符串 | 分销员关键词 / 分销分组名 |
| hasAfterSale / cpsOnly | 布尔 | 是否有售后 / 仅分销订单；cpsOnly 仅 true 启用 |
| orderType / orderTypeList | 字符串 / 字符串数组 | 订单类型精确值（见 `trade-enums.md` OrderType）；从详情 orderType 获取，单值与多值不同时传 |
| payType | 字符串 | CASH / POINTS_AND_CASH / POINTS_ONLY |
| itemAfterSaleStatus / itemAfterSaleStatusList | 整数 / 整数数组 | 订单级售后聚合码；与商品行 afterSaleStatus 不同，取当前返回值；单值与多值不同时传 |
| markColor | 字符串 | RED/YELLOW/GREEN/BLUE/PURPLE；NONE 表示无标记 |
| invoiceStatus | 字符串 | 仅使用 APPLIED（有申请）/NOT_APPLIED（无申请）；传 ISSUED 等也只查有申请，不能查精确发票状态 |
| trackingNumber | 字符串 | 完整运单号精确匹配 |
| reviewStatus | 整数 | 评价状态精确码；只使用已核实记录的值 |
| groupStatus / groupBuyId / giftMode | 字符串 | PENDING/SUCCESS/FAILED / 团实例标识 / SINGLE或GROUP |
| completeStartTime / completeEndTime | 时间字符串 | 完成时间范围（`yyyy-MM-dd HH:mm:ss`），作用于订单完成时间维度，独立于 timeType；search 与 tab-count 均生效 |
| cursorMode / searchAfterParentOrderNo / searchAfterOrderNo / cursorToken | 布尔 / 字符串 | 内部游标字段，本 Skill 不使用；维持普通分页，禁止编造游标 |

状态筛选使用 `trade-enums.md` 订单状态表的大写枚举名（普通 status 使用名称，不传数字）。前端独有 `giftReceiverUid/giftClaimStartTime/giftClaimEndTime` 当前不在 Java DTO 中，禁止使用，避免静默无效。

返回来源：`PageResult<OrderVO>`，分页清单 `records`、`total`、`pageNum`、`pageSize`、`totalPages`、`hasMore`；记录的 `orderNo/orderStatus/orderStatusDesc/dataSource/orderType/fulfillmentMode/deliveryMethod/items` 用于定位候选，详情才用于写前校验。字段定义来源 `OrderPageQuery`、`PageQuery`、`OrderVO`；筛选实际实现 `OrderSearchServiceImpl.buildBoolQuery`；前端交叉核验 `api/trade/types.ts` 的 `OrderPageQuery` 与订单列表筛选构造。

```json
{
  "capability": "ops.trade.order.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20,
    "status": "PENDING_SHIPMENT"
  },
  "summary": "查询待发货订单"
}
```

---

## ✅ 订单阶段计数 — ops.trade.order.tab-count

用途：查看权限范围内购买单的阶段数量。空输入统计可见订单；统计包含传入的 status/statusList，不会自动去掉状态条件。返回状态计数，不等于可操作清单。

| 输入 | 类型/必填 | 生效范围 |
|---|---|---|
| 筛选字段 | 全部可选；类型同 search | keyword、uid、startTime、endTime、orderNo、receiverName、receiverPhone、productName、skuName、noKeyword、personKeyword、goodsKeyword、orderSource、orderChannel、storeName、deliveryMethod、fulfillmentMode、parentOrderNo、salesGuideName、minAmount、maxAmount、cpsSettleStatus、cpsUid、orderType、orderTypeList、payStartTime、payEndTime、payType、categoryIds、itemAfterSaleStatus、itemAfterSaleStatusList、markColor、chanId、invoiceStatus、distributorKeyword、groupName、groupId、spuId、hasAfterSale、timeType、trackingNumber、parentOrderNos、expectedShipStart、expectedShipEnd、groupStatus、giftMode、completeStartTime、completeEndTime、status、statusList |

运行时仅复制上述筛选，`hasUrge`、直播字段、`orderNos`、`couponTemplateIds`、`subOrderStatusList`、`groupBuyId`、`cpsOnly`、评价/签收上界等不能用本统计得出同口径结论（`giftMode` 与完成时间范围 `completeStartTime/completeEndTime` 均被复制生效）。分页、排序不参与计数。

返回 `OrderTabCountVO`：`totalCount`，各阶段 `pendingPaymentCount/pendingFinalPaymentCount/pendingGroupCount/pendingReceiveCount/pendingShipmentCount/pendingPickupCount/pendingDeliveryCount/partialShippedCount/shippedCount/receivedCount/completedCount/closedCount/periodFulfillingCount`；`todayActiveUrgeOrderCount` 为今日活跃催单专项统计，不能当作当前筛选总量。来源 `OrderSearchServiceImpl.tabCount` 的筛选复制与聚合构造。返回不是订单清单，不用于直接批量写入。

```json
{
  "capability": "ops.trade.order.tab-count",
  "input": {},
  "summary": "统计订单状态"
}
```
