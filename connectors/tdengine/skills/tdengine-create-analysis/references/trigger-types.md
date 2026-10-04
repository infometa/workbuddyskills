# Trigger Types

The public `trigger_type` enum has exactly these values, in this order:

```text
Period, AnomalyDetection, Count, Interval, State, Session, Event, DataInput, SPC
```

## Machine-Readable Trigger Contract

The manifest is review and test evidence for the live public tool. `required`
means required for that branch after MCP normalization. Conditions describe
cross-field rules which cannot be represented by a single JSON Schema field.

<!-- analysis-trigger-contract:start -->
```json
{
  "order": ["Period", "AnomalyDetection", "Count", "Interval", "State", "Session", "Event", "DataInput", "SPC"],
  "duration_pattern": "^\\d+[asmhdn]$",
  "offset_pattern": "^[+-]?\\d+[buasmhdwny]$",
  "common": {
    "watermark": {"kind":"integer","required":false,"default":0,"conditions":["when supplied, must equal 0"]},
    "ignoreExpired": {"kind":"boolean","required":false,"default":false,"conditions":["when supplied, must be false"]},
    "ignoreUpdate": {"kind":"boolean","required":false,"default":false,"conditions":["when supplied, must be false"]},
    "fillHistory": {"kind":"boolean","required":false,"default":false},
    "fillHistoryFirst": {"kind":"boolean","required":false,"default":false,"conditions":["true requires fillHistory=true"]},
    "fillHistoryStartTime": {"kind":"non-negative-millisecond-timestamp","required":false,"minimum":0,"conditions":["supplied value requires fillHistory=true"]},
    "generateHistoryEvent": {"kind":"boolean","required":false,"default":false,"conditions":["true requires fillHistory=true"]},
    "preFilter": {"kind":"boolean","required":false,"default":false},
    "preFilterExpression": {"kind":"sql-fragment","required":false,"conditions":["non-blank value requires or injects preFilter=true"]},
    "maxDelay": {"kind":"duration","required":false}
  },
  "types": {
    "Period": {
      "fields": {
        "periodTime": {"kind":"duration","required":true},
        "offsetTime": {"kind":"offset","required":false}
      },
      "output_attributes": "required"
    },
    "AnomalyDetection": {
      "fields": {
        "sliding": {"kind":"duration","required":true},
        "anomalyDetectionConfig": {"kind":"object","required":true},
        "anomalyDetectionConfig.algorithm": {"kind":"non-blank-string","required":true},
        "anomalyDetectionConfig.whiteNoiseDataCheck": {"kind":"boolean","required":false,"default":false,"conditions":["the frontend authoring default is true; send true explicitly for frontend-equivalent behavior"]},
        "anomalyDetectionConfig.algorithmParameters": {"kind":"string","required":false,"conditions":["the frontend authoring default is an empty string; send an explicit empty string to preserve that frontend value"]},
        "anomalyDetectionConfig.targetAttributeExpressions": {"kind":"non-empty-string-array","required":true}
      },
      "output_attributes": "required"
    },
    "Count": {
      "fields": {
        "count": {"kind":"integer","required":true,"minimum":2},
        "slidingCount": {"kind":"integer","required":false,"default":0,"minimum":0},
        "expressions": {"kind":"non-empty-string-array","required":true}
      },
      "output_attributes": "required"
    },
    "Interval": {
      "fields": {
        "sliding": {"kind":"duration","required":true}
      },
      "output_attributes": "required"
    },
    "State": {
      "fields": {
        "states": {"kind":"non-empty-string-array","required":true},
        "duration": {"kind":"duration","required":false,"conditions":["required for DURATION, DURATION_AND_COUNT, and DURATION_OR_COUNT","not allowed for COUNT"]},
        "extend": {"kind":"integer","required":false,"minimum":0,"maximum":2,"conditions":["required when zerothStates contains a value other than NO_ZEROTH"]},
        "zerothStates": {"kind":"string-token-array","required":false,"conditions":["empty or same length as states"]},
        "countVal": {"kind":"positive-integer","required":false,"minimum":1,"conditions":["required for COUNT, DURATION_AND_COUNT, and DURATION_OR_COUNT"]},
        "trueForMode": {"kind":"enum","required":false,"enum":["DURATION","COUNT","DURATION_AND_COUNT","DURATION_OR_COUNT"]}
      },
      "output_attributes": "required"
    },
    "Session": {
      "fields": {
        "interval": {"kind":"duration","required":true}
      },
      "output_attributes": "required"
    },
    "Event": {
      "fields": {
        "eventTrigger": {"kind":"object","required":true,"conditions":["starts is a non-empty array of top-level leaves","one start requires end.expression","multiple starts use identical duration/count/trueForMode tuples"]},
        "eventTrigger.starts[].name": {"kind":"non-blank-string","required":true},
        "eventTrigger.starts[].expression": {"kind":"sql-fragment","required":true},
        "eventTrigger.starts[].parameters": {"kind":"expression-parameter-array","required":false},
        "eventTrigger.starts[].duration": {"kind":"duration","required":false,"conditions":["required by DURATION, DURATION_AND_COUNT, and DURATION_OR_COUNT true-for modes"]},
        "eventTrigger.starts[].countVal": {"kind":"positive-integer","required":false,"minimum":1,"conditions":["required by COUNT, DURATION_AND_COUNT, and DURATION_OR_COUNT true-for modes"]},
        "eventTrigger.starts[].trueForMode": {"kind":"enum","required":false,"enum":["DURATION","COUNT","DURATION_AND_COUNT","DURATION_OR_COUNT"]},
        "eventTrigger.starts[].allowAck": {"kind":"boolean","required":false,"default":false,"conditions":["the frontend start-leaf default is true; send true explicitly for frontend-equivalent behavior"]},
        "eventTrigger.starts[].severityLevel": {"kind":"enum","required":false,"enum":["Default","Information","Warning","Minor","Major","Critical"],"conditions":["the frontend default is Information; omission leaves the Java value unset"]},
        "eventTrigger.end.expression": {"kind":"sql-fragment","required":false,"conditions":["required when starts contains exactly one leaf"]},
        "eventTrigger.end.parameters": {"kind":"expression-parameter-array","required":false},
        "eventTrigger.parameters[].label": {"kind":"string","required":false},
        "eventTrigger.parameters[].type": {"kind":"string","required":false},
        "eventTrigger.parameters[].detail": {"kind":"string","required":false},
        "eventTrigger.parameters[].apply": {"kind":"string","required":false}
      },
      "output_attributes": "optional-with-event"
    },
    "DataInput": {
      "fields": {
        "slidingCount": {"kind":"integer","required":false,"default":0,"minimum":0},
        "expressions": {"kind":"non-empty-string-array","required":true}
      },
      "output_attributes": "required"
    },
    "SPC": {
      "fields": {
        "spcConfig.targetAttributeExpression": {"kind":"sql-fragment","required":true},
        "spcConfig.rules": {"kind":"unique-integer-array","required":true,"minimum":1,"maximum":8}
      },
      "output_attributes": "optional-with-event"
    }
  }
}
```
<!-- analysis-trigger-contract:end -->

