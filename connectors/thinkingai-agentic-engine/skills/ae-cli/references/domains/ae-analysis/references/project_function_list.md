# project function list

Use when the user needs to list all project-level functions.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project function list --company-id <company_id> --project-id <project_id>
ae-cli project function list --dry-run
```

Capability id: `project.function.list`.

Input sends `company_id`, `project_id`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--company-id` | No | Company ID. |
| `--project-id` | No | Project ID. |
