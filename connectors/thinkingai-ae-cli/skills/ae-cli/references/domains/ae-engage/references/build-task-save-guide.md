# ae-cli `engage-task task build-save-guide`

Build a scenario-specific guide for constructing `save_task.req`.

Mapped command: `ae-cli engage-task task build-save-guide`

This is a read-only helper. It does not save tasks, submit approvals, or trigger execution. Its job is to tell you how to build a valid `save_task` request for the current scenario.

---

## 1. Recommended Workflow

Use this sequence when creating or updating a task draft:

1. Query channels with `ae-cli engage-setting channel list --project-id <projectId>`.
2. Call `ae-cli engage-task task build-save-guide --project-id <projectId> --req '{...}'`.
3. Use semantic definitions for audience, trigger, and completion fields:

- `targetConfig.definitionRequest`
- `triggerConfig.triggerDefinition` (required for `triggerType=3/4/5`)
- `completionIndicatorDef.completionIndicators[].eventDefinition`

Build event primitives from `ae-analysis` user-cluster / audience models. Hermes wraps those
primitives in the task-specific envelope selected by `channelType`, `triggerType`, and
`eventTriggerType`, then validates the final persisted QP before save. Never construct persisted
execution QP. Follow the documented closed semantic shapes: unknown fields are rejected, and a
property `field` may be a technical-name string or a `{name,type}` reference.
Every custom-audience `event` and `behavior_sequence` requires its own `time_range`. For
`recent` and `previous`, use a positive integer `value` and only `unit=day`; `custom` requires
both `start_time` and `end_time`.

Custom audiences support `behavior_sequence` nodes, including sequence/step windows, step
filters, `completed`, and `relative_to_first`. A task `get` may return top-level `compound`
nodes when the stored member-group, event-group, and outer relations differ. Preserve those
compounds when reusing `definition_request`; flattening them changes audience semantics.
For the second sequence step, omit `relative_to_first` or set it to `false`; use `true` only
from the third step onward when its window must be measured from step 1.

For server-side existing-cluster audiences (`targetClusterType=2`), you may copy server-authored definitions via:

```bash
ae-cli analysis user-cluster get --project-id <projectId> --cluster-names '["<cluster_name>"]'
```

Server-side channels allow custom (`1`) or existing (`2`) audiences and reject all users (`3`).
`client_push` (`channelType=3`) allows custom (`1`) or all users (`3`) and rejects existing (`2`).
Always pass `channelType` in `context` so the guide can validate this matrix.

4. Build the final grouped `save_task.req`.
5. Submit with `ae-cli engage-task task save --project-id <projectId> --req '{...}'`.

Important:

- Do not treat audience creation as a fixed preflight step.
- Discover event/property metadata when semantic definitions reference those fields.
- Omit the server-authored `clientConfig.clientQp`; partial updates preserve it.

---

## 2. CLI Shape

The CLI call shape is:

```bash
ae-cli engage-task task build-save-guide --project-id <projectId> --req '<req-json>'
```

This CLI requires `--req`, but `{}` is valid when you want a generic guide without scenario context.

Common request patterns:

```bash
ae-cli engage-task task build-save-guide --project-id 1 --req '{}'
ae-cli engage-task task build-save-guide --project-id 1 --req '{"context":{"triggerType":2,"channelId":"channel_123"}}'
ae-cli engage-task task build-save-guide --project-id 1 --req '{"context":{"channelType":2,"triggerType":3,"eventTriggerType":2}}'
ae-cli engage-task task build-save-guide --project-id 1 --req '{"draft":{"baseInfo":{"taskName":"Demo Task"}}}'
```

Supported request fields:

- `context`
  - a lightweight scenario selector
  - use it when you know key dimensions such as trigger type, audience type, channel, or experiment mode
- `draft`
  - a partial `save_task` request
  - use it when you already have part of the final payload and want missing fields, examples, or corrections
- `reqDraft`
  - alias of `draft`
