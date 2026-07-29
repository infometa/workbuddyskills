---
name: linkfox-fastmoss-product-search
description: 基于FastMoss数据搜索和筛选TikTok全球电商商品，支持关键词搜索、多维度筛选（类目、店铺类型、佣金率、销量、达人数等）和排序。当用户提到TikTok选品、TikTok商品搜索、TikTok产品数据、TikTok达人带货、TikTok佣金率、TikTok爆款追踪、TikTok GMV分析、TikTok product search, TikTok product research, TikTok creator sales, TikTok commission rate, TikTok GMV analysis, FastMoss时触发此技能。即使用户未明确提及"FastMoss"，只要其需求涉及在TikTok平台搜索商品数据或分析商品表现，也应触发此技能。
---

# FastMoss-TikTok商品搜索

## 基本信息

- **业务工具名**：`/fastmoss/productSearch`
- **所属分组**：FastMoss · TikTok 选品
- **功能说明**：基于 TikTok 全球电商数据，通过关键词检索商品信息。该工具是挖掘 TikTok 爆款、分析竞品表现的核心入口，涵盖以下核心维度：
- **关键词**：FastMoss, TikTok 选品, 商品搜索, 达人带货量, 佣金率, TikTok GMV, 爆款追踪, 电商大数据


## 何时使用

当用户意图与“FastMoss-TikTok商品搜索”匹配，或需要以下能力时使用本工具：基于 TikTok 全球电商数据，通过关键词检索商品信息。该工具是挖掘 TikTok 爆款、分析竞品表现的核心入口，涵盖以下核心维度：

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 示例：`1` | 页码，默认1 |
| `region` | `string` | 否 | 最长 1000；示例：`US`, `GB`, `ID`, `VN`, `MY`, `TH`, `PH`, `MX` | 国家/地区代码,支持如下国家：['US','GB','MX','ES','DE','IT','FR','ID','VN','MY','TH','PH','BR','JP','SG'] |
| `isSshop` | `boolean` | 否 | 示例：`true` | 是否全托管商品（TikTok S店=全托管商品） |
| `keyword` | `string` | 否 | 最长 1000；示例：`phone case`, `LED light` | 搜索关键词（商品标题模糊匹配） |
| `category` | `string` | 否 | 最长 1000；示例：`Phone Cases`, `LED Light` | 类目名称（文本，用于匹配 TikTok 英文类目并解析为类目 ID）。TikTok 类目为英文,若用户输入非英语，请先在对话侧译为英语再传入本参数。 |
| `pageSize` | `integer` | 否 | 最大 10；示例：`10` | 每页条数，每页最多10条，默认10 |
| `shopType` | `integer` | 否 | 示例：`1`, `2` | 店铺类型：1-本土店铺，2-跨境店铺 |
| `orderField` | `string` | 否 | 格式 `day7_units_sold\|day7_gmv\|commission_rate\|total_units_sold\|total_gmv\|creator_count`；示例：`day7_units_sold`, `day7_gmv`, `commission_rate`, `total_units_sold`, `total_gmv`, `creator_count` | 排序字段（默认降序排列） |
| `isNewListed` | `boolean` | 否 | 示例：`true` | 是否新品 |
| `isTopSelling` | `boolean` | 否 | 示例：`true` | 是否热销商品 |
| `isFreeShipping` | `boolean` | 否 | 示例：`true` | 是否包邮 |
| `unitsSoldRange` | `object` | 否 |  |  |
| `isLocalWarehouse` | `boolean` | 否 | 示例：`true` | 是否本地仓 |
| `creatorCountRange` | `object` | 否 |  |  |
| `commissionRateRange` | `object` | 否 |  |  |

### 嵌套输入结构：`unitsSoldRange`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `max` | `integer` | 否 |  | 范围上限（最大值，含），不设置则不限上限 |
| `min` | `integer` | 否 |  | 范围下限（最小值，含），不设置则不限下限 |

### 嵌套输入结构：`creatorCountRange`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `max` | `integer` | 否 |  | 范围上限（最大值，含），不设置则不限上限 |
| `min` | `integer` | 否 |  | 范围下限（最小值，含），不设置则不限下限 |

