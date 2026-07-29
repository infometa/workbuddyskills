---
name: linkfox-sellersprite-market-research
description: 使用卖家精灵选市场列表能力，基于类目维度筛选亚马逊细分市场，支持市场规模、竞争度、头部集中度、卖家结构、新品占比、价格/评分/毛利区间等大量条件，用于发现可进入市场与评估选品方向。当用户提到亚马逊市场调研、细分类目研究、市场机会筛选、市场集中度分析、新品机会、选市场、SellerSprite market research、category market research时触发此技能。即使用户未明确提及"卖家精灵"，只要需求是按类目维度筛选和评估亚马逊市场，也应触发此技能。
---

# 卖家精灵-选市场列表

## 基本信息

- **业务工具名**：`/sellersprite/market/research`
- **所属分组**：卖家精灵 · 亚马逊选品
- **功能说明**：支持按亚马逊站点、类目关键字路径、平均价格、月均销售额、卖家数量、FBA占比、Amazon自营占比、商品集中度、卖家集中度、退货率、新品数据等多维度条件筛选亚马逊类目市场，返回各类目的平均价格、月均销售额、月总销售额、平均评分、FBA占比、退货率、卖家归属地等核心市场指标，帮助卖家发现高潜力蓝海市场和选品机会。
- **关键词**：卖家精灵, 选市场, 市场调研, 类目筛选, 蓝海市场, FBA占比, 市场机会, 选品决策, 竞争分析, 类目市场


## 何时使用

