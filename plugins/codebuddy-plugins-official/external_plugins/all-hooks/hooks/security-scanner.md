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

- gitleaks or similar secret scanner (optional)

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ -n "$file_path" ]] && [[ -f "$file_path" ]]; then
  # Check for common secret patterns
  if grep -qE '(api[_-]?key|secret|password|token)[[:space:]]*[=:][[:space:]]*["\047]?[a-zA-Z0-9+/=]{20,}' "$file_path" 2>/dev/null; then
    echo "Warning: Potential secrets detected in $file_path" >&2
  fi
fi
```
