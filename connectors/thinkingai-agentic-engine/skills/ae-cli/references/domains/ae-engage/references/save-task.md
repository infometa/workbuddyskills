# ae-cli `engage-task task save`

Create or update a Hermes task draft.

Mapped command: `ae-cli engage-task task save`

This command is the final write step. Do not use it as the first step in task construction.

Recommended workflow:

1. `ae-cli engage-setting channel list --project-id <projectId>`
2. `ae-cli engage-task task build-save-guide --project-id <projectId> --req '{...}'`
3. If the guide indicates a custom target audience, build the semantic
   `targetConfig.definitionRequest` contract used by Analysis. Hermes compiles it to persisted QP.
   Use `triggerConfig.triggerDefinition` and
   `completionIndicatorDef.completionIndicators[].eventDefinition` for event conditions.
   For existing-cluster audiences, use `analysis user-cluster get`.
   Never construct persisted execution QP.
4. Build the final grouped `req`
5. `ae-cli engage-task task save --project-id <projectId> --req '{...}'`

Audience creation is not a fixed preflight step. Use direct create/get only when the guide indicates that you must construct:

- `targetConfig.definitionRequest`
- `triggerConfig.triggerDefinition`
- `completionIndicatorDef.completionIndicators[].eventDefinition`

For the full guide contract, request format, return sections, and handoff usage, read:

- `references/build-task-save-guide.md`

---

## 1. General Principles

`engage-task task save` accepts the grouped draft-save payload. For a custom audience
(`targetClusterType=1`), pass semantic `targetConfig.definitionRequest`; do not pass raw
persisted audience fields.

The command supports two modes:

- create mode: omit `req.taskId`
- update mode: include `req.taskId` for an existing draft or paused task

Regardless of mode, this tool only saves a draft:

- it does not submit approval
- it does not start sending
- it does not register or start trigger execution

The CLI call shape is:

```bash
ae-cli engage-task task save --project-id <projectId> --req '<req-json>'
```

Notes:

- the outer Capability input uses `project_id` and `req`; fields inside `req` keep the native camelCase DTO shape shown below
- Hermes assigns the outer `--project-id` to `req.projectId`; if `req.projectId` is also present, the outer value wins
- the whole `req` must be a JSON object, not a stringified JSON string
- for update mode, Hermes allows modifying **draft** or **paused** tasks (`status` 0 or 2); running/ended tasks are rejected with `invalid_status`
- in update mode, omitted fields are backfilled from the existing task before validation, so partial updates (e.g. rename only) are allowed

### Response shape

The save result is under `data.result`, and any object keys inside it are recursively snake_case.
A successful create/update commonly yields the task ID as `data.result`; validation failures use
fields such as `data.result.operation_mode`, `data.result.errors`, and `data.result.warnings`.

---

## 2. Required Workflow

### 2.1 Query Real Channels First

Run:

```bash
ae-cli engage-setting channel list --project-id <projectId>
```

Purpose:

- get the real project channel list
- resolve the real `channelId`
- confirm the final `channelType`

Never invent a `channelId`.

### 2.2 Build the Scenario Guide

Run:

```bash
ae-cli engage-task task build-save-guide --project-id <projectId> --req '{...}'
```

Use the guide to determine:

- required grouped blocks
- required fields for the current trigger and audience mode
- unsupported combinations
- correct content schema
- current handoff template
- whether the current payload is already close to submit-ready

### 2.3 Build Semantic Conditions

If the guide indicates that audience or event conditions are needed, build semantic definitions
directly. Resolve real events and properties through Analysis metadata.

Use semantic event definitions for:

- `triggerConfig.triggerDefinition`
- `completionIndicatorDef.completionIndicators[].eventDefinition`

Task aggregate and completion event definitions support:

- `aggregation`: `count`, `sum`, or `distinct_count`
- `operator`: `gt`, `gte`, or `eq`

Completion target and experiment main-goal event filters must not use properties whose metadata
`select_type` is `datetime`. The supported filter-property select types are `string`, `number`,
`bool`, `bool-s`, `date`, `array`, `array_string`, `row`, and `array_row`. This restriction applies
to `completionIndicatorDef.completionIndicators[].eventDefinition.filters`; it does not apply to
trigger-event filters.

For an event property whose metadata `select_type` is `array_row`, never submit it as a flat
property filter. Use an object-group filter and place only that parent's child properties inside
`conditions`:

```json
{
  "type": "object_group",
  "field": "equipment_list",
  "operator": "any_satisfy",
  "conditions": {
    "relation": "and",
    "items": [
      {
        "field": "equipment_list.item_level",
        "operator": "gte",
        "values": [10]
      }
    ]
  }
}
```

Object-group operators are `any_satisfy`, `none_satisfy`, and `all_satisfy`. Resolve the parent
and child fields from current metadata. Hermes validates the metadata type, child-parent
relationship, and supported operators before saving, so do not flatten `array_row` or invent child
field names.

