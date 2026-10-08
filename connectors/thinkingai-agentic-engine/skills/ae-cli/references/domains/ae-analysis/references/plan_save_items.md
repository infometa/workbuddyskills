# tracking plan save-items

Use when save tracking plan items.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking plan save-items --project-id <project_id> [--events '<json_array>'] [--event-props '<json_array>'] [--user-props '<json_array>'] [--common-event-props '<json_array>']
```

Capability id: `tracking.plan.save_items`

Input sends `project_id` and the provided `events`, `event_props`, `user_props`, and `common_event_props` arrays. At least one item array must be non-empty. Event/property objects use the existing tracking-plan snake_case contract; do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | Numeric project ID. | Yes |
| `--events` | Event objects with fields such as `event_name`, `display_name`, `event_desc`, `event_tag`, `data_origin`, and `props`. | No |
| `--event-props` | Event property objects with fields such as `name`, `display_name`, `type`, and `desc`. | No |
| `--user-props` | User property objects with fields such as `name`, `display_name`, `type`, `update_type`, `prop_tag`, and `desc`. | No |
| `--common-event-props` | Common event property objects. | No |
