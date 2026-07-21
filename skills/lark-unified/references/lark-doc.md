# Lark-Doc - Cloud Documents

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

### Document Types & Tokens

Different document types have different URL formats and token handling:

| URL Format | Example | Token Type | Usage |
|-----------|---------|-----------|-------|
| `/docx/` | `larksuite.com/docx/doxcnxxxxxxx` | file_token | Direct token from URL |
| `/doc/` | `larksuite.com/doc/doccnxxxxxxx` | file_token | Direct token from URL |
| `/wiki/` | `larksuite.com/wiki/wikcnxxxxxxx` | wiki_token | ⚠️ Must query to get obj_token |
| `/sheets/` | `larksuite.com/sheets/shtcnxxxxxxx` | file_token | Direct token from URL |
| `/drive/folder/` | `larksuite.com/drive/folder/fldcnxxxx` | folder_token | Folder token from URL |

### Wiki Link Special Handling (Important!)

Wiki links may point to different document types (docx, doc, sheet, bitable, slides, file, mindnote). **Cannot assume URL token is file_token**.

**Processing flow**:
1. Query node: `lark-cli wiki spaces get_node --params '{"token":"wiki_token"}'`
2. Extract from response: `node.obj_type` (document type) and `node.obj_token` (real token)
3. Use appropriate API based on obj_type

| obj_type | Usage |
|----------|-------|
| docx | `drive file.comments.*`, `docx.*` |
| doc | `drive file.comments.*` |
| sheet | `sheets.*` |
| bitable | `bitable.*` |
| slides | `drive.*` |
| file | `drive.*` |
| mindnote | `drive.*` |

## Reading user-provided documents

When the user gives a document URL and asks to read/summarize it:

1. Prefer `--as user` because the user likely has access even when the bot is not a collaborator.
2. Before reading, run `lark-cli auth status`; if user OAuth is missing, complete `lark-cli auth login --domain all --recommend` first.
3. If `--as user` returns `need_user_authorization`, stop and complete user OAuth. Do not retry the same API with unrelated flags.
4. If `--as bot` returns `forBidden`/`forbidden`, stop bot retries and explain that the bot/app is not a document collaborator. Ask the user to use user OAuth or add the bot/app to the document permissions.

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+docs-create` | Create document from Markdown or plain text |
| `+docs-get` | Get document content |
| `+docs-list` | List documents in workspace |
| `+docs-search` | Search documents by keyword |
| `+docs-update` | Update document (append/replace/insert/delete) |

## API Resources

### docs
- `create` — Create document
- `get` — Get document content
- `list` — List user documents
- `update` — Update document
- `delete` — Delete document
- `raw_content` — Get raw document content

### docx
- `document.blocks.*` — Manage document blocks
- `document.children.*` — Manage child elements

### drive (file operations)
- `file.comments.*` — Manage document comments

## Permission Table

| Method | Required Scope |
|--------|----------------|
| docs.create | docs:document:create |
| docs.get | docs:document:read |
| docs.list | docs:document:read |
| docs.update | docs:document:edit |
| docs.delete | docs:document:delete |
| docx.document.blocks.* | docs:document:read/edit |
| file.comments.* | drive:file:read/write |

