---
name: dependency-checker
description: Monitor and audit dependencies for security vulnerabilities and updates
category: automation
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# dependency-checker

Monitor and audit dependencies for security vulnerabilities and updates

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: automation

## Environment Variables

- `CLAUDE_TOOL_FILE_PATH`

## Requirements

- npm audit (for Node.js)
- safety (for Python)
- cargo-audit (for Rust)

