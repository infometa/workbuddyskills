---
name: linkfox-multimodal-product-similarity
description: 多模态产品图片相似度分析与分组。当用户提到产品图片相似度、视觉分组、查找外观相似的商品、基于图片去重、竞品同款检测、同款商品聚类、按外观分组、image similarity, product image comparison, visual clustering, same-style recognition, appearance deduplication, image grouping时触发此技能。即使用户未明确说"图片相似度"，只要其意图涉及商品主图对比、视觉聚类、识别视觉上相同或相似的商品，或根据外观、颜色、构图等视觉特征对商品列表进行后处理，也应触发此技能。
---

# Multimodal Product Image Similarity Analysis

This skill guides you on how to analyze and group products by the visual similarity of their main images. It helps Amazon sellers identify same-style products, detect competitor lookalikes, and organize product lists into visually coherent clusters.

## Core Concepts

Product Image Similarity Analysis uses multimodal AI to compare the main images of products and automatically group them based on visual features such as appearance, color, composition, and material. It is a **post-processing** tool -- it operates on product data that has already been retrieved by a preceding step (e.g., product search, product recommendations).

**Similarity threshold**: The `similarityThreshold` parameter controls how visually close two products must be to land in the same group. It is an integer from 0 to 100 representing a percentage. A higher value means stricter matching (only near-identical images group together); a lower value means more lenient matching (broader visual clusters). The default is **60**.

**Single-brand group filtering**: The `includeSingleBrandGroups` flag (default `true`) controls whether groups containing products from only one brand are included in the results. Setting it to `false` filters out single-brand groups, which is useful when the user wants to focus on cross-brand visual overlaps (e.g., competitor lookalike analysis).

## Input Data Requirement

This tool requires a `products` list from a preceding step. It cannot fetch product data on its own. The typical workflow is:

1. Run a product search or recommendation tool to obtain a product list.
2. Pass that product list into this tool via `refResultData` for visual similarity grouping.

The input data must be a JSON object containing a `products` array.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| similarityThreshold | integer | No | Similarity threshold (0-100), default `60`. Higher = stricter matching. |
| includeSingleBrandGroups | boolean | No | Whether to include groups with only one brand, default `true`. Set to `false` to focus on cross-brand similarity. |
| refResultData | string | No | JSON string of the preceding tool's result data containing the product list. |
| userInput | string | No | The original user query or instruction text. |

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| groups | array | List of similarity groups. Each group contains `groupNumber`, `reason`, `brandCount`, and an `asins` array of product details. |
| analysisInfo | object | Summary: `totalProductsAnalyzed`, `totalGroupsFound`, `similarityThreshold`, `analysisTimestamp`. |
| tables | array | Tabular result data, each element with `data`, `columns`, and `name`. |
| total | integer | Total number of result items. |
| title | string | Result title. |
| type | string | Rendering style hint. |
| costToken | integer | Total LLM tokens consumed (input + output). |

### Group Item (asins array element)

| Field | Type | Description |
|-------|------|-------------|
| asin | string | Product ASIN |
| productId | string | Product ID |
| brand | string | Brand name |
| price | number | Price |
| rating | number | Rating score |
| ratings | integer | Number of ratings |
| monthlySalesUnits | integer | Monthly sales units |
| monthlySalesRevenue | number | Monthly sales revenue |
| monthlySalesUnitsGrowthRate | number | Monthly sales growth rate |
| imageUrl | string | Main image URL |
| productImageUrls | array | All product image URLs |
| imagePrompt | string | AI-generated image description |
| asinUrl | string | Product detail page URL |
| availableDate | string | Listing date |
| color | string | Color |
| material | string | Material |

## 调用方式

- **API 端点**：`POST /multimodal/analyzeProductSimilarity`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/multimodal_analyze_product_similarity.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-multimodal-product-similarity-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

**1. Group search results by visual similarity (default threshold)**
After obtaining a product list from a search tool, pass the results to this tool to cluster visually similar items:
```
User: "Group these products by how similar they look."
Action: Call the API with refResultData set to the preceding product list JSON, using the default similarityThreshold of 60.
```

**2. Find near-identical products (strict matching)**
```
User: "Which of these products have almost the same main image?"
Action: Call the API with similarityThreshold set to 85 or higher for strict visual matching.
```

**3. Cross-brand competitor lookalike detection**
```
User: "Show me groups where different brands have similar-looking products."
Action: Call the API with includeSingleBrandGroups set to false to filter out single-brand clusters.
```

**4. Broad visual clustering (lenient threshold)**
```
User: "Roughly categorize these products by appearance."
Action: Call the API with similarityThreshold set to 40 for broad grouping.
```

**5. Combined: strict similarity across brands**
```
User: "Find products from different brands that look nearly identical."
Action: Call the API with similarityThreshold set to 80 and includeSingleBrandGroups set to false.
```

## Display Rules

1. **Present grouping results clearly**: Show each similarity group with its group number, the reason for grouping, brand count, and a table of products within the group.
2. **Show product images when possible**: If image URLs are available, include them to help users visually verify the grouping.
3. **Highlight cross-brand groups**: When the user cares about competitor analysis, emphasize groups containing multiple brands.
4. **Analysis summary**: Always present the analysis summary (total products analyzed, total groups found, similarity threshold used, timestamp).
5. **No subjective advice**: Present the grouping data objectively. Do not inject business recommendations unless the user asks.
6. **Large result sets**: When there are many groups, show the most significant ones first (e.g., groups with the most products or the most brands) and inform the user about additional groups.
7. **Error handling**: When a request fails, explain the reason based on the response message and suggest adjustments (e.g., check that the input product data is valid, adjust the threshold).
## Important Limitations

- **Post-processing only**: This tool cannot fetch product data on its own. It must receive product data from a preceding step.
- **No database storage**: Results are not stored in a database. Do not use database query tools for secondary analysis on the output.
- **Input format**: The input must be a JSON object containing a `products` array.
- **Direct to summary**: After this tool completes, pass the results directly to the summary stage. Do not perform additional intermediate data computations.

## User Expression & Scenario Quick Reference

**Applicable** -- Visual similarity analysis on product lists:

| User Says | Scenario |
|-----------|----------|
| "Group these by how they look" | Visual clustering |
| "Find similar-looking products", "find lookalikes" | Similarity detection |
| "Which products look the same" | Image deduplication |
| "Show me competitor copycats" | Cross-brand lookalike analysis |
| "Cluster by appearance / color / style" | Visual categorization |
| "Are there duplicates in this list" | Image-based dedup |
| "Same-style products from different brands" | Cross-brand similarity |

**Not applicable** -- Needs beyond image similarity:

- Text-based product comparison (titles, descriptions, keywords)
- Price or sales-based grouping without visual component
- Product search or discovery (this tool only post-processes existing lists)
- Review analysis, listing optimization, advertising strategy

## 积分消耗规则

按动态规则计费：消耗积分 = sum(每个商品主图提示词生成调用的(输入消耗的积分 + 输出结果消耗的积分))。

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