- `detailLevel`
  - `brief`: core requirements only
  - `full`: includes enums, unsupported cases, examples, and self-check information

---

## 3. `context` and `draft`

### 3.1 `context`

Use `context` when you want scenario-specific guidance without writing a partial `save_task.req`.

Typical fields:

- `triggerType`
- `eventTriggerType`
- `targetClusterType`
- `channelType`
- `channelId`
- `channelTemplateId`
- `enableExp`
- `expIndicatorBizType`

Example:

```json
{
  "context": {
    "channelType": 2,
    "triggerType": 3,
    "eventTriggerType": 2,
    "targetClusterType": 2,
    "channelId": "channel_123"
  }
}
```

### 3.2 `draft`

Use `draft` when you already have a partial `save_task.req` and want the guide to tell you:

- what is still missing
- what is invalid
- whether the payload is already close to submit-ready
- what template or schema to use to finish it

Example:

```json
{
  "draft": {
    "baseInfo": {
      "taskName": "Demo Task"
    },
    "triggerConfig": {
      "triggerType": 2
    }
  }
}
```

---

## 4. Output Structure

The guide returns structured metadata rather than free-form prose. The top-level sections are:

- `valid`
- `errors`
- `warnings`
- `missingInputs`
- `saveTaskContract`
- `scenario`
- `requiredInput`
- `fieldRules`
- `handoff`

### 4.1 `valid`

- `true` means the current scenario or draft has no structural blocking errors
- `false` means you should inspect `errors`, `missingInputs`, and `handoff.blockingPlaceholders`

### 4.2 `errors`

Use `errors` for hard blockers such as:

- invalid enum values
- unsupported combinations
- unsupported trigger types

The guide may expose invalid values separately so you can correct them instead of silently dropping them.

### 4.3 `warnings`

Use `warnings` for non-fatal guidance, for example:

- channel content schema is unavailable because no `channelId` was provided
- click-rate experiment setup still needs a channel context

### 4.4 `missingInputs`

Use `missingInputs` as the to-do list for fields you still need before you can submit `save_task`.

Typical examples:

- missing `baseInfo.taskName`
- missing `channelConfig.channelId`
- missing `channelConfig.groupContentList`
- missing `triggerConfig.triggerTime` for scheduled single tasks

### 4.5 `saveTaskContract`

This section describes the high-level contract:

- final tool is `save_task`
- required preflight is `query_channel_list -> build_task_save_guide`
- audience, trigger, and completion conditions use semantic definitions
- `save_task.req` must be a grouped JSON object

### 4.6 `scenario`

This section shows the resolved scenario, such as:

- create vs update draft
- trigger type
- audience type
- channel type / channel id
- whether the scenario is unsupported

### 4.7 `requiredInput`

This section tells you which grouped blocks and fields are required in the current scenario.

Use it to understand what must appear in:

- `baseInfo`
- `channelConfig`
- `targetConfig`
- `triggerConfig`
- `controlConfig`
- `expConfig` when experiment mode is enabled

When experiment mode is enabled (`context.enableExp=true` or draft `expConfig.enableExp=true`):

- capability `engage-task.task.build-save-guide` enriches `handoff.reqTemplate.channelConfig.groupContentList`
  so each entry carries `expGroupName`, `expGroupType`, `percentageInExperiment`, `order`, and `contentList`
- do not drop those association fields when filling content; they must stay aligned with `expConfig.expGroupList`
- copy the complete group tuple (`expGroupName`, `expGroupType`, `percentageInExperiment`, `order`)
  into both lists; matching only by list position is not sufficient

### 4.8 `fieldRules`

This is the most important construction section.

It includes:

- grouped block rules
- structured conditional rules
- the server/client × `triggerType` × `eventTriggerType` combination matrix
- type-specific aggregate, continuous, ordered, and every-completion event shapes
- related-parameter rules
- unsupported fields / values / combinations
- `channelContentSchema`
- enum values and wrong examples when `detailLevel=full`

