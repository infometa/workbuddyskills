# analysis sql-table columns

List queryable columns for one server-authorized SQL table.

First call `analysis sql-table list --project-id <project_id>`, then copy an exact returned `table_ref`. Do not guess table or column names.

```bash
ae-cli analysis sql-table columns \
  --project-id <project_id> \
  --table-ref <table_ref> \
  [--usage analysis|tag_cluster]
```

The result identifies the resolved catalog/schema/table and returns its columns with machine names, types, and available descriptions. A unique table-only reference is accepted; ambiguous references fail with candidate tables instead of selecting one arbitrarily.

Pass the same `usage` used for `sql-table list`. For SQL tags and SQL clusters this must be `--usage tag_cluster`; the default is `analysis`.

When copying returned columns into Trino SQL, delimit identifiers containing `#`, `$`, `@`, spaces, or punctuation with double quotes, for example `"#user_id"` or `"$part_event"`. Single quotes are string literals. The CLI does not auto-rewrite SQL.

If the selected table is an event table, the SQL must include a date-partition predicate on the discovered `"$part_date"` column, for example `WHERE "$part_date" BETWEEN '2026-07-01' AND '2026-07-07'`. The backend rejects event-table SQL without this condition. Do not apply this rule to a table whose discovered columns do not include `$part_date`.
