---
name: ae-engage
version: 1.0.0
description: "AE Engage capability gateway: config center, flows, push/config channels, strategies, templates, task management, operation activities, and query lifecycle. Trigger words: config center, scene config, push channel, config channel, operation strategy, operation task, operation activity, query lifecycle, template, config item, Engage, Hermes, engage-scene, engage-setting, engage-flow, engage-task, engage-activity, engage-query."
---

# ae-engage

AE CLI (`ae-cli`) is the command-line tool for the ThinkingEngine data analysis platform, used by AI Agents and human users.

## Global AE CLI Rules

AE CLI (`ae-cli`) is the command-line tool for the AE / TE / ThinkingEngine analysis platform. For AE analysis-side requests, prefer `ae-cli` and this skill's reference docs over model memory.

Global parameters:

| Parameter | Description |
|---|---|
| `--format <json\|table>` | Output format. Default is JSON. |
| `--jq <expr>` | jq filter expression for JSON output. |
| `--host <url>` | Override the active AE host. Available on every command and may be placed after the subcommand, e.g. `ae-cli engage-flow flow list --host <url>`. |

Output and errors:
- Successful commands return machine-readable JSON by default. Envelope may include optional `_notice.host_compat`.
- Failed commands return `{ "ok": false, "error": { "type": "...", "message": "...", "hint": "..." } }` and exit non-zero.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.

Safety constraints:
- Read commands can execute directly after required IDs and references are verified.
- Write commands require explicit user intent. Ordinary `write` commands execute without CLI confirmation; only `high-risk-write` commands use the confirmation gate.
- Never invent command names, flags, JSON payloads, `project_id`, resource IDs, field names, event names, property names, metric definitions, or date formats. Read the matching command reference and discover real project metadata first.
- **NEVER fabricate or guess resource names** (reports, dashboards, events, properties, metrics, clusters, tags, alerts). Always use list commands to discover real resources first. If a resource is not found after fuzzy search and full list fallback, explicitly tell the user "resource not found" and stop - do not proceed with fabricated names.

## Overview

The `ae-engage` package provides Hermes Engage capabilities across config items, flows, channel settings, task data, and query lifecycle. Use capability-gateway commands through `ae-cli engage-flow|engage-task|engage-setting|engage-scene|engage-query <resource> <action>`; low-frequency reports use the L3 references below.

Typical use cases include:

- Querying and managing channels, config channels, approvers, and whitelists
- Querying project channel touch-limit or fatigue-control rules
- Querying task lists, task details, experiment reports, and metric reports
- Querying config items and strategies, copying templates, and managing strategy status
- Querying flow lists, node schemas, and flow reports, and saving or managing flows

## Keyword Routing

When the user mentions a product term below (including common Chinese UI labels), open the listed reference(s) first — do not guess commands or IDs.

| Keyword | Product meaning | CLI domain | Primary reference | Related references |
|---|---|---|---|---|
| **Config center** | Engage scene management / config center overview | `engage-scene` | `references/scene-config-item.md` | `scene-config-param.md`, `scene-config-group.md`, `scene-preset-metric.md`, `scene-config-metric.md`, `scene-config-channel.md`, `channel-mgmt.md`, `scene-strategy.md`, `scene-template.md`; L3 reports: `config-item-trigger-report.md`, `config-item-analysis-report.md`, `config-item-strategy-comparison.md` |
| **Scene config** | Same as config center; params, groups, metrics, channels, strategies, and templates under a config item | `engage-scene` | `references/scene-config-item.md` | Same as above; params/groups/metrics: `scene-config-param.md`, `scene-config-group.md`, `scene-preset-metric.md`, `scene-config-metric.md` |
| **Config item** | A single config item in the config center | `engage-scene` | `references/scene-config-item.md` | `scene-config-param.md`, `scene-preset-metric.md`, `scene-config-metric.md`, `scene-strategy.md`, `scene-template.md` |
| **Push channel** | Project-level message push channels (Webhook, FCM, APNS, etc.) | `engage-setting` | `references/channel-list.md` | `channel-detail.md`, `add-channel.md` (**Webhook vs Client differ**: `url` = HTTP vs scene key; custom params `user:` vs `user:`/`client:`), `update-channel-status.md`, `delete-channel.md`, `channel-update-config.md`, `channel-test-send.md`, `channel_touch_limits_list.md` |
| **Config channel** | Config-center Webhook/client config channels (not the same as push channels) | `engage-scene` | `references/scene-config-channel.md` | `channel-mgmt.md` (create/enable-disable/copy/delete workflows). User params in `config.customsParamList` require `columnName` with `user:` prefix (e.g. `user:#account_id`); preflight names with ae-analysis `analysis-meta property list/get`. |
| **Operation strategy** | Ops/delivery strategies under a config item | `engage-scene` | `references/scene-strategy.md` | Custom audience: [`scene-strategy-audience.md`](references/scene-strategy-audience.md) — semantic `definitionRequest` (Analysis condition shape); do not pass `targetClusterQp`/`qp`; preflight props (stop + list if missing); template: `scene-template.md` |
| **Operation task** | Hermes push/engagement tasks (list, save, lifecycle, reports) | `engage-task` | `references/task-list.md` | `task-detail.md` (get), `save-task.md`, `build-task-save-guide.md`, `task-stats.md`, `task-delete.md`, `push-record-query.md`, `task-user-detail-export.md`, `task-indicator-user.md`, `task-data-overview.md`, `task-data-detail.md`, `task-metric-detail.md`, `task-experiment-report.md` |
| **Operation activity** | Campaign activity management and delivery trends by activity, topic, or standalone task | `engage-activity` | `references/activity-activity.md` | `activity-data-detail.md`, `activity-topic.md`, `activity-task.md`, `activity-approval.md` |
| **Template** | Strategy templates under a config item | `engage-scene` | `references/scene-template.md` | `scene-config-param.md` (template fields reference `paramId`); enable via `template update` then `template update-status` before strategy create |

**Easy to confuse:**

