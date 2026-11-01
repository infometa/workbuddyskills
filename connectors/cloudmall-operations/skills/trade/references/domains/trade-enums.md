# 交易域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写与取值以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `trade-concepts.md`；物流子域状态与字典见 `logistics.md`。
> 能力契约见 `references/apis/trade/`，操作流程见 `references/flows/`。

---

## 订单状态（OrderStatus，大写枚举名 + 代码）

订单筛选使用大写枚举名（普通 status 用名称，不传数字）；返回状态代码按对应契约解释。来源：`OrderStatus` 及订单检索实现的枚举解析，不能使用自创别名。

| 枚举名 | 代码 | 含义 |
|---|---|---|
| `PENDING_PAYMENT` | 0 | 待付款 |
| `PENDING_SHIPMENT` | 1 | 待发货 |
| `PENDING_PICKUP` | 2 | 待自提 |
| `PENDING_DELIVERY` | 3 | 待配送 |
| `SHIPPED` | 4 | 已发货 |
| `RECEIVED` | 5 | 已签收 |
| `COMPLETED` | 6 | 已完成 |
| `CLOSED` | 9 | 已关闭 |
| `PARTIAL_SHIPPED` | 10 | 部分发货 |
| `PENDING_FINAL_PAYMENT` | 11 | 待付尾款（仅定金预售） |
| `PENDING_GROUP` | 12 | 待成团 |
| `PENDING_RECEIVE` | 13 | 待好友领取 |
| `GIFT_ALL_CLAIMED` | 14 | 好友已全部领取（送礼单，可人工完成） |
| `GIFT_CLAIM_ENDED` | 15 | 领取已结束（送礼单，可人工完成或关闭） |
| `SERVICE_PENDING_APPOINTMENT` | 20 | 待预约 |
| `SERVICE_PENDING_DISPATCH` | 21 | 待派单 |
| `SERVICE_PENDING_SERVICE` | 22 | 待服务 |
| `SERVICE_IN_PROGRESS` | 23 | 服务中 |
| `SERVICE_APPOINTED` | 24 | 已预约（状态机中为不可流转态） |
| `PERIOD_FULFILLING` | 100 | 周期购购买单聚合态（状态机中为不可流转态），不作为履约子单处置 |

### 订单状态流转（按订单类型）

来源：`OrderStatus.canTransit` 与 `OrderEvent` 事件迁移定义。

| 场景 | 状态流 |
|---|---|
| 普通配送 | `PENDING_PAYMENT` →（支付成功）`PENDING_SHIPMENT` → `SHIPPED` / `PARTIAL_SHIPPED` →（签收）`RECEIVED` →（人工完成）`COMPLETED` |
| 门店自提 | `PENDING_SHIPMENT` →（确认备货）`PENDING_PICKUP` →（核销签收）`RECEIVED` → `COMPLETED` |
| 同城配送 | `PENDING_SHIPMENT` →（开始配送）`PENDING_DELIVERY` →（确认配送完成）`RECEIVED` |
| 定金预售 | `PENDING_PAYMENT` →（定金支付）`PENDING_FINAL_PAYMENT` →（尾款支付）`PENDING_SHIPMENT`；尾款支付超时 / 取消尾款 → `CLOSED`（取消尾款退定金） |
| 拼团 | `PENDING_PAYMENT` →（支付成功）`PENDING_GROUP` →（成团）`PENDING_SHIPMENT`；拼团失败 → `CLOSED` |
| 部分发货 | `PENDING_SHIPMENT` → `PARTIAL_SHIPPED`；追加发货保持 `PARTIAL_SHIPPED`，全部发完 → `SHIPPED` |

关闭路径（`CLOSED` 的进入事件，存储 OrderEvent 枚举名作为关闭原因）：待付款超时（`PAYMENT_TIMEOUT`）/ 买家取消（`CANCEL`）/ 发货前取消（`CANCEL_BEFORE_SHIP`）/ 自提取消与自提超时（`CANCEL_PICKUP` / `CANCEL_PICKUP_TIMEOUT`）/ 配送取消（`CANCEL_DELIVERY`）/ 尾款超时与取消（`FINAL_PAYMENT_TIMEOUT` / `CANCEL_FINAL_PAYMENT`）/ 售后全额退（`AFTER_SALE_CLOSE`）。定金售后退款后订单同样关闭。

## 订单维度枚举

