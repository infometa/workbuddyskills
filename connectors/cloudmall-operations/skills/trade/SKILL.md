---
name: trade
display_name: 云MALL订单
display_name_en: CloudMall Orders
description: 云MALL订单域查询。当用户要求查订单、订单列表、订单状态、待发货/待付款订单、按门店或时间筛选订单、查看订单详情时使用。
description_zh: 查询当前授权租户的云MALL订单：订单列表、状态筛选、订单详情。
description_en: Query CloudMall orders for the authorized tenant: order list, status filtering, and order details.
allowed-tools: cloudmall_query
version: 0.1.0
author: 云MALL
---

# 云MALL订单域

以当前运营账号的实时接口权限与数据权限，查询云MALL订单数据。第一期提供订单分页查询与订单详情两项能力，本 Skill 随域内能力扩展持续更新。

## 域内能力与参数

### ops.trade.order.search — 订单分页查询

| 参数 | 必填 | 说明 |
|---|---|---|
| pageNum / pageSize | 是 | 分页参数；pageSize 上限 100，默认建议 20 |
| status | 否 | 订单状态：PENDING_PAYMENT / PENDING_SHIPMENT（待发货）/ PENDING_PICKUP / PENDING_DELIVERY / SHIPPED / RECEIVED / COMPLETED / CLOSED / PARTIAL_SHIPPED / PENDING_FINAL_PAYMENT（仅定金预售）/ PENDING_GROUP / PENDING_RECEIVE / PERIOD_FULFILLING。中文含义以返回的 orderStatusDesc 为准；不存在的枚举值（如 WAIT_SHIP）会被拒绝 |
| orderNo | 否 | 订单号模糊匹配（部分单号即可命中，1~64 字符）；需要精确匹配请用 noKeyword |
| noKeyword | 否 | 订单号/父订单号精确匹配（term） |
| personKeyword | 否 | 人员类组合关键词，多维度 OR 命中：收货人姓名（模糊）/ 收货人电话（精确）/ 门店名（模糊）/ 导购名（模糊）/ 会员电话（精确）/ 会员 uid（纯数字时精确）。不是门店精确过滤条件 |
| goodsKeyword | 否 | 商品关键词（商品名/规格名/SKU/SPU/商家编码，多维度组合） |
| storeName | 否 | 门店名称（模糊匹配，见「调用流程」） |
| startTime / endTime | 否 | 下单时间范围，格式 yyyy-MM-dd HH:mm:ss |
| orderType | 否 | 订单类型枚举：NORMAL（普通）/ PRE_SALE_FULL（全款预售）/ PRE_SALE_DEPOSIT（尾款预售）/ SECKILL（秒杀）/ GROUP_BUY（拼团）/ POINTS_MALL（积分商城）/ PERIOD_BUY（周期购）；传错值会静默返回空结果，务必使用枚举值 |
| fulfillmentMode | 否 | 履约方式：DELIVERY（配送）/ SELF_PICKUP（自提） |

### ops.trade.order.detail — 订单详情

| 参数 | 必填 | 说明 |
|---|---|---|
| orderNo | 是 | 订单号（1~64 字符） |

## 调用流程（固定）

1. 已知订单号直接调用 detail；查询意图不明确时先向用户追问。
2. search → 唯一命中 → 用 orderNo 调 detail 补全明细；多命中 → 先向用户确认目标订单再继续。
3. 用户未指定店铺时，先问「查全部有权门店还是指定门店」；指定门店使用 storeName 参数。
4. storeName 是模糊匹配：出现重名或近似门店命中时，不得声称结果是单店精确结果，应向用户确认目标门店。
5. personKeyword 不是门店过滤条件（门店名只是其多个模糊命中维度之一）——按门店筛选必须使用 storeName。

## 调用示例

```json
{"capability": "ops.trade.order.search", "input": {"pageNum": 1, "pageSize": 20, "status": "PENDING_SHIPMENT"}, "summary": "查询待发货订单"}
```

```json
{"capability": "ops.trade.order.search", "input": {"pageNum": 1, "pageSize": 20, "storeName": "中心店"}, "summary": "查询中心店的订单"}
```

```json
{"capability": "ops.trade.order.detail", "input": {"orderNo": "SO20260905000001"}, "summary": "查询订单详情"}
```

## 输出

统一成功结构 `{ capability, data, traceId, truncated }`。search 的 data 为分页对象（records/total/pageNum/pageSize/totalPages/hasMore）；detail 为单个订单对象（含 items 商品行）。字段以服务端 allowlist 为准：列表含 orderNo/orderStatus/orderStatusDesc/storeName/needPayAmount/paidAmount/createTime 等，详情另含 items、payTime/shipTime/receiveTime 等。金额字段单位为元；finalPayEndTime 为毫秒时间戳；receiverPhone 是后端脱敏展示字段，不得尝试还原。

## 翻页与 truncated

truncated=true 表示响应预算触发精确重定位：MCP 已按原 offset 返回较小完整页。必须改用 truncation 中的 effectivePageNum/effectivePageSize/nextPageNum 继续翻页，不能沿用原 pageNum/pageSize，否则会出现跳项或重复。

## 错误恢复

- AUTH_REQUIRED：授权已失效，提示用户在 WorkBuddy 重新连接，不要求粘贴任何 Token。
- PERMISSION_DENIED：当前账号没有该接口权限，向用户说明后停止，不尝试其他权限码或接口。
- INPUT_INVALID：按参数表检查字段与枚举（例如正确值是 PENDING_SHIPMENT 而不是 WAIT_SHIP），修正后重试。
- UPSTREAM_TIMEOUT：稍后重试，并缩小查询范围（缩小时间范围或减小 pageSize）。

## 禁止事项与边界

- 不得询问或传入租户、账号、Token、接口路径、权限码等身份/路由信息；身份由连接授权自动绑定。
- Snowflake ID（如 uid）一律按十进制字符串处理，禁止转成数字。
- 第一期本域仅开放只读查询：门店库存明细、物流、售后、报表及任何写操作（创建/修改/取消/发货/退款等）均不支持。用户提出时明确说明不支持，不得尝试绕过。
