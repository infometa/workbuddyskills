---
name: security-scanner
description: Scan code for security vulnerabilities and secrets after modifications
category: security
event: PostToolUse
matcher: Edit|Write
language: bash
version: 1.0.0
---

# security-scanner

Scan code for security vulnerabilities and secrets after modifications

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit|Write`
- **Category**: security

## Environment Variables

None required

## Requirements

None

