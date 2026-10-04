# analysis dashboard handover

Use when the user explicitly wants to transfer one or more dashboards to another project user.

Do not use to share dashboards without ownership transfer. Use `dashboard share`.

Command:

```bash
ae-cli analysis dashboard handover --project-id <project_id> --dashboard-ids '[1001,1002]' --to-user-id <user_id>
```

Input sends `project_id`, `dashboard_ids`, and `to_user_id`.

Output is the gateway envelope. `data` contains the handover result.
