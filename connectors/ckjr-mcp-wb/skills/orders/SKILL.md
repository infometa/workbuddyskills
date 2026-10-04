---
name: ckjr-orders
description: 查询已授权创匠店铺的订单列表或订单统计。
---

订单明细使用 `orders_list`，订单汇总使用 `orders_statistics`。两个工具共用筛选参数，但返回形状不同；不要用明细结果代替统计，也不要把统计结果当作订单行。

常用参数直接放在工具参数对象中：

| 参数 | 含义 |
| --- | --- |
| `searchType` / `searchName` | 搜索类型和值：订单号、交易单号、学员编码 ID、买家昵称/姓名/手机号、收货人姓名/手机号、物流单号、商品 ID 等 |
| `timeType` | 时间类型：`1` 下单时间、`2` 付款时间、`3` 结算时间 |
| `startAt` / `endAt` | `YYYY-MM-DD` 日期范围 |
| `minAmount` / `maxAmount` | 金额范围，字符串传值以保留精度 |
| `status` / `afterStatus` | 订单状态和售后状态，`-1` 表示全部 |
| `invoice` / `invoiceStatus` | 发票申请和开票状态 |
| `prodName` / `prodType` / `orderType` | 商品名称、商品类型、订单类型 |
| `fromAPP` / `paymentMethod` / `mchType` / `deliverType` | 渠道、支付、收款和发货方式 |
| `hasGiftOrder` | 是否包含赠品 |
| `page` / `limit` | 分页；默认 `1/10`，每页最多 50 |

不要传 `isStatistics`；列表工具传入 `0`，统计工具传入 `1`。不要传 `companyId`、`storeId`、`chainStoreId`、`excelCompanyId`、`excelStoreId`、`excelLoginAdminUserId` 或上游地址。管理员和店铺范围来自 OAuth 授权。

只请求一页并准确说明页码和条数。沿用后台慢查询保护：可能缩小查询范围、把统计改为列表、返回上次缓存或空结果。以实际返回内容为准，不把列表当作统计，不把空结果解释为店铺没有订单。

统计工具暂不接受 `searchType=10`（收货人姓名）或 `searchType=11`（收货人手机号），因为后台统计分支不会应用这两个筛选条件；需要这类筛选时使用 `orders_list`。
