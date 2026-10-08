# analysis dashboard-daily-report send-status

Use after `dashboard-daily-report send` to inspect the actual delivery result.
Do not use it to read or change the saved daily report configuration.

Command:

```bash
ae-cli analysis dashboard-daily-report send-status --project-id <project_id> --task-id <task_id>
```

The normalized `status` is one of:

- `queued`
- `rendering`
- `sending`
- `succeeded`
- `partially_succeeded`
- `failed`
- `canceled`

Output also includes `progress`, `message`, and per-channel status when the backend task contains channel details.
