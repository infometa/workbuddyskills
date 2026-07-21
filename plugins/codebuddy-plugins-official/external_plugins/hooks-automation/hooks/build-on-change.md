---
name: build-on-change
description: Automatically trigger build processes when source files change
category: automation
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# build-on-change

Automatically trigger build processes when source files change

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: automation

## Environment Variables

- `CLAUDE_TOOL_FILE_PATH`
- `CLAUDE_PROJECT_DIR`

## Requirements

None