The old `Sliding` discriminator is not a creation branch. Use `Interval` with
`trigger.sliding`; a frontend-compatible request may set
`output.rollup_window.enabled` to `false`.

For a fixed lookback, keep cadence and window separate. For example, "every
five minutes calculate over the previous hour" uses `trigger.sliding="5m"`
and `output.rollup_window={"enabled":true,"interval":"1h"}`. Do not send
`trigger.interval`; the Java creation path derives the Sliding window interval
only from the enabled output rollup.

| Type | Required trigger fields | Important boundaries |
| --- | --- | --- |
| Period | `periodTime` | duration token |
| AnomalyDetection | `sliding`, `anomalyDetectionConfig` | non-blank algorithm and target list; explicit frontend defaults |
| Count | `count`, `expressions` | `count >= 2`, non-negative `slidingCount` |
| Interval | `sliding` | fixed lookback belongs in enabled `output.rollup_window.interval` |
| State | `states` | non-empty state expressions; validate true-for fields |
| Session | `interval` | duration token |
| Event | `eventTrigger` | top-level leaf starts only; see output reference |
| DataInput | `expressions` | non-empty expressions; non-negative sliding count |
| SPC | `spcConfig` | one target, unique rules 1 through 8, event template |

Duration fields use `^\\d+[asmhdn]$`. Valid examples include `1a`, `1s`, `1m`,
`1h`, `1d`, and `1n`. Offset fields use
`^[+-]?\\d+[buasmhdwny]$`; zero and signed offsets are valid. Reject decimal,
unit-only, whitespace-bearing, multi-token, and SQL-delimiter values.

