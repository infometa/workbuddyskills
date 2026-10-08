# project member import

Use when the user needs to import members and roles from another project.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project member import --project-id <project_id> --source-project-id <source_project_id>
ae-cli project member import --dry-run --project-id <project_id> --source-project-id <source_project_id>
```

Capability id: `project.member.import`.

Input sends `project_id`, `source_project_id`, `yes`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.
For execution, dry-run first, summarize the impact, then rerun the unchanged command with global `--yes` only after explicit user confirmation. The CLI sends `yes=true` after its own high-risk gate.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--source-project-id` | Yes | Project ID to import members from. |
