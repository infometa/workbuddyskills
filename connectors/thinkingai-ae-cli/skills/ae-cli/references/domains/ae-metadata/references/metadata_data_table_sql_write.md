# metadata data-table sql-write

> Capability id: `metadata.data_table.sql_write` · Domain: `metadata`.

## Command

```bash
ae-cli metadata data-table sql-write --project-id <project_id> --operation create --table-name datatable_<project_id>_<name> --columns '<columns_json>' --qp '<qp_json>' --zone-offset 8
ae-cli metadata data-table sql-write --project-id <project_id> --operation update --data-table-id <id> --columns '<columns_json>' --qp '<qp_json>' --strategy overwrite --update-cron '0 0 * * * ?'
```

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` / `-p` | Yes | Numeric project ID. |
| `--operation` | Yes | `create` or `update`. |
| `--columns` | Yes | Column definitions JSON array. Preferred fields are `column_name`, `column_type`, and `column_desc`; CLI also accepts `name`, `type`, and `display_name` aliases. Must match SQL output column names. |
| `--qp` | Yes | `SqlDatatableDef` JSON object (see below). |
| `--data-table-id` | For update | Existing data table ID. |
| `--table-name` | For create | Technical table name. Use `datatable_<project_id>_<name>`. |
| `--display-name` | No | Human-readable name. |
| `--remarks` | No | Table remarks. |
| `--zone-offset` | No | Time zone offset in hours. For example, UTC+8 is `8` and UTC-5 is `-5`. Valid range: -12 to 14. |
| `--strategy` | For update | `overwrite` or `insert`. Ignored for create. |
| `--update-cron` | For update | Scheduled update cron. Ignored for create. |

## QP contract (`SqlDatatableDef`)

`--qp` must be a JSON object with this shape. **Do not** pass a top-level `sql` field.

```json
{
  "taSqlVo": {
    "sql": "select '1' as id, 'demo' as name",
    "sqlVoParams": []
  },
  "taSqlView": {}
}
```

| Field | Required | Description |
|---|---|---|
| `taSqlVo` | Yes | SQL entity definition (`TaSqlVo`). |
| `taSqlVo.sql` | Yes | SELECT statement. Output columns must appear in `--columns`. |
| `taSqlVo.sqlVoParams` | No | Dynamic SQL parameters. Use `[]` when none. |
| `taSqlView` | No | SQL view (`TaSqlView`). Use `{}` when no dynamic view params. |
| `taSqlView.sqlViewParams` | No | View dynamic parameters. |

Inspect the live schema. For complex `qp` / `columns`, use **on-demand** pre-check (motto: validate = fix params; dry-run = confirm ready to run). Prefer **`--validate` only** while iterating — then execute. Do **not** stack `--validate` then `--dry-run` on the same final input by default (`dry-run` already validates params).

```bash
ae-cli capability inspect metadata.data_table.sql_write
ae-cli metadata data-table sql-write \
  --project-id 1 \
  --operation create \
  --table-name datatable_1_orders_dim \
  --columns '[{"name":"id","type":"string"},{"name":"name","type":"string"}]' \
  --qp '{"taSqlVo":{"sql":"select '\''1'\'' as id, '\''demo'\'' as name","sqlVoParams":[]},"taSqlView":{}}' \
  --zone-offset 8 \
  --validate
```

`--validate` only checks/normalizes parameters (`valid` + `normalized_input`). It does not create the table. After `valid=true`, execute without `--yes`. Use `--dry-run` **instead of** `--validate` only when you need risk/output/cancel preview — not both.

## Create example

```bash
# Typical complex-qp path: validate while fixing, then execute (no mandatory dry-run).
ae-cli metadata data-table sql-write \
  --project-id 1 \
  --operation create \
  --table-name datatable_1_orders_dim \
  --display-name "Orders dim" \
  --columns '[{"name":"id","type":"string","display_name":"id"},{"name":"name","type":"string","display_name":"name"}]' \
  --qp '{"taSqlVo":{"sql":"select '\''1'\'' as id, '\''demo'\'' as name","sqlVoParams":[]},"taSqlView":{}}' \
  --zone-offset 8 \
  --validate

ae-cli metadata data-table sql-write \
  --project-id 1 \
  --operation create \
  --table-name datatable_1_orders_dim \
  --display-name "Orders dim" \
  --columns '[{"name":"id","type":"string","display_name":"id"},{"name":"name","type":"string","display_name":"name"}]' \
  --qp '{"taSqlVo":{"sql":"select '\''1'\'' as id, '\''demo'\'' as name","sqlVoParams":[]},"taSqlView":{}}' \
  --zone-offset 8
```

## Decision Rules

- Write command. Motto: validate = fix params; dry-run = confirm ready to run. **Pick one pre-check on demand** — do not stack both on the same final input.
- Complex `qp` / `columns`: use `--validate` while iterating until `valid=true`, then execute without CLI confirmation. Skip `--dry-run` unless you specifically need risk/output/cancel preview.
- If you need that preview instead, use `--dry-run` **once** on the final input (it already validates params) — do not validate then dry-run as a habit.
- Global `--validate` → `/validate`; `--dry-run` → `/dry-run`. Neither creates the table. Do not pass both flags together.
- Keep `columns` and `qp` as valid JSON. `qp` must follow `SqlDatatableDef`; validate / dry-run check structure but do not execute SQL.
- If you provide a table name, it must include the project segment, for example `datatable_2_orders_sql`.
- If execute fails with `CAPABILITY_EXECUTION_FAILED`, fix qp with `--validate`, then retry before investigating backend SQL/Presto issues.
