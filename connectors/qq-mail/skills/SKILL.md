---
name: qq-mail
description: "QQ邮箱(QQ Mail)全功能操作技能。触发场景：看邮箱、查邮件、收件箱、看看邮件、有没有新邮件、未读邮件、帮我看看邮箱、打开邮箱、最近的邮件、邮件列表、发邮件、写邮件、发一封邮件、回复邮件、转发邮件、删除邮件、搜邮件、找邮件、搜索邮箱、下载附件、邮件附件、check email、inbox、send email、reply、forward、search mail、attachments。覆盖：收发邮件、搜索、附件下载、回复转发删除等所有邮箱操作。All QQ Mail operations MUST go through the qq-mail MCP server tools."
---

# QQ Mail Skill

This skill enables the agent to operate QQ Mail on behalf of the user via the **qqmail MCP server**. All email operations MUST be performed by calling qqmail MCP tools directly.

The qqmail MCP server and its authorization are managed by the QQ Mail Connector — token management is handled by the Connector, not by this skill.

---

## Required Call Sequence

### Always call GetMe first (at session start)

Before any operation, call `GetMe` to obtain the `alias_id` required by all other tools, and to understand available permissions and limits.

```
Tool: GetMe
Arguments: (none)
```

Example response (based on real API):
```json
{
  "data": {
    "scopes": ["alias:read", "mail:read", "mail:send"],
    "aliases": [
      { "alias_id": "alias_q8Mxe-...", "email": "darranadamchou@qq.com", "name": "darranadamchou", "is_primary": true },
      { "alias_id": "alias_2XZMj...", "email": "609709286@qq.com", "is_primary": false }
    ],
    "rate_limits": {
      "requests_per_minute": 10,
      "requests_per_hour": 200,
      "daily_send_quota": 2000
    },
    "constraints": {
      "max_attachment_size_bytes": 1048576,
      "max_total_attachments_size_bytes": 3145728,
      "max_attachment_count": 3
    }
  }
}
```

Key fields:
- `aliases[].alias_id` — required for all other tool calls; use the one where `is_primary: true` by default unless the user specifies otherwise
- `aliases[].email` — the actual email address of this alias
- `scopes` — confirms which operations are permitted; check before calling tools:
  - `mail:read` → ListMessages, GetMessage, SearchMessages, ListAttachments, DownloadAttachment
  - `mail:send` → SendMessage, ReplyMessage, ForwardMessage
  - `mail:delete` → DeleteMessage (if missing, DeleteMessage will return 403)
- `constraints` — actual attachment limits to enforce: max 3 files, 1 MB per file, ~3 MB total

---

## Tool Reference

### GetMe

Bootstrap endpoint. Call this first in every session.

```
Tool: GetMe
Required: (none)
```

---

### ListMessages

List emails in a folder with optional filters.

```
Tool: ListMessages
Required:
  alias_id: "alias_abc123"        # from GetMe

Optional:
  dir: "inbox"                    # inbox | sent | trash | spam
  limit: 20                       # max 50, default 10
  cursor: "<cursor>"              # omit for first page; use value from previous response for next page
  after: "2026-01-01T00:00:00Z"  # ISO 8601, only messages after this time
  before: "2026-04-01T00:00:00Z" # ISO 8601, only messages before this time
  has_attachments: true           # true = with attachments only
  is_read: false                  # true = read only, false = unread only
```

---

### GetMessage

Retrieve full content of a single email.

```
Tool: GetMessage
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"      # from ListMessages or SearchMessages
```

Note: Returns attachment metadata (id, filename, size) but NOT file content. To get file content, call `DownloadAttachment` separately.

---

### SearchMessages

Search emails by keyword, sender, recipient, date, or folder.

```
Tool: SearchMessages
Required:
  alias_id: "alias_abc123"        # from GetMe

Optional:
  q: "project report"             # search keyword or phrase
  search_in: "SEARCH_IN_ALL"      # SEARCH_IN_ALL (default) | SEARCH_IN_SUBJECT | SEARCH_IN_CONTENT
                                  # Use SEARCH_IN_SUBJECT when user says "search in subject/title"
                                  # Use SEARCH_IN_CONTENT when user says "search in body/content"
  from: "boss@example.com"        # filter by sender email
  to: "me@qq.com"                 # filter by recipient email
  dir: "inbox"                    # inbox | sent | trash | spam
  after: "2026-01-01T00:00:00Z"
  before: "2026-04-01T00:00:00Z"
  has_attachments: true
  is_read: false
  limit: 20                       # max 50, default 10
  cursor: "<cursor>"
```

---

### ListAttachments

List attachment metadata for an email without downloading content.

```
Tool: ListAttachments
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"
```

