---
name: dataops-table
version: 1.0.0
description: "Data table and view management: search tables, view table details, create physical tables/views. Trigger keywords: create table, table creation, view, data dictionary, table details, datatable, DDL."
metadata:
  requires:
    bins: ["ae-cli"]
---

# DataOps Data Table and View Management

> **Prerequisites:** Read [`ae-dataops/SKILL.md`](../SKILL.md) for general rules.

Use the `dataops_datatable` subcommand to manage data tables.

**Core Rules:**
- Creating/modifying/deleting workspace task tables **must use dataops_datatable**, prohibited to use dataops_ide
- Use `+dict_search_tables` as the default discovery command for the visible DataOps catalog
- Use `dataops_ide +search_tables` only when raw engine-side metadata is needed
- Use `dataops_ide +ide_list_tables` only after catalog/schema are known and you need schema browsing
- Confirm no table with the same name exists before creation
- When creating views or data tables, generate DDL according to **Trino DDL specifications**
- `+create_table` and `+create_view` create objects in the DEV environment only. Publish PROD separately with `+publish_entity`.

---

## Workflow A: Search and View Table Information

```bash
# Default table discovery: search the DataOps table catalog. Prefer precise keywords; avoid broad scans.
ae-cli dataops_datatable +dict_search_tables --spaceCode "${spaceCode}" --search "user" --maxResults 20

# Get compact detail. TASK_ENV without --env returns DEV and PRODUCT.
ae-cli dataops_datatable +get_table_detail --spaceCode "${spaceCode}" --tableName "dwd_user_info"
```

---

## Workflow B: Create Physical Table

```bash
# Step 1: Confirm no table with same name exists
ae-cli dataops_datatable +dict_search_tables --spaceCode "${spaceCode}" --search "dwd_user_info"

# Step 2: Create physical table in DEV (DDL must follow Trino specifications)
ae-cli dataops_datatable +create_table --spaceCode "${spaceCode}" \
  --ddl "CREATE TABLE dwd_user_info (user_id VARCHAR, user_name VARCHAR, age INTEGER) WITH (format = 'ORC')"

# Step 3: Publish explicitly. name is enough when it resolves to one TASK_ENV entity.
ae-cli dataops_datatable +publish_entity --spaceCode "${spaceCode}" \
  --name "dwd_user_info"
```

---

## Workflow C: Create View

```bash
# Step 1: Confirm no view with same name exists
ae-cli dataops_datatable +dict_search_tables --spaceCode "${spaceCode}" --search "v_user_info"

# Step 2: Create DataOps view in DEV. This example expands ${spaceCode} but keeps ${env} literal.
ae-cli dataops_datatable +create_view --spaceCode "${spaceCode}" \
  --ddl "CREATE VIEW v_user_info AS SELECT user_id, user_name FROM hive.ws_${spaceCode}_\${env}.dwd_user_info"

# Step 3: Publish explicitly. name is enough when it resolves to one TASK_ENV entity.
ae-cli dataops_datatable +publish_entity --spaceCode "${spaceCode}" \
  --name "v_user_info"
```

---

## Command Quick Reference

| Command | Purpose | Key Flags |
|---------|---------|-----------|
| `+dict_search_tables` | DataOps table catalog search, default 50 results | `--spaceCode` `--search` `--maxResults` |
| `+get_table_detail` | DataOps catalog detail | `--spaceCode` `--tableName` `--manageMode` `--env` `--entityType TABLE|VIEW` |
| `+create_table` | Create DataOps physical table in DEV | `--spaceCode` `--ddl` |
| `+create_view` | Create DataOps view in DEV | `--spaceCode` `--ddl` |
| `+publish_entity` | Publish table/view from DEV to PROD | `--spaceCode` `--name` `[--entityId]` `[--entityType]` |

## Parameter Notes

- **dict_search_tables**: Searches task, IDE, system, and authorized-space tables visible to `spaceCode`. Prefer precise `--search`; default `maxResults` is 50 and max is 200. Returns `tables`, `totalCount`, `returnedCount`, `hasMore`, and `hint` when truncated. `comment` and `remark` are returned only when present.
- **get_table_detail**: Prefer exact `--tableName`. Add `--manageMode` or `--entityType TABLE|VIEW` when ambiguous. TASK_ENV without `--env` returns `environments.DEV/PRODUCT`; otherwise returns `detail`. Empty optional fields are omitted.
- **create_table**: Requires `--spaceCode` and `--ddl`; no optional flags. Creates a DataOps physical table in DEV only. The backend parses Trino-compatible DDL and saves TASK_ENV metadata in the default workspace warehouse (`repo=te_etl`, `catalog=hive`). Publish by name with `+publish_entity --name <tableName>`.
- **create_view**: Requires `--spaceCode` and `--ddl`; no optional command flags. Creates a DataOps view in DEV only. The backend saves TASK_ENV metadata through the DataView save flow in the default workspace warehouse (`repo=te_etl`, `catalog=hive`). Publish by name with `+publish_entity --name <viewName>`. Keep the literal `${env}` placeholder when referencing current-space task tables, for example `ws_${spaceCode}_${env}`.
- **publish_entity**: Requires `--spaceCode` and `--name`. Publishes one existing TASK_ENV table/view from DEV to PROD. Optional `--entityId` disambiguates same-name matches; optional `--entityType TABLE|VIEW` validates the resolved type. Returns `action/result/status`; result includes published ids/names and `ONLINE` status, or `errorType`/`candidates`/`errors`.
- **schema naming**: DEV environment uses `ws_${spaceCode}_dev`, PROD environment uses `ws_${spaceCode}_product`. Do not hardcode either schema in current-space view DDL; use `ws_${spaceCode}_${env}` with literal `${env}`.
- **Table name rule**: `^[a-z][0-9a-z_]{0,127}$`
