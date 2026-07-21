---
name: lark-unified
description: "Unified Lark/Feishu CLI suite covering messaging, documents, collaboration, scheduling, and more. Provides 200+ commands across 11 business domains including instant messaging (IM), cloud documents, spreadsheets, base/tables, calendars, mail, tasks, wikis, video conferences, and custom integrations. Use when working with Lark/Feishu through CLI or needing to understand Lark API capabilities for: sending/receiving messages, managing documents and files, creating spreadsheets, managing tasks and calendars, searching conversations, building custom workflows, or accessing any Lark business application."
description_zh: "飞书/Lark 全能套件（消息、文档、表格、日历、任务、Wiki 等 11 个业务域）"
description_en: "Lark/Feishu unified CLI: messaging, docs, sheets, calendar, tasks, wiki & more"
version: "1.0.3"
allowed-tools: Bash, Read
---

# Lark Unified

Lark (飞书) is a comprehensive collaboration platform combining messaging, documents, spreadsheets, tables, calendars, and more. This skill provides unified access to the **Lark CLI** (`lark-cli`), a production-grade command-line tool with 200+ commands across 11 integrated business domains, along with 19 AI Agent-optimized skills.

## ⚠️ SETUP RULES — READ BEFORE DOING ANYTHING

**FORBIDDEN — never run these commands under any circumstances:**
- `lark-cli config init --new`
- `lark-cli config init` (interactive)
- `lark-cli config set-default`

These require a TTY, output a broken QR code in WorkBuddy, and must never be used.

**REQUIRED setup procedure — follow exactly:**

```bash
# Step 1: resolve or install lark-cli
LARK_CLI="$(command -v lark-cli || true)"
if [ -z "$LARK_CLI" ]; then
  env -u NODE_OPTIONS npm install -g @larksuite/cli
  LARK_CLI="$(command -v lark-cli || true)"
fi
if [ -z "$LARK_CLI" ]; then
  NPM_PREFIX="$(npm prefix -g 2>/dev/null || true)"
  LARK_CLI="$(find "$HOME/.npm-global/bin" "$NPM_PREFIX/bin" -name lark-cli -type f 2>/dev/null | head -1)"
fi
if [ -z "$LARK_CLI" ]; then
  echo "LARK_CLI_NOT_FOUND"
  exit 1
fi
"$LARK_CLI" --version

# Step 2: check if already configured (look for "appId" in output, NOT exit code)
"$LARK_CLI" config show 2>&1 | grep -q "appId" && echo "CONFIG_OK" || echo "NOT_CONFIGURED"
```

If step 2 prints `NOT_CONFIGURED`, run the setup script:

```bash
SETUP=$(find ~/.workbuddy/skills -name lark_setup.py 2>/dev/null | head -1)
LARK_CLI="$LARK_CLI" python3 "$SETUP"

# Lark (international) users:
LARK_CLI="$LARK_CLI" python3 "$SETUP" --brand lark

# If browser cannot open automatically:
# Print the URL clearly, ask the user to open it in a browser, and keep this command running while it polls.
LARK_CLI="$LARK_CLI" python3 "$SETUP" --no-browser
```

**IMPORTANT: The setup script is a multi-step device flow.**
- Step 1 (begin): The script requests a device code from Feishu. This call may return HTTP 400 transiently — **this is normal, just retry**.
- Step 2 (browser): The script opens a browser URL for the user to authorize.
- Step 3 (poll): The script polls until the user completes authorization in the browser. The poll API returns `authorization_pending` (as HTTP 400) while waiting — **this is expected, NOT an error**. Keep polling.
- Step 4 (save): Once authorized, the script saves the config.

**If the setup script fails or you ran the begin step manually:**
1. You already have the `device_code` — just keep polling with it until the user confirms in the browser.
2. Do NOT re-run the begin step unnecessarily. Reuse the existing device_code.
3. The `authorization_pending` response during polling is **normal** — it means the user hasn't finished yet. Wait and retry.

**CRITICAL: App setup is not user OAuth.** The setup script only creates/saves the app credentials. It does **not** guarantee the user is logged in. For personal data operations such as reading a user's accessible document, calendar, mail, task, or chat history, always check `auth status` first and complete user OAuth if needed.

## First-use bootstrap — app setup + user OAuth must be chained

When the user asks for a personal-resource operation (for example reading a document URL, searching docs, checking calendar, mail, tasks, or chat history), the first-use flow MUST complete both stages before attempting the business API:

