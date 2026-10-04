# Complete Create-Panel Requests

These are complete public MCP argument objects. Replace placeholder IDs,
names, expressions, and query text only with values established through public
discovery or supplied by the user. Each request intentionally supplies one
representative type-specific chart override; omitted visual fields receive
frontend load-time defaults when the panel is opened.

## Direct and Template Routes

The `line-direct` request is also the advanced SQL example. It omits
`template_id`, so it must return `creation_route=direct`. The final
`line-template` request uses the same panel type and owner but includes a
string-safe PanelTemplate ID. It must return `creation_route=template`, the
same exact `template_id`, a positive `panel_id`, and `persisted: true`.

Supplying only `template_id` is never sufficient. The template request carries
the complete effective definition, including `name`, `panel_type`, bindings,
query range, and chart override, as the frontend does after loading a template
draft.

## Fourteen-Type Inventory

### Line, direct advanced SQL

<!-- complete-example: line-direct -->
```json
{
  "element_id": 1001,
  "name": "Temperature trend from SQL",
  "panel_type": "line",
  "enable_advanced": true,
  "advanced_queries": [
    {
      "refId": "A",
      "query": "SELECT _wstart, AVG(temperature) AS temperature FROM telemetry INTERVAL(5m)"
    }
  ],
  "from_text": "now-24h",
  "to_text": "now",
  "down_sampling": {
    "maxDataPoints": 1200,
    "aggr": "sum"
  },
  "chart": {
    "series": {
      "style": "lines",
      "line_interpolation": "smooth",
      "line_width": 2
    }
  }
}
```

Expected omitted defaults include points `auto`, solid line type, no gradient,
and no fill. Advanced SQL is valid only when the selected live-schema panel
type supports query results, `enable_advanced` is true, and
`advanced_queries` is non-empty.

### Stat

<!-- complete-example: stat-direct -->
```json
{
  "element_id": 1001,
  "name": "Latest pressure",
  "panel_type": "stat",
  "ya_attributes": [
    {
      "uuid": "pressure-stat",
      "attributeExpression": "attributes['pressure']",
      "expression": "LAST(${attributes['pressure']})",
      "alias": "pressure",
      "checked": true
    }
  ],
  "chart": {
    "display_time": "on",
    "series": {
      "orientation": "horizontal",
      "graph_mode": "area"
    }
  }
}
```

Expected omitted defaults include automatic text alignment and no background
color until a background color mode is selected.

### Bar gauge

<!-- complete-example: bar-gauge-direct -->
```json
{
  "element_id": 1001,
  "name": "Tank level bars",
  "panel_type": "bar-gauge",
  "ya_attributes": [
    {
      "uuid": "tank-level-gauge",
      "attributeExpression": "attributes['tank_level']",
      "expression": "${attributes['tank_level']}",
      "alias": "tank_level",
      "checked": true
    }
  ],
  "chart": {
    "orientation": "vertical",
    "display_mode": "basic",
    "bar_size_mode": "manual",
    "bar_min_width": 12
  }
}
```

Expected omitted defaults include display time on, unfilled area shown, and
value-color display.

### Gauge

<!-- complete-example: gauge-direct -->
```json
{
  "element_id": 1001,
  "name": "Current vibration",
  "panel_type": "gauge",
  "ya_attributes": [
    {
      "uuid": "vibration-gauge",
      "attributeExpression": "attributes['vibration']",
      "expression": "${attributes['vibration']}",
      "alias": "vibration",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "style": "arc",
      "segments": 3,
      "segments_spacing": 0.1,
      "bar_width_factor": 0.25
    }
  }
}
```

Expected omitted defaults include automatic orientation, value-and-name text,
visible thresholds, and hidden labels.

### Table