Trigger events have an additional envelope contract selected by `eventTriggerType`. Do not apply
one aggregate event shape to every trigger type. Use the matrix and examples in section 4.4.

`clientConfig.clientQp` is not an AI-authored field. Always omit it from Capability requests;
partial task updates preserve existing server state.

Do not create an audience by default for every task. It is conditional, not mandatory.

### 2.4 Build Final `req` and Save

Only after the above steps should you construct the final grouped `req` and submit it with `engage-task task save`.

---

## 3. Final `req` Shape

The final object passed to `--req` should have this grouped shape:

```json
{
  "taskId": "<string, optional>",
  "baseInfo": {},
  "channelConfig": {},
  "targetConfig": {},
  "triggerConfig": {},
  "controlConfig": {},
  "expConfig": {},
  "activityConfig": {},
  "clientConfig": {}
}
```

Top-level notes:

- `taskId` is used only in update mode
- `baseInfo` / `channelConfig` / `targetConfig` / `triggerConfig` / `controlConfig` are the main blocks
- optional blocks should usually be omitted rather than filled with invented values
- use `build_task_save_guide` output as the source of truth for the current scenario

---

## 4. How To Build Major Blocks

### 4.1 `taskId`

Use `taskId` only when you are updating an existing draft or paused task.

- create mode: omit `taskId`
- update mode: include `taskId`
- update mode can send only the fields that need changing (e.g. `baseInfo.taskName` for rename)
- update mode fails with `invalid_status` if the task is running or ended
- for paused tasks that already started pushing, Hermes rejects changes to key attributes (channel, trigger time/type, audience cluster, timezone, completion indicators); renames and other non-key fields remain allowed

### 4.2 `channelConfig`

Core fields:

- `channelType`
- `channelId`
- `groupContentList`
- optional `channelTemplateId`

Rules:

- derive `channelType` and `channelId` from real channel metadata
- do not guess template IDs
- `groupContentList` maximum size is `5`
- `occasionKeys` are parsed from content automatically and are not accepted as input
- when `expConfig.enableExp=true`, each `groupContentList` item must include
  `expGroupName`, `expGroupType`, `percentageInExperiment`, and `order`, and the list must
  mirror `expConfig.expGroupList` one-to-one by `expGroupName`
- capability `engage-task.task.save` rejects misaligned experiment `groupContentList`
  (`TASK_EXPERIMENT_GROUP_CONTENT_INVALID`) before the inner save service runs
- do not submit experiment content as content-only objects such as
  `{"contentList":[...]}` without the group association fields

Content guidance:

- do not invent channel-specific payload structures from memory
- use `fieldRules.channelContentSchema` from `build_task_save_guide`
- take valid keys, expected item shape, and examples from the guide
- when schema fields include `paramType`, copy it exactly
- do not use free-form content items such as `{"text":"..."}` as the primary pattern

### 4.3 `targetConfig`

Use the guide to decide which audience shape applies:

- `targetClusterType=1`: custom audience, requires `definitionRequest`
- `targetClusterType=2`: existing cluster, requires `clusterKey`
- `targetClusterType=3`: all users, forbids `definitionRequest` and `clusterKey`

Audience availability depends on delivery side:

- Server-side channels support `targetClusterType=1` (custom) and `2` (existing), but not `3` (all users).
- `client_push` (`channelType=3`) supports `targetClusterType=1` (custom) and `3` (all users), but not `2` (existing).
- Determine the delivery side from the selected real channel; do not infer audience support from `triggerType` alone.

For a custom audience, pass the semantic definition directly. Do not create an intermediate
cluster or copy persisted QP.

### 4.4 `triggerConfig`

Use the guide to determine the current trigger rule set:

- `triggerType=0`: requires `triggerTime`
- `triggerType=1`: requires `startDate`, `endDate`, `triggerCrontab`
- `triggerType=2`: manual, no `triggerDefinition`
- `triggerType=3/4/5`: requires `triggerDefinition`

Rules:

- `triggerType=6` is not supported
- use the guide for cron format and wrong-example checks
- if `triggerDefinition` is needed, build it from semantic event definitions and resolve real
  event/property names through Analysis metadata
- always set the A rule's `eventTriggerType` explicitly
- always set the A rule's `periodTimeSymbol` to `TS01`, `TS02`, `TS03`, or `TS04`; it is
  required even when `periodStart` and `periodEnd` are present
- Hermes compiles the semantic event and then validates the final persisted trigger-rule envelope
- for semantic event-trigger tasks, Hermes backfills missing task-level `startDate` / `endDate`
  from the A rule's `periodStart` / `periodEnd`; explicit task-level dates remain authoritative

#### Trigger envelope matrix

