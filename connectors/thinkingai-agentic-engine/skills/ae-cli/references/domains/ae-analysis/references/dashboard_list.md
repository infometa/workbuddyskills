# analysis dashboard list

Use when the user needs to find dashboards they can access, with optional keyword, owner, permission, favorite, or projection filters supported by the gateway payload.

Do not use for dashboard report data. Use `dashboard-report-data run` or `dashboard-report-data export` instead.

Command:

```bash
ae-cli analysis dashboard list --project-id <project_id> [--queries '["growth","retention"]'] [--fields '["dashboard_id","dashboard_name"]'] [--limit 50] [--offset 0]
```

Input uses `project_id` plus optional `queries`, `fields`, `limit`, `offset`. `queries` is a JSON array of 1 to 20 non-empty strings; values use OR semantics. Matching rows include `matched_queries` and `matched_fields`. `--fields` accepts only `dashboard_id`, `dashboard_name`, and `remark`. Input and output both use snake_case; do not use `query`, `dashboardId`, `dashboardName`, generic `id`, or generic `name`.

When `has_more=true`, continue only with the returned `next_offset`; do not calculate the next page locally.

Output is the gateway envelope. `data` contains dashboard summaries and paging metadata when returned by the gateway.
