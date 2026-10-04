# project info update

Use when the user needs to update project name and remark.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project info update --project-id <project_id> --project-name <project_name> --project-remark <project_remark>
ae-cli project info update --dry-run --project-id <project_id> --project-name <project_name>
```

Capability id: `project.info.update`.

Input sends `project_id`, `project_name`, `project_remark`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--project-name` | Yes | New project name. |
| `--project-remark` | No | Optional project remark. |
