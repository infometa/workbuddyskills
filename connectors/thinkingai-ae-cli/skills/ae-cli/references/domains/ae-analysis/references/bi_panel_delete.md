# analysis bi-panel delete

Use when the user explicitly wants to delete one or more BI panels.

Do not use for dashboards. Use `dashboard delete`.

Command:

```bash
ae-cli analysis bi-panel delete --project-id <project_id> --panel-ids '[2001,2002]' --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis bi-panel delete --project-id <project_id> --panel-ids '[2001,2002]' --yes
```

Input sends `project_id` and `panel_ids`.

Output is the gateway envelope. `data` contains the delete result.
