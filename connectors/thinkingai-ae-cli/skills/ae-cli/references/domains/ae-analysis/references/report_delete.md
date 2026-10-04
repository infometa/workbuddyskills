# analysis report delete

Use when the user explicitly wants to delete one or more saved reports.

Do not use without first confirming the target report IDs through `report list` or user-provided exact IDs.

Command:

```bash
ae-cli analysis report delete --project-id <project_id> --report-ids '[1001,1002]' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis report delete --project-id <project_id> --report-ids '[1001,1002]' --yes
```

Input sends `project_id` and `report_ids`. Use an array even for one report.

Output is the gateway envelope. `data` contains deleted `report_ids` and `deleted_count`.
