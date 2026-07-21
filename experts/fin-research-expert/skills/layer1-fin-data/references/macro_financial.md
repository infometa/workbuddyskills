# Macro And Financial Reference

Use for:
- CPI、PMI、利率、汇率、黄金、商品等宏观指标
- ROE、毛利率、现金流、营收/利润同比等财务关键指标
- 申万行业 PE/PB 估值分析

Tools:

## list_featured_indicators
- Use to inspect common macro indicators by category.

## search_macro_indicators
- Use for oral names and fuzzy macro queries.
- Examples: 伦敦金、联邦基金利率、CPI、PMI.
- Prefer returned `indicator_id` for the next query.

## query_macro_series
- Use after indicator is identified.
- Prefer `indicator_id` over name.

## query_financial_indicators
- Use for A-share financial key indicators.
- Use `fiscal_year` / `fiscal_period` when user specifies reporting period.

## query_sector_valuation
- Use for industry PE/PB valuation and historical percentile.

Rules:
- Current financial tool is key-indicator snapshot, not full financial statement detail.
- Macro indicator catalog is not exhaustive; search first if unsure.
- For impact analysis, combine data with doc/news MCP and use uncertainty language.
- For price forecasts, policy impact claims, or investment-sensitive wording, also read `references/limitations.md`.
