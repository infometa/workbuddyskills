---
name: layer1-fin-data
description: "Use when you need structured financial data such as prices, rankings, limit-up/limit-down screening, stock pattern counts, ETF/industry constituents, valuation metrics, macro time series, or financial indicators."
---

# Fin Data

Use this skill for read-only structured financial data queries.

Do not use this skill for price forecasts, direct buy/sell recommendations, position sizing, strategy backtests, or raw SQL execution.

User-facing outputs must preserve 证据来源、时间窗口、数据覆盖限制和安全边界；do not turn structured market data into direct investment advice.

## Runtime Binding

This skill defines the Fin Data logical source contract; it does not declare a separate user-visible MCP connection.

- In WorkBuddy, call Fin Data tools through the single `tongzhou-fin-research` Connector. Runtime tool names use `fin_data__<tool>`, for example `fin_data__get_latest_snapshot`.
- In Codex and retained legacy clients, the same canonical tool may appear as a bare name or a client-qualified server/tool name. Match the canonical tool suffix and keep the Fin Data source label.
- Do not bypass an available `tongzhou-fin-research` Connector by selecting a similarly named global or deferred financial tool.

## Progressive References

Load only the reference needed for the current question:

- `references/market.md`: latest price, historical series, index snapshots, market daily reports
- `references/screening.md`: rankings, filters, counts, limit-up/limit-down, consecutive patterns
- `references/entity.md`: security lookup, profiles, baskets, constituents, entity links
- `references/macro_financial.md`: macro indicators, commodities, rates, financial indicators, sector valuation
- `references/limitations.md`: data coverage, realtime wording, unsupported claims, safety boundaries

Read this skill's `references/<name>.md` file before filling detailed tool parameters.

For combination queries, read multiple references. Example: "白酒行业今日涨幅前五" may need `references/entity.md` for basket discovery and `references/screening.md` for ranking.

## Routing

Choose the narrowest tool family first:

The table uses canonical tool suffixes for readability. Under the WorkBuddy Connector, prepend `fin_data__` when selecting the actual tool.

| User intent | Read reference | Preferred tools |
|---|---|---|
| 最新价、当前多少钱、盘中指数表现 | `references/market.md` | `get_latest_snapshot` |
| 日K、蜡烛图、开高低收、均线 | `references/market.md` | `get_kline_series` |
| 单指标历史走势、分钟线 | `references/market.md` | `list_metrics`, `query_data` |
| 事件后市场反应、行业/ETF/指数事件窗口收益 | `references/market.md` | `compute_market_reaction_windows` |
| 今天大A表现、早午晚报、收盘总结 | `references/market.md` | `query_advisor_report`, `get_latest_snapshot`, `query_data` |
| 涨幅榜、跌幅榜、成交额榜、估值排序 | `references/screening.md` | `rank_securities`, `list_top_movers` |
| 涨停、跌停、低价股、行业内条件筛选 | `references/screening.md` | `screen_stocks` |
| 上涨/下跌数量、涨停家数、行业分布 | `references/screening.md` | `count_stocks` |
| 连涨 N 天、连跌 N 天、连续涨停 | `references/screening.md` | `detect_stock_patterns` |
| 股票/ETF/港股名称代码互查 | `references/entity.md` | `search_security`, `get_security_profile` |
| 行业、ETF、概念、主题成分 | `references/entity.md` | `search_baskets`, `list_constituents` |
| 宏观、黄金、利率、商品时间序列 | `references/macro_financial.md` | `list_featured_indicators`, `search_macro_indicators`, `query_macro_series` |
| 财务关键指标、ROE、毛利率、现金流 | `references/macro_financial.md` | `query_financial_indicators` |
| 申万行业估值 | `references/macro_financial.md` | `query_sector_valuation` |

## Required Rules

- Use MCP tools only. Never generate or pass raw SQL.
- Expose only virtual schema/tool names to users, not physical database tables or fields.
- Resolve relative time before calling tools: 今天/昨日/本周/本月/最近N天 must map to explicit dates or a supported relative window; 最近N个交易日 must use trading-day tools/`limit=N`, not calendar-day date ranges.
- Mention the returned `trade_date`, `report_date`, `data_timestamp`, or date range in the answer.
- If the returned trading date is different from the user's calendar phrase, state the returned trading date explicitly instead of hiding the mismatch.
- If a metric/tool is not available, say the current atomic capability is not covered. Do not invent data.
- Event-window market reactions are descriptive statistics from close prices. Do not call them strategy backtests, predictions, or investment advice.
- For common broad indices, use known standard codes directly: 上证指数 `000001.SH`, 深证成指 `399001.SZ`, 创业板指 `399006.SZ`, 沪深300 `000300.SH`.
- For uncommon securities, baskets, industries, concepts, themes, or macro indicators, search/resolve first instead of guessing IDs. For industry/theme rankings, prefer `search_baskets` before `rank_securities`/`screen_stocks`.
- Keep investment wording descriptive and evidence-based. Do not turn data into deterministic forecasts or direct recommendations.
- If a multi-part user question asks for market data plus another data domain, finish the market-data table/summary and then continue with the other domain before finalizing.
- Do not answer "will query / please wait" after tool use. Continue calling the needed tool or provide the completed answer.
- Treat a non-empty list/table in MCP output as retrieved evidence. Summarize those rows; do not call it an empty result.
- For investment-sensitive wording, unsupported claims, or empty-result caveats, read `references/limitations.md`.

## Output Shape

Prefer compact tables for lists and rankings. Include:

- name/code when applicable
- metric values and units when available
- date/time of the data
- any important limitation from `references/limitations.md`
