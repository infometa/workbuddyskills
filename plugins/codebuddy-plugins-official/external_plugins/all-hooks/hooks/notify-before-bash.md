---
name: notify-before-bash
description: Show notification before any Bash command execution for security awareness
category: notifications
event: PreToolUse
matcher: Bash
language: bash
version: 1.0.0
---

# notify-before-bash

Show notification before any Bash command execution for security awareness

## Event Configuration

- **Event Type**: `PreToolUse`
- **Tool Matcher**: `Bash`
- **Category**: notifications

## Environment Variables

None required

## Requirements

- macOS: Uses built-in osascript
- Linux: Uses notify-send

### Script

```bash
command=$(jq -r '.tool_input.command // "unknown command"')
short_cmd=$(echo "$command" | head -c 50)
if [[ "$OSTYPE" == "darwin"* ]]; then
  osascript -e "display notification \"Running: $short_cmd\" with title \"Claude Code - Bash\""
else
  notify-send "Claude Code - Bash" "Running: $short_cmd" 2>/dev/null || true
fi
```
