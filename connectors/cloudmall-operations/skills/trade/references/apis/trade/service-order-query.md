# 交易域 — 服务订单查询契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；预约/派单/核销写操作见 `service-order-action.md`；运营流程：`references/flows/trade-service-order.md`
> 服务订单是「服务类商品」（上门/取送服务）的履约单据：购买单（`purchaseOrderNo`）下按次数拆履约子单（`fulfillmentOrderNo`），三层标识不能互换。所有 ID 为十进制字符串；会员信息为敏感面（脱敏展示），不复述明文。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 service-order.search · service-order.tab-count · service-order.export · service-order.detail · service-order.time-slots

---

## ✅ 服务订单搜索 — ops.trade.service-order.search

用途：分页查询服务订单（购买单视角，每条含履约子单摘要）。

入参：`ServiceOrderPageQuery`（继承分页 `pageNum`/`pageSize`）：`noKeyword`（购买单/父单/履约子单号聚合搜索）、`personKeyword`（会员姓名/手机号/UID）、`goodsKeyword`（商品名/SPU/SKU/商家编码）、`status`（订单状态枚举，同订单域）、`serviceType`（`HOME_VISIT` 上门 / `PICKUP_DELIVERY` 取送）、`storeId` / `storeName` / `supplierId`、`minPaidAmount` / `maxPaidAmount`、`createdStartTime` / `createdEndTime`（`yyyy-MM-dd HH:mm:ss`）、`appointmentStartTime` / `appointmentEndTime`（`yyyy-MM-dd HH:mm:ss`）、`staffId` / `staffName`、`verificationStatus`（核销进度筛选：`NOT_GENERATED` 未生成核销码 / `PENDING_PICKUP` 待取件核销 / `PENDING_COMPLETION` 待完成核销 / `COMPLETED` 已完成）、`appointmentExpireRisk`（预约到期筛选：`EXPIRING_WITHIN_7_DAYS` 仅看仍待预约且 7 天内到期的购买单 / `EXPIRED` 已过期）。

结果来源 `PageResult<ServiceOrderPageVO>`，每条关键字段：`orderNo`（购买单号，后续 detail 定位）、`parentOrderNo`、`orderStatus`、`uid` / `memberNickname` / `memberPhone`（**敏感面，脱敏展示**）、`item`（商品行，结构同订单域商品行）、`purchaseQuantity`（购买次数）、`paidAmount`、`serviceType` / `serviceTypeName`、`storeName` / `supplierName`、`fulfillmentSummary`（履约摘要）、`fulfillments[]`（履约子单行，含 `fulfillmentOrderNo`——派单/核销/改约的定位）、`operations[]`（当前购买单可执行操作枚举：`APPOINT` / `RESCHEDULE` / `DISPATCH` / `REDISPATCH` / `VERIFY`，仅尚有未预约次数时含 `APPOINT`）。

`fulfillmentSummary` 结构（`ServiceFulfillmentSummaryVO`）：`totalCount` 总次数 / `appointedCount` 已预约 / `completedCount` 已完成 / `unappointedCount` 未预约 / `nextAppointmentAt` 最近预约时间。`fulfillments[]` 关键子字段见 detail 节的履约子单表（列表行为其子集，不含金额扩展）。

```json
{
  "capability": "ops.trade.service-order.search",
  "input": { "pageNum": 1, "pageSize": 20 },
  "summary": "查询服务订单"
}
```

---

## ✅ 服务订单阶段计数 — ops.trade.service-order.tab-count

用途：统计服务订单各履约阶段工作量。入参同 search（均可选，空 body `{}` 即全部）。结果来源 `ServiceOrderTabCountVO`：`totalCount`、`pendingPaymentCount`、`pendingAppointmentCount`（待预约）、`fulfillingCount`、`pendingDispatchCount`（待派单）、`pendingServiceCount`（待服务）、`inProgressCount`（服务中）、`completedCount`、`closedCount`。

```json
{
  "capability": "ops.trade.service-order.tab-count",
  "input": {},
  "summary": "统计服务订单阶段"
}
```

---

## ✅ 服务订单导出 — ops.trade.service-order.export

用途：按筛选条件导出服务订单（🟢 URL 型）。入参同 search。结果 `ExportResultVO`：`downloadUrl`（预签名，约 60 分钟时效）等；链接转告用户，不代下载。

