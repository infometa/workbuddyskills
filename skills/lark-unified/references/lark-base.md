# Lark-Base - Multi-Dimensional Tables

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Base**: Container for tables (base_id: app_xxx)
- **Table**: Data table within base (table_id: tbl_xxx)
- **Field**: Column definition (field_id: fld_xxx) — text, number, select, date, lookup, formula, etc.
- **Record**: Row in table (record_id: rec_xxx)
- **View**: Saved query/filter on table (view_id: vew_xxx)
- **Workflow**: Automation rules in table

## Resource Hierarchy

```
Base (app_xxx)
├── Table (tbl_xxx)
│   ├── Field (fld_xxx)
│   │   ├── Property (field type, formula, lookup)
│   │   └── Permission
│   ├── Record (rec_xxx)
│   │   ├── Field value
│   │   └── Link to other records
│   ├── View (vew_xxx)
│   │   ├── Filter
│   │   ├── Sort
│   │   └── Group
│   └── Form/Dashboard/Workflow
└── Role/Automation/Notification
```

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+tables-records-list` | List records from table (supports filter, sort, pagination) |
| `+tables-records-create` | Create new record in table |
| `+tables-records-update` | Update existing record |
| `+tables-records-delete` | Delete records |
| `+fields-list` | List all fields in table |
| `+views-list` | List all views in table |

## Typical Workflow

1. **List bases**: `lark-cli base bases list`
2. **List tables**: `lark-cli base tables list --base-id app_xxx`
3. **Get fields**: `lark-cli base +fields-list --base-id app_xxx --table-id tbl_xxx`
4. **Query records**: `lark-cli base +tables-records-list --base-id app_xxx --table-id tbl_xxx --limit 100`
5. **Filter & sort**: `lark-cli base +tables-records-list --base-id app_xxx --table-id tbl_xxx --filter "[condition]" --sort "[sort_spec]"`
6. **Create record**: `lark-cli base +tables-records-create --base-id app_xxx --table-id tbl_xxx --data '{"field_id":"value"}'`
7. **Update record**: `lark-cli base tables records update --base-id app_xxx --table-id tbl_xxx --record-id rec_xxx --data '{...}'`

## Field Types

- Text, Long Text, Email, URL, Phone
- Number (integer, decimal)
- Select (single/multi), Tag
- Date, Time, Datetime
- Checkbox, Rating, Progress
- User, Department, Lookup, Link
- Formula, Rollup, Count
- Attachment, Custom Fields

## API Resources

### bases
- `list` — List all accessible bases
- `get_meta` — Get base metadata

### tables
- `list` — List tables in base
- `get_meta` — Get table metadata
- `create` — Create new table
- `delete` — Delete table

### fields
- `list` — List fields in table
- `get` — Get field definition
- `create` — Create field
- `update` — Update field
- `delete` — Delete field

### records
- `list` — List records (supports filter, sort, pagination)
- `search` — Search records
- `create` — Create record
- `update` — Update record
- `batch_update` — Batch update records
- `delete` — Delete record
- `batch_delete` — Batch delete records

### views
- `list` — List views in table
- `get_meta` — Get view metadata
- `query` — Query view data

### dashboards
- `list` — List dashboards
- `get_meta` — Get dashboard metadata

### workflows
- `list` — List automation workflows
- `trigger` — Manually trigger workflow

## Permission Table

| Method | Required Scope |
|--------|----------------|
| bases.list | bitable:base:read |
| tables.list | bitable:base:read |
| fields.list | bitable:base:read |
| records.list | bitable:base:read |
| records.create | bitable:base:edit |
| records.update | bitable:base:edit |
| records.delete | bitable:base:edit |
| workflows.trigger | bitable:base:edit |

