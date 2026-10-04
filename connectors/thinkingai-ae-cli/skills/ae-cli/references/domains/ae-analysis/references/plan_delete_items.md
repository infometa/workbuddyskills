# tracking plan delete-items

Use when delete tracking plan items.

Do not use for commands listed under the sheet's non-CLI section or for unrelated metadata/report operations. If the command needs a complex JSON object, read the backend schema or existing asset first and send snake_case fields only.

Command:

```bash
ae-cli tracking plan delete-items --project-id <project_id> [--events '<json_array>'] [--event-prop-names '<json_array>'] [--user-prop-names '<json_array>'] [--common-event-prop-names '<json_array>'] --confirm true --dry-run
# Summarize the target and impact, then wait for explicit user confirmation.
ae-cli tracking plan delete-items --project-id <project_id> [--events '<json_array>'] [--event-prop-names '<json_array>'] [--user-prop-names '<json_array>'] [--common-event-prop-names '<json_array>'] --confirm true --yes
```

Capability id: `tracking.plan.delete_items`

Input sends `project_id`, the provided name arrays, and `yes` mapped from `--confirm`. At least one name array must be non-empty. Do not send camelCase aliases.

Output is the capability gateway envelope: success is `ok=true,data,meta`; failure is `ok=false,error`. Export commands return lifecycle data such as `run_id` and `artifact_id` for inspect/download.

Parameters:

| Parameter | Description | Required |
| --- | --- | --- |
| `--project-id` | Numeric project ID. | Yes |
| `--events` | Event names to delete. | No |
| `--event-prop-names` | Event property names to delete. | No |
| `--user-prop-names` | User property names to delete. | No |
| `--common-event-prop-names` | Common event property names to delete. | No |
| `--confirm` | Must be `true`; execution also follows the global high-risk confirmation gate. | Yes |
