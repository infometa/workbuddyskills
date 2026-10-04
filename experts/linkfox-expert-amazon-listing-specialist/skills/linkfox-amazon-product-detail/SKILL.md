---
name: linkfox-amazon-product-detail
description: 通过ASIN获取亚马逊商品详细信息，包括标题、图片、五点描述、规格参数、A+页面、价格、评分评论、变体等。当用户提到亚马逊商品详情、ASIN查询、商品页面数据、Listing分析、五点描述提取、商品图片获取、变体查看、竞品Listing研究、价格查询、评论拆解、商品规格查询、Amazon product details, ASIN lookup, listing analysis, bullet points, variant info, product pricing, ratings and reviews, A+ content, product specifications, product images时触发此技能。即使用户未明确说"商品详情"，只要其需求涉及通过ASIN获取亚马逊商品页面的结构化数据，也应触发此技能。
---

# Amazon Product Detail Lookup

This skill guides you on how to retrieve and analyze detailed Amazon product information by ASIN, helping Amazon sellers and researchers extract comprehensive listing data from product pages across 22 Amazon marketplaces.

## Core Concepts

This tool performs front-end simulation of Amazon product pages to extract structured detail data. It returns rich information including the product title, main image, additional images, bullet points (About This Item), product specifications, A+ content description, pricing, ratings distribution, variant structure, and optionally "Frequently Bought Together" and "Related Products" data.

**Billing note**: This tool is billed per ASIN queried. Because the cost is higher than search-based tools, guide users to query only the ASINs they truly need rather than large exploratory batches.

**Batch support**: Up to 40 ASINs can be queried in a single request, provided as a comma-separated string.

## Parameter Guide

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| asins | Yes | -- | Comma-separated ASIN list (up to 40). Example: `B072MQ5BRX,B08N5WRWNW` |
| amazonDomain | No | `amazon.com` | Amazon marketplace domain. See Supported Marketplaces below |
| language | No | -- | Locale code for response language, e.g. `en_US`, `de_DE`, `ja_JP` |
| deliveryZip | No | -- | Postal/ZIP code for delivery-dependent pricing and availability |
| device | No | `desktop` | Device type: `desktop`, `mobile`, or `tablet` |
| returnBoughtTogether | No | `false` | Include "Frequently Bought Together" products in the response |
| returnRelatedProducts | No | `false` | Include "Related Products" list in the response |
| returnAuthorsReviews | No | `false` | Include top customer reviews in the response |

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
| amazon.com.tr | Turkey |
| amazon.com.mx | Mexico |
| amazon.eg | Egypt |
| amazon.cn | China |
| amazon.com.be | Belgium |

Default marketplace is **amazon.com** (US). Use `amazon.com` when the user doesn't specify a marketplace.

## 调用方式

- **API 端点**：`POST /amazon/product/detail`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/amazon_product_detail.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-amazon-product-detail-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Usage Examples

**1. Basic single-ASIN lookup**
```
Look up the details of ASIN B072MQ5BRX on Amazon US.
```
Parameters: `{"asins": "B072MQ5BRX"}`

**2. Multi-ASIN batch lookup**
```
Get product details for B072MQ5BRX and B08N5WRWNW.
```
Parameters: `{"asins": "B072MQ5BRX,B08N5WRWNW"}`

**3. Lookup on a non-US marketplace**
```
Fetch product info for B09V3KXJPB on Amazon Germany.
```
Parameters: `{"asins": "B09V3KXJPB", "amazonDomain": "amazon.de"}`

**4. Lookup with reviews and bought-together**
```
Get full product details including reviews and frequently bought together for B08N5WRWNW on Amazon Japan.
```
Parameters: `{"asins": "B08N5WRWNW", "amazonDomain": "amazon.co.jp", "returnBoughtTogether": true, "returnAuthorsReviews": true}`

**5. Competitor listing comparison**
```
Compare bullet points and pricing for these 3 ASINs: B072MQ5BRX, B08N5WRWNW, B09V3KXJPB.
```
Parameters: `{"asins": "B072MQ5BRX,B08N5WRWNW,B09V3KXJPB"}`

**6. Mobile-specific product page check**
```
Show me how product B072MQ5BRX looks on mobile in the UK.
```
Parameters: `{"asins": "B072MQ5BRX", "amazonDomain": "amazon.co.uk", "device": "mobile"}`

## Display Rules

1. **Present data clearly**: Show product details in a well-structured format -- use tables for specifications and pricing comparisons, bullet lists for "About This Item" content
2. **Image handling**: When the response includes image URLs (`productImageUrls`, `thumbnail`, `imageUrl`), present them as clickable links or embedded images as appropriate
3. **Multi-ASIN results**: When multiple ASINs are queried, organize results so each product is clearly separated and labeled by ASIN and title
4. **Price formatting**: Always include the currency symbol/code alongside price values. Show both current price and original price (if discounted) to highlight deals
5. **Rating breakdown**: When `customerReviews` data is present, show the star distribution (5-star through 1-star percentages) alongside the overall rating and total review count
6. **Variant display**: When variants exist, present them in a compact table grouped by variant dimension (color, size, etc.)
7. **Error handling**: When a query fails, explain the reason and suggest checking that the ASIN is valid and the marketplace domain is correct
8. **Cost awareness**: Remind users that this tool charges per ASIN, so they should batch only what they need
## User Expression & Scenario Quick Reference

**Applicable** -- Tasks that require structured Amazon product page data:

| User Says | Scenario |
|-----------|----------|
| "Look up this ASIN", "Get product details for ..." | Single/batch ASIN detail lookup |
| "What are the bullet points for this product" | Listing content extraction |
| "Show me competitor listings" | Multi-ASIN comparison |
| "What's the price of this ASIN on Amazon DE" | Cross-marketplace price check |
| "How many reviews does this product have" | Rating & review analysis |
| "What variants does this product offer" | Variant structure inspection |
| "Get the A+ content / product description" | Product description retrieval |
| "What's the main image for this ASIN" | Product image extraction |
| "Is this product Prime eligible" | Eligibility / badge check |
| "What are the product specs / dimensions" | Specification lookup |

**Not applicable** -- Needs beyond product detail page data:

- Keyword / search term analysis (use ABA Data Explorer instead)
- Search result rankings or organic position tracking
- Advertising / PPC campaign data
- Sales estimation or revenue calculations
- Inventory management or FBA fee analysis
- Review sentiment analysis requiring NLP beyond raw review text
- Historical price tracking over time (this tool returns current snapshot only)

**Boundary judgment**: When users say "analyze this product" or "research this ASIN", if it boils down to retrieving the current product page data (title, price, bullets, images, reviews, variants), this skill applies. If they need historical trends, sales estimates, or advertising insights, it does not apply.

## 积分消耗规则

按动态规则计费：消耗积分 = 成功返回商品数 × 15。

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
