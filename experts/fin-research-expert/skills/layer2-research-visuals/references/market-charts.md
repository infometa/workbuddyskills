# Market Chart Contract

Use this reference only after loading `references/common.md` and `layer1-fin-data/references/market.md`.

## Choose the smallest useful chart

| Evidence and user intent | Visual | Do not use |
|---|---|---|
| User asks for 日K/K线 and valid daily OHLC exists | Candlestick; add volume only when available | A line chart that hides intraday range |
| User asks for 走势/趋势 and one numeric series is enough | Line chart | A forced candlestick without a user need |
| User compares two evidenced series on a compatible scale | Two-line chart with direct labels | More than two dense series in one normal answer |
| Tool returns event-window aggregate with valid samples | Signed event-return bars | Bars for windows with no valid sample |
| Same Boat returns `column` or `grouped_column` | Dedicated comparison bars | A trend line that hides category comparison |
| Same Boat returns `line_column` | Dedicated combination chart; split axes only for incompatible units | Rescaling one source unit into another |
| Same Boat returns aligned radar values with a stated scale | Dedicated radar | A radar without source `scale_min`, `scale_max` and `scale_description` |

## Retrieve chart-ready market evidence

For daily candlesticks, call `get_kline_series` and consume its `chart-evidence/1` result directly. Only when an older connected `fin-data-query` server does not expose that tool may you temporarily use `query_data` with the supported subset of `open`, `high`, `low`, `close`, `volume`. Use `list_metrics` first when compatibility-path support is uncertain. For a simple trend, request only the needed metric, usually `close`.

- 最近 N 个交易日: use `limit=N` and do not convert it into a calendar-day range.
- For `get_kline_series`, preserve its ascending `points`, `quality`, `evidence_window`, `unit` and optional `overlays` without a second normalization pass.
- On the temporary `query_data` path, parse returned `columns` and `rows`, never `raw_preview`, and normalize valid points by trading time ascending.
- Use returned trading dates and state them explicitly when they differ from the user's calendar wording.
- Keep the first release to a readable window, normally 20 to 60 daily points. For a longer request, retain the evidence table and use a trend chart with thinned labels.
- `get_kline_series` already returns `chart-evidence/1`; wrap it only with the renderer title, description and bounded options. Convert the compatibility result to that schema once. Never expose the virtual-table response shape to the Widget runtime.

## OHLCV validation

For every candidate candle:

1. `open`, `high`, `low` and `close` must be finite positive numbers.
2. `high` must be at least the maximum of `open`, `close` and `low`.
3. `low` must be at most the minimum of `open`, `close` and `high`.
4. `volume`, when present, must be finite and non-negative.
5. Trading time must be present and unique after deterministic duplicate removal.

Skip an invalid row rather than repairing it. If too few valid rows remain for a meaningful candlestick, use a valid close trend or the table fallback and disclose the gap.

## Candlestick and moving average rules

- Candle up or unchanged: red `#d92d20`; candle down: green `#079455`.
- Show high-low wick and open-close body. Preserve direction with body treatment and signed summary, not color alone.
- Use the dedicated K-line template's compact header for latest close, interval return, interval high/low and evidence dates. Keep the price axis on the right, moving-average values above the plot and OHLCV details available on pointer hover.
- Use a separate volume band when valid volume exists; volume bars follow the candle direction.
- A moving average is computed only from the normalized close sequence and is omitted until its full window exists.
- Use at most three moving average windows in a normal candlestick answer. Do not invent missing earlier history merely to start a line.
- The packaged Widget script transforms evidence rows into coordinates and may compute requested simple moving averages. The model must not hand-calculate coordinates, polylines or rewrite source prices.
- The date-label selector keeps the first and last valid point, chooses interior labels at deterministic intervals and omits any adjacent label that would violate a 52-unit gap. In particular, do not draw both the penultimate and final trading date at the right edge.

## Direct Widget payload and template

Use `references/widget-svg-runtime.md` to choose exactly one template:

- `candlestick_volume` -> `references/widget-kline-runtime.md`: validated OHLCV points in ascending time order plus zero to three bounded moving-average windows.
- `line` -> `references/widget-trend-runtime.md`: one or two validated named series on compatible units.
- `event_return_bar` -> `references/widget-event-runtime.md`: valid event windows with signed return and real sample count.
- `column` / `grouped_column` from `research-visual/1` -> `references/widget-compare-runtime.md`: ordered categories and exact source series values.
- `line_column` from `research-visual/1` -> `references/widget-combo-runtime.md`: preserve line/column series types and per-series units.
- renderable `radar` from `research-visual/1` -> `references/widget-radar-runtime.md`: aligned dimensions/values and an explicit source scale.

For a Same Boat `line` chart, adapt categories and exact values to the existing trend runtime once: each category becomes `time`, each source value becomes `value`, and no interpolation or unit conversion is permitted. Media entries stay outside Widget code as ordinary Markdown images. `fallback_only`, unknown chart types and malformed entries use the returned `fallback_table`.

Load only the selected family template. Replace its payload placeholder and call `show_widget`. Do not load or merge the other chart scripts, write a script, execute a local renderer, save an SVG or paste a fully expanded per-point SVG into the tool call.

## Trend chart rules

- Keep one primary series; a second series is allowed only for an explicitly requested, comparably scaled benchmark or metric.
- Use direct labels or a compact legend and include the unit.
- Do not infer an intraday path from daily closes.
- Summaries may report observed high, low and period change only when those values are directly available or deterministically computed from the displayed series.

## Event-return chart rules

Use `compute_market_reaction_windows` after event evidence and the target have already been resolved.
When one event set is compared across multiple targets, use `compute_batch_reaction_windows` once and render one series per returned target instead of issuing one tool call per target.

- Read each aggregate window's `average_return`, `median_return`, `sample_count` and `missing_count`.
- Plot a window only when `sample_count` is greater than zero and the selected return is finite.
- Omit an empty long window from the chart, headline and combined judgment. Explain it only in the data-coverage note.
- Show signed percentage labels and `n=<sample_count>` beside each plotted window.
- Positive bars are red; negative bars are green; zero is neutral.
- State `missing_count` in the note or fallback table when it is non-zero.
- Label the result as historical descriptive evidence. It is not a prediction, trading signal or strategy backtest.

## Fallback tables

Candlestick/trend fallback columns:

| Date | Open | High | Low | Close | Volume |
|---|---:|---:|---:|---:|---:|

Include only columns actually returned. For a long series, show a representative compact table and state the full returned window without claiming omitted rows were absent.

Event fallback columns:

| Window | Average return | Median return | sample_count | missing_count |
|---|---:|---:|---:|---:|

Do not include a window that has no return in the directional conclusion. It may appear only as an explicit insufficient-sample row when that helps explain the gap.
