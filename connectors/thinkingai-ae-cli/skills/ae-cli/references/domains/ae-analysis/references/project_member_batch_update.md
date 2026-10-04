# project member batch-update

Use when the user needs to batch update project members.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member batch-update --project-id <project_id> --payload <payload>
ae-cli project member batch-update --dry-run --project-id <project_id> --payload <payload>
```

Capability id: `project.member.batch_update`.

Input sends `project_id`, `payload`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Batch member edit payload matching EditBatchMembersReq in snake_case. |
