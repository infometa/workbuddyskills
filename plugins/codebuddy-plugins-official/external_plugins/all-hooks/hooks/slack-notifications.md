---
name: slack-notifications
description: Send Slack notifications when Claude Code finishes working
category: automation
event: Stop
matcher: "*"
language: bash
version: 1.0.0
---

# slack-notifications

Send Slack notifications when Claude Code finishes working

## Event Configuration

- **Event Type**: `Stop`
- **Tool Matcher**: `*`
- **Category**: automation

## Environment Variables

- `SLACK_WEBHOOK_URL`

## Requirements

- curl
- Slack webhook URL configured

### Script

```bash
#!/bin/bash
if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
  exit 0
fi

message="Claude Code has finished working on your request."
payload=$(jq -n --arg text "$message" '{"text": $text}')

curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$payload" >/dev/null 2>&1
```