- **Push channel** → `ae-cli engage-setting channel …` (Hermes push channel settings)
- **Config channel** → `ae-cli engage-scene config-channel …` (config-center channels; see `channel-mgmt.md`)
- Flow / Task canvas nodes use `channelId` from **push channels**; config items bind `channel_id` from **config channels**

## Parameter Conventions

- Use regular flags for simple parameters, for example `--project-id`, `--task-id`, and `--flow-uuid`
- Use JSON flags for array parameters, for example `--strategy-uuid-list '["id1","id2"]'`
- Use named JSON flags for object parameters, for example `--req '{...}'` and `--flow-list '[...]'`
- Optional global parameters work the same way as in other domains, for example `--host`, `--mcp-url`, and `--dry-run`

Naming boundary:

- CLI flags use kebab-case; outer Capability input and all Capability response keys use snake_case.
- Nested business DTOs passed through `--req` or `--payload` keep their documented native camelCase fields. Do not mechanically convert those nested DTO keys to snake_case.
- Semantic audience, event, trigger, completion, and metric definitions are closed contracts. The CLI rejects malformed or unknown semantic fields locally; `--validate` applies the same precise Hermes capability schema without writing.
- Successful migrated commands return their business payload under `data`; read the matching reference's Response shape before selecting fields.

## JSON Parameter Format

Common JSON flag examples:

```bash
--provider-list '["webhook","fcm"]'
--strategy-uuid-list '["strategy_a","strategy_b"]'
--flow-id-list '["flow_1","flow_2"]'
--req '{"pageNum":1,"pageSize":20}'
```

## Common Scenarios

### 1. setting

```bash
# Query the channel list
ae-cli engage-setting channel list --project-id 1

# Filter by provider
ae-cli engage-setting channel list --project-id 1 --provider-list '["webhook","fcm"]'

# Query config channels (config center channel management — use engage-scene, not legacy +config_channel_*)
ae-cli engage-scene config-channel list --project-id 1 --channel-type 0

# Query project channel touch-limit rules
ae-cli engage-setting channel-touch-limits list --project-id <project_id>

# Update a channel's config / reach-funnel settings
ae-cli engage-setting channel update-config --project-id <project_id> --channel-id <channel_id> --enable-touch-event 1

# Send a test message to a channel
ae-cli engage-setting channel test-send --project-id <project_id> --channel-id <channel_id> --push-id <send_id> --content-list '[{"key":"title","value":"hello"}]'

# Batch update / toggle / save channel touch-limit (fatigue-control) rules
ae-cli engage-setting channel-touch-limits batch-update --project-id <project_id> --items '[{"rule_id":"r1","enable":true,"rule_def":"[]"}]'
ae-cli engage-setting channel-touch-limits toggle --project-id <project_id> --rule-id <rule_id> --enable false
ae-cli engage-setting channel-touch-limits save --project-id <project_id> --channel-biz-type <biz_type> --rule-def '[]' --enable true

# Remove an approver from a project
ae-cli engage-setting approval-approver delete --project-id <project_id> --approver <open_id> --yes

# Whitelist add / update / delete / verify
ae-cli engage-setting whitelist add --project-id <project_id> --prop-code <prop_code> --column-name <column_name> --column-type string --whitelist-list '[{"entity_id":"u1","source_value":"v1"}]'
ae-cli engage-setting whitelist update --project-id <project_id> --whitelist-id <id> --note-name <name>
ae-cli engage-setting whitelist delete --project-id <project_id> --whitelist-ids '["wl-1"]' --yes
ae-cli engage-setting whitelist verify --project-id <project_id> --prop-code <prop_code> --column-type string --whitelist-prop-list '["v1"]'

# Push-language (localization) get / set
ae-cli engage-setting push-language get --project-id <project_id>
ae-cli engage-setting push-language set --project-id <project_id> --push-language-column <prop_code>

# Client param update / delete / list
ae-cli engage-setting client-param create --project-id <project_id> --column-name level --column-type varchar --column-desc Level
ae-cli engage-setting client-param update --project-id <project_id> --column-name level --column-desc Level
ae-cli engage-setting client-param delete --project-id <project_id> --column-name level --yes
ae-cli engage-setting client-param list --project-id <project_id>

# Config table upload / save / list / query-data / update-data / delete
ae-cli engage-setting config-table upload --project-id <project_id> --request-id <rid> --file-name data.csv --file-content "$(base64 -i data.csv)"
ae-cli engage-setting config-table save --project-id <project_id> --request-id <rid> --info-name <table_name>
ae-cli engage-setting config-table list --project-id <project_id>
ae-cli engage-setting config-table query-data --project-id <project_id> --info-id <info_id>
ae-cli engage-setting config-table update-data --project-id <project_id> --request-id <rid> --info-name <table_name> --info-id <info_id>
ae-cli engage-setting config-table delete --project-id <project_id> --info-id <info_id> --yes

# Preset event list / update
ae-cli engage-setting preset-event list --project-id <project_id>
ae-cli engage-setting preset-event update --project-id <project_id> --add-event-definition '<semantic_event_json>'

# Common metric list / get / create / update / delete
ae-cli engage-setting common-metric list --project-id <project_id>
ae-cli engage-setting common-metric get --project-id <project_id> --metric-name <name>
ae-cli engage-setting common-metric create --project-id <project_id> --metric-type 1 --metric-name <name> --metric-definition '<semantic_metric_json>' --metric-window-num 1 --metric-window-time-unit day --display-name <display>
ae-cli engage-setting common-metric update --project-id <project_id> --metric-type 1 --metric-name <name> --metric-definition '<semantic_metric_json>' --metric-window-num 1 --metric-window-time-unit day --display-name <display>
ae-cli engage-setting common-metric delete --project-id <project_id> --metric-name <name> --yes
```

### 2. task

