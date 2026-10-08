# analysis capability-gateway commands

> Prerequisite: follow [`../SKILL.md`](../SKILL.md), especially `PROJECT_ID_GATE`.

These commands use the capability gateway instead of MCP tool names. The CLI command shape is:

```bash
ae-cli analysis <resource> <action> [options]
```

Flags use kebab-case. The gateway input JSON uses snake_case. Do not pass camelCase flags or payload keys unless a nested backend DTO explicitly requires them inside `--payload`.

This file is an overview only. Before running an L2 command, read the dedicated command reference named `references/<resource>_<action>.md` with hyphens converted to underscores, for example `dashboard_report_data_export.md`. L3 capabilities without a dedicated reference use dynamic discovery per [`ae-capability`](../../ae-capability/SKILL.md) and the L3 section below.

For analysis data retrieval commands, read [`analysis_data_retrieval.md`](analysis_data_retrieval.md) before choosing `run` or `export`. That routing policy applies only to analysis data retrieval and must not be generalized to other `te-cli` business modules.

## When to use

Use these commands for ad-hoc model analysis, report definition/data/management, dashboard, BI panel and panel versions, project-space, folder, favorite, public-link, dashboard-definition, dashboard-daily-report, dashboard/BI page data, metadata governance, and user cluster/tag/history-tag workflows.

When the routing policy chooses async artifact retrieval, use export commands:

```bash
ae-cli analysis dashboard-report-data export --project-id 1 --dashboard-id 1001
ae-cli analysis report-data export --project-id 1 --report-ids '[1001]'
ae-cli analysis run inspect --run-id run_0123456789abcdef0123456789abcdef
ae-cli analysis artifact download --run-id run_0123456789abcdef0123456789abcdef --artifact-id artifact_0123456789abcdef0123456789abcdef --output /tmp/dashboard.jsonl.gz
ae-cli analysis bi-panel-page-data export --project-id 1 --panel-id 2001 --page-key main --result-type charts
ae-cli analysis query cancel --run-id run_0123456789abcdef0123456789abcdef
```

## When not to use

Do not use these commands for schema helpers, alerts, project lookup, dashboard locks, BI panel locks, dashboard filters, UI reorder/tree/move operations, daily report retry/download/get-config, or public-link logs/source-list/get. Use the existing `+<tool_name>` references for those.

## Output

All commands return the gateway envelope:

```json
{
  "ok": true,
  "data": {},
  "meta": {}
}
```

