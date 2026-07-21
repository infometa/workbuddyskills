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

None

