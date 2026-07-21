# Market Reference

Use for:
- 最新价、当前价格、实时/接近实时快照
- 个股、ETF、港股、指数、概念的历史走势
- 普通问答 K 线、收盘趋势和事件收益图所需的结构化证据
- 大盘早盘、午盘、收盘总结

Tools:

## get_latest_snapshot
- Use when user asks 最新价、当前价格、现在多少钱、盘中表现.
- `ticker`: required.
- `market`: `a_stock` | `index`.
- Common indices: 上证指数 `000001.SH`, 深证成指 `399001.SZ`, 创业板指 `399006.SZ`, 沪深300 `000300.SH`.

## list_metrics
- Use before `query_data` when the requested metrics or market/granularity support are uncertain.
- Do not use it to resolve common broad index codes; use the known standard codes above.

## get_kline_series
- Use for 日K、蜡烛图、开高低收、成交量带 or bounded simple moving averages.
- `market`: `a_stock` | `etf` | `hk_stock` | `index` | `concept`.
- Current scope is `granularity=daily` and `adjustment=none`; never describe the result as forward- or backward-adjusted.
- 最近 N 个交易日 -> use `limit=N` without converting it to a calendar-day range.
- `moving_average_windows` supports at most three values from `5,10,20,30,60`.
- Consume ascending `points`, optional `overlays`, `evidence_window`, `unit` and `quality` directly. Do not re-sort, repair OHLC, or replace insufficient points.
- If `quality.latest_bar_status=partial`, say the latest daily bar may still change. If `quality.status=insufficient_data`, return the quality explanation instead of drawing a K line.
- The result is already `chart-evidence/1`. Pass its evidence to `layer2-research-visuals`; do not rebuild it with a local script.

## query_data
- Use for generic historical daily/minute metrics and simple one-series trends; prefer `get_kline_series` for daily candlesticks.
- `market`: `a_stock` | `etf` | `hk_stock` | `index` | `concept`.
- `granularity`: `daily` | `minute`.
- Minute data is partially supported and must stay within a single day.
- 最近 N 个交易日收盘价/走势 -> do not provide calendar `start_date`; call `query_data(metrics=["close"], limit=N)` and use the returned trading dates.
- 本周/本月/最近 N 天 -> convert to explicit `start_date`/`end_date` only when the user asks for calendar periods, and mention returned trading dates.
- 简单走势图 -> request only the series needed, normally `close`; do not fetch OHLCV merely to make a more complex chart.
- Parse `results.<virtual_table>.columns` together with its `rows`; `raw_preview` is only a small preview and cannot represent the complete requested chart window.
- Sort returned valid points by trading time ascending for presentation, while preserving the exact returned dates and values.

## compute_market_reaction_windows
- Use for batch event-window market reactions after the event list has already been retrieved.
- `target`: `{"market": "a_stock|etf|index|concept|hk_stock", "ticker": "<code>"}`.
- `events`: each item needs `event_id` and `event_date`/`date`/`publish_date`.
- `windows`: trading-day windows, default `3,5,7,20`; pass `60` explicitly only for a long-horizon / roughly three-month supplement.
- Use this for industry-index, ETF, concept-index, or representative-stock reaction evidence.
- Do not use it as a strategy backtest or prediction engine.
- If the target is an industry page, label whether the result is 行业指数、ETF、概念指数, or 相关个股; do not present related-stock reactions as industry backtest.

## query_advisor_report
- Use for 今天大A表现怎么样、早盘总结、午盘总结、收盘总结.
- `session`: `all` | `morning` | `midday` | `evening`.
- Combine with index snapshot/series when fresh index numbers are needed.

Rules:
- Resolve relative dates before tool calls, then verify against returned dates.
- Always mention returned data date/time.
- For 今天/昨日, prefer tool defaults/latest trading date when querying market data; if the latest trading date differs from calendar date, say so.
- Do not promise tick-level realtime data.
- Do not make deterministic price or index forecasts.
- Do not compute single-event returns manually when many historical events need aggregation; use `compute_market_reaction_windows`.
- Do not use `query_data` to reconstruct a daily candlestick when `get_kline_series` is available.
- Normal-answer visuals are a Layer 2 presentation concern. After evidence retrieval, load `layer2-research-visuals`; do not place WorkBuddy widget rules in Layer 1 tool calls.
- For detailed data coverage and unsupported claims, also read `references/limitations.md`.
