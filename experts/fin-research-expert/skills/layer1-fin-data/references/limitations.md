# Limitations

## Realtime Wording

- Data is not a tick-by-tick realtime feed.
- For latest price questions, prefer `get_latest_snapshot` and report the returned timestamp.
- Index latest snapshots may be derived from the latest available minute bar; describe them as latest available data, not official tick-level realtime data.
- Do not use minute data as a substitute for a true realtime quote.

## Coverage

- A-share, ETF, index, concept, sector valuation, macro, and financial data coverage depends on the MCP response.
- Historical coverage varies by market and table. Do not promise arbitrary years.
- Minute data is partial and should be treated as a single-day query surface unless the MCP response says otherwise.
- Financial indicators are key metrics snapshots, not full financial statement line items.
- Macro indicators are not a complete global macro database. Search indicators first when unsure.
- `USDCNY_mid` is the USD/CNY central-parity series, not onshore spot CNY. Do not substitute offshore `USDCNH` for either one.
- `spot_CNY` and CFETS RMB indices remain unsupported until an authorized source is explicitly connected and returned by the tools.
- HK identity and daily-market coverage may be partial; identity success does not imply complete HK fundamentals, announcements, or research coverage.

## Query Boundaries

- Never expose physical table names or fields to users.
- Never write or pass raw SQL.
- Use only whitelisted MCP tool parameters.
- Respect tool limits and returned result truncation.
- If the result is empty, say no matching records were returned under the current filters and date.
- A successful non-empty response with missing fields is `partial`; preserve its valid values, dates, units, and quality flags.
- An unsupported market/metric is `unsupported`, while validation, timeout, dependency, and transport failures are `error`. Neither is an empty result and neither may be replaced with a related security or example value.
- `cache_status="stale"` is a labeled recent fallback after a live query failure, not current or realtime evidence.
- ETF candidate ranking has no AUM, bid/ask spread, order book, or realtime creation/redemption data.

## Unsupported Claims

Do not claim support for:

- price/index forecasts
- direct stock recommendations
- position sizing or timing advice
- complete strategy backtests inside `mcp-fin-data`
- arbitrary technical indicators unless a matching MCP tool exists
- tick-level quotes, order book, trade-by-trade, or streaming market data
- ETF suitability, personalized fund selection, or ranking on unavailable AUM/spread fields

## Answering Style

- State uncertainty when explaining market moves.
- Do not turn correlation into certain causality.
- Add compliance-safe language for investment-sensitive questions.
