---
name: linkfox-youying-shopee-get-product-infos
description: 友鹰Shopee商品选品工具，支持Shopee全站点的商品查询与筛选，覆盖马来西亚、中国台湾、印尼、泰国、菲律宾、新加坡、越南、巴西、墨西哥、智利、哥伦比亚等11个站点。当用户提到Shopee选品、虾皮商品搜索、Shopee爆款、虾皮市场分析、Shopee品类选品、虾皮关键词选品、Shopee销量筛选、虾皮价格筛选、东南亚电商选品、Shopee product search, Shopee product selection, Shopee bestsellers, Shopee market analysis时触发此技能。即使用户未明确提及"友鹰"或"Shopee"，只要其需求涉及在虾皮平台上搜索商品或筛选Shopee商品数据，也应触发此技能。
---

# 友鹰-shopee商品选品

## 基本信息

- **业务工具名**：`/youying/shopee/getProductInfos`
- **所属分组**：友鹰 · Shopee 选品
- **功能说明**：支持shopee全站点的商品查询，发现shopee的爆款货源。
- **关键词**：友鹰, shopee选品, 虾皮选品, 关键词选品, 品类选品，市场分析，过滤，选品工具，功能需求调研, 市场机会点, 选品决策


## 何时使用

当用户意图与“友鹰-shopee商品选品”匹配，或需要以下能力时使用本工具：支持shopee全站点的商品查询，发现shopee的爆款货源。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1` | 当前页码 |
| `pids` | `string` | 否 | 最长 10000 | 商品id列表(单次最多500个),多个商品id使用逗号隔开，如：aaa,bbb |
| `pL1Id` | `string` | 否 | 最长 1000 | 1级类目ID |
| `pL2Id` | `string` | 否 | 最长 1000 | 2级类目ID |
| `pL3Id` | `string` | 否 | 最长 1000 | 3级类目ID |
| `cidList` | `string` | 否 | 最长 1000 | 类目id列表，每组id必须指定完整路径，可指定多组id，多个组id使用｜隔开，如：AAA,BBB,CCC｜DDD,EEE |
| `keyword` | `string` | 否 | 最长 1000 | 标题 |
| `orderBy` | `string` | 否 | 最长 1000；示例：`rating`, `price`, `historical_sold`, `sold`, `payment`, `favorite`, `ratings`, `gen_time` | 排序方式: rating(评分), price(价格), historical_sold(商品总销售件数), sold(前30天销售件数), payment(前30天销售金额), favorite(Favorite数), ratings(Ratings数), gen_time(商品上架时间), estimate_sold(估算前30天销售件数) |
| `soldMax` | `integer` | 否 |  | 前30天销售件数结束值 |
| `soldMin` | `integer` | 否 |  | 前30天销售件数起始值 |
| `station` | `string` | 是 | 最长 1000；示例：`malaysia`, `MY`, `taiwan_china`, `Taiwan_CHN`, `indonesia`, `ID`, `thailand`, `TH` | Shopee站点国家代码 |
| `cbOption` | `integer` | 否 |  | 发货地点: 1-跨境, 0-本土, 不传的情况下为指定全部 |
| `merchant` | `string` | 否 | 最长 1000 | 店铺名称或用户名称 |
| `pageSize` | `integer` | 否 | 默认 `1000` | 每一页的商品数(范围1-1000) |
| `priceMax` | `number` | 否 |  | 商品总价结束值 |
| `priceMin` | `number` | 否 |  | 商品总价起始值 |
| `ratingMax` | `number` | 否 |  | 商品评分最大值 |
| `ratingMin` | `number` | 否 |  | 商品评分最小值 |
| `isHotSales` | `integer` | 否 |  | 商品是否热销: 0-非热销, 1-热销 |
| `paymentEnd` | `number` | 否 |  | 前30天销售金额结束值 |
| `ratingsMax` | `integer` | 否 |  | ratings数结束值 |
| `ratingsMin` | `integer` | 否 |  | ratings数起始值 |
| `shopIdList` | `string` | 否 | 最长 1000 | 商品店铺id列表, 可指定多个id，多个id使用逗号隔开 |
| `favoriteMax` | `integer` | 否 |  | favorite数结束值 |
| `favoriteMin` | `integer` | 否 |  | favorite数起始值 |
| `keywordType` | `integer` | 否 | 默认 `1`；示例：`1`, `2`, `3` | 商品标题查询类型: 1-整句语句(默认), 2-多个搜索词"与"关系, 3-多个搜索词"或"关系 |
| `orderByType` | `string` | 否 | 默认 `"DESC"`；最长 1000；示例：`ASC`, `DESC` | 排序类型: ASC-升序, DESC-降序 |
| `statTimeEnd` | `string` | 否 | 格式 `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | 统计时间结束值(格式:YYYY-MM-DD HH:mm:ss,如 2024-01-01 12:12:12) |
| `paymentStart` | `number` | 否 |  | 前30天销售金额起始值 |
| `shopLocation` | `string` | 否 | 最长 1000 | 店铺所在地 |
| `skuNumberEnd` | `integer` | 否 |  | Sku总数结束值 |
| `listingDateTo` | `string` | 否 | 最长 1000 | 商品上架时间结束值(格式:年-月-日) |
| `statTimeStart` | `string` | 否 | 格式 `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | 统计时间起始值(格式:YYYY-MM-DD HH:mm:ss,如 2024-01-01 12:12:12) |
| `isOfficialShop` | `integer` | 否 |  | 商品所属店铺是否官方店铺: 0-否, 1-是 |
| `skuNumberStart` | `integer` | 否 |  | Sku总数起始值 |
| `approvedDateEnd` | `string` | 否 | 最长 1000 | 店铺开张时间结束值(格式:年-月-日) |
| `estimateSoldEnd` | `integer` | 否 |  | 估算前30天销售件数结束值 |
| `lastModiTimeEnd` | `string` | 否 | 最长 1000 | 最新抓取时间结束值(格式:年-月-日) |
| `listingDateFrom` | `string` | 否 | 最长 1000 | 商品上架时间起始值(格式:年-月-日) |
| `notExistKeyword` | `string` | 否 | 最长 1000 | 商品不包含标题 |
| `isShopeeVerified` | `integer` | 否 | 示例：`0`, `1` | 虾皮优选: 0-非优选, 1-优选, 不传的情况下为指定全部 |
| `shippingIconType` | `integer` | 否 | 示例：`1`, `0` | 店铺所在地: 1-海外, 0-本地, 不传的情况下为指定全部 |
| `approvedDateStart` | `string` | 否 | 最长 1000 | 店铺开张时间起始值(格式:年-月-日) |
| `estimateSoldStart` | `integer` | 否 |  | 估算前30天销售件数起始值 |
| `historicalSoldEnd` | `integer` | 否 |  | 商品总销售件数结束值 |
| `lastModiTimeStart` | `string` | 否 | 最长 1000 | 最新抓取时间起始值(格式:年-月-日) |
| `notExistShopIdList` | `string` | 否 | 最长 1000 | 商品不包含的店铺id列表, 可指定多个id，多个id使用逗号隔开 |
| `historicalSoldStart` | `integer` | 否 |  | 商品总销售件数起始值 |
| `notExistKeywordType` | `integer` | 否 | 默认 `1` | 商品不包含标题查询类型: 1-整句语句(默认), 2-多个搜索词"与"关系, 3-多个搜索词"或"关系 |


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
    "name": "/youying/shopee/getProductInfos",
    "arguments": {
      "station": "malaysia",
      "page": 1,
      "pageSize": 1000
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 记录数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `products` | `array<object>` | 否 |  | 商品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `totalSize` | `integer` | 否 |  | 总结果数 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：shopee |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `cid` | `string` | 否 |  | 商品归属的类目ID(由一级至子类，多个以逗号分隔) |
| `pid` | `string` | 否 |  | 商品唯一ID |
| `sold` | `integer` | 否 |  | 商品前30天销售件数 |
| `price` | `number` | 否 |  | 商品默认价 |
| `stock` | `integer` | 否 |  | 库存数 |
| `title` | `string` | 否 |  | 商品标题 |
| `rating` | `number` | 否 |  | 商品评分 |
| `shopId` | `string` | 否 |  | 商品所属店铺id |
| `status` | `integer` | 否 |  | 商品状态: 1-正常, 0-下架, 8-列表中排除 |
| `genTime` | `string` | 否 |  | 商品上架时间 |
| `payment` | `number` | 否 |  | 商品前30天销售额 |
| `ratings` | `integer` | 否 |  | 商品评分数 |
| `shopUrl` | `string` | 否 |  | shopee店铺链接 |
| `cbOption` | `integer` | 否 |  | 发货地点: 1-跨境, 0-本土 |
| `currency` | `string` | 否 |  | 货币单位 |
| `favorite` | `integer` | 否 |  | 商品喜欢人数 |
| `imageUrl` | `string` | 否 |  | 商品主图 |
| `maxPrice` | `number` | 否 |  | 商品最高价 |
| `minPrice` | `number` | 否 |  | 商品最低价 |
| `notExist` | `integer` | 否 |  | 商品是否存在: 0-存在, 1-不存在 |
| `shopName` | `string` | 否 |  | 店铺名称 |
| `statTime` | `string` | 否 |  | 商品统计时间 |
| `userName` | `string` | 否 |  | 店主名称 |
| `skuNumber` | `integer` | 否 |  | sku数量 |
| `viewCount` | `integer` | 否 |  | 商品浏览数 |
| `isHotSales` | `integer` | 否 |  | 商品是否热销(预留字段) |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：shopee |
| `description` | `string` | 否 |  | 商品描述 |
| `approvedDate` | `string` | 否 |  | 店铺开张时间 |
| `estimateSold` | `integer` | 否 |  | 估算前30天销售件数 |
| `lastModiTime` | `string` | 否 |  | 商品最新抓取时间 |
| `shopLocation` | `string` | 否 |  | 店铺所在地 |
| `totalSaleCnt` | `integer` | 否 |  | 商品总销售件数 |
| `estimatedDays` | `integer` | 否 |  | 商品预计到货时间 |
| `isOfficialShop` | `integer` | 否 |  | 商品所属店铺是否官方店铺 |
| `productPageUrl` | `string` | 否 |  | shopee商品链接 |
| `isShopeeVerified` | `integer` | 否 |  | 商品是否虾皮优选 |
| `shippingIconType` | `integer` | 否 |  | 店铺所在地: 0-本地, 1-海外, 3或null-未知 |
| `categoryStructure` | `string` | 否 |  | 商品所属的类目结构 |
| `shopProductsCount` | `integer` | 否 |  | 店铺商品总数 |

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
