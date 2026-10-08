# analysis-meta super-metadata batch-create

Use this command to create effective system metadata in batch through the capability gateway: super events, event properties, and user properties.

Do not use it for ordinary event/property CRUD, metadata import from XLSX, or asset governance. Use the dedicated event/property commands, event-property-bundle import, or governance commands instead.

Command:

```bash
ae-cli analysis-meta super-metadata batch-create --project-id <project_id> --events '[{"event_name":"purchase","event_desc":"Purchase"}]' --event-properties '[{"prop_name":"amount","select_type":"number","super_event_names":["purchase"]}]' --dry-run
```

Capability id: `metadata.super_metadata.batch_create`.

Authorization requires the single project function permission `editSuperMeta` with the `metadata:write` scope. In the zh-CN permission UI, this permission is labeled `元数据管理 > 编辑`; the corresponding English label is `Metadata Management > Edit`. This is the same project permission used by `metadata.property.create`. If either command returns `PROJECT_PERMISSION_DENIED`, do not retry with a different payload and do not describe the two capability IDs as two separate permissions. Ask a project administrator to grant this shared project permission to the current identity.

Input sends `project_id` plus any non-empty JSON arrays among `events`, `event_properties`, and `user_properties`. Use snake_case object fields exactly as documented by the common-service schema:

- Event items: `event_name`, optional `event_desc`, optional `remark`, optional `super_event_prop_names`.
- Event property items: `prop_name`, `select_type`, optional `prop_desc`, optional `prop_remark`, optional `common_prop`, optional `super_event_names`.
- User property items: `prop_name`, `select_type`, optional `prop_desc`, optional `prop_remark`.

Output returns `created.events`, `created.event_properties`, and `created.user_properties` with created names and IDs, plus count metadata. If common-service rejects a duplicate, bad reference, or invalid type, preserve the gateway error code and message.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--events` | No | Super event JSON array. |
| `--event-properties` | No | Event property JSON array. |
| `--user-properties` | No | User property JSON array. |
