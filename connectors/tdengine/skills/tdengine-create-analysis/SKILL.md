---
name: tdengine-create-analysis
description: Use when an explicit TDengine mutation request requires creating an analysis from structured element, trigger, output, event, and action context.
version: "0.6.0"
author: "TDengine"
---

# TDengine Create Analysis

## Tool Routing

When this skill is loaded, `create_analysis` is the required creation route.
Use this skill to discover the public inputs, build the complete structured
request, and call `create_analysis` directly. Do not call `add_analysis` first,
use it to draft parameters, or retry with it after a structured validation
error. `add_analysis` is only for callers that do not have this skill loaded
and therefore need the server-side AI to interpret an unstructured request.

Use this skill when a deterministic analysis definition can be built from
public MCP discovery. The workflow is:

```text
discover target and attributes -> read live schema -> choose one trigger
-> read the matching references -> validate IDs and expressions
-> resolve output targets and create derived attributes when required
-> call create_analysis once -> require persisted: true
```

## Analysis Versus Panel

An analysis is a persisted stream-computing task. It is not a dashboard panel
and it must not be created for a request that only asks to display a trend,
statistic, or chart. For a display request, use `create_panel` and omit
`trigger_type`, `trigger`, `output`, and analysis window fields. Never call
`create_analysis` as a helper while creating an ordinary panel.

The trigger names are easy to confuse with panel terminology:

| Public value | Frontend meaning | Required field |
| --- | --- | --- |
| `Interval` | sliding/data-arrival trigger | `trigger.sliding` |
| `Period` | fixed scheduled trigger | `trigger.periodTime` |

Map recurring language to trigger types before building parameters:

| User intent | Required trigger type |
| --- | --- |
| Every N minutes, calculate, average, or aggregate | `Interval` |
| Every X minutes, calculate over the previous Y | `Interval` |
| Daily at 08:00 or at the top of every hour | `Period` |
| On each newly arrived data row | `DataInput` |

`Interval` is the public replacement for the deprecated `Sliding` discriminator.
Use `trigger.sliding` only for the execution cadence. When the calculation must
cover a fixed lookback Y, set `output.rollup_window.enabled=true` and put Y in
`output.rollup_window.interval`; Java creation does not read a window from the
trigger object. A rollup interval does not turn an `Interval` trigger into
`Period`. Do not emit `Period` unless the user explicitly asks for
calendar/scheduled execution.

Read [trigger-types.md](references/trigger-types.md) for the nine working
branches and their boundaries. Read [output-event-actions.md](references/output-event-actions.md)
for output, child-template, partition-tag, event, rollup, and action rules.
Use [examples.md](references/examples.md) as complete public request templates.

Discover with public MCP resources and tools such as `idmp://hierarchy`,
`idmp://element-templates`, `idmp://event-templates`,
`idmp://analysis-algorithms`, `get_element_context`,
`list_element_attributes`, `list_events`, `get_event`, and public search tools.
Read the live `create_analysis` input schema before building a request.

Follow this discovery order before choosing a trigger:

1. Inspect any provided context first; reuse it only when it identifies the
   exact element and current attribute definitions.
2. Fill missing context with public discovery calls. Determine whether the
   target is a leaf or intermediate element and whether the analysis applies
   to itself or a discovered child template.
3. Copy attribute names exactly. They are case-sensitive; never translate,
   normalize, or guess a name inside `${attributes['name']}`.
4. Confirm that the selected trigger is available for that target shape before
   constructing output fields.

Resolve positive `element_id`, positive `root_element_id`, exact names, and
public template IDs. Build exactly one `trigger` branch. Typed `output`,
`event`, and `actions` fields use snake_case. The `trigger` object is a separate
compatibility contract: use its exact field names from the live schema and
`trigger-types.md`. Do not infer alternate spellings. Do not invent IDs, copy
private generation objects, or call private endpoints.

## Output Target Selection

Treat expression attributes as read sources and output targets as write destinations.
For example, `${attributes['Current']}` reads the source metric, while
`output.attributes[].attr_id` identifies the attribute whose data reference
will be replaced with the analysis result. Confusing these roles can silently
turn a raw metric into a derived metric.

Choose the output target before any mutation:

1. When the user asks for a new, derived, calculated, or output attribute, or
   requests a calculated result without naming an existing destination, create
   a separate attribute with a calculation-specific business name. After all
   other request fields have been validated, you must call `create_attribute` before `create_analysis`
   with `reuse_if_exists:false`, then use its returned ID and exact name as
   `attr_id` and `attr_name`.
2. A generated target name must describe the result, such as
   `Current 5m Maximum`; do not name it only `Current`. The target must not be
   any raw or tag attribute referenced by the expression. In particular, you
   must not reuse any source attribute as the output target unless the user
   explicitly authorizes replacing that attribute's data reference and the
   impact has been stated before creation.
3. An existing attribute is a valid target only when the user identifies it as
   the destination or discovery proves it is already a compatible derived
   output. Discover and inspect that attribute before creation; do not use
   same-name reuse as a substitute for this decision. If a requested new name
   conflicts, choose a distinct name instead of reusing a raw source or an
   attribute used by the expression.
4. Event-only analyses with no calculated output do not need an output
   attribute. Keep `output.attributes` empty when the event branch permits it;
   do not create an unused attribute.

