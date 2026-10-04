---
name: linkfox-sif-asin-keywords
description: 使用SIF数据反查任意亚马逊ASIN的流量关键词，包括自然排名、广告排名、搜索量、流量占比、自然/付费得分、ABA TOP3点击集中度、点击转化率、搜索量同比涨跌及周/月时间窗。当用户提到ASIN关键词分析、ASIN反查、流量关键词研究、自然排名查询、广告排名查询、关键词位置追踪、SIF关键词数据、竞品关键词窥探、查看哪些关键词为产品带来流量、分析特定ASIN的关键词表现、按周/月/最近N天的关键词时间窗、ASIN reverse keyword lookup, traffic keywords, organic ranking, ad ranking, search volume, SIF keywords, competitor keyword reverse lookup, click concentration, click-to-purchase conversion, week-over-week search volume时触发此技能。即使用户未明确提及"SIF"，只要其需求涉及查找与特定亚马逊商品（ASIN）关联的关键词，也应触发此技能。
---

# SIF ASIN Keyword Analysis

This skill guides you on how to query and analyze traffic keywords for a specific Amazon ASIN, helping Amazon sellers understand which keywords drive traffic to a product and how that product ranks for each keyword.

## Core Concepts

SIF ASIN Keyword data reveals the keywords that bring traffic to a specific Amazon product (ASIN). For each keyword, you can see the product's organic search rank, SP ad rank, search volume, traffic share, display position types, and various performance markers. This is the go-to tool for reverse ASIN keyword lookup.

**Single-ASIN limitation**: This tool queries one ASIN at a time. If the user wants to compare multiple ASINs, you must make separate queries for each.

**Ranking logic**: A smaller rank value means a better (higher) position. Rank 1 means the product appears first in search results. When a user says "ranking improved", the numeric value decreased; "ranking dropped" means the value increased.

## Data Fields

### Per-keyword record (each element of `data`)

| Field | API Name | Description | Example |
|-------|----------|-------------|---------|
| Keyword | keyword | The search keyword driving traffic | wireless charger |
| Keyword Translation | translateKeyword | Localized keyword translation for the marketplace | 无线充电器 |
| ASIN | asin | The product ASIN being queried | B0XXXXXXXX |
| Organic Rank | productNaturalRank | Product's position in organic search results | 5 |
| Organic Rank (Display) | naturalRankDisplay | Organic rank as display text | 5 |
| Ad Rank | productAdRank | Product's position in SP ad results | 3 |
| Ad Rank (Display) | adRankDisplay | Ad rank as display text | 3 |
| Weekly Search Volume | weeklySearchVolume | Estimated weekly searches for this keyword | 125000 |
| Keyword Popularity Rank | keywordPopularityRank | Keyword's search volume rank among all keywords (lower = more popular) | 203 |
| Total Search Result Products | totalSearchResultProductCount | Total products shown under this keyword (organic + ads + recommendations) | 1280 |
| Traffic Share | trafficShare | Share of traffic this keyword contributes to the ASIN (1 = 100%) | 0.05 |
| Natural Traffic Share | naturalTrafficShare | Organic exposure score / total score | 0.62 |
| Paid Traffic Share | paidTrafficShare | Paid-ad exposure score / total score (SP + SB + SBV + recAd) | 0.31 |
| Natural Traffic Score | naturalTrafficScore | Organic search exposure score for this ASIN on this keyword (0 = none) | 4.2 |
| SP Ads Score | sponsoredProductsScore | Sponsored Products regular-slot score (excludes SP recommendation slots) | 2.1 |
| Brand Ad (SB) Score | brandAdScore | Sponsored Brands total score (standard + video) | 0.8 |
| Video Ad (SBV) Score | videoAdScore | Sponsored Brands Video score | 0.3 |
| SP Recommendation Score | sponsoredRecommendationScore | Combined score across SP recommendation slots (Trending now, Seen on social media, Customers frequently viewed, 4 stars and above, etc.) | 1.4 |
| SP Recommendation Breakdown | sponsoredRecommendationBreakdown | Array of `{title, score, scoreRatio}` per SP recommendation slot | [{"title":"Trending now","score":0.8,"scoreRatio":0.57}] |
| ABA TOP3 Click Concentration | clickConcentrationShare | Whether clicks under this keyword concentrate on the top ASINs (NOT a conversion rate) | 0.42 |
| Click-to-Purchase Conversion | clickToPurchaseConversionRate | `purchaseQty / clickQty` at the keyword level | 0.037 |
| Display Position Types | displayPositionTypes | Where the product appears: natural, ac, sp, top, bottom, er, vedio, tr, trfob | ["natural", "sp"] |
| Traffic Characteristic Markers | trafficCharacteristicMarkers | Traffic feature tags: isMainKw, isAccurateKw, isAccurateAboveKw, isAccurateTailKw | ["isMainKw"] |
| Conversion Performance Markers | conversionPerformanceMarkers | Conversion tags: isPurchaseKw, isQualityKw, isStableKw, isLossKw, isInvalidKw | ["isPurchaseKw"] |
| Last Organic Rank Time | lastNaturalRankTime | When the product last had a valid organic rank for this keyword | 2026-04-20 |
| Last Ad Rank Time | lastAdRankTime | When the product last had a valid SP ad rank for this keyword | 2026-04-20 |
| Period End Date | periodEndDate | End date of the current (weekly) period = start-week + 7 days | 2026-04-27 |
| Update Time | updateTime | When the keyword data was last updated | 2026-04-21 |

