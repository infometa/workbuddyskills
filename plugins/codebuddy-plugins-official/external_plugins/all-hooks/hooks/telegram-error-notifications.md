---
name: telegram-error-notifications
description: Send Telegram notifications for long-running operations and important events
category: notifications
event: PostToolUse
matcher: Bash
language: bash
version: 1.0.0
---

# telegram-error-notifications

Send Telegram notifications for long-running operations and important events

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Bash`
- **Category**: notifications

## Environment Variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Requirements

- TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables

### Script

```bash
#!/bin/bash
if [[ -z "$TELEGRAM_BOT_TOKEN" ]] || [[ -z "$TELEGRAM_CHAT_ID" ]]; then
  exit 0
fi

# Check if the tool result indicates an error
tool_result=$(jq -r '.tool_result // empty')
if echo "$tool_result" | grep -qi "error\|failed\|exception"; then
  command=$(jq -r '.tool_input.command // "unknown"' | head -c 100)
  message="⚠️ Claude Code Error: ${command}"
  url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
  curl -s -X POST "$url" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${message}" >/dev/null 2>&1
fi
```