Failures return:

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_QUERY_REQUEST",
    "message": "..."
  }
}
```

Export commands return `run_id`, `artifact_id`, `status`, `artifact_status`, `expires_at`, and `expires_at_iso`. They do not expose raw inspect/download API paths.

Artifact workflow:

1. Submit an export command and keep `data.run_id` and `data.artifact_id`.
2. Poll `ae-cli analysis run inspect --run-id <run_id>` every few seconds until `data.status` is terminal and `data.artifact_status` is complete.
3. Terminal success is `COMPLETED` or `SUCCEEDED`; terminal failure is `FAILED`, `CANCELED`, or `CANCELLED`. On failure, report the returned error fields instead of downloading.
4. Download with `ae-cli analysis artifact download --run-id <run_id> --artifact-id <artifact_id> --output <file>`.
5. Cancel long or abandoned exports with `ae-cli analysis query cancel --run-id <run_id>`.

Prefer the run/artifact commands over hand-written HTTP, Python, or curl. Analysis exports never create interactive `query_context_id`; drilldown coordinates exist only in bounded synchronous previews.

## Command matrix

| Command | Capability ID | Use for | Key input | Output |
| --- | --- | --- | --- | --- |
| `filter-value list` | `analysis.filter_value.list` | Resolve exact stored values for one known event/user property before building a filter; not property discovery or aggregation | `--property-name`, `--table-type`, optional event/prefix/snapshot inputs | Candidate values in `items` |
| `query-cluster list` | `analysis.query_cluster.list` | List physical 查询集群/data-routing options; not 用户分群/audience assets | `--project-id` | Current/accessible slave clusters and allowed routing parameters |
| `adhoc run` | `analysis.adhoc.run` | Unified ad-hoc inline query for 12 AI models: 9 common + 3 scenario models | `--project-id`, `--model-type`, AI-facing `--definition`, optional physical cluster route | Inline data plus actual route and optional `query_context_id` |
| `adhoc export` | `analysis.adhoc.export` | Unified ad-hoc async export for 12 AI models: 9 common + 3 scenario models | same as run, plus optional `--artifact-format`; no inline `--limit` | Async artifact descriptor; no drilldown context |
| `drilldown-events run/export` | `analysis.query.drilldown_events` / `analysis.query.drilldown_events_export` | Preview or full-stream events for an advertised `EVENT_LIST` cell | `--project-id`, `--query-context-id`, optional `--source`, `--coordinate` | Bounded event rows or `csv.gz` artifact |
| `drilldown-entities run/export` | `analysis.query.drilldown_entities` / `analysis.query.drilldown_entities_export` | Preview/export users or custom entities for an advertised entity cell | `--project-id`, `--query-context-id`, optional `--source`, `--coordinate` | Subject plus entity rows/artifact |
| `query drilldown-user-events` | `analysis.query.drilldown_user_events` | Query one drilldown user's event sequence | `--project-id`, `--drilldown-context-id`, `--user-id` | Event sequence rows |
| `query create-result-cluster` | `analysis.query.create_result_cluster` | Save the advertised user/custom-entity cell population as its result cluster | `--project-id`, `--query-context-id`, optional `--source`, `--coordinate`, `--cluster-name` | Result cluster creation result |
| `report list` | `analysis.report.list` | Find accessible reports | `--project-id`, optional `--queries`, `--fields`, `--limit`, `--offset` | Paginated report summaries |
| `report list-export` | `analysis.report.list_export` | Export report catalog | same as list, plus optional `--artifact-format`, `--request-id` | Async artifact descriptor |
| `report get` | `analysis.report.get` | Inspect current report definition as AI QP | `--project-id`, `--report-id` | Report metadata plus `model_type` and `definition` |
| `report create` | `analysis.report.create` | Create a report from AI QP definition | `--report-name`, `--model-type`, `--definition` | Created report ID and normalized definition |
| `report update` | `analysis.report.update` | Update metadata or AI QP definition | `--report-id`, `--report-version`, update fields | Update result |
| `report delete` | `analysis.report.delete` | Delete reports | `--report-ids '[...]'` | Delete result |
| `report-data run` | `analysis.report_data.run` | Bounded inline report data | `--report-ids`, optional overrides, `--cluster-query-scope`, conditional `--slave-cluster-id`, time/limit | Inline data plus actual route and optional `query_context_id` |
| `report-data export` | `analysis.report_data.export` | Large/long report data | same as run, plus optional `--artifact-format` | Async artifact descriptor; no drilldown context |
| `query cancel` | `analysis.query.cancel` | Cancel any async analysis export | `--run-id`, optional `--reason` | Cancellation result |
| `report-change-log list` | `analysis.report_change_log.list` | List one report's change logs | `--report-id` | Change log summaries |
| `report-change-log get` | `analysis.report_change_log.get` | Inspect one change log detail | `--report-id`, optional `--history-version` | Change log detail with AI QP definition when available |
| `report-version rollback` | `analysis.report_version.rollback` | Rollback a report version | `--report-id`, `--target-version` | Rollback result |
| `report-abnormal get` | `analysis.report_abnormal.get` | Inspect report abnormal dependencies | `--report-id` | Abnormal info |
| `dashboard-report add` | `analysis.dashboard_report.add` | Add reports to a dashboard | `--dashboard-id`, `--report-ids` | Add result |
| `dashboard list` | `analysis.dashboard.list` | Find accessible dashboards | `--project-id`, optional `--queries`, `--fields`, `--limit`, `--offset` | Paginated dashboard summaries |
| `dashboard create` | `analysis.dashboard.create` | Create a dashboard | `--project-id`, `--dashboard-name`, optional `--space-id`, `--folder-id` | Created dashboard |
| `dashboard get` | `analysis.dashboard.get` | Inspect one dashboard location/definition/share/report structure, including notes, creator, and creation/update time | `--project-id`, `--dashboard-id` | Dashboard detail with location and normalized notes |
| `dashboard update` | `analysis.dashboard.update` | Update settings, create or patch a note, or replace the dashboard-level business filter | `--operation settings|note-upsert|business-filter`; `--dashboard-id` is required for notes; omit `--note-id` to create | Update result |
| `dashboard share-info` | `analysis.dashboard.share_info` | Read dashboard sharing info | `--project-id`, `--dashboard-id` | Share info |
| `dashboard share` | `analysis.dashboard.share` | Modify dashboard sharing | `--project-id`, `--dashboard-id`, `--payload` or `--member-authorities` | Share update result |
| `dashboard delete` | `analysis.dashboard.delete` | Delete dashboards | `--project-id`, `--dashboard-ids '[...]'` | Delete result |
| `dashboard handover` | `analysis.dashboard.handover` | Transfer dashboards | `--dashboard-ids`, `--to-user-id` | Handover result |
| `dashboard copy` | `analysis.dashboard.copy` | Copy a dashboard; omitted target IDs copy to the source location | `--dashboard-id`, `--dashboard-name`, optional target IDs | Copied dashboard |
| `dashboard freeze` | `analysis.dashboard.freeze` | Freeze/unfreeze dashboards | `--dashboard-ids`, optional `--freeze false` | Freeze status |
| `dashboard abnormal-get` | `analysis.dashboard.abnormal_get` | Inspect abnormal dependencies | `--dashboard-id` | Abnormal info |
| `dashboard task-status` | `analysis.dashboard.task_status` | Inspect scheduled task status | `--dashboard-id` | Task status |
| `dashboard-report-data run` | `analysis.dashboard_report_data.run` | Bounded inline dashboard report data; omitted route follows saved dashboard configuration | `--dashboard-id`, optional reports/filters/time and physical cluster route | Inline data plus actual route and optional `query_context_id` |
| `dashboard-report-data export` | `analysis.dashboard_report_data.export` | Large/long dashboard report data | same as run, plus optional `--artifact-format jsonl` | Async artifact descriptor; no drilldown context |
| `run inspect` | `analysis.run.inspect` | Poll async export status | `--run-id` | Run and artifact status |
| `artifact download` | `analysis.artifact.download` | Download run-bound export artifact | `--run-id`, `--artifact-id`, `--output` | Local output file info |
| `query cancel` | `analysis.query.cancel` | Cancel gateway run/export | `--run-id`, optional `--reason` | Cancellation result |
| `dashboard-definition export` | `analysis.dashboard_definition.export` | Export dashboard definition JSON | `--dashboard-id`, `--dashboard-ids`, `--dashboard-folder-ids`, `--shared-spaces`, or `--payload` | Definition JSON |
| `dashboard-definition import` | `analysis.dashboard_definition.import` | Validate/import dashboard definition | `--definition`, optional `--validate-only true` | Validation or import result |
| `dashboard-daily-report get` | `analysis.dashboard_daily_report.get` | Get one saved daily report config with secrets and webhook URLs redacted | `--dashboard-id` | Config state |
| `dashboard-daily-report update` | `analysis.dashboard_daily_report.update` | Patch-style create or update; omitted fields remain unchanged | `--dashboard-id`, optional config flags or `--payload` | Config result |
| `dashboard-daily-report send` | `analysis.dashboard_daily_report.send` | Send immediately; destination fields infer channels, omission reuses saved destinations | `--dashboard-id`, optional destination/content flags or `--payload` | Async task ID |
| `dashboard-daily-report send-status` | `analysis.dashboard_daily_report.send_status` | Inspect one immediate-send task and per-channel outcome | `--task-id` | Send task status |
| `bi-panel list` | `analysis.bi_panel.list` | Find accessible BI panels | `--project-id`, optional list filters | Paginated BI panel summaries |
| `bi-panel get` | `analysis.bi_panel.get` | Inspect released BI panel page structure only | `--panel-id`, optional `--fields` | Panel structure |
| `bi-panel create` | `analysis.bi_panel.create` | Create an empty BI panel shell | required `--panel-name`; optional destination IDs | Created shell identifiers |
| `bi-panel update` | `analysis.bi_panel.update` | Rename a BI panel without changing content | required `--panel-uuid`, `--panel-name` | Rename result |
| `bi-panel delete` | `analysis.bi_panel.delete` | Delete BI panels | `--panel-ids '[...]'` | Delete result |
| `bi-panel share` | `analysis.bi_panel.share` | Modify BI panel sharing | `--panel-id`, `--payload` | Share update result |
| `bi-panel copy` | `analysis.bi_panel.copy` | Copy a BI panel | optional source/target flags and `--payload` | Copied panel |
| `bi-panel-version get` | `analysis.bi_panel_version.get` | Inspect BI panel released or draft version | `--panel-id` or `--panel-uuid`, optional `--version-type release|draft` | Version detail |
| `bi-panel-version publish` | `analysis.bi_panel_version.publish` | Publish current BI panel draft after source version matches | `--panel-id` or `--panel-uuid`, `--source-version` | Published version |
| `bi-panel-page-data run` | `analysis.bi_panel_page_data.run` | Bounded inline BI page data | `--panel-id`, `--page-key`, `--result-type charts|summary` | Inline page data |
| `bi-panel-page-data export` | `analysis.bi_panel_page_data.export` | Large/long BI page data | same as run, optional `--artifact-format jsonl` | Async artifact descriptor |
| `project-space list` | `analysis.project_space.list` | Find accessible project spaces | `--project-id`, optional list filters | Paginated project spaces |
| `project-space business-filter-upsert` | `analysis.project_space.business_filter_upsert` | Create or replace the space-level business filter | `--project-id`, `--space-id`, `--filter` | Saved space filter |
| `project-space get` | `analysis.project_space.get` | Inspect one project space | `--project-id`, `--space-id` | Project space detail |
| `favorite add` | `analysis.favorite.add` | Favorite dashboard/BI/folder | required `--asset-id`, `--asset-type`; optional `--space-id` | Favorite result |
| `favorite remove` | `analysis.favorite.remove` | Remove favorite | same as add | Remove result |
| `public-link create` | `analysis.public_link.create` | Generate public link | `--resource-type`, `--resource-id`, `--effective-at`, `--expires-at` | Link result |
| `public-link list` | `analysis.public_link.list` | List public links | `--project-id`, optional list filters | Paginated links |
| `public-link update` | `analysis.public_link.update` | Edit public link | `--link-id`, `--effective-at`, `--expires-at` | Update result |
| `public-link offline` | `analysis.public_link.offline` | Take links offline | `--link-id` or `--link-ids` | Offline result |
| `public-link delete` | `analysis.public_link.delete` | Delete public links | `--link-id` or `--link-ids` | Delete result |
| `user-cluster list` | `analysis.user_cluster.list` | Find accessible user clusters | `--project-id`, optional `--queries`, `--fields`, `--limit`, `--offset` | Paginated cluster summaries |
| `user-cluster export` | `analysis.user_cluster.export` | Export complete matching cluster catalog | `--project-id`, optional filters, required `--output` | Local JSONL catalog and integrity sidecar |
| `user-cluster get` | `analysis.user_cluster.get` | Inspect exact clusters | `--cluster-names '[...]'` | Cluster details |
| `user-cluster-member list` | `analysis.user_cluster_member.list` | Bounded inline cluster members | `--cluster-name`, optional properties/fields/query/limit/offset | Member rows |
| `user-cluster-member export` | `analysis.user_cluster_member.export` | Stream native full cluster members as csv.gz | `--cluster-name`, optional properties | Async artifact descriptor |
| `user-cluster create` | `analysis.user_cluster.create` | Create condition/sql cluster directly from semantic intent | `--cluster-name`, `--display-name`, `--definition-request` | Create result and canonical request |
| `user-cluster update` | `analysis.user_cluster.update` | Update condition/sql cluster after confirmation without changing its type or analysis entity | `--cluster-name`, fields to change, optional `--definition-request` with the existing type, then `--yes` after dry-run and explicit confirmation | Update result |
| `user-cluster create-id` | `analysis.user_cluster.create_id` | Map imported values to an entity and create a cluster | `--display-name`, `--entity-id`, exactly one input source, conditional `--association-property` | Processing state; poll get for final match summary |
| `user-cluster update-id` | `analysis.user_cluster.update_id` | Remap imported values for an ID cluster | `--cluster-name`, exactly one input source, conditional `--association-property` | Processing state; poll get for final match summary |
| `user-cluster refresh` | `analysis.user_cluster.refresh` | Trigger cluster recompute | `--cluster-name` | Refresh result |
| `user-cluster delete` | `analysis.user_cluster.delete` | Delete cluster after dependency review | `--cluster-name`, `--confirmed`, `--yes` | Delete result |
| `user-tag list` | `analysis.user_tag.list` | Find accessible user tags | `--project-id`, optional `--queries`, `--fields`, `--limit`, `--offset` | Paginated tag summaries |
| `user-tag export` | `analysis.user_tag.export` | Export complete matching tag catalog | `--project-id`, optional filters, required `--output` | Local JSONL catalog and integrity sidecar |
| `user-tag get` | `analysis.user_tag.get` | Inspect exact tags | `--tag-names '[...]'` | Tag details |
| `user-tag-member list` | `analysis.user_tag_member.list` | Bounded inline tag members | `--tag-name`, optional `--snapshot-date`, properties/fields/query/limit/offset | Member rows |
| `user-tag-member export` | `analysis.user_tag_member.export` | Stream native full tag members as csv.gz | `--tag-name`, optional `--snapshot-date`, properties | Async artifact descriptor |
| `user-tag create` | `analysis.user_tag.create` | Create tag directly from semantic intent, optionally with periodic refresh | `--tag-name`, `--display-name`, `--definition-request`, optional `--auto-refresh-schedule` or `--auto-refresh-cron` | Create result and canonical request |
| `user-tag update` | `analysis.user_tag.update` | Update tag | `--tag-name`, fields to change, optional `--definition-request` | Update result |
| `user-tag refresh` | `analysis.user_tag.refresh` | Trigger tag recompute | `--tag-name` | Refresh result |
| `user-tag create-id` | `analysis.user_tag.create_id` | Map imported values to an entity and create a tag | `--display-name`, `--entity-id`, exactly one input source, conditional `--association-property` | Processing state; poll get for final match summary |
| `user-tag update-id` | `analysis.user_tag.update_id` | Remap imported values for an ID tag | `--tag-name`, exactly one input source, conditional `--association-property` | Processing state; poll get for final match summary |
| `user-tag delete` | `analysis.user_tag.delete` | Delete tag after dependency review | `--tag-name`, `--confirmed`, `--yes` | Delete result |
| `history-tag list` | `analysis.history_tag.list` | List history snapshots for a tag | `--tag-name` | Snapshot summaries |
| `history-tag refresh` | `analysis.history_tag.refresh` | Refresh one history snapshot | `--tag-name`, `--refresh-date` | Refresh result |
| `history-tag batch-refresh` | `analysis.history_tag.batch_refresh` | Batch refresh snapshots | `--tag-name`, `--refresh-request` | Async refresh result |
| `history-tag clear` | `analysis.history_tag.clear` | Clear snapshots in date range | `--tag-name`, date range, `--confirmed`, `--yes` | Clear result |
| `history-tag-data run` | `analysis.history_tag_data.run` | Bounded inline history tag statistics | `--tag-name`, `--view`, optional `--preview-rows` | Statistic result |
| `history-tag-data export` | `analysis.history_tag_data.export` | Export history tag statistics as jsonl | `--tag-name`, `--view` | Async artifact descriptor |
| `history-tag-data-drilldown run` | `analysis.history_tag_data_drilldown.run` | Bounded inline users for one statistic value/bucket | `--tag-name`, `--snapshot-date`, `--group-col`, `--view`, optional member fields | Drilldown member rows |
| `history-tag-data-drilldown export` | `analysis.history_tag_data_drilldown.export` | Stream native full users for one statistic value/bucket as csv.gz | `--tag-name`, `--snapshot-date`, `--group-col`, `--view`, optional properties | Async artifact descriptor |

## L3 project-space and folder capabilities

Per [`capability-command-admission` §10](../../../docs/capability-command-admission.md): new gateway capabilities default to **dynamic discovery** (`capability search` → `inspect` →（按需二选一：`validate` **或** `dry-run`，默认不叠打）→ `run`); standalone skill references are **exceptions only** (L2 bar, confusion, high-risk delete, multi-step orchestration).

For **create / delete / share**, read the linked reference before `capability inspect` then `run` (optional pre-check per [`ae-capability`](../../ae-capability/SKILL.md) on-demand table). For **`*.members` read**, use this matrix only — no separate `references/*.md` (pilot).

| Capability ID | Use for | Reference / discovery |
| --- | --- | --- |
| `analysis.project_space.create` | Create a project space | [`project_space_create.md`](project_space_create.md) |
| `analysis.project_space.delete` | Delete project spaces | [`project_space_delete.md`](project_space_delete.md) |
| `analysis.project_space.share` | Modify project-space members | [`project_space_share.md`](project_space_share.md) |
| `analysis.project_space.members` | Read project-space members | Matrix only (see below) |
| `analysis.folder.create` | Create personal/project-space folder | [`folder_create.md`](folder_create.md) |
| `analysis.folder.delete` | Delete folders | [`folder_delete.md`](folder_delete.md) |
| `analysis.folder.share` | Modify folder members | [`folder_share.md`](folder_share.md) |
| `analysis.folder.members` | Read folder members | Matrix only (see below) |

### L3 members (matrix-only pilot)

Read-only member lists; `risk=read`. Do not use to modify members — use the matching `*.share` capability.

**When to use:** inspect who has access to a project space or folder.

**When not to use:** modify members → `analysis.project_space.share` or `analysis.folder.share`.

```bash
ae-cli capability inspect analysis.project_space.members
ae-cli capability run analysis.project_space.members --input '{"project_id":1,"space_id":10}'

ae-cli capability inspect analysis.folder.members
ae-cli capability run analysis.folder.members --input '{"project_id":1,"folder_id":1001}'
```

| field | type | required | capability |
| --- | --- | --- | --- |
| `project_id` | integer | yes | both |
| `space_id` | integer | yes | `project_space.members` |
| `folder_id` | integer | yes | `folder.members` |

Output is the gateway envelope; `data` contains members.

## Examples

```bash
ae-cli analysis dashboard list --project-id 1 --queries '["retention","留存"]' --limit 50
ae-cli analysis adhoc run --project-id 1 --model-type sql --definition '{"sql":"select * from events limit 20"}'
ae-cli analysis adhoc export --project-id 1 --model-type sql --definition '{"sql":"select * from events where country ${Text:country}","params":[{"name":"country","type":"text","value":"US"}]}' --artifact-format jsonl
ae-cli analysis report list --project-id 1 --queries '["revenue","收入"]' --limit 50
ae-cli analysis report-data run --project-id 1 --report-ids '[1001]' --preview-rows 50
ae-cli analysis report-data run --project-id 1 --report-ids '[1001]' --filters '{"relation":"and","items":[{"field":{"name":"country","type":"user_property"},"operator":"eq","values":["US"]}]}' --group-by '[{"field":{"name":"country","type":"user_property"}}]' --sql-params '[{"name":"platform","value":"ios"}]' --preview-rows 50
ae-cli analysis drilldown-entities run --query-context-id ctx_0123456789abcdef0123456789abcdef --source '{"report_id":1001}' --coordinate '{"cohort_date":"2026-07-01","group_values":[],"period_index":1,"population":"retained"}'
ae-cli analysis query create-result-cluster --query-context-id ctx_0123456789abcdef0123456789abcdef --source '{"report_id":1001}' --coordinate '{"cohort_date":"2026-07-01","group_values":[],"period_index":1,"population":"retained"}' --cluster-name retained_users
ae-cli analysis dashboard update --project-id 1 --operation note-upsert --dashboard-id 1001 --note-title "Summary" --description "Weekly note"
ae-cli analysis dashboard-definition export --project-id 1 --dashboard-id 1001 --export-file-name retention_dashboard
ae-cli analysis dashboard-definition import --project-id 1 --definition '{"dashboard_folders":[],"shared_spaces":[]}' --validate-only true
ae-cli analysis public-link create --project-id 1 --resource-type dashboard --resource-id 1001 --effective-at "2026-07-08 00:00:00" --expires-at "2026-08-08 00:00:00"
ae-cli analysis user-cluster list --project-id 1 --queries '["retained","retention"]' --limit 50
ae-cli analysis user-cluster-member export --project-id 1 --cluster-name retained_users --artifact-format csv
ae-cli analysis user-tag create --project-id 1 --tag-name user_level --display-name "User Level" --definition-request '{"type":"condition","condition_values":[]}'
```
