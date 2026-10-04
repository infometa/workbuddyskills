---
name: linkfox-keepa-product-request
description: 通过ASIN获取亚马逊商品详情，包括价格、标题、主图、上架日期、材质、重量、变体月销量及近12个月的月销数据。当用户查询亚马逊商品详情、ASIN查询、商品定价、销售排名历史、月销量趋势、商品尺寸、FBA费用、产品规格、批量ASIN查询、Keepa product details, ASIN detail lookup, monthly sales data, pricing info, product specifications, FBA fees, batch ASIN query时触发此技能。即使用户未明确提及"Keepa"，只要其需求涉及获取一个或多个亚马逊ASIN的结构化商品数据，也应触发此技能。
---

# Keepa Product Data Request

This skill guides you on how to retrieve Amazon product details via the Keepa product request API, helping Amazon sellers and analysts obtain structured product data for one or more ASINs across multiple Amazon marketplaces.

## Core Concepts

The Keepa Product Request API returns detailed product listing data from Amazon, sourced through Keepa. Given one or more ASINs and a marketplace, it returns comprehensive product information: pricing, title, main image, listing date, material, weight, dimensions, sales rank, monthly sales units (current and up to 12 months of history), FBA fees, ratings, review counts, category tree, and more.

**Key points**:
- You can query up to **5 ASINs** in a single request by separating them with commas.
- The `domain` parameter is a numeric marketplace ID (e.g., `1` = Amazon.com US), not a country code.
- Setting `history` to `1` includes historical sales data (monthly sales for up to 12 prior months, average sales rank over 30/90/180 days). Setting it to `0` returns only current product information.
- The response does **not** include product descriptions or reviews content.

## Parameter Guide

### domain (Required)

Numeric Amazon marketplace ID. The mapping is:

| Domain ID | Marketplace |
|-----------|-------------|
| 1 | Amazon.com (US) |
| 2 | Amazon.co.uk (UK) |
| 3 | Amazon.de (Germany) |
| 4 | Amazon.fr (France) |
| 5 | Amazon.co.jp (Japan) |
| 6 | Amazon.ca (Canada) |
| 8 | Amazon.it (Italy) |
| 9 | Amazon.es (Spain) |
| 10 | Amazon.in (India) |
| 11 | Amazon.com.mx (Mexico) |
| 12 | Amazon.com.br (Brazil) |

Default to **1** (US) when the user does not specify a marketplace.

### asin (Required)

One or more Amazon Standard Identification Numbers. For multiple ASINs, separate with commas. Maximum 5 ASINs per request, with a total string length limit of 300 characters.

### history (Optional)

Whether to include historical data such as monthly sales for the past 12 months and average sales rank over 30/90/180 days. Set to `1` to include history, `0` (default) for basic info only.

## Usage Examples

**1. Single ASIN lookup (US marketplace, basic info)**
```json
{"asin": "B0088PUEPK", "domain": "1"}
```

**2. Single ASIN with historical sales data**
```json
{"asin": "B0088PUEPK", "domain": "1", "history": 1}
```

**3. Batch lookup of multiple ASINs (Germany)**
```json
{"asin": "B0088PUEPK,B00U26V4VQ,B07M68S376", "domain": "3", "history": 1}
```

**4. Product lookup on Amazon Japan**
```json
{"asin": "B09V3KXJPB", "domain": "5", "history": 0}
```

**5. Competitor comparison across multiple ASINs (US, with sales history)**
```json
{"asin": "B0CXYZ1234,B0CXYZ5678,B0CXYZ9012,B0CXYZABCD", "domain": "1", "history": 1}
```

## 调用方式

- **API 端点**：`POST /keepa/productRequest`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/keepa_product_detail.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-keepa-product-request-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
- 响应体 ≤ 8 KB：落盘后把完整 JSON 打印到 stdout
- 响应体 > 8 KB：落盘后 stdout 只输出摘要（顶层字段、常见计数如 `total`/`costToken`、最大列表字段的长度 + 前 3 条样本）
- 加 `--inline` 强制全量打印到 stdout（同样落盘）

