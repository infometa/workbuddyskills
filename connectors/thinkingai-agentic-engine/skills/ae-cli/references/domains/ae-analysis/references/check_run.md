# tracking check run

Use when run tracking plan validation.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking check run --project-id <project_id> --check-scope '<json_object>' [--result-scope '<json_object>']
```

Capability id: `tracking.check.run`

Input sends `project_id`, required `check_scope`, and optional `result_scope`. `check_scope` supports `check_data_types`, `start_time`, `end_time`, `check_events`, `event_filter`, `user_filter`, `has_empty_check`, and `prop_null_value_threshold`. `result_scope` supports `event_results` and `user_results`. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | Numeric project ID. | Yes |
| `--check-scope` | Tracking data scope and validation thresholds. | Yes |
| `--result-scope` | Event/user result categories to return. | No |