```bash
# Query the task list
ae-cli engage-task task list --project-id 1 --req '{"pageNum":1,"pageSize":20}'

# Build a save_task guide before composing the final req
ae-cli engage-task task build-save-guide --project-id 1 --req '{"context":{"triggerType":2,"channelId":"channel_123"}}'

# Save a task draft (create when req.taskId is omitted)
ae-cli engage-task task save --project-id 1 --req '{"baseInfo":{"taskName":"Demo Task"},"channelConfig":{"channelType":1,"channelId":"channel_123","groupContentList":[{"contentList":[{"pushLanguageCode":"default","content":"[]"}]}]},"targetConfig":{"targetClusterType":3},"triggerConfig":{"triggerType":2},"controlConfig":{"completionIndicatorDef":{"completionIndicators":[]}}}'

# Query task details
ae-cli engage-task task get --project-id 1 --task-id task_123

# Submit a saved draft task for approval
ae-cli engage-task task submit-approval --project-id 1 --task-id task_123

# Query task reports through the Hermes inline task-data capabilities
ae-cli engage-task effect query --project-id 1 --task-id task_123 --start-time 2026-04-01 --end-time 2026-04-07 --metric-id-list '["metric_1"]'
ae-cli engage-task data-detail query --project-id 1 --task-id task_123 --detail-type time --start-time 2026-04-01 --end-time 2026-04-07
ae-cli engage-task indicator-user sql --project-id 1 --task-id task_123 --indicator main --start-time 2026-04-01 --end-time 2026-04-07
ae-cli engage-task indicator-user run --project-id 1 --task-id task_123 --indicator secondary --secondary-index 1 --start-time 2026-04-01 --end-time 2026-04-07 --limit 100
ae-cli engage-task indicator-user export --project-id 1 --task-id task_123 --indicator metric --metric-id metric_1 --source metric --start-time 2026-04-01 --end-time 2026-04-07 --artifact-format csv

```

For L3 task reports, read `references/task-data-overview.md`, `references/task-data-detail.md`,
`references/task-metric-detail.md`, or `references/task-experiment-report.md` before invocation.
Before using `engage-task indicator-user`, read `references/task-indicator-user.md`; its grouping,
indicator, summary/detail, metric, experiment, and timezone flags have conditional compatibility rules.

### 3. config

```bash
# Query the config item list
ae-cli engage-scene config-item list --project-id 1

# Query the strategy list
ae-cli engage-scene strategy list --project-id 1 --config-id cfg_123
```

For L3 config reports, read `references/config-item-trigger-report.md`,
`references/config-item-analysis-report.md`, or `references/config-item-strategy-comparison.md` before invocation.

### 4. flow

```bash
# Query the flow list
ae-cli engage-flow flow list --project-id 1

# Query flow details
ae-cli engage-flow flow get --project-id 1 --flow-uuid flow_uuid_123

# Query flow operation records and application logs
ae-cli engage-flow operation-log query --project-id 1 --flow-id flow_id_123

# Query flow versions and task push records
ae-cli engage-flow version list --project-id 1 --flow-id flow_id_123
ae-cli engage-flow flow update-remark --project-id 1 --flow-uuid flow_uuid_123 --flow-version-desc "Second version"
ae-cli engage-task operation-log query --project-id 1 --task-id task_id_123
ae-cli engage-task push-record query --project-id 1 --task-id task_id_123 --page-num 1 --page-size 20
ae-cli engage-task user-detail export --project-id 1 --task-id task_id_123 --task-instance-id instance_123 --user-status fail --artifact-format csv
ae-cli engage-task segment-list query --project-id 1 --task-id task_id_123
ae-cli engage-task group list --project-id 1
ae-cli engage-task metric list --project-id 1 --task-id task_id_123
ae-cli engage-task channel-ref stats --project-id 1 --channel-id channel_123
ae-cli engage-task task delete --project-id 1 --task-id task_id_123 --yes
ae-cli engage-task task submit-approval --project-id 1 --task-id task_id_123

# Query the node schema
ae-cli engage-flow node-config schema --project-id 1 --node-type message_push
ae-cli engage-flow metric update --project-id 1 --flow-id flow_id_123 --metric-map '<metric_map_json>'

# Query or export newly exposed flow report surfaces
ae-cli engage-flow report metric-detail run --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --start-time 2026-04-01 --end-time 2026-04-07 --limit 100 --timeout-seconds 120
ae-cli engage-flow report metric-detail export --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --start-time 2026-04-01 --end-time 2026-04-07 --artifact-format csv --timeout-seconds 21600
ae-cli engage-flow metric-user run --project-id 1 --flow-id flow_id_123 --indicator-name entry --start-time 2026-04-01 --end-time 2026-04-07 --limit 100 --timeout-seconds 120
ae-cli engage-flow metric-user export --project-id 1 --flow-id flow_id_123 --indicator-name entry --start-time 2026-04-01 --end-time 2026-04-07 --artifact-format csv --timeout-seconds 21600
ae-cli engage-flow node-user run --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --indicator-name entry --start-time 2026-04-01 --end-time 2026-04-07 --limit 100 --timeout-seconds 120
ae-cli engage-flow node-user export --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --indicator-name entry --start-time 2026-04-01 --end-time 2026-04-07 --artifact-format csv --timeout-seconds 21600
ae-cli engage-flow node-metric-user run --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --indicator-name metric_setting_id_123 --start-time 2026-04-01 --end-time 2026-04-07 --limit 100 --timeout-seconds 120
ae-cli engage-flow node-metric-user export --project-id 1 --flow-id flow_id_123 --node-uuid node_uuid_123 --indicator-name metric_setting_id_123 --start-time 2026-04-01 --end-time 2026-04-07 --artifact-format csv --timeout-seconds 21600
```

User-detail `run` commands are for bounded inline rows and accept `--request-id`, `--limit`, and `--timeout-seconds`; metric-detail `run` returns the report object. Export commands accept `--request-id`, `--artifact-format csv|jsonl` (default `jsonl`), and `--timeout-seconds`, then return `run_id` and `artifact_id`; poll with `ae-cli engage-query run inspect --run-id RUN_ID`, then download with `ae-cli engage-query artifact download --run-id RUN_ID --artifact-id ARTIFACT_ID --output ./artifact.jsonl.gz`. Cancel running async work with `ae-cli engage-query query cancel --run-id RUN_ID`.

