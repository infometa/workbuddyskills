# analysis project-space business-filter-upsert

Use when the user wants to create, replace, or clear the space-level business filter inherited by dashboards in one project space.

Command:

```bash
ae-cli analysis project-space business-filter-upsert --project-id <project_id> --space-id <space_id> --filter '{"junction_kind":"and","ta_filters":[...]}'
```

`filter` uses snake_case QP form. Each simple condition uses fields such as `filter_type`, `column_name`, `table_type`, `column_type`, `select_type`, `calcu_symbol`, `ftv`, and `lack_value`. A condition with `lack_value=true` is stored but does not restrict query data.

The backend queries the current space filter first, then creates it when absent or updates it with the current optimistic-lock ID and timestamp. Callers do not pass `id` or `update_time`.

Space-level and dashboard-level business-filter conditions are combined with `AND` when dashboard report data is queried. Pass `{"junction_kind":"and","ta_filters":[]}` to clear the space-level conditions.

Output is the gateway envelope. `data.created` tells whether a new space filter row was created, and `data.business_filter` contains the saved filter.
