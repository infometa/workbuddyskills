---
name: telegram-notifications
description: Send Telegram notifications when Claude Code finishes working
category: notifications
event: Stop
matcher: "*"
language: bash
version: 1.0.0
---

# telegram-notifications

Send Telegram notifications when Claude Code finishes working

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

message="Claude Code has finished working on your request."
url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"

curl -s -X POST "$url" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=${message}" >/dev/null 2>&1
```
