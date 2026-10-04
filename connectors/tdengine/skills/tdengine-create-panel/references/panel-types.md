# Supported Panel Types

This reference documents only fields accepted by the live `create_panel`
schema. All `chart` field names are snake_case. The chart object and its
nested objects are closed: omit a field unless it appears under the selected
`panel_type` below. Unknown fields and fields from another type are rejected.

## Type Contract

<!-- panel-type-contract:start -->
```json
{
  "supported": [
    "line", "stat", "bar-gauge", "gauge", "table", "bar",
    "state-timeline", "state-history", "histogram", "candlestick",
    "scatter", "heatmap", "pie", "text"
  ],
  "excluded": [
    "kpi", "batch-report", "video", "image", "trend", "map", "container"
  ],
  "advanced_sql": {
    "supported_panel_types": [
      "line", "stat", "bar-gauge", "gauge", "table", "bar",
      "state-timeline", "state-history", "histogram", "candlestick",
      "scatter", "heatmap", "pie"
    ],
    "requires_enable_advanced": true,
    "requires_advanced_queries": true
  }
}
```
<!-- panel-type-contract:end -->

The excluded names are not aliases. In particular, use `line`, not `trend`,
for a persisted time-series panel. Advanced SQL is a query mode for a
supported non-text type. A `text` panel uses non-blank `text_content` and no
x/y bindings.

## Defaults

The tool always normalizes `down_sampling` to `maxDataPoints=300` and
`aggr=avg` when omitted. This is a persisted backend query hint; setting it
does not force sampling or change presentation by itself. The public bounds are
`maxDataPoints` from 1 through 5000 and `aggr` in
`avg|first|last|max|min|sum|count`.

The recommended defaults marked `recommended_default` below are safe starting
values for a newly created panel. They are guidance, not values injected into
an omitted `chart`. Send them only when that presentation choice is intended. An empty or
omitted chart is valid for every non-text type.

## Public Chart Contract

Paths are relative to `chart`. Numeric endpoints are inclusive. Every field is
optional. The live `create_panel` schema is authoritative if a deployed server
advertises a different contract.