| Channel | `triggerType` | Allowed A-rule `eventTriggerType` |
| --- | --- | --- |
| Server channels | `3` | `0`, `1`, `2` |
| Server channels | `4` | `0` only |
| Server channels | `5` | `0`, `1`, `2` |
| `client_push` (`channelType=3`) | `3` | `1`, `2`, `3` |
| `client_push` (`channelType=3`) | `5` | `1`, `2`, `3` |

For `triggerType=4/5`, the second B rule is always an aggregate rule. It also requires
`delayTime`, `delayTimeSymbol`, and `eventCondition`; use `1` for `triggerType=4` and `0` for
`triggerType=5`.

#### `eventTriggerType=0`: accumulated completion

Use aggregate semantic events:

```json
{
  "eventTriggerType": 0,
  "events": [
    {
      "type": "event",
      "event": "purchase",
      "aggregation": "sum",
      "property": "amount",
      "operator": "gt",
      "value": 100
    }
  ]
}
```

#### `eventTriggerType=1`: continuous completion

Use exactly one count event with `operator=eq` and `value>=2`. `blackList` is optional and accepts
semantic events that Hermes compiles as non-aggregate event selectors. The rule-level window is
optional; provide `windowGap` and `windowGapTimeUnit` together.
`relationProps` is optional and uses semantic event-property references. Hermes resolves their
legacy metadata before persistence:

```json
{
  "relationProps": [
    {
      "property": {
        "type": "event_property",
        "name": "#city"
      }
    }
  ]
}
```

```json
{
  "eventTriggerType": 1,
  "windowGap": 7,
  "windowGapTimeUnit": "day",
  "events": [
    {
      "type": "event",
      "event": "login",
      "aggregation": "count",
      "operator": "eq",
      "value": 3
    }
  ],
  "blackList": [
    {
      "type": "event",
      "event": "logout",
      "aggregation": "count",
      "operator": "eq",
      "value": 1
    }
  ]
}
```

#### `eventTriggerType=2`: ordered completion

Use at least two sequence steps. The first and last steps must have `hasDone=true`. Put the
Analysis semantic event inside `eventDefinition`; do not add persisted aggregate fields such as
`taPropQuota`, `uceCalcuSymbol`, or `num`.
Optional `relationProps` use the same semantic event-property structure documented for
`eventTriggerType=1`.

```json
{
  "eventTriggerType": 2,
  "events": [
    {
      "eventDefinition": {
        "type": "event",
        "event": "login",
        "aggregation": "count",
        "operator": "eq",
        "value": 1
      },
      "hasDone": true,
      "hasDistanceStart": false
    },
    {
      "eventDefinition": {
        "type": "event",
        "event": "purchase",
        "aggregation": "count",
        "operator": "eq",
        "value": 1
      },
      "hasDone": true,
      "hasDistanceStart": false,
      "windowGap": 2,
      "windowGapTimeUnit": "day"
    }
  ]
}
```

`hasDone=false` is allowed only for optional intermediate steps. Hermes removes aggregate fields
from every persisted sequence step and rejects unsafe sequence envelopes before save.

#### `eventTriggerType=3`: every completion

This type is available only for `client_push`. Use count/eq/1 events and set
`eventTriggerCaliberType` to `0` (combined trigger) or `1` (separate trigger).

```json
{
  "eventTriggerType": 3,
  "eventTriggerCaliberType": 0,
  "events": [
    {
      "type": "event",
      "event": "login",
      "aggregation": "count",
      "operator": "eq",
      "value": 1
    }
  ]
}
```

### 4.5 `controlConfig`

Minimum required field:

- `completionIndicatorDef`

When the guide points to event-based completion or experiment-driven main-goal rules, build
`completionIndicatorDef.completionIndicators[].eventDefinition` from the semantic event contract.
Read `fieldRules.blocks.controlConfig.completionIndicatorDef.filterPropertySelectTypes` and exclude
every property type listed under `excluded` before constructing its `filters`.

For a main goal (`completionIndicatorType=0`), always include `touch_cycle_num` and
`touch_cycle_num_unit`. If the user does not request another completion window, use
`touch_cycle_num=1` and `touch_cycle_num_unit="day"`. Static Capability validation may accept a
main goal without these fields, but the Hermes save service rejects it.

Important constraints that still apply:

- `doNotDisturb.enableDoNotDisturb=true` requires `startTime` and `endTime` in `HH:mm`
- `pushDelay.enablePushDelay=true` requires valid `delayType`, and its dependent fields must match the selected mode
- `pushDelay.delayType=1` is only valid for `client_push`
- `pushDelay.delayUnit` must stay within `week`, `day`, `hour`, `minute`, `second`
- `timeoutControl.enableTimeoutControl=true` requires valid `time` and `unit`
- `timeoutControl.unit` must stay within `day`, `hour`, `minute`

