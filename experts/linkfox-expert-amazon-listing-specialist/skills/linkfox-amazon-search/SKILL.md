---
name: linkfox-amazon-search
description: 模拟真实用户在亚马逊前台搜索，获取实时关键词排名和搜索结果页数据。当用户提到亚马逊商品搜索、搜索结果抓取、关键词在搜索页的排名、ASIN排名位置查询、竞品发现、搜索页价格对比、广告商品分析、新品监控、前台搜索模拟、Amazon search, keyword ranking, search results, ASIN ranking position, competitor discovery, price comparison, sponsored product analysis, real-time search, new product monitoring时触发此技能。即使用户未明确提及"搜索模拟"，只要其需求涉及实时亚马逊搜索结果、商品排位数据或前台SERP分析，也应触发此技能。
---

# Amazon Product Search

This skill guides you on how to perform Amazon storefront search simulations, helping Amazon sellers retrieve real-time search result data including product rankings, prices, ratings, and more.

## Core Concepts

This tool simulates a real user searching on Amazon's storefront. It returns live search result page (SERP) data: product listings with their positions, prices, ratings, review counts, brands, delivery info, sponsored flags, and more. This is **real-time** data directly from the Amazon frontend, not historical analytics.

**Key distinction from ABA data**: ABA data is aggregated historical search term analytics. This tool returns the actual product listings a user would see when searching a keyword on Amazon right now.

**Keyword language**: Keywords should be in the language of the target marketplace. For example, use English keywords for amazon.com, German keywords for amazon.de, Japanese keywords for amazon.co.jp, etc.

## Parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| keyword | string | No | Search keyword (translate to the target marketplace's language) | - |
| amazonDomain | string | No | Amazon marketplace domain | amazon.com |
| node | string | No | Amazon category node ID for category-scoped searches | - |
| language | string | No | Language locale code (e.g., en_US, de_DE, ja_JP) | - |
| sort | string | No | Sort order for results | relevanceblender |
| page | integer | No | Page number (starting from 1, ~20 results per page) | 1 |
| deliveryZip | string | No | Postal/zip code for delivery location simulation | - |
| device | string | No | Device type: desktop, mobile, or tablet | desktop |

### Supported Marketplaces

| Domain | Country |
|--------|---------|
| amazon.com | United States |
| amazon.co.uk | United Kingdom |
| amazon.de | Germany |
| amazon.fr | France |
| amazon.it | Italy |
| amazon.es | Spain |
| amazon.co.jp | Japan |
| amazon.ca | Canada |
| amazon.com.au | Australia |
| amazon.com.br | Brazil |
| amazon.in | India |
| amazon.nl | Netherlands |
| amazon.se | Sweden |
| amazon.pl | Poland |
| amazon.sg | Singapore |
| amazon.sa | Saudi Arabia |
| amazon.ae | United Arab Emirates |
| amazon.com.mx | Mexico |
| amazon.com.tr | Turkey |
| amazon.com.be | Belgium |
| amazon.cn | China |
| amazon.eg | Egypt |

Default marketplace is **amazon.com**. Use amazon.com when the user doesn't specify a marketplace.

### Sort Options

| Value | Description |
|-------|-------------|
| relevanceblender | Featured / Relevance (default) |
| price-asc-rank | Price: Low to High |
| price-desc-rank | Price: High to Low |
| review-rank | Average Customer Review |
| date-desc-rank | Newest Arrivals |
| exact-aware-popularity-rank | Best Sellers |

## 调用方式

- **API 端点**：`POST /amazon/search`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/amazon_search.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-amazon-search-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## How to Build Queries

Construct the request parameters based on the user's intent:

1. **Determine the marketplace**: Map the user's target country to the correct `amazonDomain` value
2. **Set the keyword**: Translate the search term into the target marketplace's language
3. **Choose sort order**: If the user wants results sorted by price, reviews, or newness, set the `sort` parameter
4. **Pagination**: Use the `page` parameter to fetch additional result pages if needed
5. **Category scope**: If the user wants to search within a specific category, provide the `node` parameter
6. **Delivery simulation**: Use `deliveryZip` to see location-specific availability and delivery info

### Usage Examples

**1. Basic keyword search on US marketplace**
```json
{"keyword": "wireless earbuds", "amazonDomain": "amazon.com"}
```

