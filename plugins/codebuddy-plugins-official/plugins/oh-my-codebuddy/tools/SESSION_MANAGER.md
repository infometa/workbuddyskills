# Session Manager Tools

Tools for navigating and searching your OpenCode session history. These enable agents to reference previous conversations and maintain continuity across sessions.

## Tools

### 1. session_list
List all OpenCode sessions with filtering.

**Usage**: `session_list(limit, since, until)`

**Parameters**:
- `limit`: Maximum number of sessions to return (default: 50)
- `since`: Start date filter (ISO format)
- `until`: End date filter (ISO format)

**Returns**: List of sessions with metadata (ID, title, created date, message count)

**Use when**: Need to find a previous session or get overview of recent work

---

### 2. session_read
Read messages and history from a specific session.

**Usage**: `session_read(sessionID, limit, offset)`

**Parameters**:
- `sessionID`: ID of session to read
- `limit`: Maximum messages to return
- `offset`: Skip first N messages

**Returns**: Complete message history including user prompts and agent responses

**Use when**: Need to review what was discussed in a previous session

---

### 3. session_search
Full-text search across session messages.

**Usage**: `session_search(query, limit, sessionID)`

**Parameters**:
- `query`: Search term or phrase
- `limit`: Maximum results to return
- `sessionID`: Optional - limit search to specific session

**Returns**: Matching messages with context and session info

**Use when**: Looking for when/where something was discussed

---

### 4. session_info
Get metadata and statistics about a session.

**Usage**: `session_info(sessionID)`

**Parameters**:
- `sessionID`: ID of session

**Returns**: Session metadata (title, created/updated dates, message count, token usage)

**Use when**: Need quick stats about a session without reading all messages

---

## Usage Patterns

### Find Previous Work

```typescript
// Search for sessions about authentication
session_search(query: "authentication implementation")

// Get recent sessions
session_list(limit: 10, since: "2025-01-01")

// Read specific session
session_read(sessionID: "abc-123-def")
```

### Continuity Across Sessions

```typescript
// Find last time we discussed this feature
session_search(query: "user permissions feature")

// Read that session's messages
session_read(sessionID: "found-session-id")

// Get session stats
session_info(sessionID: "found-session-id")
```

### Debugging Reference

```typescript
// Find when we fixed similar bug
session_search(query: "TypeError in user service")

// Review the fix
session_read(sessionID: "bug-fix-session-id", limit: 20)
```

## Data Storage

Sessions are stored in:
- **Location**: `~/.codebuddy/sessions/` (OpenCode)
- **Format**: JSON files with message history
- **Persistence**: Survives across OpenCode restarts

## Benefits

1. **Context Continuity**: Reference previous discussions without copy-paste
2. **Knowledge Retention**: Don't lose solutions to problems you've solved before
3. **Pattern Learning**: See how you approached similar tasks
4. **Audit Trail**: Complete history of AI-assisted work

## Limitations

- Only searches sessions from current OpenCode installation
- Text-based search (not semantic)
- Performance degrades with very large session history (1000+ sessions)
- Cannot modify past sessions (read-only)

## For CodeBuddy Users

Session management features are OpenCode-specific. CodeBuddy alternatives:

1. **Manual notes**: Keep a markdown file with key decisions and solutions
2. **Git commits**: Use commit messages to document AI-assisted work
3. **External tools**: Use external note-taking apps for tracking
4. **Screenshots**: Capture important conversation snippets

## Privacy Note

Session data contains your entire conversation history with the AI. This includes:
- Code snippets
- File paths
- Project details
- Questions and answers

**Security**: Sessions are stored locally, not sent to external servers (unless you use cloud sync).

## See Also

- [LSP_TOOLS.md](LSP_TOOLS.md) - Language Server Protocol tools
- [AST_GREP.md](AST_GREP.md) - AST-aware code search


