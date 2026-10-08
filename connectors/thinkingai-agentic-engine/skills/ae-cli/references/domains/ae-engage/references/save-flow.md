# ae-cli `engage-flow flow save`

Create, edit, preview, or commit a flow canvas draft.

Mapped command: `ae-cli engage-flow flow save --project-id <projectId> --req '<req-json>'`

> **Protocol v2 (current).** `save_flow` is now **operation-based**. The `--req` object must carry an `operation` of `build`, `preview`, or `commit`. Do **not** use the old `nodeList` / `edgeList` field names -- send `nodes` / `edges` instead. Posting a legacy `nodeList`/`edgeList` payload (or omitting `operation`) makes the backend reject the call with `Unsupported save_flow operation: null`.

The outer Capability input uses `project_id` and `req`; fields inside `req` keep the native camelCase DTO shape documented below. Hermes uses the outer `--project-id` as authoritative. The CLI rejects missing/unsupported `operation` values, legacy `nodeList`/`edgeList` fields, and the removed `sourceFlowUuid` clone mode; otherwise it passes `req` through to Hermes.

---

## 1. General Principles

`engage-flow flow save` does not accept natural language or vague business descriptions directly. It accepts a **flow canvas request whose `req.operation` drives a three-step lifecycle**:

```text
build  ──► status = ready_to_preview ──► preview ──► commit ──► flow_uuid
   │                                                              │
   └──► status = need_input ──► (answer slot, build again)        └──► engage-flow flow get (verify)
```

You still organize user requirements into an intermediate intent first, then map the intent to `nodes` / `edges`, then run the lifecycle.

- `build`: assemble/edit a draft from `nodes` + `edges` (or topology-only `dsl`). `data.result` returns `ready_to_preview` with `draft_id`, `draft_version`, `confirm_token`, and `preview.main_path`, or `need_input` with one more slot required.
- `preview`: validate the draft; **re-issues** fresh `data.result.draft_version` and `data.result.confirm_token` values.
- `commit`: finalize the draft using preview's returned values, mapped back to request fields `draftVersion` and `confirmToken`; the final ID is `data.result.result.flow_uuid`.
- Always verify with `ae-cli engage-flow flow get --project-id <projectId> --flow-uuid <flow_uuid>`.
- To copy an existing flow, first call `engage-flow flow get`, convert `data.flow.node_list` / `data.flow.edge_list` into compact request fields `nodes` / `edges`, then call `operation=build` as normal creation input. Do not pass `sourceFlowUuid`.

---

## 2. Workflow

1. Identify the flow intent from the user input and produce a unified intent JSON.
2. Build a semantic condition request from `ae-analysis/references/user_cluster_models.md`. Use it directly as `targetDefinitionRequest` for custom-audience node configs and branches. Create a named Analysis cluster only when the flow intentionally references an existing reusable cluster.
3. Run `ae-cli engage-setting channel list --project-id <projectId>` to get the available channels and match real `channelId` values for touchpoint nodes. For `webhook_push`, also run `ae-cli engage-setting channel get` and use `data.item.config.params_list` to build request field `contentList` (camelCase; snake_case aliases are normalized during validate).
4. Query `ae-cli engage-flow node-config schema --project-id <project_id> --node-type <type>` before constructing each non-trivial node config, then run `ae-cli engage-flow node-config validate --project-id <project_id> --node-type <type> --operation-mode save_flow --config '<config-json-string>'` before placing the config into `nodes` or `nodeConfigs`.
5. Map the intent JSON to `nodes` and `edges` (compact form, see §7 / §8).
6. `build` → resolve any `need_input` slot → `preview` → `commit`, then verify with `engage-flow flow get`.

---

## 3. `req` Schema (authoritative)

`req` accepts these fields (only `operation` is hard-required):