**读数据建议**：先看摘要判断是否足够；需要具体字段时优先用 `jq`或`ConvertFrom-Json` 从保存的 json 文件按需抽取，避免整份 JSON 进入上下文。

## 解决认证和积分问题
发生以下异常情况时，采用 references/onboarding.md 引导解决问题：

### 异常情况
- **未配置API Key**：环境变量未配置 `LINKFOX_AGENT_API_KEY`，也未配置 `LINKFOXAGENT_API_KEY`。
- **响应401或402状态码**
- **响应提示积分或余额不足**：消息含"积分余额不足/计费不足/余额不足/quota exceeded/insufficient balance/套餐到期/需充值/请充值"，或类似含义的内容。

## Display Rules

1. **Present data clearly**: Show product details in well-structured tables. Group related fields (e.g., dimensions together, sales data together) for readability.
2. **Price and currency**: Always display the price alongside its currency (e.g., "$29.99 USD"). The `currency` field in the response indicates the local currency.
3. **Sales trend**: When historical data is included, present the 12-month sales trend in a table or describe the trajectory (growing, declining, stable) to help users quickly assess momentum.
4. **Dimensions and weight**: Convert millimeter values to more intuitive units when appropriate (e.g., show both mm and inches, or mm and cm). Note that weight is in grams.
5. **Unavailable data**: Fields with value `0` or `-1` indicate data is unavailable. Do not display these as actual measurements; instead note "N/A" or omit them.
6. **Image display**: If `imageUrl` is present, display the product image to help users visually identify the product.
7. **Error handling**: When a query fails, explain the issue based on the response and suggest corrections (e.g., invalid ASIN format, unsupported marketplace).
8. **Large batch results**: For batch queries with many ASINs, present a summary table first and offer to show individual product details on request.
## Important Limitations

- **No product descriptions or reviews**: The API does not return product description text or review content.
- **Maximum 5 ASINs per request**: Batch queries are capped at 5 ASINs.
- **ASIN string length limit**: The `asin` parameter has a maximum length of 300 characters.
- **Historical data is optional**: Monthly sales history is only returned when `history` is set to `1`.
- **Data freshness**: The `lastUpdate` field indicates when the product data was last refreshed.

## User Expression & Scenario Quick Reference

**Applicable** -- Product data retrieval by ASIN:

| User Says | Scenario |
|-----------|----------|
| "Look up this ASIN", "Get product details for B0XXXXXXXX" | Single ASIN lookup |
| "What's the price of this product on Amazon" | Price query |
| "How many units does this product sell per month" | Monthly sales check |
| "Compare these ASINs", "batch lookup these products" | Multi-ASIN comparison |
| "Show me the sales trend for this ASIN" | Historical sales analysis |
| "What category is this product in" | Category / classification lookup |
| "Product dimensions", "how much does it weigh" | Physical specs query |
| "FBA fees for this product" | Fee estimation |
| "When was this product listed", "listing date" | Listing age / launch date |
| "Is this product FBA or FBM" | Fulfillment method check |

**Not applicable** -- Needs beyond ASIN-level product data:

- Search term / keyword analysis (use ABA data tools instead)
- Product reviews or listing copywriting content
- Advertising / PPC campaign data
- Seller account or store-level analytics
- Product research without specific ASINs (e.g., "find trending products in kitchen category")
- Price history charts or Buy Box history over time (only current and average rank data are available)

**Boundary judgment**: When users say "product research" or "competitor analysis", if they have specific ASINs and want structured product data (price, sales, dimensions, category), this skill applies. If they want keyword-level analysis, market-wide trends without specific ASINs, or advertising metrics, this skill does not apply.

## 积分消耗规则

按动态规则计费：消耗积分 = 0.045 × 本次商品详情查询消耗的 Keepa token。

> **重要**：本技能的服务按倍数动态计算，可能一次性消耗大量积分，必须提醒用户，由用户决定是否继续。

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in `references/api.md`. Do not interrupt the user's flow.


---
*For more high-quality, professional cross-border e-commerce skills, set [LinkFox Skills](https://skill.linkfox.com/).*
