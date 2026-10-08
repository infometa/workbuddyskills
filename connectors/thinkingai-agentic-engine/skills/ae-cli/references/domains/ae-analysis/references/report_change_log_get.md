# analysis report-change-log get

Use when the user needs a specific report change log detail, including AI QP definition when available.

Do not use for rollback. Use `report-version rollback` after choosing a version from `report-change-log list`.

Command:

```bash
ae-cli analysis report-change-log get --project-id <project_id> --report-id <report_id> [--history-version <version>]
```

Input sends `project_id`, `report_id`, and optional `version` from CLI `--history-version`.

Output is the gateway envelope. `data` contains change log fields and may include `model_type` plus AI QP `definition`.
