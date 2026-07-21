---
name: simple-notifications
description: Send simple desktop notifications when Claude Code operations complete
category: notifications
event: PostToolUse
matcher: "*"
language: bash
version: 1.0.0
---

# simple-notifications

Send simple desktop notifications when Claude Code operations complete

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `*`
- **Category**: notifications

## Environment Variables

- `CLAUDE_TOOL_NAME`

## Requirements

None

