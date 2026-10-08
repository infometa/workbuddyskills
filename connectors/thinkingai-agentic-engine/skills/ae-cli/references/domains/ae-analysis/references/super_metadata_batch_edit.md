# analysis-meta super-metadata batch-edit

Use this command to batch edit descriptions and remarks for effective system metadata through the capability gateway.

Do not use it to create metadata, delete metadata, hide metadata, update event/property relations, or edit governance assets. Use batch-create or the dedicated metadata commands instead.

Command:

```bash
ae-cli analysis-meta super-metadata batch-edit --project-id <project_id> --type event_property --items '[{"prop_name":"amount","prop_desc":"Amount","prop_remark":"Revenue amount"}]' --dry-run
```

Capability id: `metadata.super_metadata.batch_edit`.

Input sends `project_id`, `type`, and `items`. For `type=event`, each item identifies the target with `event_name` and may set `event_desc` or `remark`. For `type=event_property` or `type=user_property`, each item identifies the target with `prop_name` and may set `prop_desc` or `prop_remark`.

Output returns `type` and `updated_count`. Preserve validation errors from common-service, especially missing names, unsupported `type`, or empty `items`.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--type` | Yes | Metadata type to edit: `event`, `event_property`, or `user_property`. |
| `--items` | Yes | Batch edit item JSON array. |