<!-- panel-chart-contract:start -->
```json
{
  "line": [
    {"path":"series.style","kind":"enum","enum":["lines","bars","points","arc"],"recommended_default":"lines"},
    {"path":"series.line_interpolation","kind":"enum","enum":["linear","smooth","step-start","step-middle","step-end"],"recommended_default":"linear"},
    {"path":"series.line_width","kind":"number","minimum":0,"recommended_default":1},
    {"path":"series.graph_mode","kind":"enum","enum":["none","area"],"recommended_default":"area"},
    {"path":"series.bar_width_factor","kind":"number","minimum":0.1,"maximum":1,"recommended_default":0.6},
    {"path":"series.fill_opacity","kind":"number","minimum":0,"maximum":1,"recommended_default":0},
    {"path":"series.gradient_mode","kind":"enum","enum":["none","opacity","hue","scheme"],"recommended_default":"none"},
    {"path":"series.stack","kind":"enum","enum":["off","samesign","all","positive","negative"],"recommended_default":"off"},
    {"path":"series.show_values","kind":"enum","enum":["auto","always","never"],"recommended_default":"auto"},
    {"path":"series.show_points","kind":"enum","enum":["auto","always","never"],"recommended_default":"auto"}
  ],
  "stat": [
    {"path":"display_time","kind":"enum","enum":["on","off"],"recommended_default":"on"},
    {"path":"series.orientation","kind":"enum","enum":["horizontal","vertical"],"recommended_default":"horizontal"},
    {"path":"series.graph_mode","kind":"enum","enum":["none","area"],"recommended_default":"area"}
  ],
  "bar-gauge": [
    {"path":"orientation","kind":"enum","enum":["horizontal","vertical"],"recommended_default":"vertical"},
    {"path":"display_mode","kind":"enum","enum":["gradient","basic","retroLCD"],"recommended_default":"basic"},
    {"path":"bar_size_mode","kind":"enum","enum":["auto","manual"],"recommended_default":"auto"},
    {"path":"bar_min_width","kind":"number","minimum":0,"recommended_default":8}
  ],
  "gauge": [
    {"path":"series.style","kind":"enum","enum":["lines","bars","points","arc"],"recommended_default":"arc"},
    {"path":"series.segments","kind":"integer","minimum":1,"maximum":100,"recommended_default":1},
    {"path":"series.segments_spacing","kind":"number","minimum":0,"maximum":1,"recommended_default":0.1},
    {"path":"series.bar_width_factor","kind":"number","minimum":0.1,"maximum":1,"recommended_default":0.2}
  ],
  "table": [
    {"path":"show_header","kind":"boolean","recommended_default":true},
    {"path":"enable_pagination","kind":"boolean","recommended_default":true},
    {"path":"cell_height","kind":"enum","enum":["small","medium","large"],"recommended_default":"medium"},
    {"path":"col_alignment","kind":"enum","enum":["auto","left","center","right"],"recommended_default":"auto"}
  ],
  "bar": [
    {"path":"orientation","kind":"enum","enum":["horizontal","vertical"],"recommended_default":"vertical"},
    {"path":"series.bar_width","kind":"number","minimum":0,"recommended_default":0},
    {"path":"series.line_width","kind":"number","minimum":0,"recommended_default":0},
    {"path":"series.fill_opacity","kind":"number","minimum":0,"maximum":1,"recommended_default":0.8},
    {"path":"series.gradient_mode","kind":"enum","enum":["none","opacity","hue","scheme"],"recommended_default":"none"},
    {"path":"series.stack","kind":"enum","enum":["off","samesign","all","positive","negative"],"recommended_default":"off"},
    {"path":"series.show_values","kind":"enum","enum":["auto","always","never"],"recommended_default":"auto"}
  ],
  "state-timeline": [
    {"path":"series.merge_values","kind":"boolean","recommended_default":true},
    {"path":"series.show_values","kind":"enum","enum":["auto","always","never"],"recommended_default":"auto"},
    {"path":"series.row_height","kind":"number","minimum":0,"maximum":1,"recommended_default":0.6}
  ],
  "state-history": [
    {"path":"series.show_values","kind":"enum","enum":["auto","always","never"],"recommended_default":"auto"},
    {"path":"series.row_height","kind":"number","minimum":0,"maximum":1,"recommended_default":0.6},
    {"path":"series.column_width","kind":"number","minimum":0,"maximum":1,"recommended_default":0.6}
  ],
  "histogram": [
    {"path":"histogram.bucket_count","kind":"integer","minimum":1},
    {"path":"histogram.combine_series","kind":"boolean","recommended_default":false},
    {"path":"series.stack","kind":"enum","enum":["off","samesign","all","positive","negative"],"recommended_default":"off"},
    {"path":"series.line_width","kind":"number","minimum":0,"recommended_default":1},
    {"path":"series.fill_opacity","kind":"number","minimum":0,"maximum":1,"recommended_default":0.6},
    {"path":"series.gradient_mode","kind":"enum","enum":["none","opacity","hue","scheme"],"recommended_default":"none"}
  ],
  "candlestick": [
    {"path":"series.mode","kind":"enum","enum":["candles","volume","both"],"recommended_default":"both"},
    {"path":"series.candle_style","kind":"enum","enum":["candles","spveBars"],"recommended_default":"candles"},
    {"path":"series.color_strategy","kind":"enum","enum":["sinceOpen","sincePriorClose"],"recommended_default":"sinceOpen"},
    {"path":"series.include_additional_fields","kind":"boolean","recommended_default":true}
  ],
  "scatter": [
    {"path":"series.style","kind":"enum","enum":["lines","bars","points","arc"],"recommended_default":"points"},
    {"path":"series.line_width","kind":"number","minimum":0,"recommended_default":0},
    {"path":"series.fill_opacity","kind":"number","minimum":0,"maximum":1,"recommended_default":0},
    {"path":"series.stack","kind":"enum","enum":["off","samesign","all","positive","negative"],"recommended_default":"off"},
    {"path":"series.symbol","kind":"enum","enum":["heart","happy","evil","shocked","pieChart","users","mug","plane"]},
    {"path":"series.symbol_size","kind":"number","minimum":0},
    {"path":"series.line_opacity","kind":"number","minimum":0,"maximum":1,"recommended_default":1},
    {"path":"series.show_points","kind":"enum","enum":["auto","always","never"],"recommended_default":"always"}
  ],
  "heatmap": [
    {"path":"heatmap.x_bucket_mode","kind":"enum","enum":["size","count"],"recommended_default":"count"},
    {"path":"heatmap.x_bucket_count","kind":"integer","minimum":1},
    {"path":"heatmap.y_bucket_mode","kind":"enum","enum":["size","count"],"recommended_default":"count"},
    {"path":"heatmap.y_bucket_count","kind":"integer","minimum":1},
    {"path":"colors.mode","kind":"enum","enum":["scheme","continuous"],"recommended_default":"scheme"},
    {"path":"colors.scheme","kind":"string","recommended_default":"Spectral"},
    {"path":"cell_display.cell_gap","kind":"integer","minimum":0,"maximum":25,"recommended_default":2}
  ],
  "pie": [
    {"path":"series.chart_type","kind":"enum","enum":["pie","donut"],"recommended_default":"donut"},
    {"path":"series.orientation","kind":"enum","enum":["horizontal","vertical"],"recommended_default":"horizontal"},
    {"path":"series.label_fields","kind":"unique-subset","subset":["name","value","percent"],"recommended_default":["value","percent"]}
  ],
  "text": [
    {"path":"background_color","kind":"color"},
    {"path":"background_layout","kind":"enum","enum":["none","cover","repeat"],"recommended_default":"none"}
  ]
}
```
<!-- panel-chart-contract:end -->

## Cross-Field Rules

- `series.segments_spacing` is useful only when `series.segments > 1`.
- When `bar_size_mode=manual`, supply `bar_min_width`; otherwise omit it.
- A heatmap count is relevant only for the matching `*_bucket_mode=count`.
- `series.label_fields` contains no duplicates.
- All numbers must be finite JSON numbers. Do not send numeric strings.
- Do not add presentation fields that are absent from the selected type.

## Scatter Symbols

The public tool accepts friendly symbol names and performs any persistence
conversion internally. Omit `series.symbol` for the renderer's ordinary
default. Never send an encoded vector path.

<!-- scatter-symbol-contract:start -->
```json
["evil", "happy", "heart", "mug", "pieChart", "plane", "shocked", "users"]
```
<!-- scatter-symbol-contract:end -->
