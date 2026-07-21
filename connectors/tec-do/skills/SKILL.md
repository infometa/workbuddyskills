---
name: tec-do-guide
description: Guide WorkBuddy on when and how to use the Tec-Do MCP tools and local Skill blueprints for ad benchmarks, TikTok ad research, competitor analysis, and VOC sentiment analysis for global advertising and growth teams.
description_zh: 指导 WorkBuddy 何时以及如何使用 Tec-Do MCP 的工具和本地 Skill 蓝图，为出海广告投放和增长团队完成广告基准查询、TikTok 广告研究、竞品分析和用户口碑分析。
description_en: Guide WorkBuddy on when and how to use the Tec-Do MCP tools and local Skill blueprints for ad benchmarks, TikTok ad research, competitor analysis, and VOC sentiment analysis for global advertising and growth teams.
version: "1.0.0"
author: "tec-do"
---

This Connector exposes four Tec-Do 2.0 Ad & Growth Intelligence capabilities: two remote MCP tools and two local Skill blueprints.

## How to use
1. After the MCP is connected and a user sends a message, inspect the Connector
   capabilities before answering from general knowledge. In WorkBuddy this means
   using the MCP tool catalog exposed by `tools/list`.
2. Call `tools/list` to discover the current four tools.
3. For either remote MCP tool, call it directly with `tools/call`.
4. For either local Skill, call `tools/call` to get its blueprint: name,
   description, workflow, constraints, and reference URIs.
5. Call `resources/read` for each referenced file you need.
6. Execute blueprint-only Skills yourself following the returned instructions;
   the Server does not run Skill scripts or produce output files.

## Current Tool Catalog
- `get_ad_benchmark` — Remote MCP tool for CPM, CTR, CPC, and other ad benchmark data by country, platform, and industry.
- `ttcc_search_top_ads` — Remote MCP tool for TikTok top-ad search and performance data such as impressions, click-through-rate rank, and completion rate.
- `competitor-analysis-report` — Local Skill for structured competitor analysis, including feature comparison, pricing analysis, SWOT, and strategy recommendations.
- `voc-sentiment-analysis` — Local Skill for voice-of-customer (VOC) and sentiment analysis from forums and review sites.

## Remote MCP Interface Reference

### `get_ad_benchmark`

Route: `/mcp/benchmark`

Retrieves advertising benchmark data across countries/regions, platforms, and industries, including CPM, CTR, and CPC. Use it for advertising-cost estimation, ROI calculations, product selection, competitor analysis, market research, and trend analysis.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | A natural-language query. Include country/region, platform, industry/category, and desired metrics where possible. Returns aggregated data if no metric is specified. |

Examples:

- `Get CPM benchmarks for the gaming industry on Facebook in the United States`
- `Get CTR and CPC data for ecommerce on Google in China`
- `Get advertising benchmarks for casual games on TikTok`

Returns advertising benchmark data for cost estimation and ROI calculations.

### `ttcc_search_top_ads`

Route: `/mcp/ttcc_agent`

Searches TikTok Creative Center top ads and returns ad titles, brands, video details, impressions, click-through-rate rankings, completion-rate rankings, and other performance data. Use it for creative research, competitor ad-strategy analysis, inspiration, and market-trend research.

| Parameter | Type | Required | Default / Description |
|---|---|---|---|
| `keyword` | string | Yes | Search keyword. English keywords are recommended. |
| `country_code` | string | No | Comma-separated country codes. Default: `SG,US`. |
| `order_by` | string | No | Default: `impression`. Options: `for_you`, `impression`, `like`, `ctr`, `play_2s_rate`, `play_6s_rate`, `cvr`. |
| `period` | integer | No | Default: `30`. Options: `7`, `30`, or `180` days. Other values are rounded up to the nearest supported period. |
| `limit` | integer | No | Default: `15`; maximum: `50`. |

Returns a list of top ads. Each item can include `id`, `ad_title`, `brand_name`, `video_info`, `like`, `cost`, `cost_readable`, and `analytics`.

High-performing-ad guidance:

- `ctr_ranking` is a percentile ranking, not an actual click-through rate. Lower is better; `≤ 0.10` represents the top 10%.
- `cost_readable: "High Budget"` usually indicates substantial budget investment and can be a useful signal of a validated creative.
- Evaluate both `ctr_ranking` and `cost_readable`; do not rely on either metric alone.

## Notes
- In WorkBuddy, these tools are displayed with the Connector prefix (for example, `mcp__tec-do__get_ad_benchmark`).
- `tools/list` remains the source of truth for availability.