Returns: attachment IDs (`att_`-prefixed), filenames, MIME types, file sizes. Use before `DownloadAttachment` to confirm attachment IDs.

---

### DownloadAttachment

Download attachment content as Base64-encoded data.

```
Tool: DownloadAttachment
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"
  attachment_id: "att_xxxxxxxx"   # from GetMessage or ListAttachments
```

After download, verify data integrity using the SHA-1 checksum if provided.

---

### SendMessage

Send a new email. **Requires two-phase confirmation — see section below.**

```
Tool: SendMessage
Required:
  alias_id: "alias_abc123"        # from GetMe; identifies the sender
  to:                             # at least one recipient required
    - email: "recipient@example.com"
      name: "Name"                # optional
  subject: "Email subject"        # max 998 characters
  body: "Email body content"

Optional:
  cc:
    - email: "cc@example.com"
  bcc:
    - email: "bcc@example.com"
  body_format: "PLAIN"            # PLAIN (default) | HTML
  confirmation_token: "<token>"   # ONLY include after user confirms; obtained from Phase 1 response
  attachments:                    # max 3 files, 1MB each, 3MB total
    - filename: "report.pdf"
      content_type: "application/pdf"
      content: "<base64-encoded>"
      size: 102400                # original file size in bytes
      sha1: "abc123..."           # SHA-1 hex hash of original file
```

---

### ReplyMessage

Reply to an existing email. **Requires two-phase confirmation.**

```
Tool: ReplyMessage
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"      # the message being replied to
  body: "Reply content"

Optional:
  body_format: "PLAIN"            # PLAIN (default) | HTML
  reply_all: false                # true = reply to all original recipients; false = reply to sender only
  cc:
    - email: "cc@example.com"
  bcc:
    - email: "bcc@example.com"
  confirmation_token: "<token>"   # ONLY include after user confirms
  attachments:                    # max 3 files, 1MB each
    - filename: "file.pdf"
      content_type: "application/pdf"
      content: "<base64-encoded>"
      size: 102400
      sha1: "abc123..."
```

---

### ForwardMessage

Forward an email to new recipients. **Requires two-phase confirmation.**

```
Tool: ForwardMessage
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"      # the message to forward
  to:
    - email: "newrecipient@example.com"

Optional:
  cc:
    - email: "cc@example.com"
  bcc:
    - email: "bcc@example.com"
  body: "FYI — see below"         # optional note prepended to the forwarded content
  body_format: "PLAIN"            # PLAIN (default) | HTML
  include_attachments: true       # true = include original attachments; false = text only
  confirmation_token: "<token>"   # ONLY include after user confirms
  attachments:                    # additional attachments beyond original (max 3, 1MB each)
    - filename: "extra.pdf"
      content_type: "application/pdf"
      content: "<base64-encoded>"
      size: 102400
      sha1: "abc123..."
```

---

### DeleteMessage

Move an email to trash. **Requires two-phase confirmation.**

> ⚠️ **Permission note**: DeleteMessage requires the `mail:delete` scope. If `GetMe` shows only `alias:read, mail:read, mail:send` (no `mail:delete`), the API will return HTTP 403. In this case, inform the user that the current authorization does not include delete permission and guide them to re-authorize with the `mail:delete` scope.

```
Tool: DeleteMessage
Required:
  alias_id: "alias_abc123"        # from GetMe
  message_id: "msg_xxxxxxxx"

Optional:
  confirmation_token: "<token>"   # ONLY include after user confirms
```

Soft delete only — messages remain in trash for 30 days before permanent deletion.

---

## Two-Phase Confirmation (Critical)

`SendMessage`, `ReplyMessage`, `ForwardMessage`, and `DeleteMessage` all require explicit user confirmation before execution.

### Phase 1 — Get preview

Call the tool **without** `confirmation_token`. The API returns HTTP 428 with:

```json
{
  "confirmation_token": "ctk_xxxxxxxx",
  "operation_summary": {
    "from": "user@qq.com",
    "to": ["recipient@example.com"],
    "subject": "Email subject",
    "attachment_count": 1
  }
}
```

Display the full `operation_summary` in an `AskUserQuestion` confirmation card and ask for explicit confirmation. Do NOT ask for confirmation in plain chat text.

### Actual MCP error shape in WorkBuddy

In WorkBuddy connector mode, the first call may be returned as a tool error with
business code `42801` instead of a plain top-level `confirmation_token` response.

Example:

```json
{
  "error": {
    "code": 42801,
    "message": "confirmation required",
    "details": {
      "confirmation_token": "ctk_xxxxxxxx",
      "expires_at": "2026-07-09T12:00:00Z",
      "operation_summary": {
        "from": "user@qq.com",
        "to": ["recipient@example.com"],
        "subject": "Email subject",
        "attachment_count": 1
      }
    },
    "_hints": {
      "suggested_action": "confirm_with_token"
    }
  }
}
```

