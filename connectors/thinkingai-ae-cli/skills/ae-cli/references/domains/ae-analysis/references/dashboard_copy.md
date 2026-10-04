# analysis dashboard copy

Use when the user wants to copy a dashboard, optionally copying reports and targeting a project space or folder.

Do not use to create a blank dashboard. Use `dashboard create`.

If both `--to-space-id` and `--to-folder-id` are omitted, the gateway copies to the source dashboard's current location. Do not manually discover a target folder just to copy in place.

Command:

```bash
ae-cli analysis dashboard copy --project-id <project_id> --dashboard-id <source_dashboard_id> --dashboard-name <new_name> [--report-copy true] [--to-space-id <space_id>] [--to-folder-id <folder_id>]
```

Input sends `project_id`, `dashboard_id`, `dashboard_name`, `report_copy` defaulting to false, and optional `to_space_id`, `to_folder_id`.

Output is the gateway envelope. `data` contains the copied dashboard result.
