# analysis dashboard create

Use only when the user explicitly wants to create the product's analysis board (`看板`) in personal space, a project space, or a folder.

Do not use for a BI dashboard (`仪表盘`); use `analysis bi-panel create` instead. Do not use to copy an existing analysis board; use `dashboard copy` for copy workflows.

Command:

```bash
ae-cli analysis dashboard create --project-id <project_id> --dashboard-name <name> [--space-id <space_id>] [--folder-id <folder_id>] [--initial-report-id <report_id>] [--payload '{...}']
```

Input sends `project_id`, `dashboard_name`, and optional `space_id`, `folder_id`, `initial_report_id`, `payload`.

Output is the gateway envelope. `data` contains the created analysis-board identity or backend create result.
