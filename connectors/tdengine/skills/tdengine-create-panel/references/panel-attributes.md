# Panel Attributes, Queries, and Windows

The outer MCP fields use snake_case, as do typed chart fields. Attribute
bindings follow the live open-object binding contract demonstrated by the
complete examples. Read the live `create_panel` schema before sending a
request; this reference adds semantic rules for open nested objects.

## ID Domains and Ownership

| Field | Domain | Meaning |
| --- | --- | --- |
| `element_id` | Element | Positive persisted panel owner and URL target. |
| `template_id` | PanelTemplate | Optional baseline selecting the template creation route. |
| `other_element_template_id` | ElementTemplate | Optional attribute and template/tag-filter query context. |
| `root_element_id` | Element | Optional non-persisted hierarchy context used only with `other_element_template_id`. |

`root_element_id` is not the panel owner and is not expected in panel
read-back. Ordinary concrete-element requests omit it. `template_id` and
`other_element_template_id` are different ID domains and must never be
substituted for one another.

`analysis_state` belongs to the excluded AnalyzeWorkbench panel type. It must
not appear in a complete request for the 14 supported creation types.
Caller-supplied `element_attributes` must not be supplied. It is not a public
write field; Java resolves persisted element attributes from x/y bindings.

## General Request Boundaries

- `element_id` is required and positive. Optional `dashboard_id`,
  `template_id`, `parent_id`, `root_element_id`, and
  `other_element_template_id` are positive when supplied. Use quoted decimal
  strings for schema fields that allow them when an ID exceeds JSON's exact
  integer range.
- `name` is non-blank and contains at most 255 UTF-16 code units.
- `categories` and `event_ids` contain unique positive integers.
  `analysis_ids` contains unique positive decimal IDs and supports quoted
  values where the live schema permits them.
- `limit` is an integer at least zero. `from_text` and `to_text`, when
  supplied, are non-blank and override `params.fromText`/`params.toText`.
  The deterministic query-range defaults are `now-12h` and `now`.
- `chart` is a closed typed presentation object. Use only fields listed for the
  selected type in the live schema and in `panel-types.md`. `notifications`,
  `thumbnail`, categories, and relation IDs pass through after outer validation.

Partial hierarchy-query context, not a complete creation example:

<!-- partial-example: hierarchy-query-context -->
```json
{
  "element_id": 1001,
  "root_element_id": 1000,
  "other_element_template_id": 2001
}
```

## Attribute Objects

Each `xa_attributes` and `ya_attributes` entry is a public `PanelAttribute`
object. Discover names and IDs before building it. Never synthesize names,
IDs, unit IDs, expressions, filters, or window fields.

Common nested fields:

- `uuid`: non-blank and unique in the request. Omission lets MCP generate one.
- `attributeExpression`: unwrapped raw source binding, such as
  `attributes['temperature']` or `9001|attributes['temperature']`. Never put
  `${...}` or an aggregate in this field.
- `expression`: evaluated expression, normally wrapping the raw source in
  `${...}` or an aggregate.
- `checked`, `groupBy`, `formula`: JSON booleans when present.
- `alias`, `filter`, `qualityColumn`: strings when present.
- The function is deprecated. Do not send `function` in new requests. Put an
  intentional aggregation directly in `expression`, for example
  `AVG(${attributes['temperature']})`. The tool accepts a non-empty legacy
  `function` only as compatibility input, merges it into a raw expression when
  necessary, and clears it before persistence. Legacy values are limited to
  `AVG|MAX|MIN|SUM|COUNT|LAST|FIRST|HYPERLOGLOG|SPREAD|STDDEV|STDDEV_POP|VAR_POP`;
  unknown values are rejected instead of being silently discarded.
- `orderBy`: `none`, `asc`, or `desc`. On an ordinary metric, `asc` or
  `desc` sorts by the metric result column, not by time. For chronological
  time-series panels such as `line`, omit `orderBy` or use `none`; the query's
  natural time order must be preserved. Only use `asc` or `desc` when the user
  explicitly requests sorting by metric value and a non-chronological result
  is intentional.
