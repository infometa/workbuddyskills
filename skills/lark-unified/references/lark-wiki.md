# Lark-Wiki - Knowledge Spaces & Documentation

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Space**: Knowledge space container (space_id)
- **Node**: Document/page in space (wiki_token, obj_token)
- **Hierarchy**: Nested page structure
- **Shortcut**: Quick link to document in space
- **obj_type**: Type of node (docx, doc, sheet, bitable, slides, file, mindnote)

## Resource Hierarchy

```
Space (space_id)
└── Node (wiki_token)
    ├── obj_type: docx (cloud document)
    ├── obj_type: sheet (spreadsheet)
    ├── obj_type: bitable (multi-dimensional table)
    ├── obj_type: slides (presentation)
    ├── obj_type: file (regular file)
    └── Child nodes (nested)
```

## Important Note: Wiki Links Require Resolution

Wiki links (wiki_token) cannot be used directly. Must query to get the actual object type and token:

```bash
lark-cli wiki spaces get_node --params '{"token":"wiki_token"}'
# Returns: obj_type, obj_token, title
```

Then use appropriate API based on obj_type (docs, sheets, bitable, drive, etc.).

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+spaces-create` | Create new knowledge space |
| `+wiki-pages-list` | List pages in space |
| `+wiki-pages-create` | Create page in space |

## Typical Workflow

1. **List spaces**: `lark-cli wiki spaces list`
2. **Get space details**: `lark-cli wiki spaces get_meta --space-id space_xxx`
3. **List nodes**: `lark-cli wiki spaces list_nodes --space-id space_xxx`
4. **Query wiki link**: `lark-cli wiki spaces get_node --params '{"token":"wiki_token"}'`
5. **Create page**: `lark-cli wiki spaces create_node --space-id space_xxx --title "New Page" --parent-node-token xxx`
6. **Move node**: `lark-cli wiki spaces move_node --wiki-token xxx --parent-node-token new_parent_xxx`

## API Resources

### spaces
- `list` — List knowledge spaces
- `get_meta` — Get space metadata
- `list_nodes` — List nodes in space
- `get_node` — Get node info (critical: resolves wiki_token to obj_token)
- `create_node` — Create page in space
- `update_node` — Update node properties
- `delete_node` — Delete node
- `move_node` — Move node to different parent
- `copy_node` — Copy node to different parent

### spaces.members
- `create` — Add member to space
- `list` — List space members
- `delete` — Remove member

## Permission Table

| Method | Required Scope |
|--------|----------------|
| spaces.list | wiki:space:read |
| spaces.get_meta | wiki:space:read |
| spaces.list_nodes | wiki:space:read |
| spaces.get_node | wiki:space:read |
| spaces.create_node | wiki:space:create |
| spaces.update_node | wiki:space:edit |
| spaces.delete_node | wiki:space:delete |
| spaces.move_node | wiki:space:edit |