<!-- complete-example: table-direct -->
```json
{
  "element_id": 1001,
  "name": "Recent measurements",
  "panel_type": "table",
  "xa_attributes": [
    {
      "uuid": "measurement-time",
      "attributeExpression": "attributes['measurement_time']",
      "expression": "${attributes['measurement_time']}",
      "alias": "measurement_time",
      "checked": true
    }
  ],
  "ya_attributes": [
    {
      "uuid": "measurement-value",
      "attributeExpression": "attributes['temperature']",
      "expression": "${attributes['temperature']}",
      "alias": "temperature",
      "checked": true
    }
  ],
  "chart": {
    "show_header": true,
    "enable_pagination": true,
    "cell_height": "medium",
    "col_alignment": "auto"
  }
}
```

Expected omitted defaults include a three-second flip interval and false
wrapping, filtering, auto-flip, row-color, and cell-inspection flags.

### Bar

<!-- complete-example: bar-direct -->
```json
{
  "element_id": 1001,
  "name": "Hourly energy",
  "panel_type": "bar",
  "ya_attributes": [
    {
      "uuid": "energy-bar",
      "attributeExpression": "attributes['energy']",
      "expression": "SUM(${attributes['energy']})",
      "alias": "energy",
      "checked": true
    }
  ],
  "chart": {
    "orientation": "vertical",
    "series": {
      "bar_width": 40,
      "fill_opacity": 0.8,
      "gradient_mode": "none"
    }
  }
}
```

Expected omitted defaults include no stacking, zero line width, and automatic
bar width when no override is supplied.

### State timeline

<!-- complete-example: state-timeline-direct -->
```json
{
  "element_id": 1001,
  "name": "Pump state timeline",
  "panel_type": "state-timeline",
  "ya_attributes": [
    {
      "uuid": "pump-state-timeline",
      "attributeExpression": "attributes['pump_state']",
      "expression": "${attributes['pump_state']}",
      "alias": "pump_state",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "merge_values": true,
      "show_values": "auto",
      "row_height": 0.6
    }
  }
}
```

Expected omitted defaults include centered labels and never connecting or
disconnecting null values.

### State history

<!-- complete-example: state-history-direct -->
```json
{
  "element_id": 1001,
  "name": "Valve state history",
  "panel_type": "state-history",
  "ya_attributes": [
    {
      "uuid": "valve-state-history",
      "attributeExpression": "attributes['valve_state']",
      "expression": "${attributes['valve_state']}",
      "alias": "valve_state",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "show_values": "auto",
      "row_height": 0.6,
      "column_width": 0.5
    }
  }
}
```

Expected omitted defaults include automatic value labels and switch-time row
height 0.6.

### Histogram

<!-- complete-example: histogram-direct -->
```json
{
  "element_id": 1001,
  "name": "Temperature distribution",
  "panel_type": "histogram",
  "ya_attributes": [
    {
      "uuid": "temperature-histogram",
      "attributeExpression": "attributes['temperature']",
      "expression": "${attributes['temperature']}",
      "alias": "temperature",
      "checked": true
    }
  ],
  "chart": {
    "histogram": {
      "bucket_count": 20,
      "combine_series": false
    },
    "series": {
      "stack": "off",
      "fill_opacity": 0.6
    }
  }
}
```

Expected omitted defaults include offset zero, single-lane display, one-pixel
lines, and no gradient. Limit lines are created only when their dialog opens.

### Candlestick

<!-- complete-example: candlestick-direct -->
```json
{
  "element_id": 1001,
  "name": "Pressure candle summary",
  "panel_type": "candlestick",
  "ya_attributes": [
    {
      "uuid": "pressure-candle-source",
      "attributeExpression": "attributes['pressure']",
      "expression": "${attributes['pressure']}",
      "alias": "pressure",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "mode": "both",
      "candle_style": "candles",
      "color_strategy": "sinceOpen",
      "include_additional_fields": true
    }
  }
}
```

MCP expands this one source into the five canonical metrics. Expected omitted
defaults include `#26a69a` up, `#ef5350` down, and an empty field mapping. The
overlay is created only when its dialog opens.

