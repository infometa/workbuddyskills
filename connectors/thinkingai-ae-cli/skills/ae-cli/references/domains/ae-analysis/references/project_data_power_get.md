# project data-power get

Use when the user needs to get one data power detail.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project data-power get --project-id <project_id> --data-power-id <data_power_id>
ae-cli project data-power get --dry-run --project-id <project_id> --data-power-id <data_power_id>
```

Capability id: `project.data_power.get`.

Input sends `project_id`, `data_power_id`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--data-power-id` | Yes | Data power ID. |
