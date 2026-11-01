# 交易域 — 售后查询契约

> 概念知识：`references/domains/trade-concepts.md`，状态与枚举：`references/domains/trade-enums.md`；售后处置/审核写操作见 `aftersale-action.md`，代客创建见 `aftersale-behalf.md`；运营流程：`references/flows/trade-aftersale.md`
> 所有 ID 均为十进制字符串；查询只取事实，敏感字段（手机号、凭证、联系方式）不得向用户复述。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 aftersale.search · aftersale.tab-count · aftersale.detail · aftersale.reasons-detail · aftersale.reasons.list · aftersale.refunded-summary · aftersale.exchangeable-skus · aftersale.remarks.list · aftersale.export

---

## ✅ 售后分页搜索 — ops.trade.aftersale.search

用途：定位需要审核、收货、换货或退款跟进的售后单。返回摘要，不能把摘要当详情或退款成功证明。常用字段为 `keyword`、`afterSaleNo`、`orderNo`、`afterSaleType`、`afterSaleStatus`、`receiveStatus`、`shippedStatus`、`nearTimeout` 与 `todayProcessed`；不要把单选 `afterSaleType` 误传成数组。

输入字段均可选；未提供的筛选不生效。来源：`AfterSalePageQuery`、公共 `PageQuery`；匹配语义由 `AfterSaleSearchServiceImpl.buildBoolQuery` 实现，前端 `api/trade/types.ts` 的售后检索类型对照。

| 参数 | 类型 | 含义与约束 |
|---|---|---|
| pageNum / pageSize | 整数 | 页码默认 1；每页默认 20，范围 1～100 |
| keyword | 字符串 | 综合售后号、订单号、手机号、会员名搜索 |
| uid | ID字符串 | 精确指定客户 |
| startTime / endTime | 时间字符串 | 申请时间边界，`yyyy-MM-dd HH:mm:ss`，分别可省略 |
| afterSaleNo / orderNo / parentOrderNo | 字符串 | 精确售后号、子订单号、父订单号，各最多 32 字符 |
| memberPhone | 字符串 | 精确手机号，必须满足 `^1\d{10}$` |
| productName / skuName | 字符串 | 商品名称、规格名称模糊搜索，各最多 200 字符 |
| afterSaleType | 字符串 | 单值 `REFUND_ONLY`、`RETURN_REFUND`、`EXCHANGE` |
| afterSaleStatus | 字符串数组 | 精确状态名（见 `trade-enums.md` 售后状态表），不能传数字码 |
| afterSaleInitiator | 字符串 | `CUSTOMER`、`MERCHANT`、`SYSTEM`；最多 32 字符 |
| memberName / auditUser | 字符串 | 客户姓名、审核人模糊搜索，各最多 64 字符 |
| shopName | 字符串 | 下单门店模糊搜索，最多 128 字符 |
| receiveStatus / shippedStatus | 整数 | `0` 未收/未发，`1` 已收/已发；是两个独立事实 |
| nearTimeout | 布尔值 | true 筛选待审核且距审核超时不超过 6 小时的单据 |
| todayProcessed | 布尔值 | true 筛选今日审核同意/拒绝，不含客户取消 |
| orderSource | 字符串 | 订单来源精确值，最多 32 字符；复制已知来源，不自造枚举 |
| categoryIds | ID字符串数组 | 售后商品任一分类命中即满足 |
| noKeyword | 字符串 | 售后号或订单号精确组合搜索，最多 64 字符 |
| personKeyword | 字符串 | 客户名/门店/审核人模糊或手机号精确组合搜索；纯数字还匹配客户 uid，最多 128 字符 |
| goodsKeyword | 字符串 | 规格名模糊或 SKU、SPU、商家商品编码、商家规格编码精确组合搜索，最多 200 字符 |
| chanId | 字符串 | 来源渠道标识，精确匹配，复制真实值 |

可用状态使用 `trade-enums.md` 售后状态表的大写枚举名；大小写严格一致；错状态不得以空列表当作业务结论。

结果来源：`PageResult<AfterSaleVO>`，`records` 为本页集合，`total` 为总条数，`pageNum` / `pageSize` 为分页信息。每条主要读取 `afterSaleNo`（后续详情定位）、`orderNo`、`afterSaleType`、`afterSaleStatus`、`dataSource`、`totalRefundAmount`、`items`、`returnMethod`。`items` 为摘要 `AfterSaleItemVO`，不是创建售后商品项；不得把其 `id` 当订单商品项 ID。先筛选唯一目标，再读取详情进行写入。

