---
name: linkfox-sorftime-amazon-product-query
description: 基于Sorftime数据的亚马逊多维度产品搜索与筛选，涵盖14个站点，支持历史月份快照回看。当用户提到Sorftime产品搜索、亚马逊产品筛选、竞品调研、类目分析、品牌热销、卖家分析、季节性产品、历史快照回看、产品搜索、月销量月销额、ABA关键词找产品、价格范围筛选、新品发现、多条件组合筛选、product search, competitor research, category analysis, brand bestsellers, seller analysis, seasonal products, historical snapshot时触发此技能。即使用户未明确提及\"Sorftime\"，只要其需求涉及亚马逊产品搜索、筛选、对比或类目/品牌/卖家维度的产品探索，也应触发此技能。
---

# Sorftime-亚马逊产品搜索

## 基本信息

- **业务工具名**：`/sorftime/amazon/productQuery`
- **所属分组**：Sorftime · 亚马逊选品
- **功能说明**：支持多样化检索，基于 ASIN 找同类产品、类目/品牌/卖家追踪、ABA 关键词调研，以及标题/属性关键词匹配。数据涵盖：价格信息（原价、实际售价及 Coupon 政策）、BSR 排名趋势（支持大类及各细分小类排名追踪）、以及历史月度销量与销额。此外，该工具还提供 FBA 配送费/仓储费明细、平台佣金、产品毛利及毛利率，为定价策略调整、利润空间测算及库存计划提供核心数据支撑。
- **关键词**：Sorftime, 产品筛选, 竞品调研, 类目分析, 历史快照,利润分析,FBA费用分析


## 何时使用

