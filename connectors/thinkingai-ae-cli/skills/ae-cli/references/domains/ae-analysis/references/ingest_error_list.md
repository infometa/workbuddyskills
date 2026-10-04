# tracking ingest-error list

Use when list tracking ingest errors for one data name.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking ingest-error list [options]
```

Capability id: `tracking.ingest_error.list`

Input sends `project_id`, `data_name`, `start_time`, and `end_time`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--data-name` | See command help | Yes |
| `--start-time` | See command help | No |
| `--end-time` | See command help | No |

