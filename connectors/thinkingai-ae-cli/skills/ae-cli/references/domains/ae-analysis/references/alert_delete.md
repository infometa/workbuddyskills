# analysis alert delete

Use when delete an alert.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli analysis alert delete --project-id <project_id> --alert-id <alert_id> --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli analysis alert delete --project-id <project_id> --alert-id <alert_id> --yes
```

Capability id: `analysis.alert.delete`

Input sends `project_id` and `alert_id`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--alert-id` | See command help | Yes |
