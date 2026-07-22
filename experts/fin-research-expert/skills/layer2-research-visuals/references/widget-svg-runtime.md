# Widget SVG Runtime Router

Use this router only after `references/common.md` and `references/market-charts.md`. Each chart family has its own script and renderer version so its layout and interaction can evolve without forcing unrelated charts through one generic implementation.

## Template selection

| `chart_type` | Template | `renderer_version` | Intended presentation |
|---|---|---|---|
| `candlestick_volume` | `references/widget-kline-runtime.md` | `workbuddy-kline-svg/2` | Responsive OHLC candles, moving averages, volume, interval summary and hover details |
| `line` | `references/widget-trend-runtime.md` | `workbuddy-trend-svg/2` | Responsive one- or two-series trend, endpoint summary and hover details |
| `event_return_bar` | `references/widget-event-runtime.md` | `workbuddy-event-svg/2` | Responsive signed event-window bars with a non-overlapping value/sample column |
| `column` / `grouped_column` | `references/widget-compare-runtime.md` | `workbuddy-compare-svg/1` | Bounded category comparison with exact hover values and readable labels |
| `line_column` | `references/widget-combo-runtime.md` | `workbuddy-combo-svg/1` | Column and line evidence; dual axes only when source units are incompatible |
| `radar` | `references/widget-radar-runtime.md` | `workbuddy-radar-svg/1` | Aligned research dimensions with an explicit source scale and value panel |

Select exactly one family for one normal-answer chart. Do not load all templates, merge their scripts or change a payload to a different chart type merely to reuse a renderer.

## Shared payload boundary

The packaged `scripts/render_widget.mjs` selects the reviewed template and replaces `__TONGZHOU_CHART_PAYLOAD__` exactly once with validated JSON containing:

- `renderer_version`: the exact version from the selection table.
- `schema_version`: `chart-evidence/1` for market K-line/trend/event evidence, or `research-visual/1` for Same Boat comparison/combination/radar evidence.
- `chart_type`: the exact type selected above.
- `title` and `description`: user-readable and JSON-escaped.
- `evidence`: only the current validated evidence bundle.
- `options`: only options documented by the selected template.

Run the packaged renderer relative to this Skill directory:

```text
node scripts/render_widget.mjs --input <normalized-payload.json>
```

Its stdout is the complete JSON arguments object for `show_widget`. Pass that object unchanged. The renderer guarantees that `widget_code` begins with `<svg`, ends with `</script>` and keeps payload JSON in a non-executable data block. Do not hand-edit the template, precompute SVG coordinates or expand one SVG element per evidence point in the model response.

Each fragment keeps the host-required initial `viewBox="0 0 680 340"`, then measures the rendered container and expands its internal coordinate width between 680 and 1280 while retaining the fixed 340-pixel height. Do not replace this with a stretched `preserveAspectRatio="none"` layout, which distorts text and chart geometry.

## Failure rule

If the renderer rejects the payload, correct the normalized JSON once without switching families. If it still fails, stop rendering and return the already prepared table/text fallback. Do not switch to an ad hoc script or generated chart artifact.
