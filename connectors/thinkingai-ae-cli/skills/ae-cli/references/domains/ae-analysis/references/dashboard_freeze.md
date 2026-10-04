# analysis dashboard freeze

Use when the user wants to freeze or unfreeze one or more dashboards.

Do not use for dashboard lock/version operations; those are intentionally not CLI-enabled.

Command:

```bash
ae-cli analysis dashboard freeze --project-id <project_id> --dashboard-ids '[1001,1002]' [--freeze true]
```

Input sends `project_id`, `dashboard_ids`, and optional `freeze`.

Output is the gateway envelope. `data` contains the freeze or unfreeze result.
