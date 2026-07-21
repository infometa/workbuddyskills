---
name: lint-on-save
description: Automatically run linting tools after file modifications
category: development
event: PostToolUse
matcher: Edit|MultiEdit|Write
language: bash
version: 1.0.0
---

# lint-on-save

Automatically run linting tools after file modifications

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit|MultiEdit|Write`
- **Category**: development

## Environment Variables

- `CLAUDE_TOOL_FILE_PATH`

## Requirements

None

