---
name: dataops-query
version: 1.0.0
description: "Data exploration and SQL query: browse data warehouse metadata, search tables, execute SQL queries, get results. Trigger keywords: query, SQL, data exploration, search tables, view table structure, browse data, IDE, catalog, select."
metadata:
  requires:
    bins: ["ae-cli"]
---

# DataOps Data Exploration and SQL Query

> **Prerequisites:** Read [`ae-dataops/SKILL.md`](../SKILL.md) for general rules.

Use the `dataops_ide` subcommand for data exploration and SQL queries.

**Core Rule: IDE only allows query operations, prohibits creating/modifying/deleting data tables (use dataops_datatable for task table DDL).**

**Table discovery rule:** use `dataops_datatable +dict_search_tables` first for the visible DataOps catalog. Use `dataops_ide +search_tables` only when raw engine metadata is needed, and `dataops_ide +ide_list_tables` only for known catalog/schema browsing.

If `spaceCode` is unknown, run `ae-cli dataops_repo +list_spaces` first. Use the only returned `spaceCode` directly; when multiple spaces are returned, choose by user intent or ask the user instead of guessing.

---

## Workflow A: Browse Data Warehouse Metadata

Explore data warehouse structure step by step: repository → catalog → schema → table → column.

```bash
# Step 1: List available IDE warehouse repositories
ae-cli dataops_ide +ide_list_repos --spaceCode "${spaceCode}"

# Step 2: List accessible catalogs and schema names. Defaults: connType=SPACE, repoCode=te_etl.
ae-cli dataops_ide +ide_list_catalogs --spaceCode "${spaceCode}"

# Step 3: List physical tables under one schema. Defaults: connType=SPACE, repoCode=te_etl, entityType=TABLE, pageNum=1, pageSize=20.
# This command does not support keyword filtering; use +search_tables only for engine-side keyword search.
ae-cli dataops_ide +ide_list_tables --spaceCode "${spaceCode}" \
  --catalog "${catalog}" --schema "${schema}" --pageSize 20

# To list views under the same schema
ae-cli dataops_ide +ide_list_tables --spaceCode "${spaceCode}" \
  --catalog "${catalog}" --schema "${schema}" --entityType VIEW --pageSize 20

# Step 4: Get engine-side table/view detail. Defaults: connType=SPACE, repoCode=te_etl, engineType=TASK_ENGINE_TRINO; entityType is auto-detected; tableDdl is hidden unless --includeDdl true.
ae-cli dataops_ide +ide_get_table_detail --spaceCode "${spaceCode}" \
  --catalog "${catalog}" --schema "${schema}" --tableName "${tableName}"
```

---

## Workflow B: Search and View Tables

When you don't know the exact table location, search by keyword. Prefer `dataops_datatable +dict_search_tables`; use the IDE search below only when raw engine metadata is needed.

```bash
# Search engine-side warehouse tables/views by keyword. Defaults: connType=SPACE, repoCode=te_etl, size=20.
ae-cli dataops_ide +search_tables --spaceCode "${spaceCode}" --searchKey "user"
```

---

## Workflow C: Execute SQL Query (Download-Centered Async Flow)

Use this flow for exactly one read-only SQL query. Result rows are not returned through MCP/CLI; submit creates a Gaia download-center task directly. The query semantics are preserved, but the result remains platform-bounded; when present, `downloadRowLimit` reports that cap. This is not an unlimited or full export.

```bash
# Step 1: Submit SQL and create a download task. Defaults: repoCode=te_etl, engineType=TASK_ENGINE_TRINO.
ae-cli dataops_ide +submit_sql_query --spaceCode "${spaceCode}" --repoCode "te_etl" \
  --sql "SELECT * FROM hive.ws_default_dev.dwd_user LIMIT 10" \
  --engineType "TASK_ENGINE_TRINO"

# Step 2: Poll the download task status by spaceCode/downloadTaskId. Rows are not returned through MCP/CLI.
ae-cli dataops_ide +get_sql_query_status --spaceCode "${spaceCode}" --downloadTaskId ${downloadTaskId}

# Step 3: CLI-only streaming save after downloadStatus=SUCCESS. The target is replaced only after the stream completes.
ae-cli dataops_ide +get_sql_query_status --spaceCode "${spaceCode}" --downloadTaskId ${downloadTaskId} --downloadTo "./result.zip"

# (Optional) Cancel the download task.
ae-cli dataops_ide +cancel_sql_query --spaceCode "${spaceCode}" --downloadTaskId ${downloadTaskId}
```

---

