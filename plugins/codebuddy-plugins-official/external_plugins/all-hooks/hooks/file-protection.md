---
name: file-protection
description: Protect critical files from accidental modification
category: security
event: PreToolUse
matcher: Edit|MultiEdit|Write
language: bash
version: 1.0.0
---

# file-protection

Protect critical files from accidental modification

## Event Configuration

- **Event Type**: `PreToolUse`
- **Tool Matcher**: `Edit|MultiEdit|Write`
- **Category**: security

## Environment Variables

- `CLAUDE_TOOL_FILE_PATH`

## Requirements

None

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
protected_patterns=('.env' 'package-lock.json' '.git/' 'node_modules/')
for pattern in "${protected_patterns[@]}"; do
  if [[ "$file_path" == *"$pattern"* ]]; then
    echo "Blocked: Cannot modify protected file: $file_path" >&2
    exit 2
  fi
done
exit 0
```
