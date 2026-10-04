# analysis dashboard delete

Use when the user explicitly wants to delete one or more dashboards.

Do not use for soft archival or hiding unless the gateway contract defines that behavior.

Command:

```bash
ae-cli analysis dashboard delete --project-id <project_id> --dashboard-ids '[1001,1002]' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis dashboard delete --project-id <project_id> --dashboard-ids '[1001,1002]' --yes
```

Input sends `project_id` and `dashboard_ids`.

Output is the gateway envelope. `data` contains the delete result.