## Command Quick Reference

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `+ide_list_repos` | List IDE repositories grouped by connType | `--spaceCode` |
| `+ide_list_catalogs` | List IDE catalogs and schemas | `--spaceCode` `[--connType]` `[--repoCode]` |
| `+ide_list_tables` | List tables or views in one catalog/schema | `--spaceCode` `--catalog` `--schema` `[--connType]` `[--repoCode]` `[--entityType]` `[--pageNum]` `[--pageSize]` |
| `+ide_get_table_detail` | Get engine-side table/view detail; `tableDdl` only with `--includeDdl true` | `--spaceCode` `--catalog` `--schema` `--tableName` `[--connType]` `[--repoCode]` `[--engineType]` `[--entityType]` `[--includeDdl]` |
| `+get_schema_info` | Get schema statistics only (`schema/tableNum/viewNum`) | `--spaceCode` `--catalog` `--schema` `[--connType]` `[--repoCode]` |
| `+search_tables` | Search engine-side warehouse tables/views by keyword | `--spaceCode` `--searchKey` `[--connType]` `[--repoCode]` `[--size]` |
| `+submit_sql_query` | Submit SQL and create a download task | `--spaceCode` `--sql` `[--repoCode]` `[--engineType]` |
| `+get_sql_query_status` | Poll download task status; `--downloadTo` is CLI-only local save after `downloadStatus=SUCCESS` | `--spaceCode` `--downloadTaskId` `[--requestId]` `[--downloadTo]` |
| `+cancel_sql_query` | Cancel download task; `--requestId` is trace-only | `--spaceCode` `--downloadTaskId` `[--requestId]` |

## Parameter Notes

- **connType**: `SPACE` (data warehouse for daily queries, default) | `ETL` (ETL engine) | `APP` (app warehouse for external services)
- **Repository list**: `+ide_list_repos` requires `--spaceCode` and has no optional flags. It returns an array grouped by `connType`; each group has `repos` with `repoCode`, `repoDesc`, and `engineTypes`.
- **Catalog list**: `+ide_list_catalogs` requires `--spaceCode`; `--connType` and `--repoCode` are optional and default to `SPACE` and `te_etl`. It returns an array of catalogs with `catalog`, `catalogBelongEnum`, `schemaNum`, and `schemas`.
- **Table list**: `+ide_list_tables` requires `--spaceCode`, `--catalog`, and `--schema`. `--connType`, `--repoCode`, `--entityType`, `--pageNum`, and `--pageSize` are optional and default to `SPACE`, `te_etl`, `TABLE`, `1`, and `20`. It returns `items`, `pageNum`, `pageSize`, `returnedCount`, `hasMoreMaybe`, and `nextAction`.
- **Table search**: `+search_tables` requires `--spaceCode` and `--searchKey`. `--connType`, `--repoCode`, and `--size` are optional and default to `SPACE`, `te_etl`, and `20`. It returns `items`, `searchKey`, `size`, `totalCount`, `tableCount`, `viewCount`, `returnedCount`, `hasMore`, and `nextAction`.
- **Table detail**: `+ide_get_table_detail` requires `--spaceCode`, `--catalog`, `--schema`, and `--tableName`. `--connType`, `--repoCode`, `--engineType`, `--entityType`, and `--includeDdl` are optional and default to `SPACE`, `te_etl`, `TASK_ENGINE_TRINO`, auto-detect, and `false`. It returns identity, storage metadata, columns, partitions, partition keys, optional layout fields, and `tableDdl` only when requested.
- **Schema info**: `+get_schema_info` requires `--spaceCode`, `--catalog`, and `--schema`. `--connType` and `--repoCode` are optional and default to `SPACE` and `te_etl`. It returns only `schema`, `tableNum`, and `viewNum`.
- **SQL submit**: `+submit_sql_query` requires `--spaceCode` and exactly one read-only query in `--sql`. `--repoCode` and `--engineType` are optional and default to `te_etl` and `TASK_ENGINE_TRINO`. On success it returns task metadata and, when exposed by Gaia, `downloadRowLimit`; rows are never returned and the result remains platform-bounded.
- **SQL status**: `+get_sql_query_status` requires `--spaceCode` and `--downloadTaskId`. `--requestId` is optional trace-only. `--downloadTo` is CLI-only; after `downloadStatus=SUCCESS` it streams the result zip to a temporary sibling file, publishes it only after completion, and adds `localFile`. It returns status/progress metadata, `nextAction`, `downloadApi`, and `downloadParams`; rows are never returned.
- **SQL cancel**: `+cancel_sql_query` requires `--spaceCode` and `--downloadTaskId`. `--requestId` is optional trace-only. It returns cancellation request metadata such as `downloadCancelStatus`.
- **engineType**: `TASK_ENGINE_TRINO` (default, interactive queries) | `TASK_ENGINE_STARROCKS` (high-concurrency analytics)
- **entityType**: optional `TABLE` or `VIEW` hint. Omit it unless the target type must be forced.
- **includeDdl**: defaults to false. Use `--includeDdl true` only when the raw DDL text is needed.
