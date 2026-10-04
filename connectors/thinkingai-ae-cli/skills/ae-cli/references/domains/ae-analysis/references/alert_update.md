# analysis alert update

Use when update an alert.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli analysis alert update [options]
```

Capability id: `analysis.alert.update`

Input sends `project_id`, `alert_id`, and `definition_request`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--alert-id` | See command help | Yes |
| `--definition-request` | See command help | Yes |
