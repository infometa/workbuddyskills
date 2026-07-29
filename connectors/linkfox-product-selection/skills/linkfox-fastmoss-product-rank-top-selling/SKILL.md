---
name: linkfox-fastmoss-product-rank-top-selling
description: 通过FastMoss数据查询TikTok全球电商市场的热销商品排行榜，支持按日/周/月维度和类目维度分析。当用户提到TikTok热销榜、TikTok爆品排行、TikTok销量排行、TikTok GMV排名、TikTok类目热销、TikTok选品周报、TikTok top-selling rankings, TikTok bestseller charts, TikTok GMV ranking, TikTok category hot sellers, TikTok weekly product report, FastMoss时触发此技能。即使用户未明确提及"FastMoss"，只要其需求涉及查看TikTok平台的热销排行榜或按时间维度的销售排名，也应触发此技能。
---

# FastMoss-TikTok热销榜单

## 基本信息

- **业务工具名**：`/fastmoss/productRankTopSelling`
- **所属分组**：FastMoss · TikTok 选品
- **功能说明**：通过时间轴（日/周/月）与类目交叉维度，精准调取 TikTok 全球电商市场的爆款排行榜。本工具专注于“趋势发现”与“榜单复盘”，核心功能包括：
- **关键词**：FastMoss, TikTok 榜单, 销量排行榜, GMV 排名, 爆款发现, 增长率分析, 类目调研, 选品周报


## 何时使用

当用户意图与“FastMoss-TikTok热销榜单”匹配，或需要以下能力时使用本工具：通过时间轴（日/周/月）与类目交叉维度，精准调取 TikTok 全球电商市场的爆款排行榜。本工具专注于“趋势发现”与“榜单复盘”，核心功能包括：

调用前应先确认所有必填参数。涉及站点、国家、日期、语言、ASIN、SKU、图片或 URL 时，应使用用户提供的信息，不要擅自虚构真实业务标识。

## 输入参数

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `page` | `integer` | 否 | 示例：`1` | 页码，默认1 |
| `region` | `string` | 是 | 最长 1000；示例：`US`, `GB`, `MX`, `ES`, `ID`, `VN`, `MY`, `TH` | 国家/地区代码，与商品搜索相同白名单：['US','GB','MX','ES','DE','IT','FR','ID','VN','MY','TH','PH','BR','JP','SG'] |
| `orderby` | `object` | 否 |  |  |
| `category` | `string` | 否 | 最长 1000；示例：`Phone Cases` | 类目名称（文本，用于匹配 TikTok 英文类目并解析为一级类目 ID）。TikTok 类目为英文，服务端按英文做 BM25 匹配；若用户输入非英语，请先在对话侧译为英语再传入本参数。 |
| `dateInfo` | `object` | 是 |  |  |
| `pageSize` | `integer` | 否 | 最大 10；示例：`10` | 每页条数，每页最多10条，默认10 |

### 嵌套输入结构：`orderby`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `field` | `string` | 是 | 最长 1000；示例：`units_sold`, `gmv`, `total_units_sold`, `total_gmv`, `growth_rate` | 排序字段名 |
| `order` | `string` | 否 | 最长 1000；示例：`desc`, `asc` | 排序方向：desc-降序, asc-升序，默认 desc |

### 嵌套输入结构：`dateInfo`

| 字段 | 类型 | 必填 | 约束/默认值 | 说明 |
|---|---|:---:|---|---|
| `type` | `string` | 是 | 最长 1000；示例：`day`, `week`, `month` | 日期类型：day-按天, week-按周, month-按月 |
| `value` | `string` | 是 | 最长 1000；示例：`2025-02-01`, `2025-18`, `2025-02` | 日期值，格式取决于type：day→'2025-02-01', week→'2025-18', month→'2025-02' |

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
    "name": "/fastmoss/productRankTopSelling",
    "arguments": {
      "region": "US",
      "dateInfo": {
        "type": "day",
        "value": "2025-02-01"
      }
    }
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
| `price` | `number` | 否 |  | 商品价格.数值类型，含价格范围时取最低值，货币单位见currency字段 |
| `title` | `string` | 否 |  | 商品名称 |
| `region` | `string` | 否 |  | 区域代码.如US、GB、ID等 |
| `coverUrl` | `array<any>` | 否 |  | 商品封面图URL列表 |
| `currency` | `string` | 否 |  | 货币符号 |
| `imageUrl` | `string` | 否 |  | 商品图片URL |
| `maxPrice` | `number` | 否 |  | 最高价格.仅当原始价格为范围时有值，货币单位见currency字段 |
| `minPrice` | `number` | 否 |  | 最低价格.仅当原始价格为范围时有值，货币单位见currency字段 |
| `shopName` | `string` | 否 |  | 店铺名称 |
| `productId` | `string` | 否 |  | TikTok产品ID.如1730696681877443081 |
| `growthRate` | `number` | 否 |  | 销量增长率(单位%) |
| `shopAvatar` | `string` | 否 |  | 店铺头像URL |
| `sourceTool` | `string` | 否 |  | 来源工具 |
| `sourceType` | `string` | 否 |  | 商品来源 |
| `categoryIds` | `array<any>` | 否 |  | 商品品类ID列表.一级到三级，如["24","914824","819984"] |
| `categoryName` | `string` | 否 |  | 商品品类名称路径.如Food & Beverages -> Drinks -> Meal Replacement & Protein Drinks |
| `shopSellerId` | `string` | 否 |  | 店铺ID |
| `totalSaleCnt` | `integer` | 否 |  | 总销量.累计历史总销量 |
| `offShelvesText` | `string` | 否 |  | 是否下架.是=已下架，否=在售 |
| `totalSale1dCnt` | `integer` | 否 |  | 1天内销量 |
| `totalSale7dCnt` | `integer` | 否 |  | 7天内销量.仅dateType=week时有值 |
| `totalSale30dCnt` | `integer` | 否 |  | 30天内销量.仅dateType=month时有值，与筛选周期一致的区间销量 |
| `totalSaleGmvAmt` | `number` | 否 |  | 总销售额.累计历史总销售额，货币单位见currency字段 |
| `totalSaleGmv1dAmt` | `number` | 否 |  | 1天内销售额.仅dateType=day时有值，货币单位见currency字段 |
| `totalSaleGmv7dAmt` | `number` | 否 |  | 7天内销售额.仅dateType=week时有值，货币单位见currency字段 |
| `shopTotalUnitsSold` | `integer` | 否 |  | 店铺总销量 |
| `totalSaleGmv30dAmt` | `number` | 否 |  | 30天内销售额.仅dateType=month时有值，货币单位见currency字段 |
| `productCommissionRate` | `integer` | 否 |  | 商品佣金比例.基点制整数，1000表示10%，除以100得百分比值 |

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