| Field | Type | Used in | Notes |
|---|---|---|---|
| `operation` | string | all | **Required.** `build` \| `preview` \| `commit` |
| `flowName` | string | build | Flow name. If it is the only content, returns a `need_input` draft with no default nodes |
| `flowDesc` | string | build | Flow description, **max 200 characters** |
| `groupId` | int | build | Flow group ID, default `0` |
| `tzOffset` | number | build | Timezone offset in hours; defaults to server setting |
| `versionType` | int | build | `1=current, 2=update, 3=new, 4=test` |
| `nodes` | array | build | Compact nodes for structured build (see §7) |
| `edges` | array | build | Compact edges for structured build (see §8) |
| `dsl` | string | build | Topology-only: lines `node <id> <type>` and `edge <source> -> <target>` |
| `flowUuid` | string | build | Draft flow UUID for update-draft mode |
| `parentFlowUuid` | string | build | Base version flow UUID for new-version mode |
| `userIntent` | string | build | Natural-language intent (optional) |
| `nodeConfigs` | array | build (edit) | Declarative node config replacements; each item needs `nodeId` + `config` |
| `deleteNodeIds` | array | build (edit) | Node IDs to delete from the draft |
| `deleteEdges` | array | build (edit) | Edges to delete (by `edgeId` or `source`+`target`) |
| `slotAnswer` | object | build (continue) | Answer for the current server-requested slot when status is `need_input` |
| `draftId` | string | preview, commit, build(continue) | Server draft ID returned by `build` |
| `expectedVersion` | int | preview, build(edit) | Expected draft version for editing or preview |
| `draftVersion` | int | commit | Draft version returned by `preview` |
| `confirmToken` | string | commit | Opaque token returned by **preview** (not build) |

`flowUuid` and `parentFlowUuid` are mutually exclusive; when creating a brand-new draft, provide neither.

### Response shape

The Capability envelope is `data.result`, and every key below it is recursively snake_case. When
feeding a returned value into the next `req`, map it back to the camelCase request field shown in §3.
Common response paths include:

| Field | Meaning |
|---|---|
| `data.result.status` | Draft state, such as `need_input`, `ready_to_preview`, `previewed`, or `committed` |
| `data.result.draft_id` / `data.result.draft_version` | Server draft identity and version; use as request `draftId` / `draftVersion` |
| `data.result.selected_mode` | Server-selected authoring mode, such as structured build, wizard, or draft edit |
| `data.result.confidence` / `data.result.reason` | Router confidence and explanation for the selected mode |
| `data.result.next_slot` | One missing slot to answer when `status=need_input`; use as request `slotAnswer` |
| `data.result.preview` | Human-readable preview; use it for user confirmation |
| `data.result.confirm_token` | Token returned by preview; use as request `confirmToken` for commit |
| `data.result.warnings` / `data.result.errors` | Soft warnings and hard validation failures |
| `data.result.supported_operations` | Server-advertised `build`, `preview`, and `commit` contract |
| `data.result.result.flow_uuid` | Final flow UUID after commit |

### Compact node (`nodes[]`)

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Request-local node ID, unique within the request |
| `type` | Yes | Flow node type (see §7.2) |
| `config` | No | Full node business config — JSON object or JSON string |
| `name` | No | Display name |
| `desc` | No | Node description |

### Compact edge (`edges[]`)

| Field | Required | Description |
|---|---|---|
| `source` | Yes | Upstream node ID |
| `target` | Yes | Downstream node ID |
| `edgeId` | No | Edge ID, unique within the canvas |
| `sourceBranchId` | No | Branch ID for edges leaving a split/judge node, or a push action node with two branch outgoing edges |
| `config` | No | Edge business config as JSON string |

---

## 4. Step One: Intent Identification

### 4.1 Information That Must Be Confirmed First

Before building, confirm at least these four categories:

| Item | Description |
|---|---|
| business scenario | new-user activation, churn win-back, paid conversion, etc. |
| target users | who can enter the flow |
| touchpoint method | Push, WeChat subscription, Webhook, etc. |
| branching conditions | whether grouped handling is needed, and the conditions |

If any is missing, do not build.

### 4.2 Intent Output Format

Organize the user requirement into an intermediate intent JSON (not the final `req`):

