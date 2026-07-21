# Additional Lark Domains

## Lark-Contact - Contacts & User Directory

**When to use**: Search for users, fetch user profiles, query organizational structure.

### Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+me` | Get current user profile |
| `+users-search` | Search users by name/email/phone |
| `+departments-list` | List organization departments |

### Typical Operations

```bash
# Get current user info
lark-cli contact +me

# Search users
lark-cli contact +users-search --query "John" --limit 20

# Get department structure
lark-cli contact departments list
```

### Key Resources

- `user.get` — Get user profile
- `user.list` — List users
- `user.search` — Search users
- `department.list` — List departments
- `department.get` — Get department info

---

## Lark-VC - Video Conferences & Meetings

**When to use**: Access meeting recordings, retrieve meeting notes, manage video conference settings.

### Common Scenarios

1. **Search past meetings**: Find meetings from last week
2. **Get meeting notes**: Retrieve automated summaries, action items, or transcripts
3. **Download recordings**: Access meeting video recordings

### Typical Operations

```bash
# Search meetings from past week
lark-cli vc +meetings-search --from-user ou_xxx --start-time 2024-02-08 --end-time 2024-02-15 --limit 100

# Get meeting minutes/notes
lark-cli vc minutes get --meeting-id vc_xxx

# Get meeting recording
lark-cli vc recordings get --meeting-id vc_xxx
```

### Key Resources

- `meetings.list` — List meetings
- `meetings.search` — Search meetings by organizer/attendee/time
- `meetings.get` — Get meeting details
- `minutes.get` — Get meeting notes/summary
- `recordings.list` — List recordings
- `recordings.get` — Get recording details

### Note on Freebusy vs Meetings

- Use **lark-calendar** for **future** events and scheduling
- Use **lark-vc** for **past** meetings, recordings, and notes

---

## Lark-Minutes - Meeting Minutes

**When to use**: Retrieve meeting minutes metadata and associated content.

### Typical Operations

```bash
lark-cli minutes minutes-list --meeting-id vc_xxx
lark-cli minutes minutes-get --minutes-id minutes_xxx
```

---

## Lark-Whiteboard - Drawing & Diagrams

**When to use**: Create or manage diagrams using DSL (Domain Specific Language).

### Rendering

Supports Mermaid syntax for flowcharts, sequence diagrams, state machines, etc.

### Typical Operations

```bash
# Create whiteboard with Mermaid diagram
lark-cli whiteboard create --title "Architecture Diagram" --content "graph LR; A[Start] --> B[Process] --> C[End]"
```

---

## Lark-Event - Real-Time Event Subscriptions

**When to use**: Subscribe to real-time events (messages, document changes, base updates) via WebSocket.

### Usage Pattern

```bash
# Subscribe to message events
lark-cli event subscribe --event-type message.receive --endpoint wss://your-endpoint
```

### Supported Events

- Messages: create, update, delete
- Documents: updated
- Base: record created/updated/deleted
- Calendar: event changes
- And many more...

---

## Lark-Shared - Core Authentication & Configuration

**Always read this first** before using any other Lark skill.

### Key Concepts

- **Identity**: User vs Bot
- **Token Types**: user_access_token vs tenant_access_token
- **Scopes**: Permissions required for each operation
- **Configuration**: How to set up credentials

### Critical Notes

- User operations (`--as user`): Use user's permissions
- Bot operations (`--as bot`): Use bot's app scopes and membership
- Some APIs support only one identity type
- Always check the reference for identity requirements

---

## Lark-OpenAPI-Explorer - API Discovery

**When to use**: Discover and test Lark APIs directly, explore API schemas.

### Usage

```bash
lark-cli openapi search --query "message"  # Search available APIs
lark-cli openapi get --api im.messages.send  # Get API details
```

---

## Lark-Skill-Maker - Create Custom Skills

**When to use**: Build custom skills by wrapping Lark APIs for specialized workflows.

### Typical Usage

Skill-maker allows you to:
- Define custom commands
- Wrap complex API sequences
- Add business logic
- Export as reusable skills

See official documentation for detailed skill authoring guidelines.