```json
{
  "capability": "ops.trade.aftersale.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20,
    "afterSaleStatus": [
      "PENDING_AUDIT"
    ]
  },
  "summary": "查询待审核售后"
}
```

---

## ✅ 售后阶段计数 — ops.trade.aftersale.tab-count

用途：统计各售后阶段的工作量，用于排队和排优先级；不是“当前列表条数”的通用替代。今日/超时指标另有统计口径，不能与当前列表直接相等。

| 参数 | 类型 / 必填 | 统计约束 |
|---|---|---|
| search 表中除下一行外的全部字段 | 同 search，均可选 | 字段意义及长度约束沿用 search 表；统计跨全部售后阶段 |
| pageNum、pageSize、afterSaleStatus、nearTimeout、todayProcessed | 不传 | 实现不复制这些条件，传入也不能限定统计 |

结果来源：`AfterSaleTabCountVO` 与 `AfterSaleSearchServiceImpl.tabCount`。`totalCount`、`pendingAuditCount`、`pendingBuyerReturnCount`、`pendingMerchantReceiveCount`、`pendingMerchantShipCount`、`pendingBuyerReceiveCount`、`rejectedCount`、`refundFailedCount`、`refundingCount`、`completedCount` 表示本次普通筛选范围的状态计数；`nearTimeoutCount`、`todayProcessedCount`、`todayApprovedCount`、`todayRejectedCount` 由独立统计计算，不沿用本次业务筛选。不要将这些独立指标解释成某客户/订单的计数。结果未单列关闭计数，各已列计数之和未必等于全部。

```json
{
  "capability": "ops.trade.aftersale.tab-count",
  "input": {},
  "summary": "统计售后状态"
}
```

---

## ✅ 售后详情 — ops.trade.aftersale.detail

用途：读取单笔售后的类型、阶段、退款金额、商品行、退回方式与地址，是任何售后写操作的前置事实。`afterSaleNo` 必须来自检索结果或用户明确提供；敏感字段（凭证、退回联系方式）不得向用户复述。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| afterSaleNo | 字符串 | 是 | search 返回或用户明确提供的售后单号 |

| 结果字段 | 用途与边界 | 字段来源 |
|---|---|---|
| afterSaleNo / orderNo / dataSource | 核对目标与历史迁移只读边界 | AfterSaleDetailVO |
| afterSaleType / afterSaleStatus | 判断各操作是否适用；描述字段仅用于展示 | AfterSaleDetailVO |
| fulfillmentMode / returnMethod | 订单履约与售后退回方式不是同一个概念，审核地址和线下完结以 returnMethod 为准 | AfterSaleDetailVO、AfterSaleHelper |
| applyItemAmount / expectedItemAmount | 申请商品金额快照 / 预计商品退款额；不可把展示字段直接作为审核可编辑入参 | AfterSaleDetailVO |
| freightRefundAmount / packagingRefundAmount / totalRefundAmount / maxFreightRefundAmount | 运费、包装费、合计与运费上限；合计不证明已退款 | AfterSaleDetailVO |
| items[].id / skuId / orderLineNo | 售后商品项标识 / 规格标识 / 订单行号，id 不是订单商品项 ID | AfterSaleDetailItemVO |
| items[].refundQuantity / refundAmount / applyRefundAmount / exchangeShippableQuantity | 退回数量、预计/申请金额、换货可发数量 | AfterSaleDetailItemVO |
| items[].exchangeItemInfo | 换入规格快照对象，结构见下表，可能为空 | AfterSaleDetailItemVO、AfterSaleConvert、ExchangeItemInfo |
| refund | 退款对象：applyRefundAmount、refundStatus、refundPayMethod、refundInitiateTime、refundTransactionNo、refundPhase、refundDetails | AfterSaleRefundVO；退款状态是展示文本，不替代支付域退款单状态 |
| remark / operationRemarks[] | 单条覆盖备注 / 追加的运营流水，两者独立 | AfterSaleDetailVO、AfterSaleRemarkVO |
| statusLogs / negotiationLogs / logistics | 状态记录、协商记录与运单；用于回读动作结果 | AfterSaleDetailVO |
| reasonId / applyReason / reasonGroupName / responsibility | 售后原因及责任快照 | AfterSaleDetailVO |
| mediaJson | 凭证序列化字符串，解析规则见代客创建契约 | AfterSaleDetailVO、前端 ReasonInfoCard |
| exchangeStockAvailable | 仅换货待审核时有值；false 时禁止同意，null 不能解释为库存充足 | AbstractAfterSaleService.detail |
| returnContactName / returnContactPhone / returnFullAddress | 已选退回地址快照，不是可用于 returnAddressId 的 ID | AfterSaleDetailVO |