1. **Resolve/install `lark-cli`** using the setup procedure above.
2. **Check app configuration** with `config show`.
3. If app configuration is missing, run `lark_setup.py` and keep polling until it saves `appId/appSecret`.
4. **Do not stop after app setup.** Immediately run `auth status`.
5. If `auth status` reports no logged-in user, run user OAuth with recommended scopes.
6. Keep polling the same `device_code` until OAuth succeeds or expires.
7. Run `auth status` again and confirm `identity` is `user` and `tokenStatus` is `valid` or refreshable.
8. Only then retry the original user task once.

Tell the user the first-use flow may show two authorization pages:

> 第一次使用飞书套件需要完成两步连接：先初始化飞书 CLI 应用配置，再授权访问你有权限的飞书数据。两步完成后我会自动继续当前任务；这不是重复授权。

Use this exact command pattern after app setup succeeds:

```bash
# App setup may have just completed. Now continue with user OAuth; do not wait for another user prompt.
"$LARK_CLI" auth status
"$LARK_CLI" auth login --domain all --recommend --no-wait --json
"$LARK_CLI" auth login --device-code "<device_code>"
"$LARK_CLI" auth status
```

If the user OAuth device flow prints a `verification_url`, show that URL clearly and keep the polling command running. Do not start a new app setup or user OAuth flow while `authorization_pending` is still polling.

**CRITICAL: polling timeout must outlive the device code.** Device codes commonly expire after 10 minutes. When running `lark_setup.py` or `lark-cli auth login --device-code`, use a tool timeout longer than `expires_in` (recommended at least 700000 ms / 11+ minutes) or run the polling command in the background. If the polling command is interrupted by a tool timeout but the device code has not expired, reuse the same `device_code` and continue polling; do not start a new `--no-wait` or app setup flow. Only generate a new code after `expired_token`, `invalid_grant`, or a confirmed deadline expiry.

## Fail-fast rules for auth and permission errors

Stop retrying business APIs when any of these errors appears. Do not switch identities or change unrelated flags repeatedly.

| Error signal | Meaning | Required action |
|---|---|---|
| `need_user_authorization` / `No user logged in` / `failed to get access token` | User OAuth is missing or expired | Stop API retries. Run user device-flow login, show the verification URL clearly, keep polling with the same `device_code`, then rerun `auth status`. |
| `forBidden` / `forbidden` with `--as bot` | The bot/app is not authorized for the target resource, commonly because it is not a document collaborator | Stop bot retries. Use `--as user` after user OAuth, or ask the user to add the bot/app as a collaborator to the document/resource. |
| `App scope not enabled` / `required scope ...` | The current app has not enabled the required Open Platform scope; user OAuth alone cannot grant it | Stop retries. Tell the user/admin which scope must be enabled in the Feishu developer console, then retry after the app scope is enabled and OAuth includes it. |
| `authorization_pending` | The user has not finished the browser authorization yet | Keep the existing polling command running. Do not start a new setup/login flow unless the device code expires. |
| `expired_token` / `invalid_grant` | The device code expired | Start exactly one new login/setup flow and give the user the new URL. |

**Retry budget:** after one failed business API call with an auth/permission error, diagnose and switch to the required auth step. Never perform repeated API attempts with `--as user`, `--as bot`, `--format`, or unrelated command variants.

## Getting Started

```bash
# Verify app setup is complete
"$LARK_CLI" config show

# Verify user authorization status
"$LARK_CLI" auth status
```

If `auth status` reports no logged-in user and personal operations are needed, run the recommended-scope login. Before starting, tell the user clearly:

> 本次将连接飞书并授权推荐权限范围，覆盖多数常见飞书操作。由于飞书权限按能力拆分，后续执行文档搜索、云盘检索、导出等更具体操作时，仍可能需要补充授权；补充授权不是重新连接，而是为当前新增能力追加 scope。

```bash
# Start user device-flow login for recommended scopes across domains
"$LARK_CLI" auth login --domain all --recommend --no-wait --json

# Tell the user: "请复制并打开 verification_url，在浏览器里完成飞书授权。"
# Then keep polling with the returned device_code until success or timeout.
"$LARK_CLI" auth login --device-code "<device_code>"

# Verify tokenStatus is valid and identity is user before reading personal resources
"$LARK_CLI" auth status
```

**When additional scopes are needed:** `--scope` cannot be combined with `--domain` or `--recommend`. Do not replace recommended login with a tiny explicit scope set unless you are intentionally narrowing the token. For a supplemental authorization, explain the exact missing capability and scope to the user, for example:

> 当前任务需要补充授权：飞书文档搜索权限 `search:docs:read`。授权后，后续搜索飞书文档不会再次要求这个权限。