If `create_analysis` fails after `create_attribute` succeeds, do not create
another attribute during the retry. Correct the analysis request and reuse the same returned attribute ID
and name. If creation is abandoned, report the
orphaned attribute as a persisted side effect because the public MCP surface
does not provide attribute deletion.

After creation, use `get_analysis` to verify the stored output target ID and name
as well as the expression and trigger. A response is not verified when a source
attribute was stored as the target, even if `persisted: true` was returned.

## Frontend-Equivalent Constraints

Apply these cross-field rules before calling the tool. They are enforced by
the frontend through dynamic controls and validators, so they are not all
visible as single-field schema requirements:

1. Trigger availability depends on `output.apply_on_self` and, for child
   output, the discovered `output.element_template.id`. Only use a trigger
   returned as supported for that target; do not assume every enum is valid.
2. `output.attributes` must contain valid expressions and a positive write target
   (`attr_id` + `attr_name`, or `event_attr_id` + `event_attr_name`) whenever
   an output row is supplied. The analysis must have either an event template
   or at least one output attribute. Event-only output is valid only when an
   event template is supplied.
3. `SPC` always requires a positive event template, even when its output list
   is empty. `AnomalyDetection` requires at least one output attribute.
4. `apply_on_self=false` requires a positive child `element_template.id`.
   `partition_by_tags` is allowed only for child/template output and every tag
   must be a discovered `TDengineTag`. Normalize tags to
   `${attributes['tag']}` only at the public request boundary when required.
5. For `Count`, `State`, `Session`, `Event`, `DataInput`, and `SPC`, an
   enabled `output.rollup_window` requires both `start_time` and `end_time`.
   `AnomalyDetection` uses a dedicated output builder and should omit
   rollup/time-column fields unless the live schema explicitly permits them.
6. Frontend defaults are not a request to mix branches: `Interval`/`sliding`
   defaults to `1m`, Count defaults to `count=2, slidingCount=0`, and the
   output rollup defaults are frontend form state only. Send them explicitly
   only when that behavior is intended.
7. `Period` hides history-fill controls; do not carry `fillHistory` settings
   from another trigger branch.
8. State expressions must use supported state-window metric types. If using
   `zerothStates`, its length must equal `states`; a real zeroth value requires
   `extend`, while `NO_ZEROTH` means no zeroth value. Match `trueForMode` with
   its required duration/count fields.
9. Count and DataInput expressions must be non-empty discovered metric
    expressions. Count is at least `2`; sliding counts are non-negative.

## Event Alert Semantics

Use the following semantic workflow and express every decision only through
the public MCP schema:

1. Discover the exact target element, metric names, metric types, normal limits,
   and event template. Never infer thresholds or IDs from a display label.
2. Use `Event` for a threshold alert. A duration-only request such as
   "continuous for N" or "sustained for N" requires every start leaf to set
   `trueForMode: DURATION` and the requested `duration`. Use the matching
   count or combined mode when the request also specifies a record count. A
   duration field by itself is not enough to preserve continuous semantics.
3. If the user asks for a continuous or sustained condition without stating
   how long, propose and confirm a concrete duration such as the frontend
   default `1m`; do not create until the user confirms it.
4. Give threshold alerts a recovery condition in
   `trigger.eventTrigger.end.expression`. It normally negates the opening
   boundary so the event can close when the metric returns to normal. For
   multiple start leaves, use one global recovery expression that closes only
   after all active threshold conditions have cleared. If that expression
   cannot be derived unambiguously, ask before creating.
5. Before the mutation, summarize the target, metric, threshold, requested duration,
   severity, recovery condition, and start-after-create choice. If
   the user requests confirmation before creation, stop after the summary and
   do not call `create_analysis` until the user confirms in a later turn.
6. After `create_analysis` succeeds, call `get_analysis` with the returned
   `element_id` and `analysis_id`. Verify the stored trigger type, every start
   expression, `trueForMode`, duration, end expression, severity, event
   template, and running/paused choice. Report `Status: Verified` only after
   this read-back matches the confirmed semantics. A mismatch means the
   resource is persisted but not verified: report the mismatch, do not retry creation,
   and avoid creating a duplicate analysis.

When a request does not mention scheduling, streaming, alerts, derived output,
or another analysis behavior, stop and use `create_panel` instead. Do not infer
an analysis from words such as “trend”, “display”, “show”, or “chart”.

Call `create_analysis` once after local validation. Progress is advisory: report
success only when the final result contains `persisted: true`, `analysis_id`,
`trigger_type`, and `element_id`, and the required read-back succeeds. Keep
permission, conflict, and upstream errors visible. Return the exact
`analysis_url` from that result as the clickable analysis link; do not
reconstruct its host, port, path, or query parameters. Copy the URL verbatim
from its scheme through its final character,
including the complete query string. Hierarchy parameters such as
`?ids=/1/...` are required routing data: never
omit, shorten, decode, summarize, or move them outside the clickable URL.
A path-only URL is invalid when the returned URL contains query parameters.
Treat `content[type=resource_link].uri` as an indivisible URL and return it
without editing. Its value must exactly equal `analysis_url`; report a tool
contract error instead of choosing between two different values.
