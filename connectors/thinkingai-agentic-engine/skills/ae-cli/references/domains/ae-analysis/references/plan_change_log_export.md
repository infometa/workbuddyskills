# tracking plan-change-log export

Use when export one tracking plan change log.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking plan-change-log export [options]
```

Capability id: `tracking.plan_change_log.export`

Input sends `project_id`, `log_id`, optional `request_id`, and optional `timeout_seconds`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--log-id` | See command help | Yes |
| `--request-id` | See command help | No |
| `--async-timeout-seconds` | See command help | No |