`exchangeItemInfo` 虽以 Object 声明，运行时由 `ExchangeAfterSaleService.resolveExchangeItemInfoJson` 创建，`AfterSaleConvert` 解析。前端 `types.ts` 与 `ItemsCard` 消费以下固定字段：

| 对象字段 | 类型与含义 |
|---|---|
| spuId / skuId / storeId / warehouseIds[] | 商品、规格、门店、仓库数字标识，保留十进制字符串精度 |
| spuCode / skuCode / merchantSkuCode / merchantProductCode | 商品/规格及商家编码字符串 |
| skuName / productName / productType / productThumbnail / specInfo | 换入规格名称、商品名、类型、缩略图、规格描述字符串 |
| salePrice / activityPrice | 金额；换货金额仍继承原商品行，不据此计算退款 |
| spuInfo / skuInfo | 序列化快照字符串，当前创建实现填 `"{}"`，不能当作完整商品属性 |

同规格历史记录可为 null；解析异常的旧值可能原样返回字符串。遇到非对象值保留原始证据并停止依赖其字段的编排，不能补造对象或把整个快照回传为写参数。

```json
{
  "capability": "ops.trade.aftersale.detail",
  "input": {
    "afterSaleNo": "AS20260905000001"
  },
  "summary": "查询售后详情"
}
```

---

## ✅ 售后原因详情 — ops.trade.aftersale.reasons-detail

用途：读取按售后类型分组的可选原因、原因大类和责任归属；用于代客创建或拒绝时选择真实原因，不能自行拼造 `reasonId`。

入参：无，传 `{}`。结果来自 `AfterSaleReasonService.listGroupedByTypeDetail` 与 `ReasonDetailVO`：按 `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE` 售后类型分组的对象，每组为数组，元素包含 `id`（后续 reasonId）、`reasonName`、`groupName`、`responsibility`（`USER` / `MERCHANT` / `SHARED`）。分组可能缺失，不得填造原因。这是具名分组映射，不是自由字段对象。选择与申请类型相符的原因；审核拒绝使用文本 `rejectReason`，不可误把原因 ID 传成拒绝原因编码。

```json
{
  "capability": "ops.trade.aftersale.reasons-detail",
  "input": {},
  "summary": "查询售后原因"
}
```

---

## ✅ 售后原因轻量映射 — ops.trade.aftersale.reasons.list

用途：读取按售后类型分组的轻量原因映射（`Map<String, List<ReasonVO>>`，键为 `REFUND_ONLY` / `RETURN_REFUND` / `EXCHANGE`）。每个原因只含 `id` 与 `reasonName`；需要责任归属、大类名等详情时使用 `reasons-detail`。入参：无，传 `{}`。

```json
{
  "capability": "ops.trade.aftersale.reasons.list",
  "input": {},
  "summary": "查询售后原因轻量映射"
}
```

---

## ✅ 已退款汇总 — ops.trade.aftersale.refunded-summary

用途：读取订单维度的已退款汇总，代客创建售后前核对剩余可退金额（配合 create-on-behalf 的金额约束）。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| orderNo | 字符串 | 是，路径参数 | 订单检索/详情或用户明确提供 |

结果来源 `RefundedSummaryVO`，金额字段均为元（JSON 数字）：`refundedTotalAmount`（已退总额）、`refundedFreightAmount`（已退运费）、`refundedPackagingAmount`（已退包装费）、`orderPaidAmount`（订单实付）、`remainRefundableAmount`（剩余可退）、`orderFreightAmount`（订单运费）、`maxFreightRefundable`（运费最大可退）。剩余可退金额是申请金额上限的事实依据；零余额不能发起仅退款/退货退款。

