---
name: slack-error-notifications
description: Send Slack notifications when Claude Code encounters long-running operations or when tools take significant time
category: notifications
event: Notification
matcher: "*"
language: bash
version: 1.0.0
---

# slack-error-notifications

Send Slack notifications when Claude Code encounters long-running operations or when tools take significant time

## Event Configuration

- **Event Type**: `Notification`
- **Tool Matcher**: `*`
- **Category**: notifications

## Environment Variables

None required

## Requirements

- SLACK_WEBHOOK_URL environment variable

### Script

```bash
#!/bin/bash
if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
  exit 0
fi

# Forward the notification message to Slack
message=$(jq -r '.message // "Claude Code notification"')
payload=$(jq -n --arg text "$message" '{"text": $text}')

curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$payload" >/dev/null 2>&1
```
