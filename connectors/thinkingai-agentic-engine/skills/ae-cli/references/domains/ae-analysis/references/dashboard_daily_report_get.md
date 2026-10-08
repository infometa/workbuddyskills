# analysis dashboard-daily-report get

Use when the user wants to inspect one dashboard's saved daily report configuration.

Command:

```bash
ae-cli analysis dashboard-daily-report get --project-id <project_id> --dashboard-id <dashboard_id>
```

Output:

- `exists` indicates whether a saved configuration exists.
- `config` contains the saved schedule, content, enabled channels, and destinations.
- Internal SMTP selection is not exposed.
- Feishu secrets and all webhook URLs are redacted.

Use patch-style `dashboard-daily-report update` to change selected fields. Do not submit redacted values back as configuration.
