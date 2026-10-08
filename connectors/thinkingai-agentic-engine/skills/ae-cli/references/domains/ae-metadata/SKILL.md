---
name: ae-metadata
version: 1.0.1
description: "AE/TE metadata capability-gateway CLI: metadata data-table management and property dimension-table binding. Metadata CLI routes through the analysis gateway. Input-file upload and event/property detail belong to ae-analysis."
---

# ae-metadata

CLI domain **`metadata`** routes to the analysis capability gateway (`/api/cli/analysis/v1/...`), using auth header **`cli-token`**.

Parallel to **`ae-analysis`**. Use **this skill** for gateway-backed metadata detail and data-table/dimension-table operations; use **`ae-analysis`** for metadata list/search, metrics, virtual create, and batch edit.

## Global AE CLI Rules

| Parameter | Description |
|---|---|
| `--format <json\|table>` | Output format. Default JSON. |
| `--jq <expr>` | jq filter on JSON output. |
| `--host <url>` | Override active AE host, e.g. `ae-cli metadata data-table list --host <url> ...`. |
| `--validate` | Optional: fix params only (`/validate`). Alone while iterating complex `qp` / payload — then run. Do not stack with `--dry-run`. |
| `--dry-run` | Optional: confirm ready to run (`/dry-run`). Alone for risk/output preview. Do not stack with `--validate`. |

Output and errors:
- Success: JSON envelope (default). May include optional `_notice.host_compat`.
- Failure: `{ "ok": false, "error": { "type", "message", "hint" } }`, non-zero exit.
- **CRITICAL — Host compat (do this first):** After each `ae-cli` run, check stderr and `_notice.host_compat`. If either is present, open the user reply with a short ⚠️ version warning and **quote the `npm i -g` / `npx skills add` (or update-cluster) lines verbatim**, then present the business result. Soft tip; `ok: true` can still carry the notice.

Safety:
- Read-only commands can run directly after IDs/names are verified.
- Ordinary writes (`data-table *-write`, `property-bindings-update`, dimension-table bind/create) execute without `--yes`. Delete commands are `high-risk-write`: dry-run first, summarize impact, wait for explicit confirmation, then execute with `--yes`.
- **Before any command**, read the matching `references/<name>.md` (filename = command with spaces → underscores, e.g. `metadata data-table list` → `metadata_data_table_list.md`).
- Never invent `project_id`, event/property names, `input_file_id`, or `data_table_id`. Discover names via `ae-analysis` and data table IDs via `metadata data-table list`.
- `metadata data-table download` is an async artifact command: plain invocation submits, `--wait` waits, and `--output <file>` waits then streams atomically. Resume with `analysis run wait`; local interruption never cancels the remote run.

## When to Use

Switch to **`ae-metadata`** when the user needs:

- Metadata data-table list/get/create/update/delete/download
- For local uploads, switch to `ae-analysis` and use `analysis input-file upload` with a discovered purpose.
- Bind an existing data table to a property, or create a CSV dimension table and bind it

Stay on **`ae-analysis`** for: metadata event/property detail, metadata event/property/metric list/search, metric CRUD, batch metadata, virtual create, project config, tracking plans.

## Command Format

```bash
ae-cli metadata <resource> <action> [options]
ae-cli metadata property <dimension-table-action> [options]
```

- Commands and flags use **kebab-case**: `data-table`, `dimension-table`, `--project-id`, `--data-table-id`.
- Gateway `input` body fields remain **snake_case** (`project_id`, `event_name`, …); ae-cli maps flags automatically.

## PROJECT_ID_GATE

Same rules as `ae-analysis`: reuse verified project context in one conversation; otherwise `ae-cli project info list` (or `ae-analysis` skill) to resolve `project_id`.

## Commands (10)

| User command | Capability id | Reference |
|---|---|---|
| `metadata data-table list` | `metadata.data_table.list` | [metadata_data_table_list.md](references/metadata_data_table_list.md) |
| `metadata data-table get` | `metadata.data_table.get` | [metadata_data_table_get.md](references/metadata_data_table_get.md) |
| `metadata data-table csv-write` | `metadata.data_table.csv_write` | [metadata_data_table_csv_write.md](references/metadata_data_table_csv_write.md) |
| `metadata data-table sql-write` | `metadata.data_table.sql_write` | [metadata_data_table_sql_write.md](references/metadata_data_table_sql_write.md) |
| `metadata data-table csv-delete` | `metadata.data_table.csv_delete` | [metadata_data_table_csv_delete.md](references/metadata_data_table_csv_delete.md) |
| `metadata data-table sql-delete` | `metadata.data_table.sql_delete` | [metadata_data_table_sql_delete.md](references/metadata_data_table_sql_delete.md) |
| `metadata data-table download` | `metadata.data_table.download` | [metadata_data_table_download.md](references/metadata_data_table_download.md) |
| `metadata data-table property-bindings-update` | `metadata.data_table.property_bindings_update` | [metadata_data_table_property_bindings_update.md](references/metadata_data_table_property_bindings_update.md) |
| `metadata property bind-existing-dimension-table` | `metadata.property.bind_existing_dimension_table` | [metadata_property_dimension_table_bind_existing.md](references/metadata_property_dimension_table_bind_existing.md) |
| `metadata property create-and-bind-csv-dimension-table` | `metadata.property.create_and_bind_csv_dimension_table` | [metadata_property_dimension_table_create_and_bind_csv.md](references/metadata_property_dimension_table_create_and_bind_csv.md) |

## Quick Verification

```bash
ae-cli metadata --help
ae-cli metadata data-table list --help
ae-cli metadata data-table list --project-id 1 --dry-run
ae-cli analysis input-file purpose list --project-id 1
```

## Related Skills

- **`ae-analysis`**: `analysis-meta event get` / `analysis-meta property get` for detail, and `analysis-meta event list` / `analysis-meta property list` to discover names.