### 嵌套输入结构：`commissionRateRange`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `max` | `integer` | 否 |  | 范围上限（最大值，含），不设置则不限上限 |
| `min` | `integer` | 否 |  | 范围下限（最小值，含），不设置则不限下限 |

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
    "name": "/fastmoss/productSearch",
    "arguments": {}
  }
}
```

> 示例值仅用于展示请求结构。实际调用时必须替换为用户的真实查询条件。

## 输出字段

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 |  | 当前页码 |
| `type` | `string` | 否 |  | 响应类型 |
| `total` | `integer` | 否 |  | 结果总数 |
| `columns` | `array<object>` | 否 |  | 列定义 |
| `costTime` | `integer` | 否 |  | 接口耗时毫秒 |
| `pageSize` | `integer` | 否 |  | 每页条数 |
| `products` | `array<object>` | 否 |  | 商品列表 |
| `costToken` | `integer` | 否 |  | 消耗Token数量 |
| `matchedCategoryIdPath` | `string` | 否 |  | 匹配类目ID路径 |
| `matchedCategoryNamePath` | `string` | 否 |  | 匹配类目名称路径 |

### 嵌套输出结构：`products`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `price` | `number` | 否 |  | 商品价格.数值类型，货币单位见currency字段 |
| `title` | `string` | 否 |  | 商品名称 |
| `region` | `string` | 否 |  | 区域代码.如US、GB、ID等 |
| `source` | `string` | 否 |  | 商品来源标识 |
| `coverUrl` | `array<any>` | 否 |  | 图片URL列表 |
| `currency` | `string` | 否 |  | 货币符号 |
| `imageUrl` | `string` | 否 |  | 商品图片URL |
| `maxPrice` | `number` | 否 |  | 最高价格.部分商品无此数据时为null，货币单位见currency字段 |
| `minPrice` | `number` | 否 |  | 最低价格.部分商品无此数据时为null，货币单位见currency字段 |
| `shopName` | `string` | 否 |  | 店铺名称 |
| `skuCount` | `integer` | 否 |  | SKU数量 |
| `productId` | `string` | 否 |  | TikTok产品ID.如1730759153212362829 |
| `tiktokUrl` | `string` | 否 |  | TikTok商品链接 |
| `shopAvatar` | `string` | 否 |  | 店铺头像URL |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 商品来源 |
| `categoryIds` | `array<any>` | 否 |  | 商品品类ID列表.一级到三级，如["16","909064","910728"] |
| `fastmossUrl` | `string` | 否 |  | FastMoss商品链接 |
| `isSShopText` | `string` | 否 |  | 是否全托管商品.是/否，S店=TikTok全托管 |
| `reviewCount` | `integer` | 否 |  | 评论总数.部分商品无此数据时为null |
| `totalIflCnt` | `integer` | 否 |  | 关联达人数.Influencer Count |
| `categoryName` | `string` | 否 |  | 商品品类名称路径.如Phones & Electronics -> Phone Accessories -> Power Banks |
| `shopSellerId` | `string` | 否 |  | 店铺ID |
| `totalLiveCnt` | `integer` | 否 |  | 关联直播数.部分商品无此数据时为null |
| `totalSaleCnt` | `integer` | 否 |  | 总销量.累计历史总销量 |
| `availableDate` | `string` | 否 |  | 上架时间.格式yyyy-MM-dd HH:mm:ss，如2025-10-26 18:09:29 |
| `isCrossBorder` | `integer` | 否 |  | 是否跨境.1=跨境，0=本土 |
| `productRating` | `number` | 否 |  | 商品评分.范围0.0-5.0，如4.4 |
| `totalVideoCnt` | `integer` | 否 |  | 关联视频数 |
| `totalSale1dCnt` | `integer` | 否 |  | 1天内总销量 |
| `totalSale7dCnt` | `integer` | 否 |  | 7天内总销量 |
| `totalSale28dCnt` | `integer` | 否 |  | 28天内总销量) |
| `totalSale90dCnt` | `integer` | 否 |  | 90天内总销量 |
| `totalSaleGmvAmt` | `integer` | 否 |  | 总销售额.累计历史总销售额，货币单位见currency字段 |
| `freeShippingText` | `string` | 否 |  | 是否包邮.是/否 |
| `totalSaleGmv7dAmt` | `integer` | 否 |  | 7天内总销售额.货币单位见currency字段 |
| `salesTrendFlagText` | `string` | 否 |  | 销售趋势标记 |
| `shopTotalUnitsSold` | `integer` | 否 |  | 店铺总销量 |
| `totalSaleGmv28dAmt` | `integer` | 否 |  | 28天内总销售额.货币单位见currency字段 |
| `productCommissionRate` | `number` | 否 |  | 商品佣金比例.小数值，0.10表示10%，0.17表示17% |

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