当用户意图与“卖家精灵-选市场列表”匹配，或需要以下能力时使用本工具：支持按亚马逊站点、类目关键字路径、平均价格、月均销售额、卖家数量、FBA占比、Amazon自营占比、商品集中度、卖家集中度、退货率、新品数据等多维度条件筛选亚马逊类目市场，返回各类目的平均价格、月均销售额、月总销售额、平均评分、FBA占比、退货率、卖家归属地等核心市场指标，帮助卖家发现高潜力蓝海市场和选品机会。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1` | 页码，从1开始 |
| `size` | `integer` | 否 | 默认 `50`；最小 1；最大 200 | 每页条数，默认50，最大200 |
| `month` | `string` | 否 | 格式 `^(nearly\|(19\|20)\d{2}(0[1-9]\|1[0-2]))$`；示例：`nearly`, `202507` | 筛选日期。支持两种写法：① nearly — 最近30天；② yyyyMM — 查询具体月份（如 202507），最多支持当前月往前共24个月内的月份 |
| `topNum` | `integer` | 否 | 默认 `10` | 头部Listing数量 |
| `maxAvgBsr` | `integer` | 否 |  | 最高平均BSR排名 |
| `maxBrands` | `integer` | 否 |  | 最大品牌数量 |
| `maxVolume` | `number` | 否 |  | 最高体积 |
| `maxWeight` | `number` | 否 |  | 最高重量 |
| `minAvgBsr` | `integer` | 否 |  | 最低平均BSR排名 |
| `minBrands` | `integer` | 否 |  | 最小品牌数量 |
| `minVolume` | `number` | 否 |  | 最低体积 |
| `minWeight` | `number` | 否 |  | 最低重量 |
| `orderDesc` | `boolean` | 否 | 默认 `true` | 排序是否降序，true降序 false升序，默认true |
| `maxSellers` | `integer` | 否 |  | 最大卖家数量 |
| `minSellers` | `integer` | 否 |  | 最小卖家数量 |
| `newProduct` | `integer` | 否 | 默认 `3` | 新品定义(月) |
| `nodeIdPath` | `string` | 否 | 最长 1000 | 类目节点ID路径，如 172282:281407 |
| `orderField` | `string` | 否 | 最长 1000；示例：`total_units`, `total_amount`, `bsr_rank`, `price`, `rating`, `reviews`, `profit`, `reviews_rate` | 排序字段(order.field)，对应表1.6。可选：total_units-月销量；total_amount-月销售额；bsr_rank-bsr排名；price-价格；rating-评分；reviews-评分数；profit-毛利率；reviews_rate-留评率；available_date-上架时间；questions-Q&A；total_units_growth-月销量增长率；total_amount_growth-月销售额增长率；reviews_increasement-月新增评分数；bsr_rank_cv-近7天BSR增长数；bsr_rank_cr-近7天BSR增长率；amz_unit-子体销量 |
| `marketplace` | `string` | 是 | 默认 `"US"`；最长 1000；示例：`US`, `JP`, `UK`, `DE`, `FR`, `IT`, `ES`, `CA` | 站点编码(marketplace)。可选：US-美国站-USD($)；JP-日本站-JPY(￥)；UK-英国站-GBP(£)；DE-德国站-EUR(€)；FR-法国站-EUR(€)；IT-意大利站-EUR(€)；ES-西班牙站-EUR(€)；CA-加拿大站-C$($)；IN-印度站-INR(₹) |
| `maxAvgPrice` | `number` | 否 |  | 最高平均价格 |
| `maxAvgUnits` | `integer` | 否 |  | 最高月均销量 |
| `maxBrandCrn` | `number` | 否 |  | 最大品牌集中度（输入 N 表示 N%，取值范围 0–100） |
| `maxGoodsCrn` | `number` | 否 |  | 最大商品集中度（输入 N 表示 N%，取值范围 0–100） |
| `maxNewCount` | `integer` | 否 |  | 最大新品数量 |
| `minAvgPrice` | `number` | 否 |  | 最低平均价格 |
| `minAvgUnits` | `integer` | 否 |  | 最低月均销量 |
| `minBrandCrn` | `number` | 否 |  | 最小品牌集中度（输入 N 表示 N%，取值范围 0–100） |
| `minGoodsCrn` | `number` | 否 |  | 最小商品集中度（输入 N 表示 N%，取值范围 0–100） |
| `minNewCount` | `integer` | 否 |  | 最小新品数量 |
| `maxAvgProfit` | `number` | 否 |  | 最高平均毛利率（输入 N 表示 N%，取值范围 0–100） |
| `maxAvgRating` | `number` | 否 |  | 最高平均评分值 |
| `maxSellerCrn` | `number` | 否 |  | 最大卖家集中度（输入 N 表示 N%，取值范围 0–100） |
| `maxTopAvgBsr` | `integer` | 否 |  | 最高头部平均BSR |
| `minAvgProfit` | `number` | 否 |  | 最低平均毛利率（输入 N 表示 N%，取值范围 0–100） |
| `minAvgRating` | `number` | 否 |  | 最低平均评分值 |
| `minSellerCrn` | `number` | 否 |  | 最小卖家集中度（输入 N 表示 N%，取值范围 0–100） |
| `minTopAvgBsr` | `integer` | 否 |  | 最低头部平均BSR |
| `maxAvgRatings` | `integer` | 否 |  | 最高平均评分数 |
| `maxAvgRevenue` | `number` | 否 |  | 最高月均销售额 |
| `maxAvgSellers` | `number` | 否 |  | 最大平均卖家数量 |
| `maxGoodsCount` | `integer` | 否 |  | 最高商品数量 |
| `minAvgRatings` | `integer` | 否 |  | 最低平均评分数 |
| `minAvgRevenue` | `number` | 否 |  | 最低月均销售额 |
| `minAvgSellers` | `number` | 否 |  | 最小平均卖家数量 |
| `minGoodsCount` | `integer` | 否 |  | 最低商品数量 |
| `maxNewAvgPrice` | `number` | 否 |  | 最大新品平均价格 |
| `maxNewAvgUnits` | `number` | 否 |  | 最高新品月均销量 |
| `maxTopAvgUnits` | `integer` | 否 |  | 最高头部月均销量 |
| `minNewAvgPrice` | `number` | 否 |  | 最小新品平均价格 |
| `minNewAvgUnits` | `number` | 否 |  | 最低新品月均销量 |
| `minTopAvgUnits` | `integer` | 否 |  | 最低头部月均销量 |
| `sellerLocation` | `string` | 否 | 最长 1000；示例：`US,GB` | 卖家所属地，多个用英文逗号分隔，见卖家精灵表1.3 |
| `maxNewAvgRating` | `number` | 否 |  | 最大新品平均星级 |
| `minNewAvgRating` | `number` | 否 |  | 最小新品平均星级 |
| `maxEbcProportion` | `number` | 否 |  | 最大A+数量占比（输入 N 表示 N%，取值范围 0–100） |
| `maxFbaProportion` | `number` | 否 |  | 最大FBA占比（输入 N 表示 N%，取值范围 0–100） |
| `maxFbmProportion` | `number` | 否 |  | 最大FBM占比（输入 N 表示 N%，取值范围 0–100） |
| `maxNewAvgRatings` | `integer` | 否 |  | 最大新品平均评分数 |
| `maxNewAvgRevenue` | `number` | 否 |  | 最高新品月均销售额 |
| `maxNewProportion` | `number` | 否 |  | 最大新品数量占比（输入 N 表示 N%，取值范围 0–100） |
| `maxTopAvgRevenue` | `number` | 否 |  | 最高头部月均销售额 |
| `minEbcProportion` | `number` | 否 |  | 最小A+数量占比（输入 N 表示 N%，取值范围 0–100） |
| `minFbaProportion` | `number` | 否 |  | 最小FBA占比（输入 N 表示 N%，取值范围 0–100） |
| `minFbmProportion` | `number` | 否 |  | 最小FBM占比（输入 N 表示 N%，取值范围 0–100） |
| `minNewAvgRatings` | `integer` | 否 |  | 最小新品平均评分数 |
| `minNewAvgRevenue` | `number` | 否 |  | 最低新品月均销售额 |
| `minNewProportion` | `number` | 否 |  | 最小新品数量占比（输入 N 表示 N%，取值范围 0–100） |
| `minTopAvgRevenue` | `number` | 否 |  | 最低头部月均销售额 |
| `departmentKeyword` | `string` | 否 | 最长 1000 | 类目关键字路径，如 Electronics:Accessories & Supplies |
| `maxAmazonSelfProportion` | `number` | 否 |  | 最大Amazon自营占比（输入 N 表示 N%，取值范围 0–100） |
| `minAmazonSelfProportion` | `number` | 否 |  | 最小Amazon自营占比（输入 N 表示 N%，取值范围 0–100） |


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
    "name": "/sellersprite/market/research",
    "arguments": {
      "marketplace": "US",
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `data` | `array<object>` | 否 |  | 类目市场列表(对应第三方 data.items) |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总条数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costToken` | `integer` | 否 |  | 消耗token |
| `marketplace` | `string` | 否 |  | 站点编码 |

