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

None

