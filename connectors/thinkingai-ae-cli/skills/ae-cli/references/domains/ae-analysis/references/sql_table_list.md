# analysis sql-table list

List the server-authoritative SQL table references that the current user may query in one project.

## Command

```bash
ae-cli analysis sql-table list \
  --project-id <project_id> \
  [--queries '["user","event"]'] \
  [--limit <1-200>] \
  [--offset <next_offset>] \
  [--usage analysis|tag_cluster]
```

## Contract

- Use this command before writing SQL when the table is not already known. Do not ask the customer to supply the fixed project event/user table name and do not guess `v_event_<id>` or `v_user_<id>`.
- `table_ref` is the exact server-authorized reference to copy into SQL and into `analysis sql-table columns --table-ref`.
- `queries` accepts 1 to 20 non-empty strings with OR semantics. Matching rows include `matched_queries` and `matched_fields`; singular `query` is not accepted.
- Each item also returns `catalog`, `schema`, `table`, `table_type`, and `description`.
- `usage=analysis` is the default table set for SQL analysis and reports. Use `usage=tag_cluster` for SQL tags or SQL clusters. These server-authorized sets differ, and the same usage must be passed to `sql-table columns`.
- When `has_more=true`, continue only with the returned `next_offset`. Stop when `has_more=false`.
- An empty list means the current identity has no queryable SQL tables in that project; do not fabricate a table name.

## Example workflow

```bash
ae-cli analysis sql-table list --project-id 1 --queries '["user","account"]'
ae-cli analysis sql-table columns --project-id 1 --table-ref hive.ta.v_user_1
ae-cli analysis adhoc run --project-id 1 --model-type sql --definition '{"sql":"select * from hive.ta.v_user_1 limit 10"}'
```

Use the exact `table_ref` returned by the first command; the example reference is illustrative only.
