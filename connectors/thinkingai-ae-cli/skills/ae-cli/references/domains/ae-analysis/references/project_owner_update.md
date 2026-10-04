# project owner update

Use when the user needs to update project owner.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project owner update --project-id <project_id> --company-id <company_id> --owner-user-id <owner_user_id> --project-name <project_name> --project-remark <project_remark>
ae-cli project owner update --dry-run --project-id <project_id> --company-id <company_id>
```

Capability id: `project.owner.update`.

Input sends `project_id`, `company_id`, `owner_user_id`, `project_name`, `project_remark`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--company-id` | Yes | Company ID. |
| `--owner-user-id` | No | New owner user ID. Omit to only downgrade existing owner. |
| `--project-name` | No | Optional project name update. |
| `--project-remark` | No | Optional project remark update. |
