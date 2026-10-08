# project role delete

Use when the user needs to delete a role and optionally migrate users to another role.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project role delete --project-id <project_id> --role-name <role_name> --new-role-name <new_role_name>
ae-cli project role delete --dry-run --project-id <project_id> --role-name <role_name>
```

Capability id: `project.role.delete`.

Input sends `project_id`, `role_name`, `new_role_name`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--role-name` | Yes | Role name to delete. |
| `--new-role-name` | No | Role name to migrate users to before deletion. |
