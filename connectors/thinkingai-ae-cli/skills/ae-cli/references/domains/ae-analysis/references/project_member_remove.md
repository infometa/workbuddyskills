# project member remove

Use when the user needs to remove a project member and optionally hand over assets.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member remove --project-id <project_id> --payload <payload> --from-open-id <from_open_id>
ae-cli project member remove --dry-run --project-id <project_id> --payload <payload> --from-open-id <from_open_id>
```

Capability id: `project.member.remove`.

Input sends `project_id`, `payload`, `from_open_id`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Remove member payload matching RemoveProjMemberReq in snake_case. |
| `--from-open-id` | Yes | Open ID of the member to remove. |
