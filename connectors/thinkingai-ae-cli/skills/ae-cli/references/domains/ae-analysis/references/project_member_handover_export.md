# project member-handover export

Use when the user needs to run batch project member asset handover and export the generated detail file as a CLI artifact.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member-handover export --project-id <project_id> --payload <payload> --request-id <request_id>
ae-cli project member-handover export --dry-run --project-id <project_id> --payload <payload>
```

Capability id: `project.member_handover.export`.

Input sends `project_id`, `payload`, `request_id`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.
This is an artifact capability. Preserve the returned `run_id` and `artifact_id`; download only through `analysis artifact download` using the same response metadata.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Batch asset handover payload matching AssetBatchHandoverReq in snake_case. single_submit must be false or omitted. |
| `--request-id` | No | Optional caller-supplied cli_<32 lowercase hex> lifecycle ID. |
