# project receive-status update

Use when the user needs to update project data receive status.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project receive-status update --project-id <project_id> --receive-status <receive_status>
ae-cli project receive-status update --dry-run --project-id <project_id> --receive-status <receive_status>
```

Capability id: `project.receive_status.update`.

Input sends `project_id`, `receive_status`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--receive-status` | Yes | Receive status: NORMAL or STOP_RECEIVE. |