#### `fieldRules.channelContentSchema`

Treat this as the source of truth for channel content construction.

Use it to get:

- valid keys
- expected item shape
- channel-specific examples
- params that must be copied exactly, such as `paramType`

Do not invent free-form content items such as:

```json
[{"text":"hello"}]
```

Instead, use the valid item structure and put message text into `value`.

#### `fieldRules.blocks.triggerConfig.triggerDefinitionSchema`

For event-triggered tasks, read all of these fields before constructing `triggerDefinition`:

- `combinationMatrix`
- `ruleFields`
- `eventShapes`
- `examples`

The guide treats the A rule as a discriminated envelope:

- `eventTriggerType=0`: aggregate events
- `eventTriggerType=1`: exactly one count/eq event with value at least 2, plus optional blacklist
- `eventTriggerType=2`: at least two ordered steps with `eventDefinition` and `hasDone`
- `eventTriggerType=3`: client-side count/eq/1 events with `eventTriggerCaliberType`

Every event-triggered task A rule must include `periodTimeSymbol`. Use `TS01` for daily,
`TS02` for the complete configured period, `TS03` for weekly, or `TS04` for monthly.
Do not omit this field even when `periodStart` and `periodEnd` are present.

Do not copy the accumulated example and only change `eventTriggerType`. Hermes rejects a final QP
whose event structure does not match its envelope.

#### `fieldRules.blocks.controlConfig.completionIndicatorDef.filterPropertySelectTypes`

Treat this as the source of truth for completion target and experiment main-goal event-filter
property types:

- `allowed` lists the supported metadata `select_type` values.
- `excluded` lists values that must not be used.
- `datetime` is excluded because the task completion-indicator editor cannot display it.

Apply this rule only to
`completionIndicatorDef.completionIndicators[].eventDefinition.filters`. Trigger-event filters have
their own scenario rules and are not subject to this completion-filter restriction.

For `completionIndicatorType=0`, also read and preserve `requiredMainGoalFields` and
`touchCycleRule`. A valid main goal includes `touch_cycle_num` and `touch_cycle_num_unit`; use `1`
and `day` when no custom completion window is requested. Do not rely on static `--validate` alone
because the save service performs this additional business validation.

### 4.9 `handoff`

This is the final section before `save_task`.

Important fields:

- `reqTemplate`
  - a scenario-aware grouped request template
  - use it as a starting point, not as unquestioned final truth
  - for experiment tasks, keep `groupContentList` association fields from the template;
    only replace `contentList[].content` with real channel content
- `readyToSubmit`
  - `true` means the current scenario or draft has no blocking placeholders
- `blockingPlaceholders`
  - unresolved placeholders that still block submission
- `selfCheckList`
  - a final checklist before calling `save_task`
- `successUrlRule`
  - after `save_task` succeeds, build the task detail URL from current page origin plus the relative hash
  - do not hardcode host, IP, or port

---

## 5. How to Use the Guide in Practice

Recommended usage pattern:

1. resolve a real `channelId` with `engage-setting channel list`
2. call `engage-task task build-save-guide`
3. read `fieldRules.channelContentSchema`
4. read `handoff.reqTemplate`
5. fix everything in `blockingPlaceholders`
6. if the guide points to an audience, trigger, or completion condition, add the semantic
   definition directly
7. omit `clientConfig.clientQp`; partial updates preserve the server-authored value
8. call `engage-task task save`
9. after an experiment save succeeds, call `engage-task task get` and verify that both
   `exp_config.exp_group_list` and `group_content_list` contain the expected group tuples

---

## 6. Safety Notes

- `engage-task task build-save-guide` is read-only; it does not save a draft
- do not skip the guide and build `save_task.req` from memory alone
- do not treat the semantic cluster definition builder as mandatory for every task
- do not invent `channelId`, `clusterKey`, content keys, or QP structures
- if the guide exposes an unsupported scenario, correct it before calling `save_task`