### Top-level response fields (alongside `data`)

| Field | API Name | Description |
|-------|----------|-------------|
| Is Parent ASIN | isParentAsin | Whether the queried ASIN is a parent (variation hub) |
| Has Variants | hasVaiants | Whether the ASIN has variants |
| Latest ABA Week | abaCreateDateWeek | Latest ABA weekly data reference date |

## Supported Marketplaces

13 marketplaces: US (United States), UK (United Kingdom), DE (Germany), CA (Canada), JP (Japan), FR (France), ES (Spain), IT (Italy), MX (Mexico), AU (Australia), AE (United Arab Emirates), BR (Brazil), SA (Saudi Arabia).

Default marketplace is **US**. Use US when the user does not specify a marketplace. Codes outside this list will be rejected by the API pattern.

## 调用方式

- **API 端点**：`POST /sif/asinKeywords`（完整参数/响应/错误码见 `references/api.md`）
- **Python 脚本**：`python scripts/sif_asin_keywords.py '<JSON 参数>' [--inline]`
- **成本约束**：本工具会消耗积分；同一会话同一参数组合默认只调用一次，脚本带 24h 本地缓存。失败/空结果不得自动换关键词、翻页或改邮编连续试探；需要继续检索时先向用户说明会产生额外消耗。

**输出策略（脚本默认行为）**：
- **始终**将完整响应写入 `<cwd>/linkfox/<YYYY-MM-DD>/<session>/data/linkfox-sif-asin-keywords-<timestamp>.json`（`<cwd>` 为脚本执行时的工作目录，在 Claude Code 里即当前项目目录；`<session>` 取自环境变量 `SESSION_ID`，按用户任务自动聚合；**禁止写入 /tmp**，当前目录不可写则报错）
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

## Parameter Guide

### Required Parameter

- **asin** (string, required): The Amazon ASIN to look up. Only one ASIN per request.

### Optional Parameters

- **country** (string, default `US`): Marketplace code. See Supported Marketplaces above.
- **keyword** (string): Filter results to keywords containing this text. Translate the keyword into the language of the target marketplace when possible.
- **timePieceType** (string, default `latelyDay`): Time window type — `latelyDay` (most recent N days), `month` (specific month), `week` (specific week).
- **timePieceValue** (string, default `7`): Value paired with `timePieceType`.
  - When `timePieceType=latelyDay` → only `7` or `30` are supported
  - When `timePieceType=month` → `YYYY-MM` (e.g. `2026-04`)
  - When `timePieceType=week` → the week's start date `YYYY-MM-DD` (e.g. `2026-04-13`)
