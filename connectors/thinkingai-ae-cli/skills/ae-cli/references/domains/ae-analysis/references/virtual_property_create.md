# analysis-meta virtual-property create

Use when the user needs to create a SQL virtual event or user property.

Do not use it for physical/super properties.

Before building `--sql-expression` / `--related-events`, validate available properties and events with `analysis-meta property list` and `analysis-meta event list` in the same `project_id`.

Command:

```bash
ae-cli analysis-meta virtual-property create --project-id <project_id> --property-name '#vp@demo' --table-type event --select-type string --sql-expression 'event_name' --sql-event-relation-type relation_default
ae-cli analysis-meta virtual-property create --project-id <project_id> --property-name '#vp@demo' --property-desc demo --table-type event --select-type string --sql-expression "CASE WHEN status = 1 THEN 'active' ELSE 'inactive' END" --sql-event-relation-type relation_by_setting --related-events '[{"eventName":"purchase"}]' --property-remark demo
ae-cli analysis-meta virtual-property create --project-id <project_id> --sql-expression '<sql>' --v-prop '{"property":{"column_name":"#vp@demo","table_type":"event","select_type":"string"}}' --properties '[...]'
ae-cli analysis-meta virtual-property create --project-id <project_id> --sql-expression '<sql>' --v-prop '{...}' --dry-run
```

Capability id: `metadata.virtual_property.create`.

Input sends typed snake_case fields.

Output is a successful gateway envelope with no business data.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--sql-expression` | Yes | SQL expression used to calculate the virtual property. |
| `--v-prop` | No | Full virtual property JSON object with `property.column_name`, `property.table_type`, and `property.select_type`. All three fields belong inside `property`; use typed property flags unless an exact DTO is already available. |
| `--property-name` | No | Virtual property name. Must start with `#vp@`. Required when `--v-prop` is omitted. |
| `--property-desc` | No | Virtual property display name. |
| `--table-type` | No | Property table type: `event` or `user`. Required when `--v-prop` is omitted. |
| `--select-type` | No | Property value type: `string`, `number`, `bool`, or `datetime`. Required when `--v-prop` is omitted. |
| `--property-remark` | No | Optional virtual property remark. |
| `--properties` | No | Dependent property JSON array. |
| `--sql-event-relation-type` | No | `relation_default`, `relation_always`, or `relation_by_setting`. |
| `--related-events` | No | Related events JSON array for `relation_by_setting`. |
| `--tag-date-policies` | No | Tag date policies JSON array. |
| `--replace-remark` | No | Replacement remark. |
| `--replace-suggestion` | No | Replacement suggestion. |

## Decision Rules
- `sql_expression` / `related_events` cannot be written from experience alone; they must be built from real project metadata.
- For first validation, pass only required typed parameters: `--project-id`, `--property-name`, `--table-type`, `--select-type`, `--sql-expression`, and `--sql-event-relation-type`.
- If `--sql-event-relation-type=relation_by_setting`, `--related-events` must contain event names from `analysis-meta event list`.
- Columns starting with `#` or containing `@` should be double-quoted in Trino SQL.
- Use `--v-prop` only when an exact virtual property DTO is already available.
- This is an ordinary write operation; execute it without the high-risk confirmation flag.

## Recommended Chain
- `analysis-meta property list` -> `analysis-meta virtual-property create`
- `analysis-meta property list` -> `analysis-meta event list` -> `analysis-meta virtual-property create` when using `relation_by_setting`
