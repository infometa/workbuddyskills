# analysis-meta asset recent-list

Use when the user needs to list recently visited assets for the current user.

Do not use it as a general asset search or as a source of all accessible assets; use `asset search` for keyword discovery.

Command:

```bash
ae-cli analysis-meta asset recent-list --project-id <project_id> --payload '[{"res_id":<resource_id>,"res_cat":"<resource_category>"}]'
ae-cli analysis-meta asset recent-list --dry-run
```

Capability id: `metadata.asset.recent_list`.

Input sends `project_id`, `payload`.

Output `data.resources[]` contains the recent-view records resolved for the supplied resource identities.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--payload` | Yes | Non-empty JSON array of `{res_id,res_cat}` resource identities. This payload is an array, not an object. |
