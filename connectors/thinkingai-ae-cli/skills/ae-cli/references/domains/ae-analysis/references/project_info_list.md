# project info list

Use when the user needs to list projects accessible to the current user.

Do not use it for unrelated project-management actions or for fields not present in the common-service capability schema. Do not send camelCase aliases.

Command:

```bash
ae-cli project info list --query <query> --fields <fields> --limit <limit> --offset <offset>
ae-cli project info list --dry-run
```

Capability id: `project.info.list`.

Input sends `query`, `fields`, `limit`, `offset`. Payload keys, JSON arrays, and projection fields must follow the common-service snake_case input schema.

Output uses the gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Preserve `request_id` and `invocation_id` when present.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--query` | No | Optional keyword filter. |
| `--fields` | No | Optional snake_case fields to return. |
| `--limit` | No | Optional page size. Default: 50, maximum: 200. |
| `--offset` | No | Optional page offset. Default: 0. |
