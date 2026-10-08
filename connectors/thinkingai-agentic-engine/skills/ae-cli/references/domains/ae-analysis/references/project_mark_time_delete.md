# project mark-time delete

Use when the user needs to delete project date markers.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project mark-time delete --project-id <project_id> --mark-time-ids <mark_time_ids>
ae-cli project mark-time delete --dry-run --project-id <project_id> --mark-time-ids <mark_time_ids>
```

Capability id: `project.mark_time.delete`.

Input sends `project_id`, `mark_time_ids`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--mark-time-ids` | Yes | Date marker IDs JSON array to delete. |