- **conditions** (string): Comma-separated condition filters. Flag-style filters:
  - `nfPosition` -- organic traffic keywords
  - `isSpAd` -- SP ad keywords
  - `isBrandAd` -- brand ad keywords
  - `isVedioAd` -- video ad keywords
  - `isAC` -- Amazon's Choice keywords
  - `isAccurateKw` -- precise traffic keywords
  - `isAccurateTailKw` -- precise long-tail keywords
  - `isPurchaseKw` -- purchase-converting keywords
  - `isQualityKw` -- high-quality conversion keywords
  - `isStableKw` -- stable conversion keywords
  - `isLossKw` -- conversion-loss keywords
  - `isInvalidKw` -- invalid-exposure keywords
  - `isMultiVariantKw` -- keywords ranking organically across multiple variants
  - `isSearchVolUpKw` -- keywords whose search volume increased year-over-year
  - `isSearchVolDownKw` -- keywords whose search volume decreased year-over-year

  Period-count filters (all / new-in):
  - `totalPeriod.in` -- newly-entered traffic keywords this period
  - `nfKeywordCnt.total` / `nfKeywordCnt.in` -- keywords with (new) organic exposure
  - `adKeywordCnt.total` / `adKeywordCnt.in` -- keywords with (new) ad exposure
  - `allSpKeywordCnt.total` / `allSpKeywordCnt.in` -- (new) SP-ad keywords (regular + recommendation)
  - `spKeywordCnt.total` / `spKeywordCnt.in` -- (new) SP regular keywords
  - `recSpKeywordCnt.total` / `recSpKeywordCnt.in` -- (new) SP recommendation keywords
  - `allSbKeywordCnt.total` / `allSbKeywordCnt.in` -- (new) SB-ad keywords
  - `sbKeywordCnt.total` / `sbKeywordCnt.in` -- (new) SB regular keywords
  - `sbvKeywordCnt.total` / `sbvKeywordCnt.in` -- (new) SBV keywords
- **sortBy** (string): Sort field. Options: `lastRank` (organic rank), `adLastRank` (ad rank), `updateTime` (update time), `searchesRank` (search popularity rank), `estSearchesNum` (monthly search volume).
- **desc** (boolean, default `true`): Sort in descending order. Set to `false` for ascending.
- **pageNum** (integer, default `1`): Page number for pagination.
- **pageSize** (integer, default `100`, range 10-100): Number of results per page.

### Building Effective Queries

1. **Always specify the marketplace**: Set `country` to one of the 13 supported codes.
2. **Pick the right time window**: The default is the latest 7 days. Pass `timePieceType=month` + `timePieceValue=YYYY-MM` for a specific month, or `timePieceType=week` + `timePieceValue=YYYY-MM-DD` for a specific ABA week.
3. **Use keyword filtering**: When the user is interested in specific keywords, pass the `keyword` parameter to narrow results.
4. **Apply condition filters**: Use `conditions` to focus on specific keyword types (e.g., only organic keywords, only purchase-converting keywords, or newly-entered SP keywords via `spKeywordCnt.in`).
5. **Choose appropriate sorting**: Sort by `estSearchesNum` for highest search volume keywords, or by `lastRank` for best-ranking keywords.
6. **Handle pagination**: The API returns at most 100 results per page. Use `pageNum` to retrieve additional pages if the total exceeds 100.

## Usage Examples

**1. Find all traffic keywords for an ASIN on the US marketplace**
```
asin: "B0XXXXXXXX", country: "US"
```

**2. Find organic traffic keywords only**
```
asin: "B0XXXXXXXX", country: "US", conditions: "nfPosition"
```

**3. Find keywords containing "charger" sorted by search volume (ascending)**
```
asin: "B0XXXXXXXX", country: "US", keyword: "charger", sortBy: "estSearchesNum", desc: false
```

**4. Find high-converting keywords**
```
asin: "B0XXXXXXXX", country: "US", conditions: "isPurchaseKw,isQualityKw"
```

**5. Find SP ad keywords on the Japan marketplace**
```
asin: "B0XXXXXXXX", country: "JP", conditions: "isSpAd", sortBy: "adLastRank", desc: false
```

**6. Find precise long-tail keywords with stable conversion**
```
asin: "B0XXXXXXXX", country: "US", conditions: "isAccurateTailKw,isStableKw"
```