### Scatter with a concrete cross-element metric

<!-- complete-example: scatter-direct -->
```json
{
  "element_id": 1001,
  "name": "Remote temperature scatter",
  "panel_type": "scatter",
  "ya_attributes": [
    {
      "uuid": "remote-temperature-scatter",
      "attributeExpression": "9001|attributes['temperature']",
      "expression": "${9001|attributes['temperature']}",
      "alias": "temperature",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "symbol_size": 12,
      "line_opacity": 0.5
    }
  }
}
```

Expected omitted defaults include point style, no stacking, and the shared
circle symbol. The concrete `9001|` source prefix is preserved unchanged.

### Heatmap

<!-- complete-example: heatmap-direct -->
```json
{
  "element_id": 1001,
  "name": "Temperature heatmap",
  "panel_type": "heatmap",
  "ya_attributes": [
    {
      "uuid": "temperature-heatmap",
      "attributeExpression": "attributes['temperature']",
      "expression": "${attributes['temperature']}",
      "alias": "temperature",
      "checked": true
    }
  ],
  "chart": {
    "heatmap": {
      "x_bucket_mode": "count",
      "x_bucket_count": 64,
      "y_bucket_mode": "count",
      "y_bucket_count": 32
    },
    "colors": {
      "mode": "scheme",
      "scheme": "Spectral"
    },
    "cell_display": {
      "cell_gap": 2
    }
  }
}
```

Expected omitted defaults include linear Y scale, left non-reversed Y axis,
linear color scale, and a visible legend.

### Pie

<!-- complete-example: pie-direct -->
```json
{
  "element_id": 1001,
  "name": "Alarm share",
  "panel_type": "pie",
  "xa_attributes": [
    {
      "uuid": "alarm-category-pie",
      "attributeExpression": "attributes['alarm_category']",
      "expression": "${attributes['alarm_category']}",
      "alias": "alarm_category",
      "groupBy": true,
      "checked": true
    }
  ],
  "ya_attributes": [
    {
      "uuid": "alarm-count-pie",
      "attributeExpression": "attributes['alarm_count']",
      "expression": "SUM(${attributes['alarm_count']})",
      "alias": "alarm_count",
      "checked": true
    }
  ],
  "chart": {
    "series": {
      "chart_type": "donut",
      "orientation": "horizontal",
      "label_fields": ["value", "percent"]
    }
  }
}
```

Expected omitted defaults include no slice sorting.

### Text

<!-- complete-example: text-direct -->
```json
{
  "element_id": 1001,
  "name": "Operations note",
  "panel_type": "text",
  "text_content": "Shift handover complete.",
  "chart": {
    "background_color": "rgba(10, 20, 30, 0.15)",
    "background_layout": "none"
  }
}
```

Text has no attributes. No image reference is synthesized; omitted background
is transparent and the layout reads as `none`.

## Template Route Variant

The PanelTemplate ID below is deliberately represented as a quoted decimal
string so no JSON floating-point conversion can alter it. It must be available
to the target element. A search candidate is not proof of membership; the
tool performs an authoritative element-scoped preflight before the write.

<!-- complete-example: line-template -->
```json
{
  "element_id": 1001,
  "template_id": "9007199254740993",
  "name": "Temperature from baseline",
  "panel_type": "line",
  "ya_attributes": [
    {
      "uuid": "temperature-template-line",
      "attributeExpression": "attributes['temperature']",
      "expression": "${attributes['temperature']}",
      "alias": "temperature",
      "checked": true
    }
  ],
  "from_text": "now-12h",
  "to_text": "now",
  "chart": {
    "series": {
      "style": "lines",
      "line_interpolation": "linear",
      "show_points": "auto"
    }
  }
}
```

Expected omitted defaults match the direct line type. Request values override
the loaded baseline, while unchanged template values remain inherited through
public panel read-back.