For flow report/user-detail commands, read the matching reference before composing non-trivial input:

- Flow canvas custom metric configuration: `references/flow-metric-update.md`
- Metric-detail report object or flattened report export: `references/flow-metric-detail-report.md`
- Users behind a process-level metric segment: `references/flow-metric-user.md`
- Users behind a node-level data segment: `references/flow-node-user.md`
- Users behind a node-level metric segment: `references/flow-node-metric-user.md`

### 5. scene (scene management / config center)

New capability-gateway command group `engage-scene` covers the config center: config items, params, groups, preset/related metrics, config channels, strategies, and templates. Complex DTOs are passed with `--payload` (native camelCase JSON).

```bash
# Config item list / get / create / update / delete
ae-cli engage-scene config-item list --project-id <project_id>
ae-cli engage-scene config-item get --project-id <project_id> --config-id <config_id>
ae-cli engage-scene config-item create --project-id <project_id> --config-id <config_id> --config-name <name> --business-type params
ae-cli engage-scene config-item update --project-id <project_id> --config-id <config_id> --config-name <name>
ae-cli engage-scene config-item delete --project-id <project_id> --config-id <config_id> --open-id <open_id> --yes

# Config param list / batch-add / update / batch-delete
ae-cli engage-scene config-param list --project-id <project_id> --config-id <config_id>
ae-cli engage-scene config-param batch-add --project-id <project_id> --config-id <config_id> --params '[{"param_name":"a","param_type":"string"}]'
ae-cli engage-scene config-param update --project-id <project_id> --config-id <config_id> --param-id <param_id> --param-name a
ae-cli engage-scene config-param batch-delete --project-id <project_id> --param-ids '[1,2]' --yes

# Config group list / batch-add / update / batch-delete
ae-cli engage-scene config-group list --project-id <project_id>
ae-cli engage-scene config-group batch-add --project-id <project_id> --group-names '["g1"]'
ae-cli engage-scene config-group update --project-id <project_id> --group-id <group_id> --group-name g2
ae-cli engage-scene config-group batch-delete --project-id <project_id> --group-ids '[1,2]' --yes

# Preset metric get / set
ae-cli engage-scene preset-metric get --project-id <project_id> --config-id <config_id>
ae-cli engage-scene preset-metric set --project-id <project_id> --config-id <config_id> --impression-event-definition '<semantic_event_json>'

# Config metric list / get / batch-add / update-rule / batch-delete
ae-cli engage-scene config-metric list --project-id <project_id> --config-id <config_id>
ae-cli engage-scene config-metric get --project-id <project_id> --metric-id <metric_id>
ae-cli engage-scene config-metric batch-add --project-id <project_id> --config-id <config_id> --ta-metric-ids '[1,2]'
ae-cli engage-scene config-metric update-rule --project-id <project_id> --metric-id <metric_id> --event-list '[{"event_name":"e1","filter":"true"}]'
ae-cli engage-scene config-metric batch-delete --project-id <project_id> --config-id <config_id> --metric-ids '[1,2]' --yes

# Config channel list / get / create / update / update-status / delete / query-log
# User params: verify each customsParamList columnName via ae-analysis property list/get first; then use user:<prop_name>
# Strategy custom audience: scene-strategy-audience.md — semantic definitionRequest; strategy predict for 预估人数
# Workflows: references/channel-mgmt.md · schema: references/scene-config-channel.md
ae-cli engage-scene config-channel list --project-id <project_id> [--channel-type 0|1]
ae-cli engage-scene config-channel get --project-id <project_id> --channel-id <channel_id>
ae-cli engage-scene config-channel create --project-id <project_id> --channel-name <name> --channel-type 0 --config '<json>'
ae-cli engage-scene config-channel update --project-id <project_id> --channel-id <channel_id> --channel-name <name> [--config '<json>']
ae-cli engage-scene config-channel update-status --project-id <project_id> --channel-id <channel_id> --channel-status 1|2
ae-cli engage-scene config-channel delete --project-id <project_id> --channel-id <channel_id> --yes
ae-cli engage-scene config-channel query-log --project-id <project_id> --channel-id <channel_id>

# Strategy create / update / log / batch-copy
ae-cli engage-scene strategy create --project-id <project_id> --payload '{"configId":"cfg-1","templateId":"tpl-1","strategyName":"s1"}'
ae-cli engage-scene strategy update --project-id <project_id> --payload '{"strategyUuid":"uuid-1"}'
ae-cli engage-scene strategy log --project-id <project_id> --strategy-uuid <uuid>
ae-cli engage-scene strategy predict --project-id <project_id> --definition-request '{"type":"condition","conditions":{...}}' --zone-offset 8 [--strategy-uuid <uuid>]
ae-cli engage-scene strategy batch-copy --project-id <project_id> --config-id <config_id> --strategy-ids '["s1"]'

# Template list / get / create / update / update-status / delete
ae-cli engage-scene template list --project-id <project_id> --config-id <config_id>
ae-cli engage-scene template get --project-id <project_id> --config-id <config_id> --template-id <template_id>
ae-cli engage-scene template create --project-id <project_id> --payload '{"configId":"cfg-1","templateId":"tpl-1","templateName":"t1"}'
ae-cli engage-scene template update --project-id <project_id> --payload '{"configId":"cfg-1","templateId":"tpl-1","config":[]}'
ae-cli engage-scene template update-status --project-id <project_id> --config-id <config_id> --template-id <template_id> --status 1
ae-cli engage-scene template delete --project-id <project_id> --config-id <config_id> --template-id <template_id> --yes
```

### 6. activity (campaign activities)

New capability-gateway command group `engage-activity` covers campaign activities: activities, approval workflow, topics, activity types, and standalone tasks. Complex DTOs are passed with `--payload` (native camelCase JSON).

### Activity payload guardrails

Before generating any activity topic or standalone-task payload, enforce the same subset exposed by the Hermes activity UI:

