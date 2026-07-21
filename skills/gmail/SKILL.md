---
name: gmail
description: 'Gmail API integration with managed OAuth. Read, send, and manage emails, threads, labels, and drafts. Use this skill when users want to interact with Gmail. For other third party apps, use
  the api-gateway skill (https://clawhub.ai/byungkyu/api-gateway).

  '
description_zh: 通过 Gmail API 收发邮件、管理标签和草稿
description_en: Read, send, and manage Gmail emails, threads, labels, and drafts via API
version: 1.0.8
metadata:
  author: maton
  version: '1.0'
  clawdbot:
    emoji: 🧠
    requires:
      env:
      - MATON_API_KEY
compatibility: Requires network access and valid Maton API key
---

# Gmail

Access the Gmail API with managed OAuth authentication. Read, send, and manage emails, threads, labels, and drafts.

## Quick Start

**CLI:**

```bash
maton google-mail message list -L 10
```

```bash
maton api '/google-mail/gmail/v1/users/me/messages?maxResults=10'
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/google-mail/gmail/v1/users/me/messages?maxResults=10')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

## Base URL

```
https://api.maton.ai/google-mail/{native-api-path}
```

Maton proxies requests to `gmail.googleapis.com` and automatically injects your OAuth token.

## Installation

**NPM:**
```bash
npm install -g @maton-ai/cli
```

**Homebrew:**
```bash
brew install maton-ai/cli/maton
```

## Authentication

**CLI:**

```bash
maton login                          # Opens browser for API key
maton login --interactive            # Skip browser, paste API key directly
maton whoami                         # Show current auth state
```

**Manual:**

1. Sign in or create an account at [maton.ai](https://maton.ai)
2. Go to [maton.ai/settings](https://maton.ai/settings)
3. Copy your API key
4. Set your API key as `MATON_API_KEY`:

```bash
export MATON_API_KEY="YOUR_API_KEY"
```

## Connection Management

Manage your Google OAuth connections at `https://api.maton.ai`.

### List Connections

**CLI:**

```bash
maton connection list google-mail --status ACTIVE
```

```bash
maton api -X GET /connections -f app=google-mail -f status=ACTIVE
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/connections?app=google-mail&status=ACTIVE')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

### Create Connection

**CLI:**

```bash
maton connection create google-mail
```

```bash
maton api /connections -f app=google-mail
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
data = json.dumps({'app': 'google-mail'}).encode()
req = urllib.request.Request('https://api.maton.ai/connections', data=data, method='POST')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
req.add_header('Content-Type', 'application/json')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

### Get Connection

**CLI:**

```bash
maton connection view {connection_id}
```

```bash
maton api /connections/{connection_id}
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/connections/{connection_id}')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

**Response:**
```json
{
  "connection": {
    "connection_id": "{connection_id}",
    "status": "ACTIVE",
    "creation_time": "2025-12-08T07:20:53.488460Z",
    "last_updated_time": "2026-01-31T20:03:32.593153Z",
    "url": "https://connect.maton.ai/?session_token=...",
    "app": "google-mail",
    "metadata": {}
  }
}
```

Open the returned `url` in a browser to complete OAuth authorization.

### Delete Connection

**CLI:**

```bash
maton connection delete {connection_id}
```

```bash
maton api -X DELETE /connections/{connection_id}
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/connections/{connection_id}', method='DELETE')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

### Specifying Connection

If you have multiple Gmail connections, specify which one to use:

**CLI:**

```bash
maton google-mail message list -L 10 --connection {connection_id}
```

```bash
maton api /google-mail/gmail/v1/users/me/messages --connection {connection_id}
```

**Python:**

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/google-mail/gmail/v1/users/me/messages')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
req.add_header('Maton-Connection', '{connection_id}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

If you have multiple connections, always specify the connection to ensure requests go to the intended account.

## Security & Permissions

- Access is scoped to messages, threads, labels, drafts, and email sending within the connected Gmail account.
- **All write operations require explicit user approval.** Before executing any create, update, or delete call, confirm the target resource and intended effect with the user.

## API Reference

### List Messages

```bash
GET /google-mail/gmail/v1/users/me/messages?maxResults=10
```

Example:

```bash
maton google-mail message list -L 10
```

With query filter:

```bash
GET /google-mail/gmail/v1/users/me/messages?q=is:unread&maxResults=10
```

Example:

```bash
maton google-mail message list --query 'is:unread' -L 10
```

### Get Message

```bash
GET /google-mail/gmail/v1/users/me/messages/{messageId}
```

Example:

```bash
maton google-mail message view {messageId} --headers
```

With metadata only:

```bash
GET /google-mail/gmail/v1/users/me/messages/{messageId}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date
```

Example:

```bash
maton google-mail message view {messageId} --fetch-format metadata --metadata-header From,Subject,Date
```

### Send Message

```bash
POST /google-mail/gmail/v1/users/me/messages/send
Content-Type: application/json

{
  "raw": "BASE64_ENCODED_EMAIL"
}
```

Example:

```bash
maton google-mail message send --to alice@example.com --subject 'Hello' --body 'Hi there!'
```

### Reply to Message

```bash
maton google-mail message reply {messageId} --body 'Thanks!'
```

### Forward Message

```bash
maton google-mail message forward {messageId} --to dave@example.com --body 'FYI'
```

### List Labels

```bash
GET /google-mail/gmail/v1/users/me/labels
```

Example:

```bash
maton google-mail label list
```

### List Threads

```bash
GET /google-mail/gmail/v1/users/me/threads?maxResults=10
```

Example:

```bash
maton google-mail thread list -L 10
```

### Get Thread

```bash
GET /google-mail/gmail/v1/users/me/threads/{threadId}
```

Example:

```bash
maton google-mail thread view {threadId}
```

### Modify Message Labels

```bash
POST /google-mail/gmail/v1/users/me/messages/{messageId}/modify
Content-Type: application/json

{
  "addLabelIds": ["STARRED"],
  "removeLabelIds": ["UNREAD"]
}
```

Example:

```bash
maton google-mail message modify {messageId} --add-label STARRED --remove-label UNREAD
```

### Trash Message

```bash
POST /google-mail/gmail/v1/users/me/messages/{messageId}/trash
```

Example:

```bash
maton google-mail message trash {messageId}
```

### Create Draft

```bash
POST /google-mail/gmail/v1/users/me/drafts
Content-Type: application/json

{
  "message": {
    "raw": "BASE64URL_ENCODED_EMAIL"
  }
}
```

Example:

```bash
maton google-mail draft create --to alice@example.com --subject 'Hello' --body 'Draft content here'
```

### Send Draft

```bash
POST /google-mail/gmail/v1/users/me/drafts/send
Content-Type: application/json

{
  "id": "{draftId}"
}
```

Example:

```bash
maton google-mail draft send {draftId}
```

### Get Profile

```bash
GET /google-mail/gmail/v1/users/me/profile
```

## Query Operators

Use in the `q` parameter:
- `is:unread` - Unread messages
- `is:starred` - Starred messages
- `from:email@example.com` - From specific sender
- `to:email@example.com` - To specific recipient
- `subject:keyword` - Subject contains keyword
- `after:2024/01/01` - After date
- `before:2024/12/31` - Before date
- `has:attachment` - Has attachments

## Code Examples

### CLI

```bash
# List unread messages with headers
maton google-mail message list --hydrate

# Filter with jq — e.g., only messages from a specific sender
maton google-mail message list -L 20 --query 'from:boss@example.com' --json --jq '.messages[].id'

# List all threads with pagination
maton google-mail thread list --paginate --query 'newer_than:7d'
```

### JavaScript

```javascript
const response = await fetch(
  'https://api.maton.ai/google-mail/gmail/v1/users/me/messages?maxResults=10',
  {
    headers: {
      'Authorization': `Bearer ${process.env.MATON_API_KEY}`
    }
  }
);
```

### Python

```python
import os
import requests

response = requests.get(
    'https://api.maton.ai/google-mail/gmail/v1/users/me/messages',
    headers={'Authorization': f'Bearer {os.environ["MATON_API_KEY"]}'},
    params={'maxResults': 10, 'q': 'is:unread'}
)
```

## Notes

- Use `me` as userId for the authenticated user
- Message body is base64url encoded in the `raw` field
- Common labels: `INBOX`, `SENT`, `DRAFT`, `STARRED`, `UNREAD`, `TRASH`
- IMPORTANT: When using curl commands, use `curl -g` when URLs contain brackets (`fields[]`, `sort[]`, `records[]`) to disable glob parsing
- IMPORTANT: When piping curl output to `jq` or other commands, environment variables like `$MATON_API_KEY` may not expand correctly in some shell environments. You may get "Invalid API key" errors when piping.

## Error Handling

| Status | Meaning |
|--------|---------|
| 400 | Missing Gmail connection |
| 401 | Invalid or missing Maton API key |
| 429 | Rate limited (10 req/sec per account) |
| 4xx/5xx | Passthrough error from Gmail API |

### Troubleshooting: API Key Issues

**CLI:**

1. Check your auth state:

```bash
maton whoami
```

2. Verify the API key is valid by listing connections:

```bash
maton connection list
```

**Manual:**

1. Check that the `MATON_API_KEY` environment variable is set:

```bash
echo $MATON_API_KEY
```

2. Verify the API key is valid by listing connections:

```bash
python <<'EOF'
import urllib.request, os, json
req = urllib.request.Request('https://api.maton.ai/connections')
req.add_header('Authorization', f'Bearer {os.environ["MATON_API_KEY"]}')
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))
EOF
```

### Troubleshooting: Invalid App Name

1. Ensure your URL path starts with `google-mail`. For example:

- Correct: `https://api.maton.ai/google-mail/gmail/v1/users/me/messages`
- Incorrect: `https://api.maton.ai/gmail/v1/users/me/messages`

## Resources

- [Gmail API Overview](https://developers.google.com/gmail/api/reference/rest)
- [List Messages](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list)
- [Get Message](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get)
- [Send Message](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send)
- [List Threads](https://developers.google.com/gmail/api/reference/rest/v1/users.threads/list)
- [List Labels](https://developers.google.com/gmail/api/reference/rest/v1/users.labels/list)
- [Create Draft](https://developers.google.com/gmail/api/reference/rest/v1/users.drafts/create)
- [Maton CLI Manual](https://cli.maton.ai/manual)
- [Maton Community](https://discord.com/invite/dBfFAcefs2)
- [Maton Support](mailto:support@maton.ai)
