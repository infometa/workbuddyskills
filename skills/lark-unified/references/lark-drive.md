# Lark-Drive - Cloud Storage & Files

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Folder**: Directory in cloud storage (folder_token: fldcn_xxx)
- **File**: Document or attachment (file_token, file_key, file_id)
- **Permission**: Access level (viewer, editor, owner)
- **Comment**: Annotation on file

## Resource Hierarchy

```
Folder (folder_token)
└── File (file_token)
    ├── Comment (comment_id)
    ├── Permission (user_id, role)
    └── Resource (attachment/version)
```

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+files-upload` | Upload file to folder |
| `+files-download` | Download file to local system |
| `+files-list` | List files in folder |
| `+files-delete` | Delete file or folder |
| `+files-copy` | Copy file or folder |
| `+files-move` | Move file to different folder |

## Typical Workflow

1. **List files**: `lark-cli drive +files-list --folder-token fldcn_xxx`
2. **Upload file**: `lark-cli drive +files-upload --folder-token fldcn_xxx --local-path "./data.csv"`
3. **Download file**: `lark-cli drive +files-download --file-token xxxxx --local-path "./output/"`
4. **Get permissions**: `lark-cli drive files permissions get --file-token xxxxx`
5. **Share file**: `lark-cli drive files copy --file-token xxxxx`

## API Resources

### files
- `get_meta` — Get file metadata
- `copy` — Copy file
- `delete` — Delete file
- `download` — Download file content
- `upload` — Upload file
- `task_check` — Check async task status

### files.permissions
- `get` — Get file permissions
- `batch_get` — Batch get permissions
- `create` — Grant permission
- `update` — Update permission
- `delete` — Revoke permission

### files.comments
- `create` — Add comment on file
- `get` — Get comment
- `list` — List comments
- `update` — Update comment
- `delete` — Delete comment

### folders
- `create` — Create folder
- `get_meta` — Get folder metadata
- `list_children` — List folder contents
- `delete` — Delete folder
- `copy` — Copy folder

## Permission Table

| Method | Required Scope |
|--------|----------------|
| files.get_meta | drive:file:read |
| files.download | drive:file:read |
| files.upload | drive:file:create |
| files.copy | drive:file:edit |
| files.delete | drive:file:delete |
| files.permissions.* | drive:file:read/edit |
| files.comments.* | drive:file:read/edit |
| folders.* | drive:folder:* |

