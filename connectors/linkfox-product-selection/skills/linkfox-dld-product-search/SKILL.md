---
name: linkfox-dld-product-search
description: 在中国1688批发平台（阿里巴巴国内B2B市场）上搜索和分析商品，用于找货源、供应商发现和选品。当用户提到1688商品搜索、1688找货源、在1688上找供应商、批发商品查询、工厂货源、一件代发供应商搜索、1688关键词选品、批发价格对比、按销量筛选、任何1688平台上的选品调研、1688 search, 1688 product selection, find suppliers, factory lookup, wholesale pricing, supplier search, domestic sourcing, 1688 products时触发此技能。即使用户未明确说"1688"，只要其需求涉及搜索批发商品、寻找国内供应商或从国内市场采购，也应触发此技能。
---

# 店雷达-1688选品库

## 基本信息

- **业务工具名**：`/dld/productSearch`
- **所属分组**：店雷达 · 1688 选品
- **功能说明**：支持1688平台的关键词搜索选品，根据销量和价格筛选优质供应商。
- **关键词**：店雷达, 1688选品, 1688搜索, 找货源, 工厂查询


## 何时使用

当用户意图与“店雷达-1688选品库”匹配，或需要以下能力时使用本工具：支持1688平台的关键词搜索选品，根据销量和价格筛选优质供应商。

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `cycle` | `string` | 否 | 格式 `7\|30`；示例：`7`, `30` | 统计周期 |
| `keyWord` | `string` | 否 | 最长 50 | 搜索关键词(搜索关键词必须是中文，如果不是请先翻译) |
| `endPrice` | `number` | 否 |  | 批发价（结束） |
| `goodsUrl` | `string` | 否 | 最长 1000 | 商品链接地址 |
| `pageSize` | `integer` | 否 | 默认 `20`；最大 100 | 每页返回数量（10-100） |
| `sendTime` | `string` | 否 | 最长 1000；示例：`24`, `48`, `72` | 发货时间（多选），多个使用“,”号隔开，如：24,48 |
| `sortType` | `string` | 否 | 默认 `"desc"`；格式 `desc\|asc`；示例：`desc`, `asc` | 排序类型 |
| `endTpYear` | `integer` | 否 |  | 结束诚信通年限 |
| `offerType` | `integer` | 否 | 示例：`0`, `2`, `3`, `4`, `5`, `6` | 商品标识 0-不限制 2-新品 3-1688严选 4-跨境 5-支持定制 6-镇店之宝 |
| `pageIndex` | `integer` | 否 | 默认 `1` | 页码（从1开始） |
| `shiLiType` | `string` | 否 | 最长 1000；示例：`superFactory`, `Power`, `TrustPass` | 卖家会员类型（多选），多个使用“,”号隔开，如：superFactory,Power |
| `sortField` | `string` | 否 | 默认 `"orderCount30d"`；格式 `orderCount7d\|saleCount7d\|saleVolume7d\|orderCount30d\|saleCount30d\|saleVolume30d\|offerCreateTime\|price\|consignPrice`；示例：`orderCount7d`, `saleCount7d`, `saleVolume7d`, `orderCount30d`, `saleCount30d`, `saleVolume30d`, `offerCreateTime`, `price` | 排序字段 |
| `beginPrice` | `number` | 否 |  | 批发价（起始） |
| `productIds` | `string` | 否 | 最长 1000 | 商品ID 多个顿号隔开，最多20个 |
| `searchType` | `integer` | 否 | 默认 `1`；示例：`1`, `3` | 商品关键词搜索类型 |
| `beginTpYear` | `integer` | 否 |  | 开始诚信通年限 |
| `companyType` | `integer` | 否 | 示例：`0`, `1`, `2` | 公司类型 0-不限 1-店铺 2-工厂 |
| `proxyRights` | `string` | 否 | 最长 1000；示例：`4360897`, `449154` | 代发权益（多选），多个使用“,”号隔开，如：4360897,449154 |
| `shopService` | `string` | 否 | 最长 1000；示例：`4057409`, `888777` | 卖家服务（多选），多个使用“,”号隔开，如：4057409,888777 |
| `endSaleCount` | `integer` | 否 |  | 销售件数（结束） |
| `endOrderCount` | `integer` | 否 |  | 销售笔数（结束） |
| `endSaleVolume` | `number` | 否 |  | 销售额（结束） |
| `beginSaleCount` | `integer` | 否 |  | 销售件数（起始） |
| `beginOrderCount` | `integer` | 否 |  | 销售笔数（起始） |
| `beginSaleVolume` | `number` | 否 |  | 销售额（起始） |
| `endConsignPrice` | `number` | 否 |  | 代发价（结束） |
| `buyerProtections` | `string` | 否 | 最长 1000；示例：`商品包邮`, `7天包退货`, `支持运费险` | 权益保障，多个用“,”隔开。如： |
| `endStartQuantity` | `integer` | 否 |  | 起购数量（结束） |
| `beginConsignPrice` | `number` | 否 |  | 代发价（起始） |
| `faceToFaceSupport` | `string` | 否 | 最长 1000；示例：`441218`, `386434`, `422914`, `422978`, `386370` | 面单支持（多选），多个使用“,”号隔开，如：441218,386434 |
| `beginStartQuantity` | `integer` | 否 |  | 起购数量（起始） |
| `endOfferCreateTime` | `string` | 否 | 格式 `^\d{4}-(0[1-9]\|1[0-2])-(0[1-9]\|[12]\d\|3[01])$` | 上架时间（结束）例如：2025-06-11 |
| `beginOfferCreateTime` | `string` | 否 | 格式 `^\d{4}-(0[1-9]\|1[0-2])-(0[1-9]\|[12]\d\|3[01])$` | 上架时间（起始）例如：2025-06-11 |


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
    "name": "/dld/productSearch",
    "arguments": {
      "pageSize": 20,
      "sortField": "orderCount30d",
      "sortType": "desc"
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

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `asin` | `string` | 否 |  | 商品编号 |
| `unit` | `string` | 否 |  | 单位 |
| `price` | `number` | 否 |  | 批发价 |
| `title` | `string` | 否 |  | 商品标题 |
| `shopId` | `string` | 否 |  | 店铺id |
| `asinUrl` | `string` | 否 |  | 商品链接地址 |
| `company` | `string` | 否 |  | 店铺名称 |
| `offerId` | `string` | 否 |  | 商品id |
| `shopUrl` | `string` | 否 |  | 店铺链接地址 |
| `currency` | `string` | 否 |  | 币种 |
| `dataType` | `string` | 否 |  | 数据类型: weeklyData: 周数据; monthlyData: 月数据 |
| `imageUrl` | `string` | 否 |  | 图片地址 |
| `levelName` | `string` | 否 |  | 类目层级名称 |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 1688 |
| `consignPrice` | `number` | 否 |  | 代发价 |
| `deliveryTime` | `string` | 否 |  | 发货时间 |
| `availableDate` | `string` | 否 | 格式 `date` | 商品上架时间，格式为 yyyy-MM-dd HH:mm:ss |
| `quantityBegin` | `integer` | 否 |  | 起批量 |
| `salesQuantity` | `integer` | 否 |  | 销售件数（按统计周期返回对应的值） |
| `quantityPrices` | `string` | 否 |  | 价格区间 |
| `salesOrderCount` | `integer` | 否 |  | 销售笔数（按统计周期返回对应的值） |
| `estimatedSalesAmount` | `integer` | 否 |  | 预估销售额（按统计周期返回对应的值） |

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
