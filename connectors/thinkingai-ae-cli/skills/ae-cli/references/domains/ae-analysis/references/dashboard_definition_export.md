# analysis dashboard-definition export

Use when the user wants to export dashboard definition JSON for one dashboard, multiple dashboards, selected private dashboard folders, or shared project spaces.

Do not use for dashboard report result data. Use `dashboard-report-data run` or `dashboard-report-data export`.

Command:

```bash
ae-cli analysis dashboard-definition export --project-id <project_id> [--dashboard-id <dashboard_id>] [--dashboard-ids '[1,2]'] [--dashboard-folder-ids '[...]'] [--shared-spaces '[...]'] [--export-file-name <name>] [--payload '{...}']
```

Input sends `project_id` and optional `dashboard_id`, `dashboard_ids`, `dashboard_folder_ids`, `shared_spaces`, `export_file_name`, `payload`.

Prefer `--dashboard-id` or `--dashboard-ids` when the user asks for a single dashboard or a known dashboard list. The gateway resolves private-folder or project-space context.

For a private folder export, `--dashboard-folder-ids '[123]'` is accepted. Use the advanced descriptor form only when you need to restrict which dashboards inside the folder are exported.

Advanced private-folder descriptor form:

```bash
ae-cli analysis dashboard-definition export --project-id <project_id> \
  --dashboard-folder-ids '[{"dashboard_folder_id":123,"dashboard_ids":[456]}]'
```

Advanced project-space descriptor form:

```bash
ae-cli analysis dashboard-definition export --project-id <project_id> \
  --shared-spaces '[{"space_id":10,"children":[{"is_folder":false,"id":456}]}]'
```

Output is the gateway envelope. `data` contains exported definition data or an export descriptor.
