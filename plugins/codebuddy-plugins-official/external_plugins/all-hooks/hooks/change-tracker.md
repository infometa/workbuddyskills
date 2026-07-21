---
name: change-tracker
description: Track file changes in a simple log
category: development
event: PostToolUse
matcher: Edit|MultiEdit
language: bash
version: 1.0.0
---

# change-tracker

Track file changes in a simple log

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit|MultiEdit`
- **Category**: development

## Environment Variables

None required

## Requirements

None

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
log_file=".claude/changes.log"
mkdir -p "$(dirname "$log_file")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Modified: $file_path" >> "$log_file"
```
