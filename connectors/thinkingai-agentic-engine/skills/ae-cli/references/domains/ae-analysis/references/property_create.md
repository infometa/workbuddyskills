# analysis-meta property create

Use when the user needs to create event or user properties and optionally associate events.

Do not use it for virtual properties or description-only updates. Choose `table-type event|user` first because the two payload variants differ.

Command:

```bash
ae-cli analysis-meta property create --project-id <project_id> --table-type event --payload '{"prop_name":"amount","prop_desc":"Amount","select_type":"number","common_prop":false,"super_event_ids":[<event_id>]}'
ae-cli analysis-meta property create --dry-run
```

Capability id: `metadata.property.create`.

Authorization requires the single project function permission `editSuperMeta` with the `metadata:write` scope. In the zh-CN permission UI, this permission is labeled `元数据管理 > 编辑`; the corresponding English label is `Metadata Management > Edit`. This is the same project permission used by `metadata.super_metadata.batch_create`. If either command returns `PROJECT_PERMISSION_DENIED`, do not retry with a different payload and do not describe the two capability IDs as two separate permissions. Ask a project administrator to grant this shared project permission to the current identity.

Input sends `project_id`, `table_type`, `payload`.

Output is a successful gateway envelope with no business data. Read back with `property get` using the same table type.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | Yes | Property table type. |
| `--payload` | Yes | Event form requires `prop_name`, `select_type`; optional `prop_desc`, `prop_remark`, `common_prop`, `super_event_ids`, `source_event_prop`. User form requires `prop_name`, `select_type`; optional `prop_desc`, `prop_remark`, `source_user_prop`. Source objects use `prop_name`, `source_type`, optional `source_route_code`. |
