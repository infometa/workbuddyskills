# project user-id-items update

Use when the user needs to update project virtual user ID item configuration.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project user-id-items update --project-id <project_id> --payload <payload>
ae-cli project user-id-items update --dry-run --project-id <project_id> --payload <payload>
```

Capability id: `project.user_id_items.update`.

Input sends `project_id`, `payload`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Virtual user ID item configuration payload, matching VirtualUserIdConfigSaveRequestDTO in snake_case. |