```json
{
  "flow_type": "<string>",
  "flow_name": "<string>",
  "flow_desc": "<string>",
  "entry": {
    "type": "<single_trigger|repeat_trigger|event_trigger>",
    "segment": "<string|null>",
    "schedule": "<string|null>",
    "start_date": "<YYYY-MM-DD|YYYY-MM-DD HH:mm|null>",
    "end_date": "<YYYY-MM-DD|YYYY-MM-DD HH:mm|null>",
    "trigger_event": { "event": "<string|null>", "op": "<string|null>", "count": "<number|null>", "property_filter": "<object|null>", "time_window": "<string|null>" }
  },
  "nodes": [
    {
      "nid": "n1",
      "node_type": "<split|judge|action|wait|end>",
      "type": "<specific semantic node type>",
      "name": "<string|null>",
      "content": "<string|null>",
      "channel_name": "<string|null>",
      "languages": ["default"],
      "condition": "<object|null>",
      "event": "<object|null>",
      "wait_time": "<string|null>",
      "split_flow_type": "<1|2|null>",
      "branches": [ { "bid": "b1", "label": "<string>", "condition": "<object|null>", "time_limit": "<string|null>", "percentage": "<number|null>" } ]
    }
  ],
  "edges": [ { "source": "n1", "target": "n2", "branch": "<branch label|null>" } ]
}
```

`channel_name` stays semantic here; match it to a real `channelId` later. `branches` later materialize into `node.config.branchList` and `edge.sourceBranchId`.

---

## 5. Step Two: Required CLI Queries

### 5.1 Semantic Audience

```bash
ae-cli analysis user-cluster create --project-id <projectId> --cluster-name <condition_cluster_name> --display-name <display_name> --definition-request '<semantic-definition-json>'
ae-cli analysis user-cluster get --project-id <projectId> --cluster-names '["<condition_cluster_name>"]'
```

Prefer the created cluster reference for an existing-cluster audience. For a custom audience, pass the semantic definition as `targetDefinitionRequest`; do not copy or construct stored execution QP.
Use only the documented semantic fields. Unknown fields are rejected, and property `field` values
may be technical-name strings or `{name,type}` references.

Custom flow audiences support `behavior_sequence`. When `flow get` returns relation-preserving
top-level `compound` nodes, retain them unchanged in subsequent saves; they preserve distinct
member-group, event-group, and outer relations.
For the second sequence step, omit `relative_to_first` or set it to `false`; use `true` only
from the third step onward when its window must be measured from step 1.

### 5.2 Project Channels

```bash
ae-cli engage-setting channel list --project-id <projectId>
```

Match a real `channel_id` for touchpoint nodes (priority: exact name match → keyword match → fallback by node/channel type), then place it in request field `channelId`. For `webhook_push`, also call `ae-cli engage-setting channel get` and drive request field `contentList` from `data.item.config.params_list`.

**The channel must be enabled.** A node referencing a disabled channel (`channel_status = 0`) fails with `disabled_channel: channelId must reference an enabled channel`, and `build` stalls on a `need_input` channel slot. Enable it first via `ae-cli engage-setting channel update-status --status 1` (write op — requires explicit user intent).

---

## 6. Step Three: Map Intent Nodes to Canvas Nodes

### 6.1 Entry Node Mapping

| Intent `entry.type` | Canvas node `type` |
|---|---|
| `single_trigger` | `single_trigger` |
| `repeat_trigger` | `repeat_trigger` |
| `event_trigger` | `event_trigger` |

There must be exactly one entry node.

### 6.2 Business Node Mapping

| Intent semantics | Canvas node `type` |
|---|---|
| Behavioral split | `event_split_flow` |
| Feature split | `feature_split_flow` |
| A/B split | `ab_split_flow` |
| Behavioral judgment | `event_judge` |
| Feature judgment | `feature_judge` |
| Push touchpoint | `message_push` |
| WeChat touchpoint | `wechat_push` |
| Webhook / external touchpoint | `webhook_push` |
| Wait | `time_control` |
| End | `exit_flow` |

### 6.3 Condition Field Mapping

| Semantic type | Target field |
|---|---|
| Audience segmentation / feature judgment / feature split branch | `targetDefinitionRequest` |
| Event trigger / behavioral judgment / behavioral split branch | `triggerDefinition.rules[].events[]` |

### 6.4 Touchpoint Node Mapping

Inside action nodes: `channel_name` → real `channelId`; `content` → `contentList`; `languages` → whether to generate multilingual `contentList` entries.

---

## 7. Step Four: Build `nodes`

### 7.1 Most Important Rules