When this happens:

- Your next action MUST be to call `AskUserQuestion`.
- Do NOT ask for confirmation in plain chat text.
- Do NOT say the email was sent until the second tool call succeeds.
- Do NOT retry automatically without explicit user confirmation.
- If the user selects the confirmation option in the `AskUserQuestion` card, retry the same QQ Mail tool with the same arguments plus:

```json
{
  "confirmation_token": "ctk_xxxxxxxx"
}
```

If the user cancels or does not confirm, do not retry and tell the user the email operation was not executed.

### Phase 2 — Execute after confirmation

If the user selects the confirmation option in the `AskUserQuestion` card, **immediately** call the same tool again with the identical arguments, adding `confirmation_token`:

```
confirmation_token: "ctk_xxxxxxxx"
```

### Rules

- `confirmation_token` expires in ~5 minutes — get user confirmation promptly
- NEVER auto-retry without explicit user approval
- NEVER persist or reuse a token across operations
- If the token expires before the user responds, restart from Phase 1
- If the user cancels or switches topics, abort entirely and discard the token
- Confirmation MUST be collected through an `AskUserQuestion` card; plain chat replies such as "确认" / "yes" are not sufficient unless they are selected in the card.
- The `AskUserQuestion` card SHOULD provide exactly two options: `确认发送` and `取消`.

### Example

```
User: "Send email to alice@example.com"

Agent: [Calls SendMessage without confirmation_token]
← API returns 428 with confirmation_token + operation_summary

Agent: [Calls AskUserQuestion with one confirmation question]
Question:
"是否确认发送这封 QQ 邮箱邮件？

发件人：user@qq.com
收件人：alice@example.com
主题：Hello
附件数：0"

Options:
- 确认发送
- 取消

User: [selects "确认发送" in the AskUserQuestion card]

Agent: [Immediately calls SendMessage again with the same arguments plus confirmation_token="ctk_xxxxxxxx"]
```

---

## Attachment Limits

| Constraint | Value |
|-----------|-------|
| Max files per email | 3 |
| Max size per file | 1 MB |
| Max total per email | 3 MB |

Attachment `content` must be Base64-encoded. Required fields per attachment: `filename`, `content_type`, `content`, `size`, `sha1`.

---

## Email Display Format

When showing an email to the user:

```
发件人：sender@qq.com
收件人：recipient@example.com
主题：Email subject
时间：2026-04-01 10:30:00
邮件正文：
	Email body content here...
附件：
	report.pdf (2.3 MB)
	photo.png (500 KB)
```

- Use Chinese field labels
- Indent body and attachment list with a tab
- If no attachments: `附件：无`
- Multiple recipients: comma-separated
- Time format: YYYY-MM-DD HH:MM:SS

---

## Email Content Rules

- Do NOT add automated signatures or footers (e.g., "Sent via QQ Mail")
- Only include a signature if the user explicitly requests it

---

## Disconnecting / Switching Accounts

If the user wants to disconnect QQ Mail or re-authorize with a different account, revoke the stored OAuth token by deleting the entry from the OAuth credentials file.

### Where the credentials are stored

The QQ Mail OAuth token is stored in a JSON file. The location depends on the environment:

| Environment | Platform | Path |
|-------------|----------|------|
| WorkBuddy / CodeBuddy IDE extension | macOS | `~/Library/Application Support/WorkBuddyExtension/Data/default/VSCode_mcp_ide_oauth.json` |
| WorkBuddy / CodeBuddy IDE extension | Windows | `%LOCALAPPDATA%\WorkBuddyExtension\Data\default\VSCode_mcp_ide_oauth.json` |
| WorkBuddy / CodeBuddy IDE extension | Linux | `~/.local/share/WorkBuddyExtension/Data/default/VSCode_mcp_ide_oauth.json` |
| CodeBuddy Code (CLI) | all platforms | `~/.codebuddy/.credentials.json` |

> If you cannot determine the environment, assume IDE extension (macOS path above) as the default.
>
> Note: The `Data/default/` path is the common case. There may also be UUID-named subdirectories (e.g., `Data/dc5dbbc6-.../`) containing the same file if multiple profiles exist — check both.

### How to revoke

1. Read the credentials file to find the QQ Mail entry (look for a key containing `qq` or `mail.qq.com`).
2. Remove only the QQ Mail entry from the `tokens` object — leave other connectors intact.
3. Save the file.
4. Restart WorkBuddy / CodeBuddy for the change to take effect. The QQ Mail Connector will show as unauthorized and can be re-authorized by scanning the QR code again.