### 嵌套输出结构：`data`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `avgBsr` | `integer` | 否 |  | 平均BSR |
| `brands` | `integer` | 否 |  | 品牌数量 |
| `nodeId` | `string` | 否 |  | 节点ID |
| `ranking` | `integer` | 否 |  | 排名 |
| `sellers` | `integer` | 否 |  | 卖家数量 |
| `avgPrice` | `number` | 否 |  | 平均价格 |
| `avgUnits` | `integer` | 否 |  | 月均销量 |
| `currency` | `string` | 否 |  | 该市场的货币类型 |
| `avgProfit` | `number` | 否 |  | 平均利润率(%) |
| `avgRating` | `number` | 否 |  | 平均评分值 |
| `avgVolume` | `number` | 否 |  | 平均体积(in³) |
| `avgWeight` | `number` | 否 |  | 平均重量(pound) |
| `avgRatings` | `integer` | 否 |  | 平均评分数 |
| `avgRevenue` | `number` | 否 |  | 月均销售额 |
| `avgSellers` | `number` | 否 |  | 平均卖家数 |
| `nodeIdPath` | `string` | 否 |  | 节点ID路径 |
| `totalUnits` | `integer` | 否 |  | 月总销量 |
| `marketplace` | `string` | 否 |  | 市场标志 |
| `returnRatio` | `number` | 否 |  | 退货率(%) |
| `top10Images` | `array<object>` | 否 |  | 前10商品图片 |
| `topProducts` | `integer` | 否 |  | 样本数量 |
| `sellerNation` | `string` | 否 |  | 最多卖家归属地 code |
| `totalRevenue` | `number` | 否 |  | 月总销售额 |
| `baseAvgVolume` | `number` | 否 |  | 平均体积(cm³) |
| `baseAvgWeight` | `number` | 否 |  | 平均重量(g) |
| `ebcProportion` | `number` | 否 |  | A+商品占比(%) |
| `fbaProportion` | `number` | 否 |  | FBA占比(%) |
| `fbmProportion` | `number` | 否 |  | FBM占比(%) |
| `nodeLabelName` | `string` | 否 |  | 节点名称 |
| `nodeLabelPath` | `string` | 否 |  | 节点名称路径 |
| `totalProducts` | `integer` | 否 |  | 商品总数 |
| `avgReturnRatio` | `number` | 否 |  | 退货率类目平均值(%) |
| `nodeLabelLocale` | `string` | 否 |  | 节点名称翻译 |
| `sellerProportion` | `number` | 否 |  | 最多卖家归属地占比(%) |
| `sellerNationLabel` | `string` | 否 |  | 最多卖家归属地 label |
| `nodeLabelPathLocale` | `string` | 否 |  | 节点名称路径翻译 |
| `amazonSelfProportion` | `number` | 否 |  | Amazon自营占比(%) |
| `searchToPurchaseRatio` | `number` | 否 |  | 搜索购买比(千分比) |

### 嵌套输出结构：`data.top10Images`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `image` | `string` | 否 |  | 图片链接 |

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
