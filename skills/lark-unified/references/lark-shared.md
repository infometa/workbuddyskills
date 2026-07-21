# Lark-Shared - Core Authentication & Permissions

**IMPORTANT**: Read this FIRST before using any Lark CLI commands.

## Recommended App Permissions

After creating the app via `lark_setup.py`, go to the app console and add these permissions before using the CLI. Without them, most commands will return empty results.

**App console URL**: https://open.feishu.cn/app (find your App ID with `lark-cli config show`)

### Core permissions (add all of these)

| Category | Permission | Purpose |
|----------|-----------|---------|
| Contacts | `contact:contact:readonly` | Search users by name |
| Contacts | `contact:user.base:readonly` | Read user profile |
| IM | `im:chat:readonly` | List and search chats |
| IM | `im:chat` | Create/manage chats |
| IM | `im:message` | Read messages |
| IM | `im:message:send_as_bot` | Send messages as bot |
| Documents | `docx:document` | Read/write docs |
| Spreadsheets | `sheets:spreadsheet` | Read/write sheets |
| Drive | `drive:drive:readonly` | Browse files |
| Drive | `drive:file` | Upload/download files |
| Base | `bitable:app` | Read/write base tables |
| Calendar | `calendar:calendar:readonly` | Read calendars |
| Calendar | `calendar:event` | Create/manage events |
| Tasks | `task:task` | Read/write tasks |
| Wiki | `wiki:wiki:readonly` | Read wiki pages |

After adding permissions: **publish a new version** in the app console, then re-run the setup script to get a fresh token with the new scopes:

```bash
SETUP=$(find ~/.workbuddy/skills -name lark_setup.py 2>/dev/null | head -1)
python3 "$SETUP"
```

## Quick Start: Configure Credentials

Check if config already exists:

```bash
lark-cli config show
```

If not configured, use the inline setup script from SKILL.md (no TTY required).

**NEVER use `lark-cli config init` or `lark-cli config init --new` directly** — these require an interactive TTY and will display a broken QR code or hang in WorkBuddy.

**Manual alternative** (if you already have an App ID and App Secret):
```bash
echo "<APP_SECRET>" | lark-cli config init --app-id <APP_ID> --app-secret-stdin
```

**Platforms**:
- Feishu (China): https://open.feishu.cn
- Lark (International): https://open.larksuite.com

Other config/auth commands:
```bash
lark-cli config show                    # View current app configuration
lark-cli auth status                    # View current user OAuth status
lark-cli auth login --domain all --recommend  # Re-authenticate user scopes
```

## Identity: User vs Bot

Every Lark CLI operation runs with one of two identities:

### User Identity (`--as user`)

- **Token**: `user_access_token`
- **Permissions**: Based on the authenticated user's own access
- **Scope**: Personal scopes (what the user can do)
- **Usage**: `lark-cli <domain> <resource> <method> --as user ...`
- **When to use**: 
  - User is performing personal actions (send message, check calendar)
  - Need to respect user's own access boundaries
  - Searching personal content (messages, documents, calendar)

### Bot Identity (`--as bot`)

- **Token**: `tenant_access_token`
- **Permissions**: Based on app's scopes + bot's membership/configuration
- **Scope**: App-level scopes (what the bot can do)
- **Usage**: `lark-cli <domain> <resource> <method> --as bot ...`
- **When to use**:
  - App/bot is performing actions (send message to others, create group)
  - Need to use app's elevated permissions
  - Bot has special roles (group owner, admin, etc.)

### Same API, Different Behavior

The **same API may succeed or fail** depending on identity:

```bash
# May work: User sending message to own chat
lark-cli im messages.get --message-id om_xxx --as user

# May fail: User lacks permission
lark-cli im messages.get --message-id om_xxx --as user  # If user not in chat

# May work: Bot has broader access
lark-cli im messages.get --message-id om_xxx --as bot  # If bot in chat
```

## Scopes: Permission Model

Operations require specific OAuth scopes. Each scope grants specific capabilities:

### Common Scopes

**Messaging**: `im:chat:read`, `im:chat:write`, `im:message`, `im:message:recall`

**Documents**: `docs:document:read`, `docs:document:edit`, `docs:document:create`

**Spreadsheets**: `sheets:spreadsheet:read`, `sheets:spreadsheet:edit`

**Base**: `bitable:base:read`, `bitable:base:edit`

**Calendar**: `calendar:calendar:read`, `calendar:event:create`

**Tasks**: `task:task:read`, `task:task:create`

**Mail**: `mail:message:read`, `mail:message:write`

**Wiki**: `wiki:space:read`, `wiki:space:create`

**Drive**: `drive:file:read`, `drive:file:write`

Check each domain's reference file for complete scope requirements.

## Configuration Files

Lark CLI stores configuration in `~/.lark-cli/config.json`. Use `lark-cli config show` and `lark-cli auth status` to inspect state instead of reading or printing secrets directly.

## Permission Errors

If an operation fails with a permission error, apply fail-fast handling before retrying:

1. If the error contains `need_user_authorization`, `No user logged in`, or `failed to get access token`, stop business API retries and run user OAuth (`lark-cli auth login --domain all --recommend`).
2. If the error contains `forBidden` or `forbidden` under `--as bot`, stop bot retries. Use `--as user` after OAuth, or ask the user to add the bot/app as a collaborator/member of the target resource.
3. If the error contains `authorization_pending`, keep the current polling command running; do not start a new flow unless the device code expires.
4. Only after auth state is valid should you retry the original business API once.

General checks:

1. **Check identity**: Is it using `--as user` or `--as bot`?
2. **Check scopes**: Does the app have the required OAuth scopes?
3. **Check membership**: Is the user/bot in the target group/chat or document?
4. **Check role**: Does the user/bot have required role (owner, admin, collaborator, etc.)?

### Example: Message Not Found

```
Error: message not found

Possible causes:
1. Message was deleted
2. User/bot not in the chat containing the message
3. Message is older than API retention period (usually 7 days for some operations)
4. Insufficient scopes
```

## Common Permission Issues

### Sender Name Not Resolving

When using bot identity and sender name shows as `open_id` instead of display name:

- **Root cause**: Bot cannot access sender's contact info
- **Solution**: Check app visibility in Developer Console. Ensure bot's visible range includes the senders.
- **Alternative**: Use `--as user` instead, which typically has broader contact access

### Chat Not Found

- **User identity**: User must be a member of the chat
- **Bot identity**: Bot must be a member AND within app's availability range

### Cannot Create Group

- **Bot only**: User identity cannot create groups
- **Use**: `--as bot` with `im:chat:create` scope

## Testing Permissions

```bash
# Check current credential status
lark-cli config show

# Test a simple operation (list chats)
lark-cli im chats list --as user

# If this fails, check:
# 1. Configuration is correct: lark-cli config show
# 2. Token is valid (might be expired)
# 3. Scopes include im:chat:read

# Re-authenticate if needed
lark-cli auth login --domain all --recommend
```

## Security Best Practices

1. **Keep tokens private**: Never commit credentials to version control
2. **Use environment variables** for automation:
   ```bash
   export LARK_TENANT_KEY="xxxxx"
   export LARK_APP_ID="xxxxx"
   export LARK_APP_SECRET="xxxxx"
   lark-cli config import-env
   ```

3. **Minimize scopes**: Only request scopes your app actually needs
4. **Rotate credentials**: Periodically rotate app secrets
5. **Validate untrusted input**: Email content, user input, etc. can be malicious

## More Help

```bash
lark-cli config --help
lark-cli --version
```

