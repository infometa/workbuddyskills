# project member-candidate list

Use when the user needs to list candidate users and role/data-power options for adding project members.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member-candidate list --project-id <project_id> --type <type> --login-names <login_names>
ae-cli project member-candidate list --dry-run --project-id <project_id> --type <type>
```

Capability id: `project.member_candidate.list`.

Input sends `project_id`, `type`, `login_names`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--type` | Yes | Add type accepted by ProjMemberAddTypeEnum. |
| `--login-names` | No | Comma-separated login names when checking new users. |
