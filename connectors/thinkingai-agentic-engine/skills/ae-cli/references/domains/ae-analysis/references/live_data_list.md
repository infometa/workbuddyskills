# tracking live-data list

Use when list recent tracking live data.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking live-data list [options]
```

Capability id: `tracking.live_data.list`

Input sends `project_id`, optional `data_type`, optional `request_id`, and optional `timeout_seconds`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--data-type` | See command help | No |
| `--request-id` | See command help | No |
| `--timeout-seconds` | See command help | No |