Common fields are deterministic: missing trigger `expressions` and `states`
become empty arrays, `fillHistoryFirst`, `generateHistoryEvent`, or a history
start timestamp require `fillHistory=true`, and `preFilterExpression` makes
`preFilter=true`. The public Java path does not persist non-neutral
`watermark`, `ignoreExpired`, or `ignoreUpdate`, so send `0`, `false`, and
`false`, or omit them.

For State, `zerothStates` is an array of strings. Use tokens such as
`"NO_ZEROTH"`, `"true"`, `"1"`, or `"'offline'"`; JSON booleans and numbers are
not string tokens. A real zeroth value requires explicit `extend` in `0..2`,
and the array length must match `states`. `trueForMode` is one of `DURATION`,
`COUNT`, `DURATION_AND_COUNT`, or `DURATION_OR_COUNT` with matching duration
and count fields.

For AnomalyDetection, send all four config fields when reproducing a frontend
request. The MCP path does not copy editor initialization: omitted
`whiteNoiseDataCheck` reaches the Java primitive as `false`, while the frontend
starts it at `true`; send `algorithmParameters: ""` explicitly to preserve the
frontend's empty value. `algorithm` must be discovered and non-blank, and
`targetAttributeExpressions` must contain at least one non-blank expression.

Event leaves use the exact camel-case trigger names above. Parameter entries
contain only `label`, `type`, `detail`, and `apply`; omit the array when no
expression-editor metadata is needed. The MCP path does not inject editor
defaults, so send `allowAck` and `severityLevel` explicitly when their values
matter. New MCP creation deliberately rejects AI-only condition data,
backend-assigned condition paths, and recursive group fields.

For sustained threshold alerts, map intent to the complete public tuple. An
explicit "continuous for N" or "sustained for N" requires both
`trueForMode: DURATION` and `duration: N` on every start leaf. If the wording
requires persistence but omits N, stop for confirmation instead of silently
creating an immediate event.

Each Event start or end expression must be based on an exact, case-sensitive
atomic raw metric discovered on the target. Do not use an aggregate or derived expression
as an Event boundary. Aggregates belong in output expressions, not in the
condition that opens or closes an event.

Derive a normal-state end expression whenever the threshold alert needs to
close. Apply logical negation to the complete start expression:

- `> X` -> `<= X`
- `< X` -> `>= X`
- `>= X` -> `< X`
- `<= X` -> `> X`
- `A AND B` -> `NOT A OR NOT B`
- `A OR B` -> `NOT A AND NOT B`

Multiple start leaves represent alternative opening boundaries and share one
persisted end boundary. Their recovery condition should require all opening
conditions to be false. For example, starts `temperature > 90` and
`pressure > 3` recover with `temperature <= 90 AND pressure <= 3`. Do not omit
the end merely because the public schema permits omission for multiple starts;
omit it only when the user explicitly requests a non-closing event or no
unambiguous shared recovery condition exists and the user confirms that choice.
For a metric outside the normal range, use alternative starts below the lower
limit and above the upper limit, then recover only when the metric is back
inside both limits.

SPC requires discovery of one metric with the limit traits exposed by public
attribute metadata. The request shape can be checked locally, but trait
eligibility must come from discovery; do not infer it from an arbitrary name.
