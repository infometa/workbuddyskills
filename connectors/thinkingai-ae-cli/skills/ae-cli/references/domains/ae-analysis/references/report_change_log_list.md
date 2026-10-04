# analysis report-change-log list

Use when the user needs the change history of one saved report.

Do not use for current report definition. Use `report get` for the current AI QP definition.

Command:

```bash
ae-cli analysis report-change-log list --project-id <project_id> --report-id <report_id>
```

Input sends `project_id` and `report_id`.

Output is the gateway envelope. `data` contains change log summaries and `total`. Only items with `can_rollback=true` are valid rollback sources; pass that item's `target_version` to `report-version rollback --target-version`. Create and unpack records are not rollbackable. Raw report QP fields are not returned in the list.