| 枚举 | 取值 | 说明 |
|---|---|---|
| OrderType | `NORMAL` / `PRE_SALE_FULL` 全款预售 / `PRE_SALE_DEPOSIT` 尾款预售 / `SECKILL` 秒杀 / `GROUP_BUY` 拼团 / `POINTS_MALL` 积分商城 / `PERIOD_BUY` 周期购 / `GIFT` 送礼 / `SERVICE` 服务 | 订单类型（9 值） |
| OrderSource | `MINI_PROGRAM` / `H5` / `APP` / `PC` / `LIVE`（直播间下单） | 订单来源（5 值） |
| UrgeSource | `MINIAPP` / `H5` / `POS` | 催单来源——**值与 OrderSource 不同**（无 LIVE、小程序是 MINIAPP） |
| PayType | `CASH` 纯现金 / `POINTS_AND_CASH` 积分+现金 / `POINTS_ONLY` 纯积分 | 支付类型；积分商城订单为后两者 |
| fulfillmentMode | `DELIVERY` 配送 / `SELF_PICKUP` 自提 / `SERVICE` 服务 | 履约模式，决定发货流程分支（与订单检索 fulfillmentMode 筛选值域一致） |
| deliveryMethod code | `express` 快递 / `city_express` 同城 / `rider_delivery` 骑手 / `self_service` 门店自配 | 配送方式；self_service 需配送人姓名电话、不需承运商与运单号 |
| markColor | `RED` / `YELLOW` / `GREEN` / `BLUE` / `PURPLE` | 运营标记颜色（无标记为 null） |
| PickupVerifyChannel | `C_SCAN` C端扫码 / `B_MANUAL` B端手输码 / `B_SCAN` B端扫码 / `GUIDE_SCAN` 导购扫码 / `SYSTEM` 系统自动 | 核销渠道（运营端执行固定渠道，不传） |
| itemAfterSaleStatus | `0` 未申请 / `1` 部分售后 / `2` 全部售后 | 订单商品行售后聚合状态 |
| 订单开票筛选 | `APPLIED` 已申请 / `NOT_APPLIED` 未申请 | 订单列表维度的开票筛选，与发票实体状态是不同概念 |
| 微信发货上报状态 | `0` 待发货 / `1` 已上报 / `2` 无需上报（纯积分）/ `3` 上报失败（待人工）/ `4` 待上报 | 支付单 `shippingReported` 字段（业务常量值） |
| 订单导出维度 | `ORDER` 订单维度 / `ORDER_ITEM` 商品详情维度 | 导出 exportType |
| CpsSettleStatus | `1` 未结算 / `2` 结算中 / `3` 结算失败 / `4` 结算成功 | CPS 佣金结算状态 |

## 售后状态（AfterSaleStatus，大写枚举名 + 代码）

售后类型：`REFUND_ONLY` 仅退款、`RETURN_REFUND` 退货退款、`EXCHANGE` 换货。售后筛选使用大写枚举名，不混用其他端的 `pending`、`approved` 聚合标签。

| 售后枚举名 | 代码 | 意义 |
|---|---|---|
| `PENDING_AUDIT` | 0 | 待审核 |
| `PENDING_BUYER_RETURN` | 1 | 待买家退回 |
| `PENDING_MERCHANT_RECEIVE` | 2 | 待商家收货 |
| `PENDING_MERCHANT_SHIP` | 3 | 待商家发货（换货） |
| `PENDING_BUYER_RECEIVE` | 4 | 待买家接收换货 |
| `REJECTED` | 5 | 已拒绝 |
| `REFUND_FAILED` | 6 | 退款失败，仍需处理 |
| `REFUNDING` | 7 | 退款中，不代表到账 |
| `COMPLETED` | 8 | 售后完成 |
| `CLOSED` | 9 | 已关闭 |

售后退回方式 returnMethod：`SELF_DELIVERY` 自行退回自提点 / `LOGISTICS` 物流寄回（仅自提订单的退货退款/换货适用）。售后原因责任归属 responsibility：`USER` / `MERCHANT` / `SHARED`。售后发起方 afterSaleInitiator：`CUSTOMER` / `MERCHANT` / `SYSTEM`。

## 退款状态的两套枚举（易混）

| 枚举 | 取值 | 归属 |
|---|---|---|
| 支付域 RefundStatusEnum | `0` 处理中 / `1` 成功 / `2` 失败 | 退款单实体状态（payment 包），跟进资金到账用它 |
| 售后域 RefundStatus | `REFUNDING`(0) / `REFUND_SUCCESS`(1) / `REFUND_FAILED`(2) | 售后单上的退款展示状态（aftersale 包）——**同名不同值域**，与支付域退款单状态是两个事实来源，判断到账以支付域退款单为准 |

| 资金实体 | 数字状态 |
|---|---|
| 支付单（PayStatusEnum） | `0` 待支付、`1` 支付成功、`2` 已关闭、`3` 退款中、`4` 已退款 |
| 退款单（RefundStatusEnum） | `0` 处理中、`1` 成功、`2` 失败 |

## 预约状态（AppointmentStatus，小写枚举）