- `timeShift`: when non-blank, matches `^[+-]?\d+[buasmhdwny]$`.
- `tsColumnType`: `none`, `_c0`, `_wstart`, `_wend`, or `_wduration`.
- `displayUom`, `defaultUomClassId`: positive integers when present.
- `parameters`, `limits`: arrays of objects when present.
- `forecast`: an object when present.
- `window`: one of the six typed objects below, never a scalar or array.

Every item needs a non-blank `attributeExpression` or `expression`.
`expression` and `filter` reject statement/comment delimiters `;`, `--`,
`/*`, and `*/`.

`alias` is the stable SQL result-column name used by the frontend to match
`columnMeta` to the requested metric. For an ordinary discovered binding, set
it to the discovered attribute name. Keep it present even for a raw expression
because density-based down-sampling may later wrap the result in an aggregate.
MCP derives a missing alias from a canonical ordinary binding as a compatibility
fallback, but callers using this skill should always provide it explicitly.

Formulas and composite bindings require an explicit alias because no single
source attribute name can be derived safely. Duplicate aliases are supported
and must not be renamed automatically; the frontend consumes repeated result
column indices in request order. MCP also unwraps the exact compatibility forms
`${attributes['name']}` and `${9001|attributes['name']}` when they are supplied
as `attributeExpression`, but new requests must use the canonical unwrapped
forms.

For ordinary discovered attribute bindings, omit `tsColumnType`; an omitted
value and `none` remain visible in the frontend metric/tag editor. Values such
as `_c0` and `_wstart` describe generated timestamp/result columns, and the
frontend intentionally excludes those rows from ordinary binding controls.

### Expression Forms

For same-element expressions use no prefix:

```text
attributes['temperature']
${attributes['temperature']}
AVG(${attributes['temperature']})
```

For a concrete cross-element source, use the real concrete source element ID
as the prefix and preserve it in both strings:

```text
9001|attributes['temperature']
${9001|attributes['temperature']}
```

`other_element_template_id` selects ElementTemplate-based attribute/query
resolution. It is not a substitute for a concrete source element ID and is
not the PanelTemplate-valued `template_id`.

## Type-Specific Binding Cardinality

- `text`: no x/y attributes; non-blank `text_content` is required.
- Every ordinary non-text request needs at least one checked `ya_attributes` metric.
  An x dimension alone, or only unchecked y metrics, creates a panel that the
  frontend refuses to query.
- `heatmap`: exactly one y metric and at most one x dimension. MCP removes
  aggregation and grouping from heatmap bindings.
- `candlestick`: one source y metric or exactly five canonical y metrics.
  One source expands to `start/FIRST`, `peak/MAX`, `valley/MIN`, `end/LAST`,
  and `sample/COUNT`, each with an independent one-hour Interval window.
- `scatter`: at most one x dimension. MCP removes aggregation/grouping that
  the scatter query cannot use, matching the frontend's single-dimension
  replacement behavior.
- `gauge`, `bar-gauge`: apply `LAST` to otherwise unaggregated y metrics.
- Other ordinary non-text types follow the checked-y requirement above and may
  additionally contain x dimensions.
- Supported advanced SQL requests set `enable_advanced: true`, provide at
  least one `advanced_queries` object, and may omit ordinary bindings.

## Aggregation Consistency

Ordinary metrics start with a raw expression such as
`${attributes['temperature']}`. Do not pre-aggregate a plain trend merely
because `down_sampling.aggr` is `avg`; the backend applies that aggregation
only when density-based downsampling is needed.

When any checked y metric has a window, or any checked x dimension has
`groupBy: true`, all checked y metrics must use aggregate expressions. For
example, use `AVG(${attributes['temperature']})`, not the deprecated pair
`expression=${attributes['temperature']}` plus `function=AVG`. Mixed raw and
aggregate y metrics are invalid in grouped/windowed queries.

## Window Contract

<!-- panel-window-contract:start -->
```json
{
  "discriminators": [
    "Interval",
    "State",
    "Session",
    "Event",
    "Count",
    "AnomalyDetection"
  ],
  "duration_pattern": "^\\d+[asmhdn]$",
  "placeholder_forbidden": [
    "single-quote",
    "backslash",
    "right-brace",
    "ASCII-control",
    "DEL"
  ],
  "event": {
    "operators": [
      "=",
      "<",
      ">",
      ">=",
      "<=",
      "!=",
      "<>",
      "+",
      "-",
      "*",
      "/",
      "AND",
      "OR"
    ],
    "max_syntax_depth": 32,
    "accepted_depth": 32,
    "rejected_depth": 33
  },
  "anomaly_detection": {
    "max_parameter_length": 255,
    "accepted_length": 255,
    "rejected_length": 256,
    "forbidden": [
      "double-quote",
      "single-quote",
      "backslash",
      "semicolon",
      "line-comment",
      "block-comment",
      "ASCII-control",
      "DEL"
    ]
  }
}
```
<!-- panel-window-contract:end -->