1. `node.id` must be unique within the request.
2. Any `branchId` later referenced by `edge.sourceBranchId` must be declared in that node's `config` first.
3. Every path must eventually end at `exit_flow`.
4. `config` may be a JSON object or a JSON string. `targetDefinitionRequest` itself is a JSON object.
5. Hermes compiles `targetDefinitionRequest` and Flow-specific `triggerDefinition` fields (including branch definitions) on `nodes[]`, `nodeConfigs[]`, and `slotAnswer.nodeConfig.config` before legacy node validation. `node-config validate` uses the same compile path. Other compatible input normalization remains unchanged.
6. Never send `targetClusterQp`; it is a server-authored execution field. Every `event` and
   `behavior_sequence` inside `targetDefinitionRequest` must include its own `time_range`.
   Entry-node `startDate` / `endDate` values do not provide an audience-event time range.
7. Audience fields must resolve through the current Flow editor metadata scope. If Hermes
   rejects a field, choose another property returned for the same project, timezone, and user
   entity instead of constructing persisted metadata manually.

### 7.2 Common Node Types

`single_trigger`, `repeat_trigger`, `event_trigger`, `event_split_flow`, `feature_split_flow`, `ab_split_flow`, `event_judge`, `feature_judge`, `message_push`, `wechat_push`, `webhook_push`, `time_control`, `exit_flow`.

Before writing any config below, call `engage-flow node-config schema` for the exact node type. The backend schema is the source of truth for required fields, defaults, allowed enum values, submit-time requirements, and examples.

### 7.3 Common `config` Templates

#### `single_trigger`

```json
{ "targetUserType": 2, "triggerTime": "<YYYY-MM-DD HH:mm>", "flowEndDate": "<YYYY-MM-DD HH:mm>", "targetClusterName": "<existing clusterName>" }
```

For custom users, use `targetUserType=1` and fill `targetDefinitionRequest` with the Analysis-compatible semantic definition. For existing clusters (`targetUserType=2`), fill `targetClusterName` from a real current-project cluster list queried with the flow `tzOffset`; do not fill `targetDefinitionRequest`. `clusterPredictCount` defaults to `0` and `clusterPredictTime` defaults to `""` when omitted.

#### `repeat_trigger`

```json
{ "targetUserType": 1, "startDate": "<YYYY-MM-DD>", "endDate": "<YYYY-MM-DD>", "flowEndDate": "<YYYY-MM-DD HH:mm>", "crontab": "0 00 09 * * ?", "entryControlLimits": { "enableMultEntry": false, "disableConcurrentEntry": false }, "targetClusterName": null, "targetDefinitionRequest": { "type": "condition", "conditions": { ... } } }
```

`entry.segment` → `targetDefinitionRequest`; `entry.schedule` → `crontab` (common default `0 00 09 * * ?`). `clusterPredictCount` defaults to `0` and `clusterPredictTime` defaults to `""` when omitted. For existing clusters (`targetUserType=2`), fill `targetClusterName` from a real current-project cluster list queried with the flow `tzOffset`; do not fill `targetDefinitionRequest`.

#### `event_trigger`

```json
{ "triggerType": 3, "targetUserType": 1, "startDate": "<YYYY-MM-DD HH:mm>", "endDate": "<YYYY-MM-DD HH:mm>", "flowEndDate": "<YYYY-MM-DD HH:mm>", "triggerDefinition": { "rules": [ { "periodStart": "<startDate>", "periodEnd": "<endDate>", "periodTimeSymbol": "TS02", "eventTriggerType": 0, "events": [] } ] }, "entryControlLimits": { "enableMultEntry": false, "disableConcurrentEntry": false }, "targetDefinitionRequest": { "type": "condition", "conditions": { ... } } }
```

`entry.trigger_event` → `triggerDefinition.rules[0].events`; add `targetDefinitionRequest` only when `entry.segment` exists. `triggerType` supports `3`, `4`, and `5`; `targetUserType=2` existing cluster is not supported for `event_trigger`; use `1` custom or `3` all users. For non-branch trigger rules, use `periodStart` / `periodEnd` / `periodTimeSymbol`. `realtime`, `clusterRefresh`, `clusterRefreshTime`, `clusterPredictTime`, and rule `zoneoffset` can be omitted and are defaulted by the backend.

#### `event_split_flow`

```json
{ "splitFlowType": 1, "branchList": [ { "branchId": "<branchId>", "branchName": "<label>", "branchType": 1, "targetClusterType": 3, "triggerDefinition": { "rules": [ { "delayTimeSymbol": "<minute|hour|day>", "delayTime": "<number>", "eventTriggerType": "<0|-1|1|2>", "events": [] } ] } } ] }
```