### 4.6 `clientConfig`

Use this block only when client-side conditions are needed.

Never include `clientConfig.clientQp` in a Capability request. It is a server-authored
compatibility field, and partial task updates preserve the existing server value. If a requested
client-side condition has no semantic field in the current contract, stop and report that it cannot
be safely authored through this Capability.

### 4.7 Verified A/B Task Template

Use this shape as the starting point for a server-channel split experiment. Replace every
placeholder with metadata discovered from the current project.

```json
{
  "baseInfo": {
    "taskName": "<taskName>",
    "taskDesc": "<taskDescription>",
    "tzOffset": "<projectTimezoneOrDefaultSentinel>"
  },
  "channelConfig": {
    "channelType": 1,
    "channelId": "<verifiedChannelId>",
    "groupContentList": [
      {
        "expGroupName": "Control",
        "expGroupType": 1,
        "percentageInExperiment": 50,
        "order": 0,
        "contentList": [{ "pushLanguageCode": "default", "content": "<channelContentJsonString>" }]
      },
      {
        "expGroupName": "Experiment A",
        "expGroupType": 2,
        "percentageInExperiment": 50,
        "order": 1,
        "contentList": [{ "pushLanguageCode": "default", "content": "<channelContentJsonString>" }]
      }
    ]
  },
  "targetConfig": {
    "targetClusterType": 1,
    "definitionRequest": "<semanticAudienceDefinition>"
  },
  "triggerConfig": { "triggerType": 2 },
  "controlConfig": {
    "completionIndicatorDef": {
      "completionIndicators": [
        {
          "completionIndicatorType": 0,
          "touch_cycle_num": 1,
          "touch_cycle_num_unit": "day",
          "eventDefinition": {
            "type": "event",
            "event": "<verifiedGoalEvent>",
            "aggregation": "count",
            "operator": "gte",
            "value": 1
          }
        }
      ]
    },
    "frequencyLimits": { "enableFrequencyLimits": false, "ruleList": [] }
  },
  "expConfig": {
    "enableExp": true,
    "expType": 1,
    "percentageInLayer": 100,
    "expIndicatorBizType": 1,
    "controlGroupSkipPush": false,
    "expGroupList": [
      { "expGroupName": "Control", "expGroupType": 1, "percentageInExperiment": 50, "order": 0 },
      { "expGroupName": "Experiment A", "expGroupType": 2, "percentageInExperiment": 50, "order": 1 }
    ]
  }
}
```

The experiment group tuple (`expGroupName`, `expGroupType`, `percentageInExperiment`, `order`)
must be identical between each `expConfig.expGroupList` entry and its corresponding
`channelConfig.groupContentList` entry. Validate the final request, save it, then call `task get`
and verify both persisted lists; a successful task ID alone is not sufficient verification.

---

## 5. Final Self-Check Before `engage-task task save`

Before submission, verify:

1. `channelId` comes from a real channel query.
2. `build_task_save_guide` has already been called for the current scenario or partial draft.
3. `fieldRules.channelContentSchema` was used as the source of truth for content structure.
4. Audience, trigger, and completion conditions use semantic definitions only.
5. `targetClusterType` matches the presence or absence of `clusterKey` / `definitionRequest`.
6. `channelType`, `triggerType`, and `eventTriggerType` match the trigger envelope matrix.
7. `completionIndicatorDef` is present and structurally valid for the current scenario.
8. `taskId` is omitted for create mode and present only for updating a draft or paused task.
9. No unsupported `triggerType=6` is used.
10. Ordered steps contain `eventDefinition` and sequence metadata, not persisted aggregate fields.
11. No placeholder IDs or fabricated resource names remain in the request.
12. Every main goal includes `touch_cycle_num` and `touch_cycle_num_unit`.
13. For experiments, `expGroupList` and `groupContentList` contain identical group tuples.

---

## 6. Standard Example Flow

Use this style of workflow, rather than jumping directly to `engage-task task save`:

```bash
ae-cli engage-setting channel list --project-id 1
ae-cli engage-task task build-save-guide --project-id 1 --req '{"context":{"triggerType":2,"channelId":"channel_123"}}'
ae-cli engage-task task save --project-id 1 --req '{...final grouped req...}'
```

If the guide indicates a custom audience or event condition, insert the semantic definition
directly before building the final `req`.

---

## 7. Safety Constraints

This command is a write operation.

- Do not treat `save_task` as “submit and launch task”
- Do not bypass `build_task_save_guide`
- Do not pass the whole `req` as a JSON string
- Do not use `triggerType=6`
- Do not invent `channelId`, `clusterKey`, audience definitions, or content keys
- Do not use `taskId` for a running or ended task
- Do not pass `occasionKeys`; Hermes derives them from content
- Do not create an intermediate cluster merely to obtain an execution QP