当用户意图与“Sorftime-亚马逊产品搜索”匹配，或需要以下能力时使用本工具：支持多样化检索，基于 ASIN 找同类产品、类目/品牌/卖家追踪、ABA 关键词调研，以及标题/属性关键词匹配。数据涵盖：价格信息（原价、实际售价及 Coupon 政策）、BSR 排名趋势（支持大类及各细分小类排名追踪）、以及历史月度销量与销额。此外，该工具还提供 FBA 配送费/仓储费明细、平台佣金、产品毛利及毛利率，为定价策略调整、利润空间测算及库存计划提供核心数据支撑。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 默认 `1`；最小 1 | 分页页码.每页最多100个产品，默认1 |
| `queryMode` | `integer` | 否 | 默认 `1`；示例：`1`, `2` | 查询方式.1：单条件查询（默认）；2：多条件组合查询（且关系） |
| `queryType` | `integer` | 否 | 示例：`1`, `2`, `3`, `4`, `5`, `6`, `7`, `8` | 查询类型（仅当query=1时生效，query=2时此参数无效）。1:基于ASIN查询同类产品（注意：并非只查该ASIN，查单个产品请用productDetail接口）；2:基于类目(NodeId)查询；3:查询品牌热销产品；4:基于卖家名称查询热销产品；5:基于卖家SellerId查询热销产品；6:基于ABA关键词查热销产品（暂仅支持ABA关键词）；7:基于产品标题或产品属性包含词查产品；8:限定销售价范围查产品，单位为当地货币最小单位（如美分，1999表示$19.99）；9:限定月销量(近30日)范围查产品；10:限定季节性产品，仅返回所查月份的季节性产品；11:限定上架时间范围查产品，日期格式yyyy-MM-dd；12:限定星级范围查产品；13:限定评论数量范围查产品；14:限定排名范围查产品（需组合大小类排名）；15:限定发货方式查产品；16:限定子体数范围查产品 |
| `queryMonth` | `string` | 否 | 格式 `^\d{4}-\d{2}$`；示例：`2025-01` | 回看历史月份产品数据，最长支持2024年1月起最多2年内数据, 选填，格式：yyyy-MM，不指定此参数时表示查实时数据，小于当月月份时为回看数据。AU BR IN暂不支持回看，US GB DE支持"不限"模式回看，其余站点支持Top100产品回看 |
| `queryValue` | `string` | 否 | 最长 1000；示例：`B0CVM8TXHP`, `3743561`, `Anker`, `AnkerDirect`, `A294P4X9EWVXLJ`, `Power Bank`, `1,1000`, `100,1000` | 查询条件值，根据query和queryType不同而格式不同。<br>【当query=1（单条件查询）时】根据queryType传入对应值：<br>queryType=1(ASIN同类): 传入ASIN，如 B0CVM8TXHP<br>queryType=2(类目): 传入NodeId，如 3743561<br>queryType=3(品牌): 传入品牌名，如 Anker<br>queryType=4(卖家名称): 传入卖家店铺名，如 AnkerDirect<br>queryType=5(卖家ID): 传入SellerId，如 A294P4X9EWVXLJ<br>queryType=6(ABA关键词): 传入关键词，如 Power Bank<br>queryType=7(标题/属性包含词): 传入匹配词，如 10,000mAh 30W<br>queryType=8(价格范围): 格式'最低,最高'(单位当地货币最小单位如美分)，如 1,1000 表示1~1000美分；省略一端表示不限，如 ,1000 表示不高于1000美分<br>queryType=9(月销量范围): 格式'最低,最高'，如 100,1000 表示月销量100~1000；,1000 表示不高于1000<br>queryType=10(季节性产品): 传入月份(逗号分隔)，如 1,2,3 表示查询1/2/3月为旺季的季节性产品<br>queryType=11(上架时间范围): 格式'开始日期,结束日期'(yyyy-MM-dd)，如 2024-06-01,2024-12-01；省略结束日期如 2024-06-01, 表示晚于该日期<br>queryType=12(星级范围): 格式'最低,最高'，如 3,5 表示3~5星；4, 表示>=4星<br>queryType=13(评论数范围): 格式'最低,最高'，如 10,500 表示10~500条；,500 表示少于500条<br>queryType=14(排名范围): 格式'大类最低,大类最高;小类最低,小类最高'，如 500,5000;1,100 表示大类排名500~5000且小类排名1~100<br>queryType=15(发货方式): 传入FBA或FBM(逗号分隔)，如 FBA,FBM<br>queryType=16(子体数范围): 格式'最低,最高'，如 1,50 表示子体数1~50<br>【当query=2（多条件组合查询）时】传入JSON数组，每项包含QueryType和Content，如 [{"QueryType":1,"Content":"B0CVM8TXHP"},{"QueryType":8,"Content":"100,500"}] |
| `marketplace` | `string` | 是 | 格式 `us\|gb\|de\|fr\|in\|ca\|jp\|es\|it\|mx\|ae\|au\|br\|sa`；示例：`us`, `gb`, `de`, `fr`, `in`, `ca`, `jp`, `es` | 亚马逊站点代码 |


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
    "name": "/sorftime/amazon/productQuery",
    "arguments": {
      "marketplace": "us",
      "page": 1
    }
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `msg` | `string` | 否 |  | 响应消息 |
| `code` | `integer` | 否 |  | 响应码（200表示成功） |
| `page` | `integer` | 否 |  | 当前页码 |
| `type` | `string` | 否 |  | 渲染的样式 |
| `total` | `integer` | 否 |  | 总数 |
| `columns` | `array<object>` | 否 |  | 渲染的列 |
| `costTime` | `integer` | 否 |  | 接口耗时(毫秒) |
| `products` | `array<object>` | 否 |  | 产品列表 |
| `costToken` | `integer` | 否 |  | 消耗的Token数量 |
| `pageCount` | `integer` | 否 |  | 总页数(最多200页) |
| `requestConsumed` | `integer` | 否 |  | 消耗的请求数 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | ASIN |
| `size` | `array<any>` | 否 |  | 尺寸.外包装[最长边,第二长边,最短边]，单位cm |
| `aPlus` | `boolean` | 否 |  | 有A+ |
| `brand` | `string` | 否 |  | 品牌 |
| `isFBA` | `boolean` | 否 |  | 是否FBA.Buybox卖家是否使用FBA物流 |
| `price` | `number` | 否 |  | 当前价格.未扣Coupon，单位为当地货币(如美元) |
| `title` | `string` | 否 |  | 商品标题 |
| `coupon` | `integer` | 否 |  | Coupon政策.值>0为抵扣金额(如500=$5)，值<0为折扣百分比(如-10=10%折扣) |
| `rating` | `number` | 否 |  | 当前评分（0.0-5.0，如4.8） |
| `weight` | `string` | 否 |  | 重量.单位g |
| `asinUrl` | `string` | 否 |  | 商品链接.亚马逊Listing详情页URL |
| `fbaFees` | `number` | 否 |  | FBA费用.单位为当地货币(如美元) |
| `ratings` | `integer` | 否 |  | 评分数量 |
| `category` | `array<any>` | 否 |  | 大类.[大类名称, NodeId] |
| `hasVideo` | `boolean` | 否 |  | 有视频 |
| `imageUrl` | `string` | 否 |  | 主图 |
| `oldPrice` | `number` | 否 |  | 划线价.单位为当地货币(如美元) |
| `fbaDetail` | `array<any>` | 否 |  | FBA明细.首项为配送费，后续为月份:仓储费，如[475,1-9:5,10-12:15] |
| `salesRank` | `integer` | 否 |  | BSR排名 |
| `sellerNum` | `integer` | 否 |  | 卖家数 |
| `onlineDays` | `integer` | 否 |  | 上架天数 |
| `parentAsin` | `string` | 否 |  | 父ASIN.有子体时为父级ASIN，无子体时为null |
| `profitRate` | `number` | 否 |  | 利润率.例25.83表示25.83% |
| `salesPrice` | `number` | 否 |  | 到手价.扣除Coupon后的实际售价，单位为当地货币(如美元) |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 来源类型 |
| `bsrCategory` | `array<object>` | 否 |  | 小类排名列表 |
| `platformFee` | `number` | 否 |  | 平台佣金.单位为当地货币(如美元) |
| `buyboxSeller` | `string` | 否 |  | Buybox卖家 |
| `profitAmount` | `number` | 否 |  | 利润.到手价-FBA费-佣金，单位为当地货币(如美元) |
| `variationNum` | `integer` | 否 |  | 变体数 |
| `availableDate` | `string` | 否 |  | 上架时间.格式yyyy-MM-dd |
| `hasBrandStore` | `boolean` | 否 |  | 有品牌店 |
| `buyBoxSellerId` | `string` | 否 |  | Buybox卖家ID |
| `productImageUrls` | `array<any>` | 否 |  | 主图列表 |
| `monthlySalesUnits` | `integer` | 否 |  | 月销量.近30日Listing维度不区分子体，推荐用于评估销量，值为-1表示无法预估 |
| `buyboxSellerAddress` | `string` | 否 |  | 卖家所在地.Buybox卖家国籍(二字码如CN、US)，亚马逊自营时为null |
| `listingSalesOfDaily` | `number` | 否 |  | 日销售额.单位为当地货币(如美元)，值为-1表示无法预估 |
| `monthlySalesRevenue` | `number` | 否 |  | 月销售额.预估值，单位为当地货币(如美元)，值为-1表示无法预估 |
| `listingSalesVolumeOfDaily` | `integer` | 否 |  | 日销量.Listing维度不区分子体，值为-1表示无法预估 |

### 嵌套输出结构：`products.bsrCategory`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `date` | `string` | 否 |  | 日期.格式yyyyMMdd |
| `name` | `string` | 否 |  | 类目名称 |
| `rank` | `string` | 否 |  | 排名 |
| `nodeId` | `string` | 否 |  | 节点ID |

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
