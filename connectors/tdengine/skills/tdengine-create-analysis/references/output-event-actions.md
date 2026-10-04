# Output, Event, And Actions

This reference documents the closed public payload accepted by
`create_analysis`. Outer fields and all fields under `output`, `event`, and
`actions` use snake_case. Unknown fields and alternate spellings are rejected.
Read the live tool schema before building a request.

## Machine-Readable Payload Contract

<!-- analysis-payload-contract:start -->
```json
{
  "outer": {
    "element_id": {"kind":"positive-id","required":true,"minimum":1},
    "name": {"kind":"non-blank-string","required":true},
    "description": {"kind":"string","required":false,"default":""},
    "root_element_id": {"kind":"positive-id","required":true,"minimum":1},
    "element_template_id": {"kind":"non-negative-id","required":false,"minimum":0},
    "trigger_type": {"kind":"enum","required":true,"enum":["Period","AnomalyDetection","Count","Interval","State","Session","Event","DataInput","SPC"]},
    "trigger": {"kind":"object","required":true},
    "name_pattern": {"kind":"string","required":false},
    "output": {"kind":"object","required":true},
    "event": {"kind":"object","required":false},
    "actions": {"kind":"array","required":false,"default":[]},
    "event_template_id": {"kind":"positive-id","required":false,"minimum":1,"conditions":["compatibility alias for event.template_id","if both forms are supplied their values must match"]},
    "severity": {"kind":"enum","required":false,"conditions":["compatibility alias for event.severity_level","if both forms are supplied their values must match"]},
    "output_column_name": {"kind":"enum","required":false,"enum":["_wstart","_wend"],"conditions":["compatibility alias for output.column_name","if both forms are supplied their values must match"]},
    "categories": {"kind":"unique-positive-id-array","required":false,"default":[],"minimum":1},
    "start_after_created": {"kind":"boolean","required":false,"default":true},
    "recalculate": {"kind":"boolean","required":false,"default":false},
    "where": {"kind":"sql-fragment","required":false},
    "stream_name": {"kind":"string","required":false},
    "del_history": {"kind":"boolean","required":false,"default":false}
  },
  "output": {
    "apply_on_self": {"kind":"boolean","required":false,"default":true},
    "attributes": {"kind":"array","required":false,"default":[]},
    "partition_by_tags": {"kind":"unique-tag-array","required":false,"default":[],"conditions":["non-empty only when apply_on_self=false","each tag is publicly discovered as TDengineTag"]},
    "element_template": {"kind":"object","required":false,"conditions":["required when apply_on_self=false","id is positive","root_element is positive or injected from root_element_id"]},
    "rollup_window": {"kind":"object","required":false},
    "column_name": {"kind":"enum","required":false,"enum":["_wstart","_wend"]},
    "offset": {"kind":"offset","required":false},
    "output_source_filter": {"kind":"sql-fragment","required":false},
    "output_result_filter": {"kind":"sql-fragment","required":false}
  },
  "output_attribute": {
    "attr_id": {"kind":"positive-id","required":false,"minimum":1,"conditions":["requires attr_name"]},
    "attr_name": {"kind":"non-blank-string","required":false,"conditions":["required with attr_id"]},
    "event_attr_id": {"kind":"positive-id","required":false,"minimum":1,"conditions":["requires event_attr_name"]},
    "event_attr_name": {"kind":"non-blank-string","required":false,"conditions":["required with event_attr_id"]},
    "expression": {"kind":"sql-fragment","required":true},
    "parameters": {"kind":"array","required":false,"default":[]},
    "uom_id": {"kind":"positive-id","required":false,"minimum":1}
  },
  "rollup": {
    "enabled": {"kind":"boolean","required":false,"default":false},
    "interval": {"kind":"duration","required":false},
    "start_time": {"kind":"enum","required":false,"enum":["_wstart","_wend"],"conditions":["required when enabled for Count, State, Session, Event, DataInput, or SPC"]},
    "end_time": {"kind":"enum","required":false,"enum":["_wstart","_wend"],"conditions":["required when enabled for Count, State, Session, Event, DataInput, or SPC"]},
    "start_time_offset": {"kind":"offset","required":false},
    "end_time_offset": {"kind":"offset","required":false}
  },
  "event": {
    "template_id": {"kind":"positive-id","required":false,"minimum":1,"conditions":["required for SPC","required when output.attributes is empty for Event"]},
    "severity_level": {"kind":"enum","required":false}
  },
  "action": {
    "condition_expression": {"kind":"sql-fragment","required":true},
    "action_template_id": {"kind":"positive-id","required":true,"minimum":1}
  }
}
```
<!-- analysis-payload-contract:end -->

Every output item has a non-blank `expression` and at least one positive target
ID. `attr_id` pairs with non-blank `attr_name`; `event_attr_id` pairs with
non-blank `event_attr_name`. Event output may carry both target kinds. A
supplied `uom_id` is positive. Public defaults are `apply_on_self=true`, an
empty `attributes` array, and `parameters: []` on each item.

Use `_wstart` or `_wend` for `column_name`, rollup time fields, and output
column time values. Validate rollup offsets with the offset pattern and a
rollup interval with the duration pattern. Enabled rollup for Count, State,
Session, Event, DataInput, or SPC requires both start and end time fields.

Child output uses `apply_on_self=false` and requires a positive
`element_template.id` and positive `element_template.root_element`. The tool
fills `root_element` from outer `root_element_id` when it is absent. Template
filters, output filters, `where`, trigger expressions, output expressions, and
action conditions reject `;`, `--`, `/*`, and `*/`. The service remains
responsible for full formula grammar validation.

`partition_by_tags` is omitted or normalized to an empty array by default. A
non-empty list is valid only with `apply_on_self=false`; each entry must be a
unique, non-blank public tag name. An exact wrapper such as
`${attributes['region']}` is normalized to `region`. Reject malformed wrappers,
control characters, and duplicates before the call. Each name must have been
discovered with public metadata whose `dataReferenceType` is `TDengineTag`.
Identifier escaping, including embedded backticks, is handled after validation.

Event uses `event.template_id` or outer `event_template_id` and may have an
empty output only when an event is created. `trigger.eventTrigger.starts` must
be non-empty top-level leaves with `name` and `expression`; nested groups are
not supported for new MCP creation. One start requires a non-blank end
expression. Multiple starts may omit the end, but all starts must share the
same duration, count, and true-for tuple because the persisted event has one
global tuple.

Prefer canonical nested `event.template_id`, `event.severity_level`, and
`output.column_name`. The three outer fields remain compatibility aliases. If
both a canonical field and its alias are present, their normalized values must
be equal; conflicts are rejected before Java is called. Category IDs must be
positive and unique.

SPC may use an empty output, but requires a positive event template. Each
action has a non-blank `condition_expression` and positive
`action_template_id`. Use `start_after_created` (default `true`), `recalculate`
(default `false`), and `del_history` (default `false`) as the outer MCP names.
