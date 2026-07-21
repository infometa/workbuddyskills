---
name: smart-formatting
description: Smart code formatting based on file type
category: development
event: PostToolUse
matcher: Edit|MultiEdit
language: bash
version: 1.0.0
---

# smart-formatting

Smart code formatting based on file type

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit|MultiEdit`
- **Category**: development

## Environment Variables

None required

## Requirements

- prettier for JS/TS
- black for Python
- gofmt for Go

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
case "$file_path" in
  *.js|*.jsx|*.ts|*.tsx|*.json|*.css|*.md)
    npx prettier --write "$file_path" 2>/dev/null || true
    ;;
  *.py)
    python3 -m black "$file_path" 2>/dev/null || true
    ;;
  *.go)
    gofmt -w "$file_path" 2>/dev/null || true
    ;;
esac
```