Then run an explicit-scope login for the missing scope or for a maintained capability bundle, and verify with `auth status` before retrying the business API once.

All commands:
```bash
lark-cli <domain> <resource> <method> [flags]
lark-cli <domain> +<shortcut> [flags]  # shortcuts preferred
```

**Default identity**: `--as auto`. It uses the logged-in user when available and falls back to bot identity when no user is logged in. For personal resources (docs the user can open, calendar, mail, tasks, chat history), prefer `--as user` after `auth status` is valid. Use `--as bot` only for app/bot operations or resources where the bot is explicitly a member/collaborator.

## Document creation identity rules

- Default to `--as user` for user-requested docs/sheets so the user owns them.
- Use `--as bot` only when the user explicitly asks for bot/app-owned content.
- If a bot-created doc must be shared, add user permission; this requires `docs:permission.member:create`. If that scope is not enabled, stop and ask an admin to enable it.

## Core Capability Domains

Lark has 11 primary business domains. Each has dozens of commands, with high-level shortcuts for common operations:

### ✉️ Instant Messaging (lark-im)
Send/receive messages, search chat history, manage groups, download files, and manage reactions.

**Common shortcuts**: `+messages-send`, `+messages-search`, `+chat-messages-list`, `+chat-create`

**Use when**: Messaging users, retrieving conversations, building chat-based workflows, downloading attachments

→ **For detailed API reference, shortcuts, and permission requirements**: See [references/lark-im.md](references/lark-im.md)

### 📄 Cloud Documents (lark-doc)
Create and edit documents, insert media, manage document permissions, and link to wikis.

**Common shortcuts**: `+documents-create`, `+documents-list`

**Use when**: Creating documents programmatically, building document workflows, embedding content

→ **For full reference**: See [references/lark-doc.md](references/lark-doc.md)

### 💾 Cloud Drive & Files (lark-drive)
Upload/download files, manage file permissions, share links, and add comments on files.

**Common shortcuts**: `+files-upload`, `+files-download`

**Use when**: Managing file storage, automating uploads/downloads, sharing files

→ **For full reference**: See [references/lark-drive.md](references/lark-drive.md)

### 📊 Spreadsheets (lark-sheets)
Read/write/append to spreadsheets, query data, and manage sheet permissions.

**Common shortcuts**: `+spreadsheets-read`, `+spreadsheets-append`, `+spreadsheets-find`

**Use when**: Automating spreadsheet operations, reading/updating sheet data, building data workflows

→ **For full reference**: See [references/lark-sheets.md](references/lark-sheets.md)

### 🗂️ Base & Multi-Dimensional Tables (lark-base)
Query and manage multi-dimensional table records, fields, views, dashboards, and run workflows.

**Common shortcuts**: `+tables-records-list`, `+tables-records-create`, `+fields-list`

**Use when**: Managing relational data, querying tables, automating base operations, triggering workflows

→ **For full reference**: See [references/lark-base.md](references/lark-base.md)

### 📅 Calendar (lark-calendar)
Query events, check availability, suggest meeting times, and manage calendar settings.

**Common shortcuts**: `+calendars-list`, `+events-list`, `+events-search-freebusy`

**Use when**: Checking schedules, coordinating meetings, finding available time slots

→ **For full reference**: See [references/lark-calendar.md](references/lark-calendar.md)

### 📋 Tasks & To-Do (lark-task)
Create tasks, organize into lists, manage reminders, and track subtasks.

**Common shortcuts**: `+tasks-create`, `+tasks-list`, `+task-lists-list`

**Use when**: Creating tasks, building task workflows, managing team task lists

→ **For full reference**: See [references/lark-task.md](references/lark-task.md)

### 📧 Mail (lark-mail)
Compose emails, manage drafts, search messages, reply/forward, and send emails.

**Common shortcuts**: `+messages-send`, `+messages-search`, `+drafts-create`

**Use when**: Building email workflows, automating mail operations, searching email history

→ **For full reference**: See [references/lark-mail.md](references/lark-mail.md)

### 📚 Wiki & Knowledge Spaces (lark-wiki)
Create knowledge spaces, organize pages into hierarchies, and manage wiki permissions.

**Common shortcuts**: `+spaces-create`, `+wiki-pages-create`, `+wiki-pages-list`

**Use when**: Building knowledge bases, organizing documentation, creating wikis

→ **For full reference**: See [references/lark-wiki.md](references/lark-wiki.md)

### 🎥 Video Conference & Meetings (lark-vc)
Search meeting recordings, retrieve meeting notes, and manage VC settings.

