---
name: telegram-detailed-notifications
description: Send detailed Telegram notifications with session information and metrics
category: notifications
event: Stop
matcher: "*"
language: bash
version: 1.0.0
---

# telegram-detailed-notifications

Send detailed Telegram notifications with session information and metrics

## Event Configuration

- **Event Type**: `Stop`
- **Tool Matcher**: `*`
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

session_id="${CLAUDE_SESSION_ID:-unknown}"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
message="*Claude Code Session Complete*

Session: \`${session_id}\`
Completed: ${timestamp}"

url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"

curl -s -X POST "$url" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=${message}" \
  -d "parse_mode=Markdown" >/dev/null 2>&1
```
