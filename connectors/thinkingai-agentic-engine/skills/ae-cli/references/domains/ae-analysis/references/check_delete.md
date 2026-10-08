# tracking check delete

Use when delete one tracking validation run.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking check delete --project-id <project_id> --uuid <uuid> --confirm true --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli tracking check delete --project-id <project_id> --uuid <uuid> --confirm true --yes
```

Capability id: `tracking.check.delete`

Input sends `project_id`, `uuid`, and lifecycle fields when exposed. Delete also sends `yes` from `--confirm`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--uuid` | See command help | Yes |
| `--confirm` | See command help | Yes |