**Use when**: Accessing meeting data, retrieving recordings and notes, managing video settings

→ **For full reference**: See [references/lark-vc.md](references/lark-vc.md)

### 👥 Contacts & Directory (lark-contact)
Search users, fetch contact profiles, and query user directory.

**Use when**: Searching for users, building user lookups, retrieving contact information

→ **For full reference**: See [references/lark-contact.md](references/lark-contact.md)

## Core Concepts & Common Patterns

### Identity & Authentication

- **User identity** (`--as user`): Operations run as the authenticated user. Uses `user_access_token`. Permissions depend on the user's own access.
- **Bot identity** (`--as bot`): Operations run as the app's bot. Uses `tenant_access_token`. Permissions depend on the bot's scopes and membership.

Most APIs support both modes, but behavior differs based on the caller's role and access.

### Common Entity IDs

- **User**: `open_id`, `user_id`, `email`
- **Chat**: `chat_id` (oc_xxx)
- **Message**: `message_id` (om_xxx)
- **Thread**: `thread_id`
- **Document**: `document_id`
- **File**: `file_key` or `file_id`
- **Table/Base**: `base_id`, `table_id`
- **Event**: `event_id`

### Working with the CLI

#### Using Shortcuts (Recommended)
Shortcuts are high-level wrappers around common operations. Always use shortcuts when available:
```bash
lark-cli im +messages-send --chat-id oc_xxx --text "Hello"
lark-cli sheets +spreadsheets-read --spreadsheet-id spr_xxx
```

#### Using Raw APIs
For operations without shortcuts, use raw API commands with schema inspection:
```bash
lark-cli schema im.messages.create       # View parameter structure
lark-cli im messages create --data '{...}'  # Call with structured data
```

**Important**: Always run `schema` before calling raw APIs to understand the exact parameter format.

#### Pagination & Filtering
Most list operations support:
- `--limit`: Number of records to return (default varies by API)
- `--offset` / `--page-token`: Pagination cursor
- `--filter`: Server-side filtering (format varies by resource)

#### Output Formatting
By default, commands return JSON. Common options:
- `--table`: Format output as ASCII table
- `--csv`: Export as CSV
- `--yaml`: YAML format
- `--raw`: Unformatted raw output

### Workflows

Lark offers two built-in workflow skills:
- **Meeting Summary Workflow** (`lark-workflow-meeting-summary`): Aggregate meeting notes
- **Standup Report Workflow** (`lark-workflow-standup-report`): Generate daily standup summaries

See `references/workflows.md` for details.

## Advanced Features

### Custom Skills & Integrations

Use `lark-skill-maker` to create custom skills by wrapping Lark APIs. See `references/skill-maker.md`.

### OpenAPI Discovery

Use `lark-openapi-explorer` to discover and test Lark APIs directly. See `references/openapi.md`.

### Event Subscriptions

Subscribe to real-time events via WebSocket with `lark-event`. See `references/events.md`.

### Other Domains

- **Minutes**: Meeting minutes metadata (`lark-minutes`)
- **Whiteboard**: Drawing/diagram creation with DSL (`lark-whiteboard`)
- **Shared**: Core authentication rules and identity management (`lark-shared`)

See `references/other-domains.md` for details.

## Quick Example

### Send a message to a chat
```bash
# First, find the chat
lark-cli im +chat-search --keyword "engineering"

# Then send a message
lark-cli im +messages-send --chat-id oc_xxx --text "Hello team!"
```

### Search past messages
```bash
lark-cli im +messages-search --query "deadline" --from-user ou_xxx --start-time 2024-01-01 --end-time 2024-01-31
```

### Create a spreadsheet and add data
```bash
lark-cli sheets +spreadsheets-create --title "Q1 Data"
lark-cli sheets +spreadsheets-append --spreadsheet-id spr_xxx --range "Sheet1!A1" --values "[[1,2,3]]"
```

### Query a base table
```bash
lark-cli base +tables-records-list --base-id app_xxx --table-id tbl_xxx --limit 100
```

## Need Help?

- **View all domains**: `lark-cli --help`
- **Domain-specific help**: `lark-cli <domain> --help`
- **Inspect API schema**: `lark-cli schema <domain>.<resource>.<method>`
- **Permission requirements**: Check the permission tables in each domain's reference file

## Next Steps

1. **Choose your domain** from the list above
2. **Read the domain reference** (linked in each section)
3. **Use shortcuts** for common operations
4. **Inspect schemas** if using raw APIs
5. **Check permissions** in the reference documentation

