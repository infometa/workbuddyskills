---
name: simple-notifications
description: Send simple desktop notifications when Claude Code operations complete
category: notifications
event: PostToolUse
matcher: "*"
language: bash
version: 1.0.0
---

# simple-notifications

Send simple desktop notifications when Claude Code operations complete

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `*`
- **Category**: notifications

## Environment Variables

- `CLAUDE_TOOL_NAME`

## Requirements

- macOS: Uses built-in osascript
- Linux: Uses notify-send (install with: sudo apt install libnotify-bin)

### Script

```bash
tool_name=$(jq -r '.tool_name // "unknown"')
if [[ "$OSTYPE" == "darwin"* ]]; then
  osascript -e "display notification \"Tool '$tool_name' completed\" with title \"Claude Code\""
else
  notify-send "Claude Code" "Tool '$tool_name' completed" 2>/dev/null || true
fi
```
