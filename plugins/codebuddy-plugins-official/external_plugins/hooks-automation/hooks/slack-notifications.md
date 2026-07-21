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

