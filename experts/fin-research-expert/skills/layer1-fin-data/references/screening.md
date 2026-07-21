# Screening Reference

Use for:
- single-day TopN ranking: 涨幅榜、跌幅榜、成交额榜、换手率榜、估值排序
- single-day controlled filters and counts: 涨停/跌停股票、低价股、上涨/下跌数量、行业分布
- multi-day window patterns: 连涨 N 天、连跌 N 天、连续 N 天涨停/跌停

Tools:

## TopN Ranking

### rank_securities
- Use for TopN ranking.
- `sort_by`: `change_ratio` | `amount` | `turnover_rate` | `pe_ttm` | `pb` | `market_cap`.
- `sort_order`: `desc` for top/highest, `asc` for bottom/lowest.
- For industry/theme/concept wording such as 半导体、新能源、低空经济, resolve with `search_baskets` first; then pass `basket_type`/`basket_id` or the exact returned industry name.

### list_top_movers
- Shortcut for gainers/losers.

## Single-Day Filters And Counts

### screen_stocks
- Use for single-day controlled filters.
- 今日涨停股票 -> `status="limit_up"`.
- 今日跌停股票 -> `status="limit_down"`.
- 股价低于10元 -> `max_close=10`.
- 白酒行业低于50元 -> `industry="白酒", max_close=50`.

### count_stocks
- 今日上涨多少家 -> `min_change_ratio=0`.
- 今日下跌多少家 -> `max_change_ratio=0`.
- 今日涨停多少家 -> `status="limit_up"`.
- 涨停分布在哪些行业 -> `status="limit_up", group_by="industry"`.
- `group_by`: `industry` | `status` | `board`.

## Multi-Day Patterns

### detect_stock_patterns
- `pattern`: `up_days` | `down_days` | `limit_up_days` | `limit_down_days`.
- 连涨3天 -> `pattern="up_days", days=3`.
- 连跌3天 -> `pattern="down_days", days=3`.
- 连续3天涨停 -> `pattern="limit_up_days", days=3`.

Rules:
- These tools currently support A-share daily data first.
- Resolve relative dates before tool calls. 今天/昨日 should normally omit `trade_date` first and use the latest returned trading date; only pass `trade_date` when the user gives an explicit date.
- Always mention actual returned trade date.
- Do not use single-day rank tools to fake consecutive patterns.
- If the query asks for a technical indicator screen such as MACD/RSI/MA, state that the current atomic tool is not covered unless a dedicated tool is available.
- For empty results, report the filters and date rather than inventing examples.
- For unsupported claims and investment-sensitive answering style, also read `references/limitations.md`.
