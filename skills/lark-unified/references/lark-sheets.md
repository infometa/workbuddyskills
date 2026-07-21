# Lark-Sheets - Spreadsheets

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Spreadsheet**: Container for sheets (spreadsheet_id: spr_xxx)
- **Sheet**: Individual worksheet within spreadsheet (sheet_id, sheet_name)
- **Range**: Cell range in A1 notation (e.g., "Sheet1!A1:C10")
- **Cell**: Individual cell with value (row, col)

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+spreadsheets-create` | Create new spreadsheet |
| `+spreadsheets-read` | Read cell values from range |
| `+spreadsheets-append` | Append rows to end of sheet |
| `+spreadsheets-find` | Find cells matching criteria |
| `+spreadsheets-update` | Update specific cells |

## Typical Workflow

1. **Create spreadsheet**: `lark-cli sheets +spreadsheets-create --title "Data"`
2. **Write header row**: `lark-cli sheets +spreadsheets-append --spreadsheet-id spr_xxx --range "Sheet1!A1" --values "[[Header1,Header2,Header3]]"`
3. **Append data**: `lark-cli sheets +spreadsheets-append --spreadsheet-id spr_xxx --values "[[1,2,3],[4,5,6]]"`
4. **Read data**: `lark-cli sheets +spreadsheets-read --spreadsheet-id spr_xxx --range "Sheet1!A1:C100"`
5. **Find values**: `lark-cli sheets +spreadsheets-find --spreadsheet-id spr_xxx --find "SearchTerm"`

## API Resources

### spreadsheets
- `create` — Create spreadsheet
- `query` — Get spreadsheet metadata
- `batch_query` — Batch get spreadsheets
- `update` — Update spreadsheet properties

### spreadsheets.sheets
- `query` — Get sheet properties
- `batch_query` — Batch get sheet info

### spreadsheets.values
- `get` — Read cell range
- `batch_get` — Batch read ranges
- `update` — Update cell range
- `batch_update` — Batch update ranges
- `append` — Append rows
- `clear` — Clear range

### spreadsheets.finds
- `find` — Find cells by value
- `batch_find` — Batch find operations

## Permission Table

| Method | Required Scope |
|--------|----------------|
| spreadsheets.create | sheets:spreadsheet:create |
| spreadsheets.query | sheets:spreadsheet:read |
| spreadsheets.values.get | sheets:spreadsheet:read |
| spreadsheets.values.update | sheets:spreadsheet:edit |
| spreadsheets.values.append | sheets:spreadsheet:edit |
| spreadsheets.finds.find | sheets:spreadsheet:read |

