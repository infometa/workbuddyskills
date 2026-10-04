# project info delete

Use when the user needs to delete a project and flush its receiver cache.

Do not use it outside the project info operation or with fields absent from the inspected capability schema.

Command:

```bash
ae-cli project info delete --dry-run --project-id <project-id>
ae-cli project info delete --project-id <project-id> --yes
```

Capability id: `project.info.delete`.

Run `--dry-run` first, summarize the affected target and impact, then wait for explicit user confirmation before rerunning the unchanged command with global `--yes`.

The response uses `ok`, `data`, and `meta`. Treat empty `data` as success when `ok=true`; preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