**7. Find newly-entered SP traffic keywords in April 2026**
```
asin: "B0XXXXXXXX", country: "US", timePieceType: "month", timePieceValue: "2026-04", conditions: "spKeywordCnt.in"
```

**8. Find keywords whose search volume is trending up**
```
asin: "B0XXXXXXXX", country: "US", conditions: "isSearchVolUpKw", sortBy: "estSearchesNum", desc: true
```

## Display Rules

1. **Present data only**: Show query results in clear tables without subjective business advice.
2. **Ranking clarification**: When showing ranking data, remind users that lower numeric values mean better (higher) positions.
3. **Share formatting**: Display `trafficShare`, `naturalTrafficShare`, `paidTrafficShare`, and `clickConcentrationShare` as percentages (multiply by 100). For example, 0.05 should be shown as 5%.
4. **Click concentration wording**: `clickConcentrationShare` measures how concentrated clicks are on top ASINs under the keyword — it is NOT a conversion rate. Label it clearly so users don't confuse it with `clickToPurchaseConversionRate`.
5. **Period disclosure**: When showing counts sourced from `*.in`/`*.total` filters or comparing numbers, annotate the period range — default is last 7 days; if `timePieceType=month` or `week` is set, surface the resolved period (`periodEndDate` / `abaCreateDateWeek`).
6. **Marker translation**: Translate marker arrays into human-readable labels. For example, `["isMainKw", "isAccurateKw"]` should display as "Main Traffic, Precise Traffic".
7. **Display position translation**: Translate position type arrays into readable labels: natural = Organic, ac = Amazon's Choice, sp = SP Ad, top = Top Brand Ad, bottom = Bottom Brand Ad, er = Editorial Recommendation, vedio = Video Ad, tr = Top Rated, trfob = Top Rated Frequently Bought.
8. **Pagination notice**: When results have more pages, inform the user of the total count and suggest fetching additional pages.
9. **Error handling**: When a query fails, explain the reason based on the `msg` field and suggest adjusting query parameters.
10. **Multi-ASIN requests**: If the user asks about multiple ASINs, make separate API calls for each and present the results together.
## Important Limitations

- **Single ASIN per request**: Only one ASIN can be queried at a time.
- **Page size cap**: Maximum 100 results per page.
- **Time window granularity**: `timePieceType=latelyDay` only supports `timePieceValue=7` or `30`; arbitrary N-day windows are not supported.
- **Marketplace coverage**: 13 marketplaces only — IN / NL / SE / PL / TR / SG are no longer available.
- **Keyword language**: The `keyword` filter should ideally be in the language of the target marketplace.

## User Expression & Scenario Quick Reference

**Applicable** -- Keyword analysis for specific Amazon products:

| User Says | Scenario |
|-----------|----------|
| "What keywords does this ASIN rank for" | Reverse ASIN keyword lookup |
| "Show me the traffic keywords for B0XXX" | Traffic keyword analysis |
| "What's the organic rank for this product" | Organic ranking check |
| "Which keywords is this product advertising on" | Ad keyword analysis |
| "Find high-converting keywords for this ASIN" | Conversion keyword mining |
| "What are the main traffic sources for this product" | Main traffic keyword identification |
| "Show me keywords with lost conversions" | Conversion loss diagnosis |
| "Which keywords have Amazon's Choice badge" | AC keyword discovery |
| "Compare keyword rankings for my ASIN" | Keyword position analysis |
| "Which new SP keywords did this ASIN get last month" | New-in period keyword discovery (`spKeywordCnt.in` + month window) |
| "Keywords whose search volume is trending up YoY" | Search-volume trend filter (`isSearchVolUpKw`) |
| "Is click concentration high on this keyword" | ABA TOP3 click concentration read |
| "Keyword click-to-purchase conversion" | Per-keyword conversion check |

**Not applicable** -- Needs beyond single-ASIN keyword lookup:
- Broad keyword research not tied to a specific ASIN (use ABA data tools instead)
- Product reviews, listing copywriting
- Sales estimation, revenue analysis
- Advertising campaign management (bids, budgets)
- Category-wide keyword trends without a specific ASIN

## 积分消耗规则

消耗 9 积分。

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
