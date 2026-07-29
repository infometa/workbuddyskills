---
name: linkfox-keepa-product-search
description: 基于Keepa数据的亚马逊高级商品搜索与筛选，支持品类、价格、月销量、关键词、BSR排名、评论数、评分、包装尺寸、重量、配送方式等多维度条件。当用户提到Keepa选品、亚马逊商品查找、高级选品、BSR筛选、按销售排名选品、月销量过滤、关键词选品、品类选品、竞品筛选、小众商品发掘、历史排名筛选、Keepa product selection, advanced product selection, BSR filtering, sales filtering, category search, competitor screening, historical data filtering, Amazon product selection时触发此技能。即使用户未明确提及"Keepa"，只要其需求涉及多条件亚马逊商品搜索、按销售指标筛选商品或超越简单关键词搜索的高级选品，也应触发此技能。
---

# Keepa-亚马逊-商品搜索

## 基本信息

- **业务工具名**：`/keepa/productSearch`
- **所属分组**：Keepa · 亚马逊商品与价格历史
- **功能说明**：支持按类目名称、价格、月销量、关键词（正向关键词、反向关键词）、商品排名BSR 等参数来 筛选 亚马逊商品，返回亚马逊商品列表页的数据：价格、商品标题、主图、上架时间、材质、重量、子体月销量、最近12个月的每个月月销量等
- **关键词**：Keepa,product find,product Search, 商品搜索 ,搜索 ,高级选品, 历史数据筛选, BSR ,best seller,关键词，销量，历史,销售排名


## 何时使用

