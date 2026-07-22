# Market Reference

Use for:
- 最新价、当前价格、实时/接近实时快照
- 个股、ETF、港股、指数、概念的历史走势
- 普通问答 K 线、收盘趋势和事件收益图所需的结构化证据
- 大盘早盘、午盘、收盘总结

## Cross-Market Identity, Dates, And Units

- 在任何数值查询前，先确认用户问的是 A 股、港股或美股，并复用身份解析返回的市场、交易所和标准代码；不要按名称猜代码或自行补后缀。
- 同名证券、两地上市或代码候选不唯一时，先展示候选并请用户确认。身份未确认前不得发起价格、估值或 K 线调用。
- 当前 Fin Data 行情不支持美股。美股请求应标注 `unsupported`，不得借用同名 A 股、港股、ADR 对应公司或宽基指数代替。
- `get_latest_snapshot` 仅支持 A 股和指数；港股只能使用明确支持 `hk_stock` 的历史序列能力，不得把历史末值冒充实时快照。
- 币种和单位只使用工具实际返回值。A 股通常标注 `CNY/人民币`，港股标注 `HKD/港元`，美股若未来有受支持数据则标注 `USD/美元`；缺少币种字段时写“币种未返回”，不得默认成人民币或自行换算。
- 多市场或多序列并列时，分别标注每个序列实际返回的最新交易日期、时区/时间和币种；不得用其中一个序列的日期代表其他市场。
- 单一行情意图只调用一个最窄能力：最新价用快照，K 线用 `get_kline_series`，简单收盘走势用 `query_data`。不要为了丰富回答顺带取无关 OHLCV、新闻或其他市场数据。

Tools:

## get_latest_snapshot
- Use when user asks 最新价、当前价格、现在多少钱、盘中表现.
- `ticker`: required.
- `market`: `a_stock` | `index`.
- Common indices: 上证指数 `000001.SH`, 深证成指 `399001.SZ`, 创业板指 `399006.SZ`, 沪深300 `000300.SH`.
- Check `snapshot_source`, `snapshot_date`, and `freshness_status`. A-share data uses the trading-session realtime table first and may fall back to the latest trading-day archive when that table is empty. Never describe an archive fallback as realtime.
- Index data uses `snapshot_source=latest_minute_table`; report its returned time and freshness rather than promising tick-level realtime.

## batch_get_latest_snapshots
- Use for two or more A-share or index latest snapshots, self-selected lists, candidate comparisons, or portfolio overviews.
- `market`: `a_stock` | `index`; all tickers in one call must belong to the same market.
- Maximum 50 input tickers. Duplicate canonical tickers are queried once and remain visible in `symbol_status`.
- Read `snapshot_source`, `freshness_status`, `completeness`, and every `symbol_status`; distinguish `not_found` from `stale` and keep successful rows when another ticker is missing.
- ETF and HK snapshots are unsupported. Use `batch_query_data(granularity="daily")` only as latest available daily history, never as realtime data.

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

## batch_query_data
- Use for two or more tickers in one market that need the same metrics, granularity, date range, and per-symbol limit.
- Maximum 20 input tickers and 5000 requested rows after deduplication (`unique ticker count * limit`). Split larger requests.
- Read compact rows with `columns`; preserve each `symbol_status` and `completeness=partial` instead of retrying missing codes in a loop.
- All tickers share one `market`. Resolve mixed-market inputs first, then use at most one batch call per market.

## compute_market_reaction_windows
- Use for batch event-window market reactions after the event list has already been retrieved.
- `target`: `{"market": "a_stock|etf|index|concept|hk_stock", "ticker": "<code>"}`.
- `events`: each item needs `event_id` and `event_date`/`date`/`publish_date`.
- `windows`: trading-day windows, default `3,5,7,20`; pass `60` explicitly only for a long-horizon / roughly three-month supplement.
- Use this for industry-index, ETF, concept-index, or representative-stock reaction evidence.
- Do not use it as a strategy backtest or prediction engine.
- If the target is an industry page, label whether the result is 行业指数、ETF、概念指数, or 相关个股; do not present related-stock reactions as industry backtest.
- The service loads one bounded price range for the whole event list; do not split one target into one call per event.

## compute_batch_reaction_windows
- Use when the same event list must be compared across multiple stocks, ETFs, indices, concepts, or HK stocks.
- Maximum 10 unique targets, 50 events, 500 target-event pairs, and a 10-year event span.
- Same-market targets share one query and mixed markets are grouped automatically; do not fan out one call per target.
- Read target aggregates independently and retain partial-query or insufficient-window status. Results are not causal proof, a backtest, or a forecast.

## query_advisor_report
- Use for 今天大A表现怎么样、早盘总结、午盘总结、收盘总结.
- `session`: `all` | `morning` | `midday` | `evening`.
- Combine with index snapshot/series when fresh index numbers are needed.

Rules:
- Preserve the resolved market and canonical ticker in every follow-up call; never strip an exchange suffix or switch markets after an empty result.
- Preserve field-level evidence: a returned date and price with a missing currency is `partial`, not `empty`. Show the date/price, label the currency gap, and never infer it from the market name.
- Treat an unsupported market, frequency, metric, or snapshot mode as `unsupported`; do not replace it with another listing, historical last value, broad index, or example number.
- Treat validation, timeout, dependency, and transport failures as `error`. Keep any valid sibling fields or evidence tasks, but do not report the failed field as zero or absent.
- Resolve relative dates before tool calls, then verify against returned dates.
- ISO 日期与星期同时展示时必须做确定性日历校验；无法校验就不写星期。不得仅凭星期推断交易日、休市或休市原因。
- Always mention returned data date/time.
- For 今天/昨日, prefer tool defaults/latest trading date when querying market data; if the latest trading date differs from calendar date, say so.
- Do not promise tick-level realtime data.
- Do not make deterministic price or index forecasts.
- Do not compute single-event returns manually when many historical events need aggregation; use `compute_market_reaction_windows`.
- Do not use `query_data` to reconstruct a daily candlestick when `get_kline_series` is available.
- Normal-answer visuals are a Layer 2 presentation concern. After evidence retrieval, load `layer2-research-visuals`; do not place WorkBuddy widget rules in Layer 1 tool calls.
- For detailed data coverage and unsupported claims, also read `references/limitations.md`.