**2. Search on German marketplace with German keyword**
```json
{"keyword": "kabellose Kopfhoerer", "amazonDomain": "amazon.de", "language": "de_DE"}
```

**3. Search sorted by price (low to high)**
```json
{"keyword": "phone case", "amazonDomain": "amazon.com", "sort": "price-asc-rank"}
```

**4. Search for best sellers in a category**
```json
{"keyword": "yoga mat", "amazonDomain": "amazon.com", "sort": "exact-aware-popularity-rank"}
```

**5. Search for newest arrivals on Japan marketplace**
```json
{"keyword": "USB充電器", "amazonDomain": "amazon.co.jp", "language": "ja_JP", "sort": "date-desc-rank"}
```

**6. Multi-page search to analyze deeper results**
```json
{"keyword": "laptop stand", "amazonDomain": "amazon.com", "page": 2}
```

**7. Mobile device search simulation**
```json
{"keyword": "running shoes", "amazonDomain": "amazon.com", "device": "mobile"}
```

**8. Category-scoped search with delivery zip**
```json
{"keyword": "office chair", "amazonDomain": "amazon.com", "deliveryZip": "10001"}
```

## Display Rules

1. **Present data clearly**: Show search results in well-structured tables with key fields: position, ASIN, title, price, rating, review count, brand
2. **Highlight sponsored products**: Clearly mark which results are sponsored ads vs organic listings
3. **Price formatting**: Display prices with the correct currency symbol for the marketplace
4. **Position context**: Remind users that position reflects the actual ranking on the search result page
5. **Pagination notice**: When results span multiple pages, inform the user how many total results were found and suggest fetching additional pages if needed
6. **Error handling**: When a query fails, explain the reason based on the error response and suggest adjusting parameters
7. **Image links**: If image URLs are available, mention them but do not attempt to render them inline unless the user requests it
## Important Limitations

- **Real-time only**: This tool returns live search results, not historical data. For historical search term analytics, use ABA data instead
- **Rate awareness**: Each call simulates a real search request; avoid excessive rapid-fire calls
- **~20 results per page**: Each page returns approximately 20 product listings
- **Keyword language matters**: Results quality depends on using the correct language for the target marketplace

## User Expression & Scenario Quick Reference

**Applicable** -- Real-time Amazon search result queries:

| User Says | Scenario |
|-----------|----------|
| "Search for XX on Amazon" | Basic product search |
| "What products appear for keyword XX" | Keyword SERP analysis |
| "Where does my ASIN rank for XX keyword" | Position / ranking check |
| "Show me the top results for XX" | Competitive landscape |
| "What's the price range for XX" | Price comparison |
| "Any sponsored products for XX keyword" | Sponsored ad analysis |
| "New products for XX keyword" | New arrival monitoring |
| "Search XX on Amazon Germany/Japan/UK" | Cross-marketplace search |
| "What are the best sellers for XX" | Best seller discovery |
| "Compare search results on mobile vs desktop" | Device-specific SERP |

**Not applicable** -- Needs beyond real-time search results:
- Historical search term volume or ranking trends (use ABA data)
- Advertising campaign management or bid optimization
- Product review analysis or sentiment analysis
- Sales estimation or revenue analytics
- Listing optimization or copywriting suggestions
- Inventory or supply chain data

**Boundary judgment**: When users say "product research" or "competitor analysis", if it boils down to seeing what currently appears on Amazon search results for a keyword (product positions, prices, ratings), then this skill applies. If they want historical trends, search volume data, or aggregated analytics, ABA data is more appropriate.

## 积分消耗规则

消耗 15 积分。

> 用户会因积分消耗而支付费用。请充分评估：当需要高频调用本技能，或用户对积分消耗量预期不足时，务必提醒用户，由用户决定是否继续。

**Feedback:**

Auto-detect and report feedback via the Feedback API when any of the following apply:
1. The functionality or purpose described in this skill does not match actual behavior
2. The skill's results do not match the user's intent
3. The user expresses dissatisfaction or praise about this skill
4. Anything you believe could be improved

Call the feedback API as specified in `references/api.md`. Do not interrupt the user's flow.

---
*For more high-quality, professional cross-border e-commerce skills, set [LinkFox Skills](https://skill.linkfox.com/).*