当用户意图与“Keepa-亚马逊-商品搜索”匹配，或需要以下能力时使用本工具：支持按类目名称、价格、月销量、关键词（正向关键词、反向关键词）、商品排名BSR 等参数来 筛选 亚马逊商品，返回亚马逊商品列表页的数据：价格、商品标题、主图、上架时间、材质、重量、子体月销量、最近12个月的每个月月销量等

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1`；示例：`1`, `2` | 页码（从1开始） |
| `size` | `array<string>` | 否 | 最多 1000 项；示例：`["large", "XL"]` | 尺码(OR匹配)，筛选指定尺码的产品 |
| `sort` | `array<object>` | 否 | 最多 1000 项 | 排序(最多3)：对象数组；每项包含 fieldName 与 sortDirection |
| `brand` | `array<string>` | 否 | 最多 1000 项；示例：`["Canon"]`, `["Apple", "Samsung"]` | 品牌(OR匹配) |
| `color` | `array<string>` | 否 | 最多 1000 项；示例：`["black", "red"]` | 颜色(OR匹配)，筛选指定颜色的产品 |
| `domain` | `string` | 是 | 格式 `1\|2\|3\|4\|5\|6\|8\|9\|10\|11`；示例：`1`, `2`, `3`, `4`, `5`, `6`, `8`, `9` | Amazon域名ID |
| `rating` | `integer` | 否 | 默认 `1`；示例：`0`, `1` | 是否获取评分信息（默认 1 获取，0 不获取） |
| `history` | `integer` | 否 | 默认 `0`；示例：`1`, `0` | 返回值是否包含历史数据,历史销量 |
| `keyword` | `string` | 否 | 最长 1000；示例：`Digital Camera Canon`, `"Digital Camera" Canon`, `-digital camera` | 标题关键词(大小写不敏感；空格表示分词AND；关键词本身包含空格时用双引号包裹；支持前缀-排除；如果含有 & 符号会被替换为空格；最多50个关键词) |
| `perPage` | `integer` | 否 | 默认 `50`；最小 50；最大 100；示例：`50`, `100` | 每页返回的最大结果数（默认50，最小50，最大100） |
| `isHazMat` | `boolean` | 否 | 示例：`true`, `false` | 是否为危险品 |
| `srAvgGte` | `integer` | 否 | 示例：`1`, `100` | 历史销售排名-最低值（from，正整数，数值越小排名越好） |
| `srAvgLte` | `integer` | 否 | 示例：`1000`, `10000` | 历史销售排名-最高值（to，正整数，数值越小排名越好） |
| `srAvgMonth` | `string` | 否 | 格式 `^\d{6}$`；示例：`202511`, `202401`, `202312` | 历史销售排名-选择月份（格式：YYYYMM，如202511表示2025年11月，最近36个月内） |
| `buyBoxIsFBA` | `boolean` | 否 | 示例：`true`, `false` | 购买按钮是否为FBA |
| `productType` | `array<integer>` | 否 | 最多 1000 项；示例：`[0,1,2]`, `[0]`, `[0,5]` | 产品类型筛选（默认[0,1,2]）：0=标准产品(所有数据可用)，1=可下载产品(无市场/第三方价格数据)，2=电子书(无市场报价数据)，5=变体父ASIN(仅销售排名和变体CSV) |
| `rootCategory` | `array<integer>` | 否 | 最多 1000 项；示例：`[3167641]`, `[562066, 493964]` | 根类目ID(最多50)，仅包含列在这些根类别中的产品 |
| `avg90SalesGte` | `integer` | 否 |  | 90天平均销售排名-最低 |
| `avg90SalesLte` | `integer` | 否 |  | 90天平均销售排名-最高 |
| `currentNewGte` | `integer` | 否 | 示例：`500` | 当前新品价格-最低（最小货币单位） |
| `currentNewLte` | `integer` | 否 | 示例：`10000` | 当前新品价格-最高（最小货币单位） |
| `buyBoxIsAmazon` | `boolean` | 否 | 示例：`true`, `false` | 购买按钮卖家是否为亚马逊 |
| `monthlySoldGte` | `integer` | 否 | 示例：`1000` | 销量/月销量-最低 |
| `monthlySoldLte` | `integer` | 否 | 示例：`10000` | 销量/月销量-最高 |
| `currentSalesGte` | `integer` | 否 | 示例：`100` | 当前销售排名-最低（数值越小排名越好） |
| `currentSalesLte` | `integer` | 否 | 示例：`1000` | 当前销售排名-最高（数值越小排名越好） |
| `packageWidthGte` | `integer` | 否 | 示例：`50` | 包装宽度-最小（毫米） |
| `packageWidthLte` | `integer` | 否 | 示例：`200` | 包装宽度-最大（毫米） |
| `singleVariation` | `boolean` | 否 | 示例：`true` | 仅返回一个变体，当设为true时，多变体产品只返回一个变体 |
| `availableDateGte` | `string` | 否 | 最长 1000；示例：`2024-01-01` | 产品上架时间-最早（日期格式：yyyy-MM-dd） |
| `availableDateLte` | `string` | 否 | 最长 1000；示例：`2024-01-01` | 产品上架时间-最晚（日期格式：yyyy-MM-dd） |
| `currentRatingGte` | `number` | 否 | 示例：`4.0`, `4.5` | 当前评分-最低（0.0-5.0，如4.0星） |
| `currentRatingLte` | `number` | 否 | 示例：`5.0`, `4.5` | 当前评分-最高（0.0-5.0，如4.5星） |
| `packageHeightGte` | `integer` | 否 | 示例：`30` | 包装高度-最小（毫米） |
| `packageHeightLte` | `integer` | 否 | 示例：`150` | 包装高度-最大（毫米） |
| `packageLengthGte` | `integer` | 否 | 示例：`100` | 包装长度-最小（毫米） |
| `packageLengthLte` | `integer` | 否 | 示例：`300` | 包装长度-最大（毫米） |
| `packageWeightGte` | `integer` | 否 | 示例：`100` | 包装重量-最小（克） |
| `packageWeightLte` | `integer` | 否 | 示例：`1500` | 包装重量-最大（克） |
| `categoriesExclude` | `array<integer>` | 否 | 最多 1000 项；示例：`[77028031,186606]` | 排除的子类目ID(最多50) |
| `categoriesInclude` | `array<integer>` | 否 | 最多 1000 项；示例：`[3010075031,12950651,355007011]` | 仅包含的子类目ID(最多50)，仅包含直接列在这些子类别中的产品 |
| `rootCategoryNames` | `array<string>` | 否 | 最多 1000 项；示例：`["Electronics"]`, `["Home & Kitchen", "Sports & Outdoors"]` | 根类目名称(最多50)，当rootCategory为空时使用，系统会自动查找对应的类目ID |
| `variationCountGte` | `integer` | 否 | 示例：`2` | 变体数量-最低 |
| `variationCountLte` | `integer` | 否 | 示例：`10` | 变体数量-最高 |
| `currentCountNewGte` | `integer` | 否 | 示例：`5` | 当前新品报价数量-最低 |
| `currentCountNewLte` | `integer` | 否 | 示例：`50` | 当前新品报价数量-最高 |
| `categoriesExcludeNames` | `array<string>` | 否 | 最多 1000 项；示例：`["Books"]`, `["Clothing, Shoes & Jewelry›Novelty & More›Clothing›Novelty›Women›Tops & Tees›T-Shirts"]` | 排除的子类目名称(最多50)，当categoriesExclude为空时使用，系统会自动查找对应的类目ID。支持传入完整类目路径（如 'Clothing, Shoes & Jewelry›Novelty & More...' 或 'Clothing, Shoes & Jewelry:Novelty & More...'），此时将包含根类目在内进行转换，结果更准确。 |
| `categoriesIncludeNames` | `array<string>` | 否 | 最多 1000 项；示例：`["Camera & Photo"]`, `["Clothing, Shoes & Jewelry›Novelty & More›Clothing›Novelty›Women›Tops & Tees›T-Shirts"]` | 包含的子类目名称(最多50)，当categoriesInclude为空时使用，系统会自动查找对应的类目ID。支持传入完整类目路径（如 'Clothing, Shoes & Jewelry›Novelty & More...' 或 'Clothing, Shoes & Jewelry:Novelty & More...'），此时将包含根类目在内进行转换，结果更准确。 |
| `currentCountReviewsGte` | `integer` | 否 | 示例：`100` | 当前评论数量-最低 |
| `currentCountReviewsLte` | `integer` | 否 | 示例：`10000` | 当前评论数量-最高 |
| `deltaPercent90SalesGte` | `integer` | 否 |  | 90天销售排名变化百分比-最低 |
| `deltaPercent90SalesLte` | `integer` | 否 |  | 90天销售排名变化百分比-最高 |
| `currentBuyBoxShippingGte` | `integer` | 否 | 示例：`1000` | 当前购买按钮含运费价格-最低（最小货币单位） |
| `currentBuyBoxShippingLte` | `integer` | 否 | 示例：`5000` | 当前购买按钮含运费价格-最高（最小货币单位） |
| `outOfStockPercentage90Gte` | `integer` | 否 | 示例：`10` | 90天缺货百分比-最低 |
| `outOfStockPercentage90Lte` | `integer` | 否 | 示例：`25` | 90天缺货百分比-最高 |

### 嵌套输入结构：`sort`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `fieldName` | `string` | 是 | 格式 `availableDate\|currentSales\|monthlySold\|currentRating\|currentCountReviews\|currentBuyBoxShipping\|currentNew`；示例：`currentSales`, `monthlySold`, `availableDate`, `currentRating`, `currentCountReviews`, `currentBuyBoxShipping`, `currentNew` | 排序字段名（驼峰格式），只允许以下值：listedSince(上架时间)、currentSales(当前销售排名)、monthlySold(销量/月销量)、currentRating(当前评分)、currentCountReviews(当前评论数)、currentBuyBoxShipping(当前购买按钮含运费价格)、currentAmazon(当前亚马逊自营价格)、currentNew(当前新品价格) |
| `sortDirection` | `string` | 是 | 格式 `asc\|desc`；示例：`asc`, `desc` | 排序方向：asc=升序，desc=降序 |

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
    "name": "/keepa/productSearch",
    "arguments": {
      "domain": "1",
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总行数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `perPage` | `integer` | 否 |  | 每页数量 |
| `products` | `array<object>` | 否 |  | 商品列表 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `sourceType` | `string` | 否 |  | 来源类型：keepa |
| `totalCount` | `integer` | 否 |  | 总数量 |
| `currentPage` | `integer` | 否 |  | 当前页码 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `brand` | `string` | 否 |  | 品牌 |
| `color` | `string` | 否 |  | 颜色 |
| `model` | `string` | 否 |  | 型号 |
| `price` | `number` | 否 |  | 当前价格（单位：元，如美元/欧元等） |
| `title` | `string` | 否 |  | 商品标题 |
| `profit` | `number` | 否 |  | 利润率（百分比，如25.5表示25.5%） |
| `rating` | `number` | 否 |  | 当前评分（0.0-5.0，如4.5星） |
| `weight` | `string` | 否 |  | 重量（克） |
| `asinUrl` | `string` | 否 |  | 亚马逊asin的详情网址 |
| `fbaFees` | `number` | 否 |  | FBA配送费（单位：元） |
| `ratings` | `integer` | 否 |  | 评分数量 |
| `urlSlug` | `string` | 否 |  | URL Slug |
| `currency` | `string` | 否 |  | 币种 |
| `imageUrl` | `string` | 否 |  | 图片URL（完整URL） |
| `isHazmat` | `boolean` | 否 |  | 是否为危险品 |
| `material` | `string` | 否 |  | 产品的材质，指其构造中使用的主要材料 |
| `dimension` | `string` | 否 |  | 尺寸 |
| `itemWidth` | `integer` | 否 |  | 商品宽度，单位为毫米，不可用时为0或-1。示例: 100 |
| `salesRank` | `integer` | 否 |  | 销售排名 |
| `sellerNum` | `integer` | 否 |  | 卖家数 |
| `itemHeight` | `integer` | 否 |  | 商品高度，单位为毫米，不可用时为0或-1。示例: 100 |
| `itemLength` | `integer` | 否 |  | 商品长度，单位为毫米，不可用时为0或-1。示例: 100 |
| `lastUpdate` | `string` | 否 |  | 最后更新时间（yyyy-MM-dd HH:mm:ss） |
| `parentAsin` | `string` | 否 |  | 父ASIN |
| `primePrice` | `number` | 否 |  | prime价格 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型：keepa |
| `fulfillment` | `string` | 否 |  | 配送方式(AMZ,FBA,FBM) |
| `reviewCount` | `integer` | 否 |  | 评论数量 |
| `salesRank30` | `integer` | 否 |  | 近30天平均销售排名 |
| `salesRank90` | `integer` | 否 |  | 近90天平均销售排名 |
| `categoryTree` | `string` | 否 |  | 类目树 |
| `manufacturer` | `string` | 否 |  | 制造商 |
| `packageWidth` | `integer` | 否 |  | 包装宽度（毫米） |
| `rootCategory` | `integer` | 否 |  | 根类目ID |
| `salesRank180` | `integer` | 否 |  | 近180天平均销售排名 |
| `variationNum` | `integer` | 否 |  | 变体数量 |
| `availableDate` | `string` | 否 |  | 上架时间（yyyy-MM-dd HH:mm:ss） |
| `packageHeight` | `integer` | 否 |  | 包装高度（毫米） |
| `packageLength` | `integer` | 否 |  | 包装长度（毫米） |
| `packageWeight` | `string` | 否 |  | 包装重量（克） |
| `subcategories` | `array<object>` | 否 |  | 子类目列表 |
| `buyBoxSellerId` | `string` | 否 |  | 购买按钮卖家ID |
| `categoryTreeId` | `string` | 否 |  | 类目树Id |
| `dimensionsType` | `string` | 否 |  | 尺寸类型 |
| `isAdultProduct` | `boolean` | 否 |  | 是否为成人产品 |
| `packageQuantity` | `integer` | 否 |  | 包装中商品的数量，不可用时为0或-1。示例: 3 |
| `productImageUrls` | `array<any>` | 否 |  | 商品图片列表 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量 |
| `packageDimensions` | `string` | 否 |  | 包装尺寸 |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额 |
| `referralFeePercentage` | `number` | 否 |  | 推荐费百分比 |
| `monthlySalesUnits1MonthAgo` | `integer` | 否 |  | 1月前月销量 |
| `monthlySalesUnits2MonthsAgo` | `integer` | 否 |  | 2月前月销量 |
| `monthlySalesUnits3MonthsAgo` | `integer` | 否 |  | 3月前月销量 |
| `monthlySalesUnits4MonthsAgo` | `integer` | 否 |  | 4月前月销量 |
| `monthlySalesUnits5MonthsAgo` | `integer` | 否 |  | 5月前月销量 |
| `monthlySalesUnits6MonthsAgo` | `integer` | 否 |  | 6月前月销量 |
| `monthlySalesUnits7MonthsAgo` | `integer` | 否 |  | 7月前月销量 |
| `monthlySalesUnits8MonthsAgo` | `integer` | 否 |  | 8月前月销量 |
| `monthlySalesUnits9MonthsAgo` | `integer` | 否 |  | 9月前月销量 |
| `monthlySalesUnits10MonthsAgo` | `integer` | 否 |  | 10月前月销量 |
| `monthlySalesUnits11MonthsAgo` | `integer` | 否 |  | 11月前月销量 |
| `monthlySalesUnits12MonthsAgo` | `integer` | 否 |  | 12月前月销量 |

### 嵌套输出结构：`products.subcategories`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `code` | `string` | 否 |  | 类目ID |
| `rank` | `integer` | 否 |  | 排名 |
| `label` | `string` | 否 |  | 类目名称 |

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
