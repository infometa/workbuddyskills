# analysis dashboard task-status

Use when the user needs scheduled task status for a dashboard.

Do not use to update daily report configuration. Use `dashboard-daily-report update`.

Command:

```bash
ae-cli analysis dashboard task-status --project-id <project_id> --dashboard-id <dashboard_id>
```

Input sends `project_id` and `dashboard_id`.

Output is the gateway envelope. `data` contains scheduled task status.
