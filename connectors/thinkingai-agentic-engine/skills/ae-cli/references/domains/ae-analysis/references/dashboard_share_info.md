# analysis dashboard share-info

Use when the user needs to inspect a dashboard's current sharing configuration.

Do not use to modify sharing. Use `dashboard share`.

Command:

```bash
ae-cli analysis dashboard share-info --project-id <project_id> --dashboard-id <dashboard_id>
```

Input sends `project_id` and `dashboard_id`.

Output is the gateway envelope. `data` contains dashboard sharing members and permissions.
