# project role-function list

Use when the user needs to list functions granted to one or more roles.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project role-function list --company-id <company_id> --project-id <project_id> --role-name <role_name> --role-names <role_names> --show-system-func <show_system_func>
ae-cli project role-function list --dry-run
```

Capability id: `project.role_function.list`.

Input sends `company_id`, `project_id`, `role_name`, `role_names`, `show_system_func`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--company-id` | No | Company ID. |
| `--project-id` | No | Project ID. |
| `--role-name` | No | Single role name. |
| `--role-names` | No | Role names JSON array. When omitted, all role functions are returned. |
| `--show-system-func` | No | Whether to include system functions. Default false. |
