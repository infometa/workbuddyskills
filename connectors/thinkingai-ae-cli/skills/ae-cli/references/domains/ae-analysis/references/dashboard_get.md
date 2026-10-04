# analysis dashboard get

Use when the user needs one dashboard detail or when an agent needs the effective settings, saved filter configuration, and business context for dashboard report data.

Do not use to query report result data. Use `dashboard-report-data run` or `dashboard-report-data export`.

Command:

```bash
ae-cli analysis dashboard get --project-id <project_id> --dashboard-id <dashboard_id> [--use-cache true]
```

Input sends `project_id`, `dashboard_id`, and optional `use_cache`.

Output is the gateway envelope. `data` contains the dashboard detail returned by the capability gateway. Business-context fields are stable snake_case:

- `dashboard_id`, `dashboard_name`, and optional `remark` identify and describe the dashboard.
- `location` always contains `space_id`, `space_name`, `folder_id`, and `folder_name`; values are null when that level does not apply. `folder_name` is the immediate parent folder.
- `notes` is an array whose items contain `note_id`, `note_title`, and `description`.

Prefer `effective_settings` over raw storage fields in `settings` when interpreting behavior:

- `approximate_calculation.enabled` says whether report queries use approximate calculation.
- `fixed_timezone.enabled` says whether the dashboard locks its timezone. When enabled, use `zone_offset`; otherwise `timezone_source=current_user_or_project_default` means the query follows the current user timezone or project default.
- `scheduled_precompute.enabled`, `schedule_hour`, and `zone_offset` describe scheduled precomputation.
- `cache.applicable`, `value`, `unit`, and `source` describe effective cache behavior. A `source` of `scheduled_precompute` means custom cache duration does not apply.

`filter_config` separates filters by source:

- `fixed_time` is the saved dashboard time range. Explicit supported `start_time` and `end_time` on a dashboard data command take precedence.
- `dashboard_default` is the dashboard-wide default filter; it excludes the current caller's personal default filter.
- `dashboard_business` is the mandatory business filter configured on the dashboard.
- `space_business` is the mandatory business filter inherited from the project space.
- `merge_relation=and` means these saved sources and any call-time `--filters` are combined with AND. Treat saved filters as already applied; do not copy them into `--filters`.

Each saved source has `enabled` and a semantic `definition`. Read conditions from `definition.relation` and `definition.items`; fields and operators are Agent-facing names rather than raw QP codes. If a condition has `supported=false`, report that its legacy definition could not be fully mapped instead of claiming that no filter exists.

When this detail is fetched before a dashboard data query, preserve non-empty `location.folder_name`, `dashboard_name`, `remark`, and `notes[].note_title/description` as dashboard context. Use them to interpret the report results, but distinguish this authored context from conclusions observed in the queried data.
