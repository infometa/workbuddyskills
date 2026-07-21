# Lark-IM - Instant Messaging

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Message**: Individual message in a chat (message_id: om_xxx). Types: text, post, image, file, audio, video, sticker, interactive (card), share_chat, share_user, merge_forward
- **Chat**: Group chat or P2P conversation (chat_id: oc_xxx)
- **Thread**: Reply thread under a message (thread_id)
- **Reaction**: Emoji reaction on a message

## Resource Hierarchy

```
Chat (oc_xxx)
├── Message (om_xxx)
│   ├── Thread (reply)
│   ├── Reaction (emoji)
│   └── Resource (image/file/video/audio)
└── Member (user/bot)
```

## Critical Notes

### Identity Matters
- `--as user`: Runs as authenticated user (user_access_token). Permissions depend on user's access.
- `--as bot`: Runs as app bot (tenant_access_token). Permissions depend on bot's scopes and membership.

Same API may succeed with one identity and fail with the other.

### Sender Name Resolution with Bot
When using `--as bot` to fetch messages, sender names may not resolve (shown as open_id instead of display name). This happens when bot cannot access sender's contact info.

**Solution**: Check app visibility settings in Lark Developer Console to ensure bot's visible range covers the senders. Alternatively use `--as user`.

### Card Messages (Interactive)
Card messages are not yet supported for compact conversion in event subscriptions. Raw event data will be returned.

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+chat-create` | Create group chat (bot-only; creates private/public, invites users/bots) |
| `+chat-messages-list` | List messages in chat or P2P (supports time range, sort, pagination) |
| `+chat-search` | Search visible group chats by keyword/member |
| `+chat-update` | Update group name or description |
| `+messages-mget` | Batch get up to 50 messages by IDs (fetches sender names, expands threads) |
| `+messages-reply` | Reply to message with bot identity (text/markdown/post/media, thread replies) |
| `+messages-resources-download` | Download images/files from message |
| `+messages-search` | Search messages across chats (keyword, sender, time, attachment filters) |
| `+messages-send` | Send message to chat or direct message (bot-only) |
| `+threads-messages-list` | List messages in thread |

## API Resources

Use `lark-cli schema im.<resource>.<method>` to view parameter structure.

### chats
- `create` — Create group (bot only)
- `get` — Get chat info
- `link` — Get share link
- `list` — List user/bot chats
- `update` — Update chat info

### chat.members
- `create` — Add user/bot to chat
- `get` — Get member list

### messages
- `delete` — Recall message
- `forward` — Forward message
- `merge_forward` — Merge forward messages
- `read_users` — Query message read status

### reactions
- `batch_query` — Batch get reactions
- `create` — Add emoji reaction
- `delete` — Delete emoji reaction
- `list` — List reactions

### images
- `create` — Upload image

### pins
- `create` — Pin message
- `delete` — Remove pin
- `list` — Get pinned messages

## Permission Table

| Method | Required Scope |
|--------|----------------|
| chats.create | im:chat:create |
| chats.get | im:chat:read |
| chats.link | im:chat:read |
| chats.list | im:chat:read |
| chats.update | im:chat:update |
| chat.members.create | im:chat.members:write_only |
| chat.members.get | im:chat.members:read |
| messages.delete | im:message:recall |
| messages.forward | im:message |
| messages.merge_forward | im:message |
| messages.read_users | im:message:readonly |
| reactions.batch_query | im:message.reactions:read |
| reactions.create | im:message.reactions:write_only |
| reactions.delete | im:message.reactions:write_only |
| reactions.list | im:message.reactions:read |
| images.create | im:resource |
| pins.create | im:message.pins:write_only |
| pins.delete | im:message.pins:write_only |
| pins.list | im:message.pins:read |