```json
{
  "capability": "ops.trade.service-order.export",
  "input": {},
  "summary": "导出服务订单"
}
```

---

## ✅ 服务订单详情 — ops.trade.service-order.detail

用途：读取单笔购买单详情与全部履约子单（预约/派单/核销前的事实来源）。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| purchaseOrderNo | 字符串 | 是，路径参数，≤64 字符 | search 返回的购买单号 |

结果来源 `ServiceOrderDetailVO`：购买单全量信息（会员、支付 `payment`、商品行 `item`、金额、服务归属、`serviceAddress` 服务地址——脱敏）+ `fulfillments[]` 履约子单详情 + `operationLogs[]` 操作日志。**`purchaseOrderNo`（购买单）与 `fulfillmentOrderNo`（履约子单）定位不同能力，不能互换**。

`fulfillments[]`（`ServiceFulfillmentDetailVO`）关键字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| fulfillmentOrderNo / sequenceNo | 字符串 / 整数 | 履约子单号 / 次数序号 |
| orderStatus / orderStatusName / orderStatusDesc | 整数 / 字符串 | 子单状态码与描述 |
| appointmentAt / appointmentExpireAt | 时间字符串 | 预约时间 / 预约有效期（`yyyy-MM-dd HH:mm:ss`） |
| rescheduleCount | 整数 | 已改约次数（计数展示，服务端不限制） |
| serviceAddress / returnAddress | 对象 | 服务地址 / 取回地址：`receiverName`、`receiverPhone`（脱敏）、`fullAddress`（脱敏） |
| serviceStaff | 对象 | 服务人员快照：`staffId`（ID字符串）、`staffName` |
| pickupVerificationStatus / completionVerificationStatus | 字符串 | 核销码状态：`NOT_GENERATED` 未生成 / `PENDING_VERIFY` 待核销 / `VERIFIED` 已核销 / `INVALID` 已失效 |
| pickupVerificationCode / completionVerificationCode | 字符串 | 核销码本体回显（生成后有值）；核销执行仍必须以客户当面提供的码为准，不得把回显码当作已与客户确认 |
| pickupVerificationTime / completionVerificationTime | 时间字符串 | 取件 / 完成核销时间 |
| quantity / paidAmount / refundableAmount | 整数 / 金额 | 本次数量 / 分摊金额 / 可退金额 |
| operations[] | 字符串数组 | 该子单当前可执行操作（同 search 节枚举） |

```json
{
  "capability": "ops.trade.service-order.detail",
  "input": { "purchaseOrderNo": "PO-SO20260905000001" },
  "summary": "查询服务订单详情"
}
```

---

## ✅ 可约时段查询 — ops.trade.service-order.time-slots

用途：按门店与 SKU 查询可预约日期及指定日期的时段容量；与 C 端共用通用容量服务，不依赖购买单、履约单、地址或次数序号。预约/改约写操作仍校验订单资格与实时容量。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| storeId | 字符串 | 是，正 Long | 服务门店 ID |
| skuId | 字符串 | 是，正 Long | 服务商品 SKU ID |
| date | 字符串 | 否，`yyyy-MM-dd`（ISO 日期） | 指定单日容量；省略时默认查询最早可预约日期的容量 |

结果来源 `ServiceTimeSlotVO`：每次都返回完整 `appointmentDates[]`（`yyyy-MM-dd`）及 `daySlots`，包含实际查询的 `appointmentDate` 和 `slots[]`。未传 `date` 时默认最早可预约日期，即使首日约满也不跳日；空预约窗口且未指定日期时省略 `daySlots`。预约窗口日期不保证仍有剩余容量，每个时段对象含：

| slots[] 字段 | 类型 | 含义 |
|---|---|---|
| appointmentTime | 字符串 | 时段起点（`HH:mm:ss`，如 `10:00:00`） |
| remainingCapacity | 整数 | 该时段剩余可约容量 |
| available | 布尔值 | 该时段当前是否可约（容量为 0 时 false） |

以 `available=true` 且容量足够的时段为候选；`available=false` 不提交预约。

```json
{
  "capability": "ops.trade.service-order.time-slots",
  "input": { "storeId": "101", "skuId": "201", "date": "2026-10-20" },
  "summary": "查询可约服务时段"
}
```
