# analysis report-version rollback

Use when the user explicitly wants to rollback one report to a previous history version.

Do not use without first choosing an item with `can_rollback=true` from `report-change-log list` or receiving an exact user-provided version. Pass the selected item's `target_version`; do not infer it from `version` or `original_version`.

Command:

```bash
ae-cli analysis report-version rollback --project-id <project_id> --report-id <report_id> --target-version <version>
```

Input sends `project_id`, `report_id`, and target `version` from CLI `--target-version`.

Output is the gateway envelope. `data` contains `report_id`, `rolled_back`, `target_version`, and `previous_version`.