`time_limit` → `delayTimeSymbol` + `delayTime`; `0` = happened, `-1` = not happened. For `branchType=1`, fill `targetClusterType`; use `3` for all users. If `targetClusterType` is not `3`, fill `clusterKey`. `occasionKeys` is optional, but each item must contain at least four colon-separated parts. Fallback branch keeps only `{ "branchId": "<branchId>", "branchType": 2 }` and must omit `triggerDefinition`.

#### `feature_split_flow`

```json
{ "splitFlowType": 1, "branchList": [ { "branchId": "<branchId>", "branchName": "<label>", "branchType": 1, "realtime": 0, "clusterRefresh": 12, "clusterPredictCount": null, "clusterPredictTime": "<YYYY-MM-DD HH:mm:ss>", "targetDefinitionRequest": { "type": "condition", "conditions": { ... } } } ] }
```

Fallback branch keeps only `branchId` + `branchType: 2`.

#### `ab_split_flow`

```json
{ "branchList": [ { "branchId": "<branchId>", "branchName": "Control Group", "branchType": 1, "order": 1, "percentageInExperiment": 34 }, { "branchId": "<branchId>", "branchName": "Experiment Group A", "branchType": 2, "order": 2, "percentageInExperiment": 33 } ], "indicatorsDef": [], "activateIndicatorsDef": null }
```

#### `event_judge`

```json
{ "transferType": 1, "meetBranchId": "<meetBranchId>", "notMeetBranchId": "<notMeetBranchId>", "triggerDefinition": { "rules": [ { "periodStart": "<YYYY-MM-DD HH:mm>", "periodEnd": "<YYYY-MM-DD HH:mm>", "periodTimeSymbol": "TS02", "eventTriggerType": 0, "events": [] } ] } }
```

`event_judge` is a non-branch flow task. Use `periodStart`, `periodEnd`, and `periodTimeSymbol` in the A segment; use `delayTime` / `delayTimeSymbol` only for a B segment when the schema/example requires it. `eventTriggerType` supports `0`, `1`, and `2`.

#### `feature_judge`

```json
{ "transferType": 1, "meetBranchId": "<meetBranchId>", "notMeetBranchId": "<notMeetBranchId>", "clusterPredictCount": null, "clusterPredictTime": "", "targetDefinitionRequest": { "type": "condition", "conditions": { ... } } }
```

#### `message_push` / `webhook_push`

```json
{ "channelId": "<matched channelId>", "channelType": "<matched channelType>", "contentList": [ { "pushLanguageCode": "default", "content": [] } ] }
```

`channel_name` → real response `channel_id` → request `channelId`; `content` → the param that best matches body text. `processType` defaults to `1`, `enableChannelTouchLimits` defaults to `0`, and `isOccasionUp` defaults to `false`. `enableChannelTouchLimits` may be supplied as a boolean for compatibility, but `normalizedConfigObject` will convert it to `1` or `0`. When the param `type = TEXT`, also add `{ "config": "[{\"type\":\"paragraph\",\"children\":[{\"text\":\"<same as value>\"}]}]" }`. `contentList[].content` should be a JSON array; validation also accepts a JSON-stringified array for compatibility. When the param `type = OBJ_ARRAY`, `value` must be a JSON array, and the item must copy the complete child field definition from `data.item.config.params_list[].obj_array`. First `contentList` entry must use `"pushLanguageCode": "default"`; generate extra languages per `languages`.

#### `wechat_push`

```json
{ "channelId": "<matched channelId>", "enableChannelTouchLimits": false, "isOccasionUp": false, "contentList": [ { "pushLanguageCode": "default", "content": [ { "key": "lang", "type": "STRING", "required": true, "paramType": 2, "name": "Language", "value": "default" }, { "key": "page", "type": "STRING", "required": true, "paramType": 2, "name": "Destination Page", "value": "" }, { "key": "miniprogramState", "type": "STRING", "required": true, "paramType": 2, "name": "Version", "value": "" } ] } ], "processType": 1 }
```

#### `time_control`

```json
{ "controlType": 1, "timeUnit": "<minute|hour|day>", "timeUnitNum": "<number>" }
```

