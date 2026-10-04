---
name: ae-dataops
version: 2.0.0
description: "AE Data Development and Operations: Data warehouse management, flow orchestration, IDE queries, and data integration"
metadata:
  requires:
    bins: ["ae-cli"]
---

# ae-dataops

> **CRITICAL - This skill is self-contained.** Use the Global AE CLI Rules below; do not require a separate shared skill for DataOps-side tasks.

The AE Data Development and Operations domain provides capabilities for data warehouse management, flow orchestration, IDE SQL queries, data integration, operations and backfill management, including the following subcommands:

| Subcommand | Responsibility | Corresponding Scenario Skill |
|------------|----------------|------------------------------|
| `dataops_repo` | Space discovery | — |
| `dataops_datatable` | Data table and view management | `dataops-table` |
| `dataops_flow` | Flow creation, node deletion, and orchestration | `dataops-flow-create` |
| `dataops_flow` | Flow execution and monitoring | `dataops-flow-monitor` |
| `dataops_operations` | Operations instance search, details, and task logs | `dataops-flow-monitor` |
| `dataops_operations` | Backfill job creation, full draft update, deletion, execution, plans, stop, and rerun | `dataops-backfill` |
| `dataops_ide` | Data exploration and SQL queries | `dataops-query` |
| `dataops_integration` | Datasource and data integration | `dataops-integration` |

---


## Global AE CLI Rules

AE CLI (`ae-cli`) is the command-line tool for the AE / TE / ThinkingEngine analysis platform. For AE analysis-side requests, prefer `ae-cli` and this skill's reference docs over model memory.

Global parameters:

| Parameter | Description |
|---|---|
| `--format <json\|table>` | Output format. Default is JSON. |
| `--jq <expr>` | jq filter expression for JSON output. |
| `--host <url>` | Override the active AE host. Available on every command and may be placed after the subcommand, e.g. `ae-cli dataops_ide +<command> --host <url>`. |

Output and errors:
- Successful commands return machine-readable JSON by default. Envelope may include optional `_notice.host_compat`.
- Failed commands return `{ "ok": false, "error": { "type": "...", "message": "...", "hint": "..." } }` and exit non-zero.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.

Safety constraints:
- Read commands can execute directly after required IDs and references are verified.
- Ordinary `write` commands execute without `--yes`; use `--yes` only for a `high-risk-write` command after explicit user confirmation.
- Never invent command names, flags, JSON payloads, `project_id`, resource IDs, field names, event names, property names, metric definitions, or date formats. Read the matching command reference and discover real project metadata first.
- **NEVER fabricate or guess resource names** (reports, dashboards, events, properties, metrics, clusters, tags, alerts). Always use list commands to discover real resources first. If a resource is not found after fuzzy search and full list fallback, explicitly tell the user "resource not found" and stop - do not proceed with fabricated names.

Domains for DataOps: `dataops_repo`, `dataops_datatable`, `dataops_flow`, `dataops_operations`, `dataops_ide`, `dataops_integration`

---

## Core Concepts and Rules

You must understand the following key concepts before use, otherwise errors are highly likely.

### ID System

| ID | Source | Usage Scope |
|----|--------|-------------|
| **executeId** | Returned by `dataops_flow +execute_flow` | Early stop handle before the scheduler `flowInstanceId` is available |
| **flowInstanceId** | Returned by `dataops_operations +search_flow_instances` | Operations perspective instance inspection and stop |
| **jobId** | Returned by `dataops_operations +create_backfill_job` or `+search_backfill_jobs` | Persistent backfill job detail and lifecycle actions |

### Environment and Defaults

| Scenario | Default Environment | Description |
|----------|---------------------|-------------|
| Most flow/ide/datatable commands | `DEV` | Development environment |
| `dataops_operations +search_flow_instances` | Operations instance search | Filter by keyword, execution date, status, and paging |
| `dataops_operations +get_flow_instance_detail` | Instance detail | Inspect one instance DAG and task statuses |
| `dataops_operations +get_task_instance_detail` | Task detail/logs | Inspect one task and include logs only when needed |
| `dataops_operations +stop_flow_instance` | Instance stop | Stop by exactly one of `executeId` or `flowInstanceId` |
| `dataops_operations +list_backfill_flows` | Backfill source discovery | Returns eligible PROD flows and whether ST is required |
| `dataops_operations +search_backfill_jobs` | Backfill job search | Filter persistent jobs and obtain `jobId` |

### Schema Naming Rules

- DEV environment: `ws_${spaceCode}_dev`
- PROD environment: `ws_${spaceCode}_product`

### Responsibility Boundaries

| Operation | Correct Tool | Prohibited |
|-----------|--------------|------------|
| Execute SELECT queries | `dataops_ide` | — |
| Create/modify/delete data tables (DDL) | `dataops_datatable` | `dataops_ide` |

### Flow Lifecycle

```
Create DEV Flow → Create/Update DEV SQL, Integration, Workflow Instance Check, or Task Instance Check Tasks → Configure Dependencies/Schedule → Preview Release → Release to PROD → PROD Manual Execution / Operations Troubleshooting
```

Backfill lifecycle: Discover eligible PROD flow → Create or fully update DRAFT job → Run explicitly → Search / inspect plans → Stop or rerun the complete job; delete only after target inspection

### CRON Format (6 fields)

`second minute hour day month weekday` — Note: one more "second" field than standard 5-field format.
- `0 0 2 * * ?` — Daily at 2 AM
- `0 0 */4 * * ?` — Every 4 hours
- `0 30 8 * * 1-5` — Weekdays at 8:30

### Preset Repository vs Non-Preset Repository