`pending_confirm` 待确认、`pending_visit` 待到访、`visited` 已到访、`completed` 已完成、`cancelled` 已取消、`rejected` 已拒绝、`no_show` 爽约。流转：待确认 →（运营确认）待到访 →（用户到店）已到访 →（完成）已完成；待确认阶段可拒绝（`rejected`）；用户可从待确认或待到访取消（`cancelled`）；爽约从待到访标记（`no_show`）。不得重复处置终态记录。来源：`AppointmentStatus.canTransit` 与预约处置实现。看板时间维度：`LAST_7_DAYS` / `LAST_30_DAYS`。

## 发票状态机

`INIT`/`PENDING`（待开票）→ `ISSUING`（开票中）→ `ISSUED`（已开票）或 `ISSUE_FAILED`（开票失败，可重试回开票中）；`RED_FLUSHED`（已红冲，从已开票进入）、`CANCELLED`（已取消，从待开票进入）为终态分支。列表筛选 `PENDING` 合并 `INIT` 与 `PENDING`。

红字确认单：部分红冲场景需在电子税务局完成确认——红票 `ISSUING` 且 `redConfirmStatus` 为 `PENDING` 待确认 / `CONFIRMED` 已确认 / `REJECTED` 已拒绝，运营确认/拒绝后红票继续或终止。

| 发票枚举 | 取值 | 说明 |
|---|---|---|
| invoiceType | `1` 蓝票（正票）/ `2` 红票（冲销票） | 发票类型 |
| buyerType | `1` 个人 / `2` 企业 | 购方类型 |
| invoiceCategory | `1` 电子普票 / `2` 电子专票 | **代客开票仅支持普票**，服务端强制置 1 |
| 发票列表状态 | `INIT/PENDING/ISSUING/ISSUED/ISSUE_FAILED/RED_FLUSHED/CANCELLED` | 见上方状态机 |

## 对账枚举

| 枚举 | 取值 |
|---|---|
| 差异处理状态 handleStatus | `PENDING` 待处理 / `MARKED_ERROR` 已标误差 / `ESCALATED` 已升级 / `RESOLVED` 已处理 |
| 差异风险 riskLevel | `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` |
| 差异类型 ReconcileDiffType | `AMOUNT_MISMATCH` 金额不一致 / `STATUS_MISMATCH` 状态不一致 / `DATA_MISSING` 数据缺失 |
| 对账节点 nodeType | `ORDER_PAYMENT` 订单支付 / `COUPON_STATUS` 券状态 / `CPS_COMMISSION` CPS 佣金 / `ORDER_AMOUNT_INTEGRITY` 订单金额完整性 |
| 对账任务 Tab | `ALL` / `HAS_DIFF` / `FAILED` |
| 差异处置操作类型 | `MARK_ERROR` / `ESCALATE` / `REMARK` / `CONFIRM` |

## 服务订单枚举

| 枚举 | 取值 | 说明 |
|---|---|---|
| serviceType | `HOME_VISIT` 上门 / `PICKUP_DELIVERY` 取送 | 服务类商品类型 |
| verificationType | `PICKUP` 取件核销 / `COMPLETION` 完成核销 | 服务核销节点；取送类须先取件核销再完成核销 |
| verificationStatus | `NOT_GENERATED` 未生成 / `PENDING_PICKUP` 待取件核销 / `PENDING_COMPLETION` 待完成核销 / `COMPLETED` 已完成 | 购买单核销进度筛选 |
| 子单核销码状态 | `NOT_GENERATED` 未生成 / `PENDING_VERIFY` 待核销 / `VERIFIED` 已核销 / `INVALID` 已失效 | 履约子单核销码状态 |
| 购买单可执行操作 | `APPOINT` / `RESCHEDULE` / `DISPATCH` / `REDISPATCH` / `VERIFY` | 仅尚有未预约次数时含 `APPOINT` |

## 售后配置与运费规则枚举

| 枚举 | 取值 |
|---|---|
| 原发货运费 originalFreight | `全退` / `不退` / `人工判定` / `0` / `-`（中文枚举文本，非数值） |
| 退回运费 returnFreight | `商家承担` / `用户自付` / `人工判定` / `-` |
| 寄新货运费 newShipmentFreight | `商家出` / `-` |
| 自提超时处理 selfPickupTimeoutAction | `AUTO_CANCEL` 自动取消订单 / `AUTO_AFTER_SALE` 自动发起售后 |
| 配置操作日志 firstModule | `AFTER_SALE_CONFIG` / `TRADE_CONFIG` |
| 配置操作日志 secondModule | `AUTO_REFUND` / `FREIGHT_RULE` / `TIMELINESS`（订单超时与售后时效共用）/ `INVENTORY` / `GIFT_WAREHOUSE` |
