# analysis-meta property list

Use when the user needs to browse or search event/user property metadata, including dimension-table and complex child properties.

Do not use it for property values. Use this command only when the user explicitly wants to inspect metadata or when a prior compiler error asks for disambiguation.

Command:

```bash
ae-cli analysis-meta property list --project-id <project_id>
ae-cli analysis-meta property list --project-id <project_id> --scope event --event-name purchase --queries '["demo","sample"]'
ae-cli analysis-meta property list --project-id <project_id> --queries '["demo","sample"]' --fields '["prop_id","prop_name","prop_desc","prop_remark","select_type","table_type","authentication_status"]' --limit 50 --offset 0
ae-cli analysis-meta property list --dry-run
```

Capability id: `metadata.property.list`.

Input sends `project_id` and optional `table_type`, `scope`, `event_name`, `queries`, `fields`, `limit`, `offset`, and `authenticated_only`.

Output always uses the directory envelope: `data.items[]`, `total`, `limit`, `offset`, `has_more`, and `next_offset`. Dimension-table and complex child properties are returned as independent flat rows, so keyword search, field projection, and pagination apply to them in the same way as top-level properties.

## Parameters
| Parameter | Required | Description |
|---|---|---|
| `--project-id` | Yes | Numeric project ID. |
| `--table-type` | No | Optional property table type: `event` or `user`. |
| `--scope` | No | Optional property scope: `event` or `user`. If omitted, all scopes are queried. |
| `--event-name` | No | Optional event name filter for event properties. |
| `--queries` | No | JSON array of 1-20 keyword filters. A row is returned when any keyword matches property name, description, or remark. |
| `--fields` | No | Optional fields to return as a JSON array. Supported fields: `prop_id`, `prop_name`, `prop_desc`, `prop_remark`, `select_type`, `table_type`, `sub_table_type`, `authentication_status`. |
| `--limit` | No | Page size. Default: 50, maximum: 200; values outside 1..200 are rejected. |
| `--offset` | No | Zero-based page offset. Default: 0; negative values are rejected. |
| `--authenticated-only` | No | When true, return only authenticated properties. |

## Decision Rules

- Prefer `--scope event` or `--scope user` when the user needs a specific table type.
- Use `--authenticated-only true` only when the user explicitly asks for authenticated assets.
- For ad-hoc analysis, pass the user's property wording in the AI-facing `definition` instead of pre-querying property metadata.
- For a complete result, use `analysis-meta property export`; do not page repeatedly to synthesize an export.
