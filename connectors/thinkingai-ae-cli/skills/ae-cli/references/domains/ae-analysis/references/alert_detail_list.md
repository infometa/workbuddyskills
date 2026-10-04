# analysis alert-detail list

Use when list alert delivery details.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli analysis alert-detail list [options]
```

Capability id: `analysis.alert_detail.list`

Input sends `project_id`, `alert_id`, optional `start_time`, and optional `end_time`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--alert-id` | See command help | Yes |
| `--start-time` | See command help | No |
| `--end-time` | See command help | No |