- **Preset Repository (te_etl)**: `datasourceId` is `te_etl@TASK_ENGINE_TRINO`, database field is empty, requires `gatewayConfig`
- **Non-Preset Repository**: `datasourceId` is specific datasource ID, database field is required

---

## Scenario Routing

Choose the appropriate scenario skill based on user intent to get complete step-by-step workflow guidance.

| User Intent | Trigger Skill | Keywords |
|-------------|---------------|----------|
| Create flow, add or delete nodes, configure schedule, release | `dataops-flow-create` | create flow, new workflow, configure schedule, add task node, delete task node, release, cron, scheduled execution |
| View execution status, troubleshoot failures, view logs | `dataops-flow-monitor` | execute flow, running instance, monitor, logs, stop, DAG, troubleshoot |
| Search operation instances across a space | `dataops-flow-monitor` | operations instance, flow instance search, status statistics, owner statistics |
| Create or operate a persistent multi-date backfill job | `dataops-backfill` | backfill, fill historical data, base date range, backfill plans, stop backfill, rerun backfill |
| Create datasource, configure sync solution, execute sync | `dataops-integration` | datasource, sync, integration, field mapping, data ingestion, MySQL, ClickHouse, DatabricksJdbc |
| Browse metadata, search tables, execute SQL queries | `dataops-query` | query, SQL, data exploration, search tables, view table structure, IDE, catalog, select |
| Create tables and views | `dataops-table` | create table, table creation, view, data dictionary, table details, DDL |

---

## 1. Space Discovery

`dataops_repo` exposes only one read command. Use it to discover a valid `spaceCode` before calling DataOps commands that require one. It returns `createTime`, `spaceCode`, and `spaceDisplayName`.

- If the user already provided a trusted `spaceCode`, reuse it.
- If `spaceCode` is unknown, run `+list_spaces` first.
- If exactly one space is returned, use its `spaceCode`.
- If multiple spaces are returned and the user intent does not identify one, ask the user which space to use. Do not guess.

```bash
# List spaces accessible to the current user
ae-cli dataops_repo +list_spaces
```

---

## 2. Data Table and View Management

Detailed workflow, command flags, examples, and parameter notes live in [`references/dataops-table.md`](references/dataops-table.md).

Key constraints:
- Start with `dataops_datatable +dict_search_tables` for visible DataOps catalog discovery.
- Use `dataops_ide +search_tables` only for raw engine metadata, and `dataops_ide +ide_list_tables` only for known catalog/schema browsing.
- Create tables/views with `dataops_datatable`, not `dataops_ide`; creation is DEV-only and must be published with `+publish_entity`.
- DDL follows Trino syntax; current-space view DDL should keep the literal `${env}` placeholder.

---

## 3. Flow Orchestration

Flow orchestration is divided into two scenario skills: **creation and configuration** and **execution and monitoring**.

**Lifecycle: DEV configuration and preview → Release to PROD → PROD manual execution and operations troubleshooting**

Detailed creation/configuration commands live in [`references/dataops-flow-create.md`](references/dataops-flow-create.md). Detailed execution, monitoring, operation instance, task log, and stop commands live in [`references/dataops-flow-monitor.md`](references/dataops-flow-monitor.md). Persistent multi-date backfill jobs live in [`references/dataops-backfill.md`](references/dataops-backfill.md).

Key constraints:
- Create and update tasks in DEV, preview/release before PROD execution.
- Treat `+delete_task` as high-risk: verify the target with `+get_flow_overview`, preview with `--dry-run`, and use `--yes` only after explicit user confirmation. Deletion affects DEV; release the flow to apply it to PROD.
- `+execute_flow` always runs PROD; it returns `executeId` for early stop.
- Prefer `flowInstanceId` from operations search for stable inspection and troubleshooting.
- A backfill job is persistent and batches multiple base dates; do not emulate it by looping `+execute_flow`.
- Create and run backfill jobs as separate steps. `+rerun_backfill_job` reruns the complete job, not only failed plans.
- `+update_backfill_job` replaces a DRAFT job's complete configuration; inspect the job first and do not treat it as a partial patch. Treat `+delete_backfill_job` as high-risk and preview it with `--dry-run` before confirmation.
- Reference workspace parameters in task SQL as `${paramKey}`.

---

## 4. IDE SQL Queries

Detailed metadata browsing, SQL query, async download, and cancel workflows live in [`references/dataops-query.md`](references/dataops-query.md).

Key constraints:
- IDE is query-only; create/modify/delete tables with `dataops_datatable`.
- Prefer `dataops_datatable +dict_search_tables` for table discovery unless raw engine metadata or schema browsing is required.
- Submit exactly one read-only SQL query. It creates a platform-bounded download task; rows are not returned inline and the result is not an unlimited or full export.

---

## 5. Data Integration

Detailed datasource, metadata browsing, sync solution, execution, and monitoring workflows live in [`references/dataops-integration.md`](references/dataops-integration.md).

Key constraints:
- Generate `sourceConfig`, `sinkConfig`, `channelConfig`, and `fieldsMapping` from the reference templates; do not invent keys.
- MySQL Source read partitioning uses `sourceConfig.splitColumn`; `fieldsMapping.shardingKey` is column metadata and must not be used for it.
- `+save_sync_solution` is not a partial patch: call `+get_sync_detail --withParams true` first, then submit complete configs. `syncName` is accepted for compatibility but ignored.
- Preset repository sync uses `te_etl@TASK_ENGINE_TRINO` and requires gateway configuration.
- Use `+list_sync_runs` to get `taskId` before stopping a running sync.

---

## Reference Documentation

For detailed command flags and usage, please refer to the command documentation in the [`references/`](references/) directory.
