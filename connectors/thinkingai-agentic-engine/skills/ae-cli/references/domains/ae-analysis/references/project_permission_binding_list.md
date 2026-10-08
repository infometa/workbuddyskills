# project permission-binding list

Use when the user needs to list project role and data-power bindings for company-level permission management.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project permission-binding list --company-id <company_id> --project-ids <project_ids>
ae-cli project permission-binding list --dry-run --company-id <company_id> --project-ids <project_ids>
```

Capability id: `project.permission_binding.list`.

Input sends `company_id`, `project_ids`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--project-ids` | Yes | Project IDs JSON array. |