`controlType=1` requires `timeUnit` + `timeUnitNum`; `2` requires `timePointStr`; `3` requires `rollTimeDayNum` + `timePointStr`; `4` requires `fixedDay` + `timePointStr`; `5` requires `relativeMonthLastDayNum` + `timePointStr`.

`30 minutes` → `minute`+`30`; `2 hours` → `hour`+`2`; `1 day` → `day`+`1`.

#### `exit_flow`

Minimum usable `config`: `{}`.

---

## 8. Step Five: Build `edges`

### 8.1 Regular Edge

```json
{ "source": "node_1", "target": "node_2" }
```

### 8.2 Branch Edge

```json
{ "source": "node_split", "target": "node_a", "sourceBranchId": "branch_a" }
```

### 8.3 Standard Outgoing-Edge Rules

| node type | Outgoing edges | `sourceBranchId` |
|---|---|---|
| `single_trigger` / `repeat_trigger` / `event_trigger` | 1 | do not provide |
| `event_split_flow` / `feature_split_flow` / `ab_split_flow` | one per branch | the corresponding `branchList[].branchId` |
| `event_judge` / `feature_judge` | 2 | `meetBranchId` and `notMeetBranchId` |
| `message_push` / `wechat_push` / `webhook_push` | 1 or 2 | omit for 1 outgoing edge; for 2 outgoing edges, use the node config's `meetBranchId` and `notMeetBranchId` |
| `time_control` | 1 | do not provide |
| `exit_flow` | 0 | do not provide |

### 8.4 Rules

1. `source` / `target` must reference existing `node.id` values.
2. Edges leaving split/judge nodes carry `sourceBranchId`. Push action nodes (`message_push`, `wechat_push`, `webhook_push`) may also carry `sourceBranchId` when they have exactly two outgoing edges.
3. For push action nodes with one outgoing edge, omit `meetBranchId` / `notMeetBranchId`; if present, the backend ignores them.
4. For push action nodes with two outgoing edges, set both `config.meetBranchId` and `config.notMeetBranchId`, and make the two `edge.sourceBranchId` values match them.
5. The graph must be a DAG (no cycles).

---

## 9. Semantic trigger-event definitions

Use `triggerDefinition` instead of `triggerRule`. Flow uses the same Analysis semantic event fields
as Task, but it does **not** use the Task trigger envelope contract. Select the Flow envelope from
the matrix below and let Hermes compile and validate the persisted `triggerRule`.

| Flow context | Allowed A-rule `eventTriggerType` |
| --- | --- |
| `event_trigger` | `0`, `1`, `2` |
| `event_judge` | `0`, `1`, `2` |
| non-fallback `event_split_flow` branch | `-1`, `0`, `1`, `2` |

`eventTriggerType=3` is the Task client-channel EVERY mode and is not valid for Flow. A second B
rule, when present, is always an accumulated (`0`) aggregate rule. It must not contain
`blackList`, `relationProps`, rule-level window fields, or sequence-step fields.

### 9.1 Accumulated or not-happened: `0` / `-1`

Use aggregate semantic events. Flow aggregate triggers support `count` and `sum`, with `eq`, `lt`,
`lte`, `gt`, or `gte`; `sum` requires `property`. `-1` means “did not happen” and is valid only
for a non-fallback `event_split_flow` branch; it cannot have a B rule.

```json
{
  "triggerDefinition": {
    "rules": [
      {
        "eventTriggerType": 0,
        "events": [
          {
            "type": "event",
            "event": "login",
            "aggregation": "count",
            "operator": "gte",
            "value": 1
          }
        ]
      }
    ]
  }
}
```

Do not include `blackList`, `relationProps`, `windowGap`, `windowGapTimeUnit`,
`eventTriggerCaliberType`, `hasDone`, or `hasDistanceStart` in this envelope.

### 9.2 Continuous completion: `1`

Use exactly one count event with `operator=eq`. `blackList` accepts semantic events that Hermes
compiles as non-aggregate selectors. `relationProps` and the rule-level window are optional; when
using a window, provide both fields.

