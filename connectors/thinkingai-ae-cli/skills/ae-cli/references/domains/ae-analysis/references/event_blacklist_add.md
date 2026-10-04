# tracking event-blacklist add

Use when add events to tracking event blacklist.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking event-blacklist add [options]
```

Capability id: `tracking.event_blacklist.add`

Input sends `project_id` and `event_names`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | See command help | Yes |
| `--event-names` | See command help | Yes |

