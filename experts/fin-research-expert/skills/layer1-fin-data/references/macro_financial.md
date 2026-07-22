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
- Examples: 伦敦金、联邦基金利率、CPI、PMI、USDCNY_mid、人民币中间价.
- Prefer returned `indicator_id` for the next query.

## query_macro_series
- Use after indicator is identified.
- Prefer `indicator_id` over name.
- A response is one descending-date page. When `has_more=true`, pass `next_cursor` unchanged to fetch older observations.
- Do not claim full historical coverage until pagination reaches `has_more=false` or the requested `start_date`.

## RMB FX Routing

- `USDCNY_mid`, `美元兑人民币中间价`, and `人民币中间价` all mean the USD/CNY central-parity series. Search the alias first, then query the returned `indicator_id`.
- Preserve the returned source, date, unit, and frequency. Do not rename central parity as `spot_CNY`, 境内即期价, 收盘价, or offshore `USDCNH`.
- DR007 and USD/CNY central parity can use `query_macro_series` for dated history. For a compact current macro panel, Fin Graph `get_macro_data` may be used as a sibling source.

## query_financial_indicators
- Use for A-share financial key indicators.
- Use `fiscal_year` / `fiscal_period` when user specifies reporting period.

## query_sector_valuation
- Use for industry PE/PB valuation and historical percentile.

Rules:
- Current financial tool is key-indicator snapshot, not full financial statement detail.
- Macro indicator catalog is not exhaustive; search first if unsure.
- `spot_CNY` and CFETS RMB index series must remain `unsupported` until a matching authorized series is returned. Do not substitute central parity or `USDCNH`.
- For impact analysis, combine data with doc/news MCP and use uncertainty language.
- For price forecasts, policy impact claims, or investment-sensitive wording, also read `references/limitations.md`.