- `triggerType` must be `0` (schedule single) or `1` (schedule repeat). Activity tasks do not support manual (`2`) or triggered (`3`-`6`) task types.
- Do not configure A/B or horse-race experiments. Omit `expConfig` or use only `{"enableExp":false}`, and provide exactly one non-experiment `groupContentList` group.
- Standalone activity tasks must use `triggerTimeStrategy: "fixed_time_zone"` and the parent activity `tzOffset`. Schedule times must remain inside the activity period.
- A topic root supports audience types `1` (custom) and `2` (existing cluster), not `3` (all users). A standalone activity task may use `1`, `2`, or `3`.
- Topic tasks inherit schedule, timezone, channel, frequency limits, channel touch limits, whitelist, and experiment settings from the topic. They may only add an inclusion-only custom `definitionRequest`; never generate task-level `clusterKey`, trigger rules, or shared-setting overrides. `topic get` may return the canonical task marker `targetClusterType=1`; preserve it for update if present, but never use another task-level value.
- Resolve the parent activity first and confirm it is editable (`mappingStatus` `0`, `2`, or `5`). Limits for topics, tasks, and languages are project configuration values; do not hardcode defaults.
- `approval submit` and `approval approve` validate every persisted activity task. Approval does not normalize unsupported task data. On `ACTIVITY_TASK_COMPATIBILITY_VIOLATION`, cancel/withdraw approval as needed, correct or recreate each reported task, and submit again.

```bash
# Activity create / update / delete / list / get / pause / end / stats / info-list
ae-cli engage-activity activity create --project-id <project_id> --payload '{"activityName":"a1","activityType":"other_type","tzOffset":8,"periodType":0}'
ae-cli engage-activity activity update --project-id <project_id> --payload '{"activityId":"act-1","activityName":"a1","activityType":"other_type","tzOffset":8,"periodType":0}'
ae-cli engage-activity activity delete --project-id <project_id> --activity-id <activity_id> --yes
ae-cli engage-activity activity list --project-id <project_id> --page 1 --page-size 20
ae-cli engage-activity activity get --project-id <project_id> --activity-id <activity_id>
ae-cli engage-activity activity pause --project-id <project_id> --activity-id <activity_id>
ae-cli engage-activity activity end --project-id <project_id> --activity-id <activity_id>
ae-cli engage-activity activity stats --project-id <project_id>
ae-cli engage-activity activity info-list --project-id <project_id> --activity-id <activity_id>

# Approval submit / approve / reject / cancel
ae-cli engage-activity approval submit --project-id <project_id> --activity-id <activity_id> [--reason <reason>]
ae-cli engage-activity approval approve --project-id <project_id> --activity-id <activity_id>
ae-cli engage-activity approval reject --project-id <project_id> --activity-id <activity_id> --reason <reason>
ae-cli engage-activity approval cancel --project-id <project_id> --activity-id <activity_id>

# Topic create / update / remove-task / delete / get / copy
# See references/activity-topic.md for topicClusterKey vs task clusterKey and triggerType notes.
ae-cli engage-activity topic create --project-id <project_id> --payload '{"activityId":"act-1","topicName":"t1","targetClusterType":2,"topicClusterKey":"<cluster>","channelType":1,"channelId":"c1","triggerType":0,"triggerTime":"2026-12-31 12:00","enableChannelTouchLimits":false,"frequencyLimits":"{}","tasks":[...]}'
ae-cli engage-activity topic update --project-id <project_id> --payload '{"topicId":"topic-1", ...}'
ae-cli engage-activity topic remove-task --project-id <project_id> --task-id <task_id> --yes
ae-cli engage-activity topic delete --project-id <project_id> --topic-id <topic_id> --yes
ae-cli engage-activity topic get --project-id <project_id> --topic-id <topic_id>
ae-cli engage-activity topic copy --project-id <project_id> --topic-id <topic_id> [--new-name <name>]

# Activity type list / batch-add / update / batch-delete
ae-cli engage-activity activity-type list --project-id <project_id>
ae-cli engage-activity activity-type batch-add --project-id <project_id> --type-names '["t1","t2"]'
ae-cli engage-activity activity-type update --project-id <project_id> --id <type_id> --type-name t3
ae-cli engage-activity activity-type batch-delete --project-id <project_id> --ids '["id1","id2"]' --yes

# Standalone task get / create / update / copy
ae-cli engage-activity task get --project-id <project_id> --task-id <task_id>
ae-cli engage-activity task create --project-id <project_id> --payload '{"taskName":"t1","activityId":"act-1", ...}'
ae-cli engage-activity task update --project-id <project_id> --payload '{"taskId":"task-1", ...}'
ae-cli engage-activity task copy --project-id <project_id> --task-id <task_id> [--new-name <name>]
```

### 7. workbench

New capability-gateway command group `engage-workbench` covers workbench metric slots: each user configures up to 4 metric cards per project. Slots are per-user; `update`/`delete` only affect the caller's own slots. The first `list` auto-initialises 4 default slots.

```bash
# Workbench slot list / add / update / delete
ae-cli engage-workbench workbench list --project-id <project_id>
ae-cli engage-workbench workbench add --project-id <project_id> --metric-type <metric_type> --date-type <date_type> --order-id 1
ae-cli engage-workbench workbench update --project-id <project_id> --slot-id <slot_id> --metric-type <metric_type> --date-type <date_type> --order-id 1
ae-cli engage-workbench workbench delete --project-id <project_id> --slot-id <slot_id> --yes
```

## `engage-flow flow save` Critical Constraints

When the user wants to "create a flow / generate a flow canvas / save a flow", do not treat `engage-flow flow save` as a normal single command. You must follow the workflow below.

### Required Workflow

1. First confirm that the user intent is specific enough. At minimum you need:
   - The business scenario
   - The target users
   - The touchpoint or delivery method
   - Whether branching is needed, and the branching conditions