```json
{
  "capability": "ops.trade.aftersale.refunded-summary",
  "input": { "orderNo": "SO20260905000001" },
  "summary": "查询订单已退款汇总"
}
```

---

## ✅ 可换规格查询 — ops.trade.aftersale.exchangeable-skus

用途：查询订单各商品行的可换规格及库存资格，换货审核或代客创建换货前确认目标规格可用性，替代猜测。

| 参数 | 类型 | 必填 | 来源 |
|---|---|---|---|
| orderNo | 字符串 | 是（body 字段，服务端校验非空） | 订单检索/详情或用户明确提供 |

结果来源 `List<ExchangeableSkuQueryResult>`：每个元素含 `orderItemId`（订单商品行 ID，字符串）与 `exchangeableSkus[]`（该行可换规格清单）。`exchangeableSkus[]` 每项结构（`ExchangeableSkuVO`）：

| 字段 | 类型 | 含义 |
|---|---|---|
| skuId | ID字符串 | 换入规格 ID（create-on-behalf 的 `exchangeSkuId` 取值来源） |
| spuName / skuName | 字符串 | 商品名 / 规格名 |
| specInfo | 字符串 | 规格描述文本（非 JSON） |
| thumbnail | 字符串 | 规格缩略图 |
| salePrice | 金额（元） | 售价（换货金额仍继承原商品行，不据此计算差价） |
| stockAvailable | 布尔值 | 库存是否充足（不足的规格不可选为换入目标） |
| onShelf | 布尔值 | 是否在架可售（下架规格不可选） |

注意请求是 POST 但纯查询语义，不产生写入。结果为空列表代表该订单无可换规格，不表示接口失败；不能凭商品名猜测换入规格，必须以此结果或 detail 的换货快照为准。

```json
{
  "capability": "ops.trade.aftersale.exchangeable-skus",
  "input": { "orderNo": "SO20260905000001" },
  "summary": "查询可换规格"
}
```

---

## ✅ 售后备注流水 — ops.trade.aftersale.remarks.list

用途：分页读取售后的运营备注流水（与 remark.add 写入的是同一流水，与覆盖式 `remark` 字段无关）。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| afterSaleNo | 字符串 | 是，路径参数 | 售后单号 |
| pageNo | 整数 | 否，默认 1 | 页码 |
| pageSize | 整数 | 否，默认 10 | 每页条数 |

结果来源 `PageResult<AfterSaleRemarkVO>`：每条含 `id`、`afterSaleNo`、`content`、`operatorName`、`createdTime`（`yyyy-MM-dd HH:mm:ss`）。追加备注后可用本能力核对最新记录。

```json
{
  "capability": "ops.trade.aftersale.remarks.list",
  "input": { "afterSaleNo": "AS20260905000001", "pageNo": 1, "pageSize": 10 },
  "summary": "查询售后备注流水"
}
```

---

## ✅ 售后清单导出 — ops.trade.aftersale.export

用途：按筛选条件导出售后清单，返回 COS 预签名下载链接（🟢 URL 型导出）。

| 参数 | 类型 | 必填 / 约束 | 说明 |
|---|---|---|---|
| exportType | 字符串 | 是 | 导出维度：`AFTER_SALE`（售后单）/ `AFTER_SALE_ITEM`（售后商品行） |
| afterSaleNo / orderNo / parentOrderNo | 字符串 | 否，各 ≤32 字符 | 单号精确筛选 |
| memberPhone | 字符串 | 否，须满足 `^1\d{10}$` | 手机号精确筛选 |
| productName | 字符串 | 否，≤200 字符 | 商品名模糊筛选 |
| afterSaleType | 字符串 | 否 | 售后类型筛选 |
| afterSaleStatus | 字符串数组 | 否 | 售后状态筛选（枚举同 search） |

来源：`AfterSaleExportRequest`。结果为 `ExportResultVO`：`downloadUrl`（预签名 URL，约 60 分钟时效）等字段。Agent 不下载文件，把链接与时效告知用户自行下载；导出为异步生成，若返回任务受理形态则按返回提示核对。

```json
{
  "capability": "ops.trade.aftersale.export",
  "input": { "exportType": "AFTER_SALE", "afterSaleStatus": ["PENDING_AUDIT"] },
  "summary": "导出待审核售后清单"
}
```
