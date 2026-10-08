# project member-receiver list

Use when the user needs to list project member handover receivers.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member-receiver list --project-id <project_id>
ae-cli project member-receiver list --dry-run --project-id <project_id>
```

Capability id: `project.member_receiver.list`.

Input sends `project_id`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
