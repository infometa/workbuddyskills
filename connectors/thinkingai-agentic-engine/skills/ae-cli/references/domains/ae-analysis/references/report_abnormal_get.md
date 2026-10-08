# analysis report-abnormal get

Use when the user needs abnormal dependency information for one saved report.

Do not use for dashboard-level abnormal information. Use `dashboard abnormal-get` for dashboard dependencies.

Command:

```bash
ae-cli analysis report-abnormal get --project-id <project_id> --report-id <report_id>
```

Input sends `project_id` and `report_id`.

Output is the gateway envelope. `data` contains report abnormal asset summary and node details when returned by the gateway.
