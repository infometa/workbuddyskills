# Widget SVG Runtime Router

Use this router only after `references/common.md` and `references/market-charts.md`. Each chart family has its own script and renderer version so its layout and interaction can evolve without forcing unrelated charts through one generic implementation.

## Template selection

| `chart_type` | Template | `renderer_version` | Intended presentation |
|---|---|---|---|
| `candlestick_volume` | `references/widget-kline-runtime.md` | `workbuddy-kline-svg/1` | OHLC candles, moving averages, volume, interval summary and hover details |
| `line` | `references/widget-trend-runtime.md` | `workbuddy-trend-svg/1` | One or two comparable series, endpoint summary and hover details |
| `event_return_bar` | `references/widget-event-runtime.md` | `workbuddy-event-svg/1` | Signed event-window bars, sample counts and missing-sample disclosure |

Load exactly one template for one normal-answer chart. Do not load all three templates, merge their scripts or change a payload to a different chart type merely to reuse a renderer.

## Shared payload boundary

Every template replaces `__TONGZHOU_CHART_PAYLOAD__` exactly once with JSON containing:

- `renderer_version`: the exact version from the selection table.
- `schema_version`: `chart-evidence/1`.
- `chart_type`: the exact type selected above.
- `title` and `description`: user-readable and JSON-escaped.
- `evidence`: only the current validated evidence bundle.
- `options`: only options documented by the selected template.

Pass the completed fragment directly to `show_widget`. Its first characters must be `<svg` and its last characters must be `</script>`; do not add `<![CDATA[` / `]]>` or a Markdown fence around it. Do not save it, execute it through a CLI, precompute SVG coordinates or expand one SVG element per evidence point in the model response.

## Failure rule

If the selected fragment fails host validation, correct the payload once without switching templates. If it still fails, stop rendering and return the already prepared table/text fallback. Do not switch to Python, a CLI or a generated local file.
