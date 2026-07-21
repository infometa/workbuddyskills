---
name: file-backup
description: Automatically backup files before editing
category: development
event: PreToolUse
matcher: Edit|MultiEdit
language: bash
version: 1.0.0
---

# file-backup

Automatically backup files before editing

## Event Configuration

- **Event Type**: `PreToolUse`
- **Tool Matcher**: `Edit|MultiEdit`
- **Category**: development

## Environment Variables

None required

## Requirements

None

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ -n "$file_path" ]] && [[ -f "$file_path" ]]; then
  backup_dir=".claude/backups"
  mkdir -p "$backup_dir"
  timestamp=$(date '+%Y%m%d_%H%M%S')
  filename=$(basename "$file_path")
  cp "$file_path" "$backup_dir/${filename}.${timestamp}.bak"
fi
```
