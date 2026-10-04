# analysis dashboard abnormal-get

Use when the user needs abnormal dependency or import/export diagnostic information for one dashboard.

Do not use for normal dashboard detail. Use `dashboard get`.

Command:

```bash
ae-cli analysis dashboard abnormal-get --project-id <project_id> --dashboard-id <dashboard_id>
```

Input sends `project_id` and `dashboard_id`.

Output is the gateway envelope. `data` contains abnormal dependency information.
