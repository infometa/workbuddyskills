---
name: discord-detailed-notifications
description: Send detailed Discord notifications with session information and rich embeds
category: notifications
event: Stop
matcher: "*"
language: bash
version: 1.0.0
---

# discord-detailed-notifications

Send detailed Discord notifications with session information and rich embeds

## Event Configuration

- **Event Type**: `Stop`
- **Tool Matcher**: `*`
- **Category**: notifications

## Environment Variables

- `DISCORD_WEBHOOK_URL`

## Requirements

- DISCORD_WEBHOOK_URL environment variable

### Script

```bash
#!/bin/bash
if [[ -z "$DISCORD_WEBHOOK_URL" ]]; then
  exit 0
fi

session_id="${CLAUDE_SESSION_ID:-unknown}"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

payload=$(jq -n \
  --arg title "Claude Code Session Complete" \
  --arg desc "Session finished at $timestamp" \
  --arg session "Session: $session_id" \
  '{
    "embeds": [{
      "title": $title,
      "description": $desc,
      "color": 5814783,
      "fields": [{"name": "Session ID", "value": $session, "inline": true}],
      "timestamp": (now | todate)
    }]
  }')

curl -s -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$payload" >/dev/null 2>&1
```
