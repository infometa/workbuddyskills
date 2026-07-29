---
name: linkfox-1688-search-by-image
description: 1688平台以图搜图，通过商品图片精准检索外观相似或同款的1688货源，返回标题、价格、起批量、月销量、复购率、交易评分等核心数据。当用户提到1688以图搜图、1688找货源、以图找同款、跨境找工厂、1688识图、图片找货源、找相似货源、image search 1688、find supplier by image时触发此技能。即使用户未明确提及"以图搜图"，只要用户提供了图片URL并希望在1688上查找匹配或相似的货源商品，也应触发此技能。
---

# 1688-以图搜图

## 基本信息

- **业务工具名**：`/alibaba1688/imageSearch`
- **所属分组**：1688 · 图像搜索
- **功能说明**：支持在1688平台通过图片链接进行视觉搜索。通过图像识别技术精准检索外观相似或同款的商品货源，返回结果包含商品标题、图片、价格、起批量、月销量、复购率、交易评分等核心数据。支持多页检索，和多条件筛选和排序。
- **关键词**：1688以图搜图，1688找货源，以图找同款，跨境找工厂，1688识图


## 何时使用

当用户意图与“1688-以图搜图”匹配，或需要以下能力时使用本工具：支持在1688平台通过图片链接进行视觉搜索。通过图像识别技术精准检索外观相似或同款的商品货源，返回结果包含商品标题、图片、价格、起批量、月销量、复购率、交易评分等核心数据。支持多页检索，和多条件筛选和排序。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `uid` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `page` | `integer` | 否 | 最小 1；示例：`1` | 页码，从1开始，默认为1 |
| `chatId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `stepId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `filters` | `array<string>` | 否 | 最多 1000 项；示例：`["isOnePsale","certifiedFactory"]`, `["totalEpScoreLv2","shipIn24Hours"]` | 过滤条件列表，数组每一项为下列可选值之一，仅支持以下过滤条件: 【履约质量】综合体验分5星(totalEpScoreLv1), 综合体验分4.5星-5.0星(totalEpScoreLv2), 综合体验分4星-4.5星(totalEpScoreLv3), 综合体验分4星以下(totalEpScoreLv4), 认证工厂(certifiedFactory), 24小时揽收率<95%(getRate24HLv1), 24小时揽收率>=95%(getRate24HLv2), 24小时揽收率>=99%(getRate24HLv3), 48小时揽收率<95%(getRate48HLv1), 48小时揽收率>=95%(getRate48HLv2), 48小时揽收率>=99%(getRate48HLv3), 当日发货(shipInToday), 24小时发货(shipIn24Hours), 48小时发货(shipIn48Hours), 7天无理由(noReason7DReturn); 【商品属性】支持一件代发(isOnePsale), 支持包邮代发(isOnePsaleFreePost), 7天上新(new7), 30天上新(new30), 1688严选(1688Selection), 全球严选(isQqyx); 【品质退款】近30天品质退款率5%-10%(qrr10), 近30天品质退款率1%-5%(qrr5), 近30天品质退款率0-1%(qrr1), 近30天品质退款率0%无品质退款(qrr0); 【排除地区】排除日本(JPFL), 排除美国(USFL), 排除韩国(KRFL), 排除越南(VNFL), 排除沙特阿拉伯(SAFL), 排除东欧(RUFL), 排除哈萨克斯坦(KZFL), 排除中国香港(HKFL), 排除中国澳门(MOFL), 排除中国台湾(TWFL) |
| `groupId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `imageId` | `string` | 否 | 最长 1000 | 图片ID(1688图片ID),以图搜图查询结果中也返回，建议当分页page>1查询时带imageId，加快响应速度 |
| `keyword` | `string` | 否 | 最长 1000；示例：`书本` | 关键词，在结果中搜索 |
| `imageUrl` | `string` | 否 | 最长 1000；示例：`https://cbu01.alicdn.com/img/ibank/O1CN01otREEX1ZFA7hteom8_!!2217114123164-0-cib.jpg` | 图片URL地址，请确保图片URL有效且可公开访问，仅支持 png、jpg、jpeg 格式 |
| `memberId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `pageSize` | `integer` | 否 | 最小 1；最大 50；示例：`20` | 每页返回的商品数量，默认20，最大不超过50 |
| `priceMax` | `number` | 否 | 最小 0；示例：`100` | 价格筛选最大值（单位：人民币元，如 100 表示 100 元） |
| `priceMin` | `number` | 否 | 最小 0；示例：`10` | 价格筛选最小值（单位：人民币元，如 10 表示 10 元） |
| `messageId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `requestId` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `sortField` | `string` | 否 | 最长 1000；示例：`price`, `monthSold` | 排序字段，仅支持：price(批发价)、rePurchaseRate(复购率)、monthSold(月销量)。不传时默认按月销量倒序 |
| `sortOrder` | `string` | 否 | 最长 1000；示例：`asc`, `desc` | 排序方式，仅支持：asc(升序)、desc(降序)。不传时默认 desc |
| `userInput` | `string` | 否 | 最长 1000 | 平台自动注入的上下文字段，Agent 通常不需要填写，不作为 1688 业务参数 |
| `imageBase64` | `string` | 否 | 最长 1000 | 图片 Base64 编码字符串（imageUrl为空时使用），仅支持 png、jpg、jpeg 格式，不包含 data:image/jpeg;base64, 前缀 |
| `productCollectionId` | `string` | 否 | 最长 1000；示例：`262105288`, `262105286`, `262105253`, `262105281`, `262105280`, `262105277`, `262105276`, `262105274` | 货盘ID，单选，仅支持以下货盘: 262105288(跨境趋势品-跨境销量飙升商品), 262105286(韩国畅销品-韩国市场上销售情况良好商品), 262105253(日本畅销品-日本市场上销售情况良好商品), 262105281(一件代发时效保障货盘-商品标签为一件代发且历史履约较好的货盘), 262105280(跨境爆品-跨境头部成交商品), 262105277(圣诞节-圣诞节节令商品货盘), 262105276(万圣节-万圣节节令商品货盘), 262105274(夏季节令货盘-夏季属性商品货盘), 262105269(全球严选畅销货盘-跨境属性商品货盘), 262185282(官方验货-官方验样保障货品外观规格与描述一致) |