2. Do not jump directly from natural language to `--req`. You must first organize a stable intermediate intent structure, then map it to the final `req`.
3. Build condition-related nodes with semantic `targetDefinitionRequest` and
   `triggerDefinition` objects. Resolve real event and property names through Analysis metadata;
   do not create an intermediate cluster merely to obtain persisted QP.

4. Before building touchpoint nodes such as `message_push`, `wechat_push`, or `webhook_push`, you must call:

```bash
ae-cli engage-setting channel list --project-id <projectId>
```

5. `engage-flow flow save` is **operation-based** (protocol v2). The `--req` object must carry an `operation` of `build`, `preview`, or `commit`. Do **not** use the old `nodeList` / `edgeList` field names — use `nodes` / `edges` with `operation=build`. A legacy `nodeList`/`edgeList` payload (or a missing `operation`) is rejected with `Unsupported save_flow operation: null`.
6. Run the lifecycle: `build` (returns `data.result.status = ready_to_preview` or `need_input`) → resolve any `data.result.next_slot` → `preview` (re-issues response fields `data.result.draft_version` + `data.result.confirm_token`) → `commit` (maps those values to request fields `draftVersion` + `confirmToken`) → reads the final ID from `data.result.result.flow_uuid`.
7. `nodes[].config` / `edges[].config` may be a JSON object or a JSON string. Custom audience nodes and branches use semantic `targetDefinitionRequest`; Hermes compiles it to the node's stored execution format.
   Never send `targetClusterQp`. Each audience `event` and `behavior_sequence` must include
   its own `time_range`; Flow entry dates do not replace that range. Use only properties that
   resolve through the Flow editor's current project, timezone, and user-entity metadata scope.
8. You must self-check before previewing/committing:
   - There is exactly one entry node
   - There is at least one `exit_flow`
   - `edge.source` and `edge.target` both reference valid nodes
   - Any branch node `sourceBranchId` has already been declared in the upstream node `config`
   - The whole graph is a DAG and contains no cycles

### Explicitly Forbidden

- Do not invent a `channelId`
- Do not fill in branching logic when the user has not provided enough information
- Do not submit business-semantic nodes directly as final `nodes`
- Do not use the legacy `nodeList` / `edgeList`, and do not omit `operation`

### Recommended Order

```text
User request
-> Organize intent
-> analysis user-cluster create/get
-> engage-setting channel list --project-id <projectId>
-> Build nodes / edges
-> Self-check
-> engage-flow flow save operation=build -> (need_input?) -> preview -> commit
-> engage-flow flow get (verify)
```

For more detailed generation rules, consult these references first:

- `references/save-flow.md`
- `references/flow-node-config-schema.md`
- `references/validate-flow-node-config.md`

## Dry-Run Debugging

```bash
ae-cli --dry-run engage-setting channel list --project-id 1
ae-cli --dry-run engage-task task list --project-id 1 --req '{"pageNum":1,"pageSize":20}'
ae-cli --dry-run engage-task task build-save-guide --project-id 1 --req '{}'
ae-cli --dry-run engage-task task save --project-id 1 --req '{"baseInfo":{"taskName":"Demo Task"},"channelConfig":{"channelType":1,"channelId":"channel_123","groupContentList":[{"contentList":[{"pushLanguageCode":"default","content":"[]"}]}]},"targetConfig":{"targetClusterType":3},"triggerConfig":{"triggerType":2},"controlConfig":{"completionIndicatorDef":{"completionIndicators":[]}}}'
ae-cli --dry-run engage-flow flow list --project-id 1
```

## References

More detailed single-command guidance is available in the business-oriented `references/` directory:

- `references/channel-list.md` (`engage-setting.channel.list`)
- `references/channel-detail.md` (`engage-setting.channel.get`)
- `references/add-channel.md` (`engage-setting.channel.create`)
- `references/update-channel-status.md` (`engage-setting.channel.update-status`)
- `references/delete-channel.md` (`engage-setting.channel.delete`)
- `references/channel_touch_limits_list.md` (`engage-setting.channel-touch-limits.list`)
- `references/channel-touch-limits-batch-update.md` (`engage-setting.channel-touch-limits.batch-update`)
- `references/channel-touch-limits-toggle.md` (`engage-setting.channel-touch-limits.toggle`)
- `references/channel-touch-limits-save.md` (`engage-setting.channel-touch-limits.save`)
- `references/channel-update-config.md` (`engage-setting.channel.update-config`)
- `references/channel-test-send.md` (`engage-setting.channel.test-send`)
- `references/approval-approver-delete.md` (`engage-setting.approval-approver.delete`)
- `references/add-approver.md` / `references/approver-list.md` (`engage-setting.approval-approver.{add,list}`)
- `references/whitelist-list.md` / `references/whitelist.md` (`engage-setting.whitelist.{list,add,update,delete,verify}`)
- `references/cancel-query-by-request-id.md` (`engage-setting.query.cancel`, L3)
- `references/cancel-query-run.md` (`engage-query.query.cancel`)
- `references/push-language.md` (`engage-setting.push-language.{get,set}`)
- `references/client-param.md` (`engage-setting.client-param.{create,update,delete,list}`)
- `references/config-table.md` (`engage-setting.config-table.{upload,save,list,query-data,update-data,delete}`)
- `references/preset-event.md` (`engage-setting.preset-event.{list,update}`)
- `references/common-metric.md` (`engage-setting.common-metric.{list,get,create,update,delete}`)
- `references/scene-config-item.md` (`engage-scene.config-item.{list,get,create,update,delete}`)
- `references/scene-config-param.md` (`engage-scene.config-param.{list,batch-add,update,batch-delete}`)
- `references/scene-config-group.md` (`engage-scene.config-group.{list,batch-add,update,batch-delete}`)
- `references/scene-preset-metric.md` (`engage-scene.preset-metric.{get,set}`)
- `references/scene-config-metric.md` (`engage-scene.config-metric.{list,get,batch-add,update-rule,batch-delete}`)
- `references/scene-config-channel.md` (`engage-scene.config-channel.{list,get,create,update,update-status,delete,query-log}`)
- `references/channel-mgmt.md` (config channel management workflows)
- `references/scene-strategy.md` (`engage-scene.strategy.{list,get,create,update,log,predict,batch-copy,manage}`)
- `references/scene-strategy-audience.md` (custom audience semantic `definitionRequest`, preflight, predict)
- `references/scene-template.md` (`engage-scene.template.{list,get,copy,create,update,update-status,delete}`)
- `references/config-item-trigger-report.md` (`engage-scene.report.config-item-trigger`, L3)
- `references/config-item-analysis-report.md` (`engage-scene.report.config-item-analysis`, L3)
- `references/config-item-strategy-comparison.md` (`engage-scene.report.strategy-comparison`, L3)
- `references/activity-activity.md` (`engage-activity.activity.{create,update,delete,list,get,pause,end,stats,info-list}`)
- `references/activity-data-detail.md` (`engage-activity.activity-data.detail`, L3)
- `references/activity-approval.md` (`engage-activity.approval.{submit,approve,reject,cancel}`)
- `references/activity-topic.md` (`engage-activity.topic.{create,update,remove-task,delete,get,copy}`)
- `references/activity-activity-type.md` (`engage-activity.activity-type.{list,batch-add,update,batch-delete}`)
- `references/activity-task.md` (`engage-activity.task.{get,create,update,copy}`)
- `references/workbench-workbench.md` (`engage-workbench.workbench.{list,add,update,delete}`)
- `references/build-task-save-guide.md`
- `references/save-task.md`
- `references/task-list.md`
- `references/flow-list.md`
- `references/operation-log-query.md` (`engage-flow.operation-log.query`)
- `references/task-operation-log-query.md` (`engage-task.operation-log.query`)
- `references/version-list.md` (`engage-flow.version.list`)
- `references/flow-update-remark.md` (`ae-cli engage-flow flow update-remark`; capability `engage-flow.version.update-remark`)
- `references/push-record-query.md` (`engage-task.push-record.query`)
- `references/task-user-detail-export.md` (`engage-task user-detail export`; capability `engage-task.user-detail.export`)
- `references/task-indicator-user.md` (`engage-task indicator-user {sql,run,export}`; capabilities `engage-task.indicator-user.{sql,run,export}`)
- `references/segment-list-query.md` (`engage-task.segment-list.query`)
- `references/group-list.md` (`engage-task.group.list`)
- `references/task-delete.md` (`engage-task.task.delete`)
- `references/task-submit-approval.md` (`engage-task.task.submit-approval`)
- `references/task-data-detail.md` (`engage-task data-detail query`; capability `engage-task.task-data.detail`)
- `references/task-metric-detail.md` (`engage-task effect query`; capability `engage-task.task-data.metric-detail`)
- `references/flow-metric-update.md` (`engage-flow metric update`; capability `engage-flow.metric.update`)

This split documentation structure is easier to extend later, because commands with more complex object inputs can stay centralized in the `references/` root directory.

## Command Groups

### setting

`channel-touch-limits list` / `channel-touch-limits batch-update` / `channel-touch-limits toggle` / `channel-touch-limits save` / `channel update-config` / `channel test-send` / `channel list` / `channel get` / `channel create` / `channel update-status` / `channel delete` / `approval-approver add` / `approval-approver list` / `approval-approver delete` / `whitelist list` / `whitelist add` / `whitelist update` / `whitelist delete` / `whitelist verify` / `push-language get` / `push-language set` / `client-param create` / `client-param update` / `client-param delete` / `client-param list` / `config-table upload` / `config-table save` / `config-table list` / `config-table query-data` / `config-table update-data` / `config-table delete` / `preset-event list` / `preset-event update` / `common-metric list` / `common-metric get` / `common-metric create` / `common-metric update` / `common-metric delete` (via `engage-setting`), plus L3 capability `engage-setting.query.cancel`

### task

`operation-log query` / `push-record query` / `user-detail export` / `indicator-user sql` / `indicator-user run` / `indicator-user export` / `segment-list *` / `ops *` / `metric *` / `race release` / `channel-ref stats` / `group *` / `task delete` / `task modify-group` / `task submit-approval` / `task get` / `task list` / `task stats` / `task build-save-guide` / `task save` / `task manage` / `effect query` / `data-detail query` (via `engage-task`), plus L3 capabilities `engage-task.task-data.{overview,detail,metric-detail,experiment-report}`

### query

`run inspect` / `artifact download` / `query cancel` (via `engage-query`), capability ID `engage-query.query.cancel`

### config

Legacy config MCP commands are migrated into the `scene` L2 group and the three L3 report capabilities below.

### scene

`config-item list` / `config-item get` / `config-item create` / `config-item update` / `config-item delete` / `config-param list` / `config-param batch-add` / `config-param update` / `config-param batch-delete` / `config-group list` / `config-group batch-add` / `config-group update` / `config-group batch-delete` / `preset-metric get` / `preset-metric set` / `config-metric list` / `config-metric get` / `config-metric batch-add` / `config-metric update-rule` / `config-metric batch-delete` / `config-channel list` / `config-channel get` / `config-channel create` / `config-channel update` / `config-channel update-status` / `config-channel delete` / `config-channel query-log` / `strategy list` / `strategy get` / `strategy create` / `strategy update` / `strategy log` / `strategy batch-copy` / `strategy manage` / `template list` / `template get` / `template copy` / `template create` / `template update` / `template update-status` / `template delete` (via `engage-scene`), capability ids `engage-scene.config-item.{list,get,create,update,delete}`, `engage-scene.config-param.{list,batch-add,update,batch-delete}`, `engage-scene.config-group.{list,batch-add,update,batch-delete}`, `engage-scene.preset-metric.{get,set}`, `engage-scene.config-metric.{list,get,batch-add,update-rule,batch-delete}`, `engage-scene.config-channel.{list,get,create,update,update-status,delete,query-log}`, `engage-scene.strategy.{list,get,create,update,log,batch-copy,manage}`, `engage-scene.template.{list,get,copy,create,update,update-status,delete}`, plus L3 capabilities `engage-scene.report.{config-item-trigger,config-item-analysis,strategy-comparison}`

