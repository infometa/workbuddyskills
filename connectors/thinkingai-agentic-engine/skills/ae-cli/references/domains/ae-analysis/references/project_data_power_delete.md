# project data-power delete

Use when the user needs to delete a data power and optionally migrate users to another data power.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project data-power delete --project-id <project_id> --data-power-id <data_power_id> --new-data-power-id <new_data_power_id>
ae-cli project data-power delete --dry-run --project-id <project_id> --data-power-id <data_power_id>
```

Capability id: `project.data_power.delete`.

Input sends `project_id`, `data_power_id`, `new_data_power_id`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--data-power-id` | Yes | Data power ID to delete. |
| `--new-data-power-id` | No | Optional replacement data power ID for affected users. |