Shared rules:

- `windowType` is required and is exactly one discriminator above.
- `timeColumn`, when present, is `_wstart` or `_wend`.
- `timeOffset`, when non-blank, matches `^[+-]?\d+[buasmhdwny]$`.
- `eventTemplateId`, when present, is positive.
- Every `eventTemplateAttrExprs` item has a positive unique `attrId`, a
  non-blank `attrName`, and a non-blank delimiter-free `expression`.
- `XYPlotCondition`, `Sliding`, and unknown discriminators are rejected.

| Window | Exact subtype contract |
| --- | --- |
| `Interval` | `interval` is required and matches `^\d+[asmhdn]$`; optional non-blank `sliding` uses the same pattern. `fillType` is `NONE|VALUE|PREV|NULL|LINEAR|NEXT`; optional `fillValues` is a string array. |
| `Count` | `size` is an integer at least 1. Fractional and string sizes are rejected. |
| `State` | `expression` is exactly one safe discovered attribute placeholder. Free SQL and formulas are rejected. |
| `Session` | `duration` is required and matches `^\d+[asmhdn]$`. |
| `Event` | `startCondition` and `endCondition` are required and use the MCP-safe grammar below. Optional `duration` matches `^\d+[asmhdn]$`. |
| `AnomalyDetection` | `expression` is one safe placeholder; `algorithm` is non-blank and matches `^[A-Za-z0-9_-]+$`; optional `whiteNoiseDataCheck` is boolean; optional `algorithmParameters` follows the exact boundary above. |

### Safe Placeholders

A placeholder is exactly `${attributes['name']}` or
`${<positive-element-id>|attributes['name']}`. The discovered name is
non-blank and rejects a single quote, backslash, `}`, every ASCII control
character `U+0000..U+001F`, and DEL `U+007F`. State and AnomalyDetection
require the entire trimmed expression to be one placeholder.

### Event Conditions

Event conditions are a deliberate MCP-safe expression subset. They support
safe placeholders, finite decimal/scientific numbers,
`true`/`false`, safe single-quoted literals, arithmetic, comparison,
parentheses, and case-insensitive `AND`/`OR`. They do not support functions,
bare identifiers, SQL keywords, comments, statements, or chained comparisons.

```text
condition  := comparison ((AND | OR) comparison)*
comparison := arithmetic comparator arithmetic
arithmetic := term ((+ | -) term)*
term       := unary ((* | /) unary)*
unary      := (+ | -) unary | primary
primary    := attribute | finite-number | boolean | string
            | "(" arithmetic ")"
comparator := = | < | > | >= | <= | != | <>
```

At least one discovered-style attribute placeholder is required. Parenthesis
nesting and recursive unary parsing share a syntax-depth limit of 32: depth 32
is accepted and depth 33 is rejected.

### Anomaly Parameters

`algorithmParameters` accepts ordinary values such as `k=1.5,p=0.05`. Its
maximum length is 255 UTF-16 code units; 255 is accepted and 256 is rejected. It
rejects double/single quotes, backslash, semicolon, `--`, `/*`, `*/`, every
ASCII control character, and DEL. These limits protect a raw window-query
boundary and do not relax the algorithm-name rule.

## Typed Downsampling

Use the exact outer field `down_sampling`; its live nested fields are
`maxDataPoints` and `aggr`.

- Defaults: `maxDataPoints=300`, `aggr=avg`.
- `maxDataPoints`: integer `1..5000`.
- `aggr`: `avg|first|last|max|min|sum|count`.

This is a persisted backend query hint. Setting it does not force sampling or
alter chart rendering. The service may skip downsampling for scatter, windowed
or grouped queries, or ranges whose density is already low. Use public
read-back and a public query call to confirm behavior in a live environment.