### activity

`activity create` / `activity update` / `activity delete` / `activity list` / `activity get` / `activity pause` / `activity end` / `activity stats` / `activity info-list` / `approval submit` / `approval approve` / `approval reject` / `approval cancel` / `topic create` / `topic update` / `topic remove-task` / `topic delete` / `topic get` / `topic copy` / `activity-type list` / `activity-type batch-add` / `activity-type update` / `activity-type batch-delete` / `task get` / `task create` / `task update` / `task copy` (via `engage-activity`), capability ids `engage-activity.activity.{create,update,delete,list,get,pause,end,stats,info-list}`, `engage-activity.approval.{submit,approve,reject,cancel}`, `engage-activity.topic.{create,update,remove-task,delete,get,copy}`, `engage-activity.activity-type.{list,batch-add,update,batch-delete}`, `engage-activity.task.{get,create,update,copy}`

### workbench

`workbench list` / `workbench add` / `workbench update` / `workbench delete` (via `engage-workbench`), capability ids `engage-workbench.workbench.{list,add,update,delete}`

### flow

`operation-log query` / `version list` / `flow update-remark` / `flow save` / `node-config schema` / `flow get` / `flow list` / `flow manage` / `node-config validate` / `flow delete` / `flow modify-base-info` / `metric update` / `report metric-detail run` / `report metric-detail export` / `metric-user run` / `metric-user export` / `node-user run` / `node-user export` / `node-metric-user run` / `node-metric-user export` (via `engage-flow`), plus L3 capabilities `engage-flow.report.{node-overview,process,node-detail,ab-split-node}`

## Date Format

Commands that accept date parameters usually use `yyyy-MM-dd`, for example `--start_time 2026-04-01`.

## Write Operation Reminder

High-risk delete commands (`risk: high-risk-write`) require explicit user authorization before execution. Ordinary write commands (`risk: write`) do not:

- Channels: `engage-setting channel create` (write), `engage-setting channel delete` (high-risk-write), `engage-setting channel update-status` (write)
- Config channels (config center channel management): `engage-scene config-channel create|update|update-status` (write), `engage-scene config-channel delete` (high-risk-write)
- Strategies and config items: `engage-scene config-item delete` (high-risk-write), `engage-scene template copy` and `engage-scene strategy manage` (write)
- Flows: `engage-flow flow update-remark` (write), `engage-flow flow save` (write), `engage-flow flow modify-base-info` (write), `engage-flow flow manage` (write), `engage-flow flow delete` (high-risk-write)
- Tasks: `engage-task task save` (write), `engage-task task submit-approval` (write), `engage-task task manage` (write)

For task draft creation or update, use this workflow:

1. `ae-cli engage-setting channel list --project-id <projectId>`
2. `ae-cli engage-task task build-save-guide --project-id <projectId> --req '{...}'`
3. For a custom audience, pass the Analysis semantic contract as
   `targetConfig.definitionRequest`. For an event-triggered task, use semantic
   `triggerConfig.triggerDefinition` and
   always include `periodTimeSymbol` (`TS01`, `TS02`, `TS03`, or `TS04`) on its primary A rule.
   Use semantic `completionIndicatorDef.completionIndicators[].eventDefinition`. Build shapes from
   `ae-analysis` user-cluster / audience models. For existing-cluster audiences
   (`targetClusterType=2`), use `analysis user-cluster get`. For event-triggered tasks, pass
   `channelType`, `triggerType`, and `eventTriggerType` to `build-save-guide`, then use its
   type-specific semantic event shape. Accumulated events are aggregate conditions, continuous
   events use count/eq with a value of at least 2, ordered events use sequence-step envelopes,
   and every-completion events use count/eq/1. Completion target and experiment main-goal event
   filters must not use properties whose metadata `select_type` is `datetime`. Never construct
   persisted QP fields.
   Select the audience by delivery side: server-side channels allow custom (`1`) or existing (`2`)
   and reject all users (`3`); `client_push` (`channelType=3`) allows custom (`1`) or all users (`3`)
   and rejects existing (`2`). Do not infer audience support from `triggerType` alone.
4. `ae-cli engage-task task save --project-id <projectId> --req '{...}'`
5. `ae-cli engage-task task submit-approval --project-id <projectId> --task-id <taskId>`

`engage-task task build-save-guide` is a read-only helper. It returns scenario-specific required fields, channel content schema, unsupported combinations, examples, and a handoff template for `save_task`.
When `enableExp=true`, capability `engage-task.task.build-save-guide` enriches the handoff so
`groupContentList` association fields
(`expGroupName`/`expGroupType`/`percentageInExperiment`/`order`) stay aligned with
`expConfig.expGroupList`; only replace `contentList[].content`. Capability `engage-task.task.save`
rejects misaligned experiment content with `TASK_EXPERIMENT_GROUP_CONTENT_INVALID`.

`engage-task task save` creates or updates a task configuration. It does not submit approval, does not start sending, and does not trigger task execution. If `req.taskId` is omitted it creates a new draft; if `req.taskId` is present it updates an existing **draft or paused** task. Update mode rejects running/ended tasks with `invalid_status`. Omitted fields inherit from the existing task before validation (partial rename/update is supported).

`engage-task task submit-approval --task-id` is the recommended approval path after `task save`.
It submits the persisted draft without requiring the Agent to reconstruct internal `trigger_rule`.
The legacy `--request` mode remains available for compatibility; provide exactly one of
`--task-id` or `--request`.

Audience creation is not a fixed preflight step. For custom task audiences, use semantic
`targetConfig.definitionRequest`; `task get` returns the same contract as
`definition_request`. `clientConfig.clientQp` is server-authored and must be omitted from
Capability requests; partial updates preserve existing server state. Do not assemble raw QP
manually.
For a `behavior_sequence`, omit second-step `relative_to_first` or set it to `false`; reserve
`true` for step 3 or later when the window is measured from step 1.
