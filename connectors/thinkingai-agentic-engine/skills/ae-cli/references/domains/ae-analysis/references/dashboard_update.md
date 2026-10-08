# analysis dashboard update

Use when the user wants to update dashboard settings in batch, upsert a dashboard note, or replace the dashboard-level business filter.

Do not use for moving/copying dashboards. Use `dashboard copy`, `dashboard handover`, or the relevant project-space/folder command.

Command:

```bash
ae-cli analysis dashboard update --project-id <project_id> --operation settings --dashboard-ids '[1001,1002]' [--zone-offset 8] [--payload '{...}']
ae-cli analysis dashboard update --project-id <project_id> --operation settings --dashboard-id <dashboard_id> --refresh-type 1 --dashboard-status normal --payload '{"dashboard_job_schedule":"0 0 8 * * ?","time_config_open":true,"time_config":{},"cache_config":{},"schedule_ui_config":{}}'
ae-cli analysis dashboard update --project-id <project_id> --operation note-upsert --dashboard-id <dashboard_id> [--note-id <note_id>] [--note-title <title>] [--description <text>]
ae-cli analysis dashboard update --project-id <project_id> --operation default-filter --dashboard-id <dashboard_id> --filter-name <name> --filter '{"junction_kind":"and","ta_filters":[...]}'
ae-cli analysis dashboard update --project-id <project_id> --operation business-filter --dashboard-id <dashboard_id> --filter '{"junction_kind":"and","ta_filters":[...]}'
```

For `operation=settings`:

- identify one dashboard with `dashboard_id`, or a batch with `dashboard_ids`;
- `refresh_type` is integer `0` (real-time) or `1` (scheduled);
- `dashboard_status` is string `normal` or `freeze`;
- `zone_offset` is an integer hour offset from `-12` to `14`;
- complex settings belong in snake_case `payload`: `reports_version` string, `dashboard_job_schedule` string, `time_config_open` boolean, and object fields `time_config`, `cache_config`, `schedule_ui_config`; `ui_config` may be a string or object.

For `operation=note-upsert`, `dashboard_id` is required. Omit `note_id` to create a note attached to that dashboard, or pass it to update an existing note. A created note defaults missing `note_title` and `description` to empty strings. An update preserves `note_title`, `description`, and `ui_config` when the corresponding field is omitted; pass an explicit empty string to clear text. Do not mix note fields with batch settings fields.

For `operation=default-filter`, pass one `dashboard_id`, `filter_name`, and `filter`. This saves a favorite filter and enables it as the dashboard-wide default filter; it is distinct from the current caller's personal default filter.

For `operation=business-filter`, pass one `dashboard_id` and a `filter` object in snake_case QP form. This replaces the dashboard-level business filter saved in `ta_dashboard_business_filter`; it is not a condition-filter favorite or a space-level filter. Each simple condition uses fields such as `filter_type`, `column_name`, `table_type`, `column_type`, `select_type`, `calcu_symbol`, `ftv`, and `lack_value`. A condition with `lack_value=true` is saved as a selectable field but does not restrict query data. Pass `{"junction_kind":"and","ta_filters":[]}` to clear all dashboard-level business-filter conditions.

Output is the gateway envelope. `data` contains the update result.
