---
name: linkfox-amazon-search-by-image
description: 基于图片的亚马逊跨站点视觉商品搜索，支持8个站点的以图搜图和视觉相似商品发现。当用户提到以图搜图、图片搜索、视觉搜索、找同款、外观相似商品、图片找货、竞品图片搜索、相似商品发现、image search, Amazon visual search, find similar products, reverse image lookup, visual search, similar items, competitor image search, product image match时触发此技能。即使用户未明确提及"图片搜索"，只要用户提供了图片URL并希望在亚马逊上查找匹配或相似的商品，也应触发此技能。
---

# Amazon Image-Based Search

This skill guides you on how to perform visual product searches on Amazon using an image URL, helping Amazon sellers and researchers find visually similar products across multiple marketplaces.

## Core Concepts

Amazon Image-Based Search (visual search) allows you to submit a product image URL and retrieve Amazon listings that are visually similar. This is invaluable for competitive analysis, sourcing alternatives, identifying counterfeits, and discovering market opportunities based on product appearance.

The tool searches across **8 Amazon marketplaces** and returns rich product data including ASIN, title, image, price, rating, review count, brand, and optionally Keepa-enriched data (sales rank, monthly sales, FBA fees, dimensions, etc.).

## Supported Marketplaces

| Marketplace | Domain | Default Zip Code |
|-------------|--------|-------------------|
| United States | amazon.com | 10001 |
| United Kingdom | amazon.co.uk | EC1A 1BB |
| Germany | amazon.de | 10115 |
| France | amazon.fr | 75001 |
| Italy | amazon.it | 00100 |
| Spain | amazon.es | 28001 |
| Japan | amazon.co.jp | 100-0001 |
| India | amazon.in | 110034 |

Default marketplace is **amazon.com** (US). Use amazon.com when the user does not specify a marketplace.

## Parameter Guide

| Parameter | Required | Description |
|-----------|----------|-------------|
| imageUrl | Yes | A valid, publicly accessible image URL to search with |
| amazonDomain | Yes | Amazon marketplace domain (e.g., `amazon.com`, `amazon.de`). Defaults to `amazon.com` |
| sort | No | Sort order for results. Supported values: `default`, `price-asc-rank`, `price-desc-rank`, `rating-asc-rank`, `rating-desc-rank`, `ratings-asc-rank`, `ratings-desc-rank` |
| deliveryZip | No | Delivery address zip code within the marketplace country. Uses the marketplace default if not specified |
| countryOrAreaCode | No | Country/region code for cross-border delivery (e.g., `CN`, `JP`, `KR`). Cannot be used together with `deliveryZip`. Note: India marketplace does not support cross-border delivery |
| aggregateByKeepaData | No | Whether to enrich results with Keepa data (sales rank, monthly sales, FBA fees, dimensions, etc.) |

### Sort Options

| Value | Description |
|-------|-------------|
| `default` | Default relevance sorting |
| `price-asc-rank` | Price: low to high |
| `price-desc-rank` | Price: high to low |
| `rating-asc-rank` | Rating: low to high |
| `rating-desc-rank` | Rating: high to low |
| `ratings-asc-rank` | Review count: low to high |
| `ratings-desc-rank` | Review count: high to low |

**Important**: If the requested sort order is not in the supported list above, do NOT attempt to use any other tool or workaround to compensate. Inform the user of the supported sort options.

## 调用方式

- **API 端点**：`POST /amazon/searchByImage`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/amazon_search_by_image.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-amazon-search-by-image-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Local Image Upload

This tool requires a **publicly accessible image URL**. If the user provides a local image file path (e.g., `C:\Users\...\photo.png`, `/home/.../image.jpg`), you must upload it first to obtain a public URL.

Run the upload script:
```bash
python scripts/upload_image.py /path/to/local/image.png
```

The script will return a public URL (valid for 24 hours) that can be used as the image URL parameter.

## Usage Examples

**1. Basic image search on the US marketplace**
```
Search Amazon US for products that look similar to this image:
https://m.media-amazon.com/images/I/61pAlIX8SZL._AC_SY575_.jpg
```

**2. Find similar products on a specific marketplace**
```
Search Amazon Germany (amazon.de) for products visually similar to this image:
https://example.com/product-photo.jpg
```

**3. Image search sorted by price (low to high)**
```
Find similar products on Amazon US for this image, sorted by price from low to high:
https://example.com/my-product.jpg
```

**4. Image search with Keepa data enrichment**
```
Search Amazon US for products matching this image and include Keepa sales data:
https://example.com/competitor-product.jpg
```

**5. Cross-border delivery search**
```
Search Amazon Japan for similar products to this image, with delivery to China:
https://example.com/item.jpg
```

**6. Competitor lookalike discovery**
```
I found this product image on a competitor's listing. Find me all similar-looking products on Amazon UK:
https://example.com/competitor.jpg
```

## Display Rules

1. **Present data clearly**: Show search results in a well-structured table. Key columns to prioritize: product image, title, ASIN, price, rating, review count, and brand
2. **Image display**: When the response includes `imageUrl` for products, display them inline so users can visually compare results
3. **Price and currency**: Always show price alongside the currency code (e.g., $29.99 USD, 24.99 EUR)
4. **Keepa data**: When `aggregateByKeepaData` is enabled and Keepa fields are present, show supplementary data (monthly sales, sales rank, FBA fees) in an expanded section or additional columns
5. **Result count**: Always inform the user of the total number of results found (`total` / `totalCount`)
6. **Error handling**: When a query fails, explain the issue and suggest checking that the image URL is valid and publicly accessible
7. **Sort limitation**: If the user requests a sort order not in the supported list, clearly explain which sort options are available rather than attempting unsupported workarounds
8. **No secondary processing**: Results from this tool are not stored in a database, so secondary SQL processing is not available
## User Expression & Scenario Quick Reference

**Applicable** -- Visual product search scenarios on Amazon:

| User Says | Scenario |
|-----------|----------|
| "Find similar products to this image" | Basic image search |
| "Search by image", "reverse image search on Amazon" | Visual search |
| "Find competitor lookalikes", "find same-style products" | Competitor analysis by appearance |
| "What products on Amazon look like this" | Product discovery |
| "Find cheaper alternatives that look the same" | Price-based visual comparison |
| "Search Amazon JP/DE/UK for this product image" | Cross-marketplace visual search |
| "Show me Keepa data for similar products" | Enriched visual search |
| "Find products similar to this photo, sorted by rating" | Sorted visual search |

**Not applicable** -- Needs beyond image-based product search:

- Text-based keyword search on Amazon (use keyword search tools instead)
- ABA search term data analysis
- Product review analysis or listing optimization
- Sales estimation without a source image
- Image editing or image generation
- Searching with a local image file (the tool requires a publicly accessible URL)

**Boundary judgment**: When users say "find similar products" or "competitor analysis", if they provide an image URL and the intent is to find visually similar Amazon listings, this skill applies. If they are asking for keyword-based search, sales data analysis, or product research without an image, it does not apply.

## 积分消耗规则

按动态规则计费：消耗积分 = 15 + 0.045 × 本次商品详情查询消耗的 Keepa token。Keepa 部分单价 90 × 本次商品详情查询消耗的 Keepa token；若未触发 Keepa 聚合，则该部分为 0。；relevance api: linkfox-keepa-product-detail

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