## MCP 调用示例

向以下地址发起 HTTP `POST`：

```text
https://mcp-tool-gateway.linkfox.com/mcp/any-tool
```

请求体：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "/alibaba1688/imageSearch",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 样式 |
| `total` | `integer` | 否 |  | 总商品数量（总行数），上游未返回总数时为 null |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `imageId` | `string` | 否 |  | 上传后的图片ID |
| `products` | `array<object>` | 否 |  | 商品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `totalPage` | `integer` | 否 |  | 总页数 |
| `sourceType` | `string` | 否 |  | 来源类型 |
| `pageItemCount` | `integer` | 否 |  | 本页商品数量 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `unit` | `string` | 否 |  | 单位 |
| `price` | `number` | 否 |  | 批发价（单位：元，人民币） |
| `title` | `string` | 否 |  | 商品标题 |
| `isJxhy` | `boolean` | 否 |  | 是否精选货源 |
| `shopId` | `string` | 否 |  | 店铺ID |
| `company` | `string` | 否 |  | 店铺名称 |
| `offerId` | `string` | 否 |  | 商品ID |
| `shopUrl` | `string` | 否 |  | 店铺链接地址 |
| `currency` | `string` | 否 |  | 币种 |
| `dataType` | `string` | 否 |  | 数据类型.weeklyData-周数据 monthlyData-月数据 |
| `imageUrl` | `string` | 否 |  | 图片URL |
| `isSelect` | `boolean` | 否 |  | 跨境select货盘标识 |
| `jxhyPrice` | `string` | 否 |  | 代发精选货源价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回） |
| `levelName` | `string` | 否 |  | 类目层级名称 |
| `isOnePsale` | `boolean` | 否 |  | 是否一件代发 |
| `modifyDate` | `string` | 否 |  | 商品修改时间（格式 yyyy-MM-dd HH:mm:ss，时区 Asia/Shanghai） |
| `productUrl` | `string` | 否 |  | 商品链接地址 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 数据来源类型 |
| `tradeScore` | `string` | 否 |  | 商品交易评分 |
| `pfJxhyPrice` | `string` | 否 |  | 批发精选货源价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回） |
| `productCode` | `string` | 否 |  | 商品编号（1688 商品 offerId） |
| `consignPrice` | `number` | 否 |  | 一件代发价（单位：元，人民币）.当isOnePsale=true时有效 |
| `deliveryTime` | `string` | 否 |  | 发货时间 |
| `hasPromotion` | `boolean` | 否 |  | 是否有营销活动 |
| `availableDate` | `string` | 否 |  | 商品上架时间（格式 yyyy-MM-dd HH:mm:ss，时区 Asia/Shanghai） |
| `promotionType` | `string` | 否 |  | 营销类型 |
| `quantityBegin` | `integer` | 否 |  | 起批量 |
| `salesQuantity` | `integer` | 否 |  | 销售件数.按dataType统计周期返回 |
| `promotionPrice` | `string` | 否 |  | 营销价（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回） |
| `quantityPrices` | `string` | 否 |  | 价格区间（单位：人民币元，字符串格式，可能为单价或价格区间，按 1688 原始返回） |
| `repurchaseRate` | `string` | 否 |  | 复购率.例如: 13% |
| `isPatentProduct` | `boolean` | 否 |  | 是否为专利商品 |
| `offerIdentities` | `string` | 否 |  | 商品标.严选 |
| `salesOrderCount` | `number` | 否 |  | 销售笔数.按dataType统计周期返回 |
| `tradeMedalLevel` | `string` | 否 |  | 卖家交易勋章等级 |
| `sellerIdentities` | `string` | 否 |  | 商家身份标识.超级工厂/实力商家/诚信通会员 |
| `estimatedSalesAmount` | `number` | 否 |  | 预估销售额（单位：元，人民币）.按dataType统计周期返回 |
| `offerExperienceScore` | `string` | 否 |  | 商品体验分 |
| `sendGoodsAddressText` | `string` | 否 |  | 发货地 |
| `compositeServiceScore` | `string` | 否 |  | 综合服务体验分 |
| `disputeComplaintScore` | `string` | 否 |  | 纠纷投诉处理分 |
| `repeatPurchasePercent` | `string` | 否 |  | 重复购买率 |
| `logisticsExperienceScore` | `string` | 否 |  | 物流体验分 |
| `afterSalesExperienceScore` | `string` | 否 |  | 售后体验分 |
| `consultingExperienceScore` | `string` | 否 |  | 咨询体验分 |

## 响应处理建议

1. 先检查 JSON-RPC 外层是否包含 `error`。
2. 成功时读取 `result`，并继续解析其中的 `content`、`data`、`products`、`items` 或其他业务字段。
3. 如果响应为 `text/event-stream`，按 SSE 事件读取 `data:` 内容，再解析 JSON。
4. 保留分页字段、总数、失败明细及 `costToken`。
5. 向用户输出分析结论，不要直接倾倒大段原始 JSON。

## 原始 Schema

原始的Input Schema 和 Output Schema 参考 references/schema.md

## 解决认证和积分问题

异常情况：未配置 `LINKFOX_AGENT_API_KEY` 和 `LINKFOXAGENT_API_KEY`；响应 401 或 402；消息含"积分余额不足/quota exceeded/insufficient balance/套餐到期/需充值"等。

措施：优先用 skill 内 onboarding.md 引导；找不到则加载 /linkfox-onboarding skill。 根据它的指引操作。

**注意**：你是workbuddy，并且渠道是workbuddy，使用linkfox-onboarding登录注册时**必须**传递channel为 workbuddy。这非常重要！
