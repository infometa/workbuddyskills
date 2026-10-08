# project role list

Use when the user needs to list project-visible roles.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project role list --company-id <company_id> --project-id <project_id> --visible-only <visible_only>
ae-cli project role list --dry-run
```

Capability id: `project.role.list`.

Input sends `company_id`, `project_id`, `visible_only`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--company-id` | No | Company ID. Required when project_id is absent. |
| `--project-id` | No | Project ID. Required when company_id is absent. |
| `--visible-only` | No | When true, list roles visible to the current user. |
