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

## Query Boundaries

- Never expose physical table names or fields to users.
- Never write or pass raw SQL.
- Use only whitelisted MCP tool parameters.
- Respect tool limits and returned result truncation.
- If the result is empty, say no matching records were returned under the current filters and date.

## Unsupported Claims

Do not claim support for:

- price/index forecasts
- direct stock recommendations
- position sizing or timing advice
- complete strategy backtests inside `mcp-fin-data`
- arbitrary technical indicators unless a matching MCP tool exists
- tick-level quotes, order book, trade-by-trade, or streaming market data

## Answering Style

- State uncertainty when explaining market moves.
- Do not turn correlation into certain causality.
- Add compliance-safe language for investment-sensitive questions.