```json
{
  "eventTriggerType": 1,
  "windowGap": 7,
  "windowGapTimeUnit": "day",
  "relationProps": [],
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

### 9.3 Ordered completion: `2`

Each sequence item wraps its semantic event in `eventDefinition`. The last step must have
`hasDone=true`, and at least one step must be completed. Optional intermediate steps may use
`hasDone=false`. Step windows require both `windowGap` and `windowGapTimeUnit`.

```json
{
  "eventTriggerType": 2,
  "relationProps": [],
  "events": [
    {
      "eventDefinition": {
        "type": "event",
        "event": "login",
        "aggregation": "count",
        "operator": "eq",
        "value": 1
      },
      "hasDone": false,
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

Do not put persisted aggregate fields (`taPropQuota`, `uceCalcuSymbol`, `num`) directly on an
ordered step, and do not copy Task ORDER/EVERY examples into Flow. Hermes supplies metadata and
numeric Flow relations. Flow get returns `triggerDefinition` plus conversion status and hides
`triggerRule`.

---

## 10. Step Six: Graph Constraint Checks

Before `preview`/`commit`, self-check:

1. `nodes` is not empty; exactly one entry node; at least one `exit_flow`.
2. Each `exit_flow` has exactly one incoming edge and no outgoing edges.
3. Each `node.id` is unique; every edge references existing nodes; the graph is acyclic.
4. **Every terminal branch must use its own dedicated `exit_flow` node** — do not let multiple upstream nodes point at one shared `exit_flow`. A flow with N terminal paths needs N separate `exit_flow` nodes (otherwise the backend rejects the shared exit). Error: `... branch must use its own dedicated exit ...`.
5. If a split node uses `splitFlowType = 2`, different branches must not converge into the same node; each branch leads to its own `exit_flow`.

---

## 11. Step Seven: Run the Lifecycle (CLI)

### 11.1 Flags

| Flag | Type | Required | Description |
|---|---|---|---|
| `--project-id` / `-p` | number | Yes | Project ID |
| `--req` | json | Yes | operation-based request object |

The CLI injects `projectId` into both the top level and `req`; you do not write `req.projectId` yourself.

### 11.2 `need_input` Continuation

`need_input` is a **soft prompt**, not a hard error:

- **`data.result.errors` empty + `data.result.next_slot` present** → server needs one more node config (trigger / channel / targetCluster). Answer with request fields `operation=build` + `draftId` + `expectedVersion` + `slotAnswer`. If response `next_slot.target_node_id` is present, request `slotAnswer.nodeConfig` may contain only `config`; otherwise include `nodeId` or `id`. **`slotAnswer.nodeConfig.config` merges into the existing node config** — send only the fields you are adding or changing, not the full config.
- For existing-cluster entry nodes (`targetUserType=2`), use `targetClusterName` or `clusterId` alias.
- For custom audiences, build an Analysis-compatible `targetDefinitionRequest`.
- For `event_trigger`, `endDate` must be **strictly earlier than** `flowEndDate`.
- **`data.result.errors` non-empty** → hard validation failure. Fix `nodes`/`edges` and `build` again (a new `data.result.draft_id` is issued; the stale draft is cleaned by TTL).

### 11.3 Minimal Working Example

```bash
# 1) build
ae-cli engage-flow flow save --project-id 1 --req '{
  "operation": "build",
  "flowName": "Welcome Flow",
  "flowDesc": "New user welcome flow",
  "groupId": 0, "tzOffset": 8, "versionType": 1,
  "nodes": [
    { "id": "n1", "type": "single_trigger", "name": "Enter", "config": { "targetUserType": 2, "triggerTime": "2026-03-31 19:00", "flowEndDate": "2026-04-04 18:00", "targetClusterName": "cohort_20260331_182643" } },
    { "id": "n2", "type": "exit_flow", "name": "End", "config": {} }
  ],
  "edges": [ { "source": "n1", "target": "n2" } ]
}'
# → data.result: status = ready_to_preview, draft_id = D, draft_version = V0, confirm_token = T0

# 2) preview (response re-issues draft_version V1 + confirm_token T1)
ae-cli engage-flow flow save --project-id 1 --req '{ "operation": "preview", "draftId": "D", "expectedVersion": 0 }'

# 3) commit (map preview draft_version/confirm_token to request draftVersion/confirmToken)
ae-cli engage-flow flow save --project-id 1 --req '{ "operation": "commit", "draftId": "D", "draftVersion": 1, "confirmToken": "T1" }'
# → data.result.status = committed, data.result.result.flow_uuid = <flow_uuid>

# 4) verify
ae-cli engage-flow flow get --project-id 1 --flow-uuid <flow_uuid>
```

> ⚠️ `commit` must map preview's `data.result.draft_version` and `data.result.confirm_token` to request fields `draftVersion` and `confirmToken`. Build's values cause a token/version mismatch.

### 11.4 Output After Successful Commit

The committed flow has `status = 0` (draft) — `commit` only freezes the draft into a flow version, it does **not** start delivery. To actually run it, enable it separately via `ae-cli engage-flow flow manage` (with explicit user intent).

Show the user the canvas name and a **clickable Markdown link**:

- Standard Markdown link syntax, not inside a code block.
- URL starts with `/#/`, no domain prefix.
- Substitute the real `flowUuid` and `projectId`.

Template: `[Open Canvas](/#/hermes/flow/detail?flowUuid=<flowUuid>&currentProjectId=<projectId>)`

Correct example: `[Open Canvas](/#/hermes/flow/detail?flowUuid=0006_831135755&currentProjectId=1)`

Common mistakes: adding a domain placeholder; putting the link inside a code block; outputting a plain-text URL instead of `[text](URL)`.

### 11.5 Output After Failure

Output the complete `req` JSON for debugging plus a clear failure reason.

---

## 12. Common Validation Errors

| Symptom | Cause | Fix |
|---|---|---|
| `Unsupported save_flow operation: null` | Legacy `nodeList`/`edgeList` payload, or `operation` missing | Put `operation` = `build`/`preview`/`commit` in `req`, use `nodes`/`edges` |
| `Flag --req.sourceFlowUuid is no longer supported` | Removed clone mode from an older protocol | Call `engage-flow flow get`, convert `data.flow.node_list`/`data.flow.edge_list` into compact request `nodes`/`edges`, then create with `operation=build` |
| operation rejected (`SAVE`/`DRAFT`/`SUBMIT`/`mode`/`action`…) | Wrong field or wrong enum | `operation` is at `req.operation`; enum is only `build`/`preview`/`commit` |
| semantic definition rejected | Unsupported condition type, operator, aggregation, or time range | Rebuild the Analysis-compatible semantic definition; see `ae-analysis` user-cluster models |
| `invalid_preset_count_expression` | Event count condition uses an unsupported semantic operator/value | Use `operator = "gte"` + `value = 1` (see §9.2) |
| `... branch must use its own dedicated exit ...` | Multiple paths share one `exit_flow` | Give every terminal branch its own `exit_flow` node (see §10.4) |
| `disabled_channel: channelId must reference an enabled channel` | Response `channel_status = 0` | `engage-setting channel update-status --status 1` first |
| commit token/version mismatch | Used build's `confirm_token`/`draft_version` | Use the values returned by **preview** |
| `flowDesc` rejected | Over 200 chars | Trim to ≤ 200 |
| `config` rejected as object where string expected | Wrong shape for TEXT rich-text or another legacy string field | `JSON.stringify` only the documented inner string values |

---

## 13. Most Common Mistakes

1. **Legacy `nodeList`/`edgeList`** — use `nodes`/`edges` with `operation=build`.
2. **Removed clone mode** — do not pass `sourceFlowUuid`; copy flows via `engage-flow flow get` and a fresh `operation=build` request.
3. **Time units must be lowercase** — `day`, `hour`, `minute`, `week`, `month` (not `DAY`/`HOUR`).
4. **Do not invent `channelId`** — get it from `ae-cli engage-setting channel list`.
5. **Define branch IDs before referencing them** — `edge.sourceBranchId` must already exist in the upstream node `config`; for two-edge push action nodes, use `meetBranchId` and `notMeetBranchId`.
6. **Custom audiences are semantic objects** — use `targetDefinitionRequest`; do not stringify or construct execution QP.
7. **TEXT rich-text `config` must also be a string** — not an object.
8. **`commit` uses preview's token/version** — not build's.
9. **Do not merge branches again when `splitFlowType = 2`**.

---

## 14. One-Sentence Summary

Drive `engage-flow flow save` as a state machine — `build` (`nodes`/`edges`, not `nodeList`/`edgeList` or `sourceFlowUuid`) → resolve any `need_input` slots → `preview` (map response `draft_version` + `confirm_token` to request `draftVersion` + `confirmToken`) → `commit` → verify with `engage-flow flow get`; submit only semantic audience and trigger definitions, and ensure touchpoint channels are enabled before referencing them.
