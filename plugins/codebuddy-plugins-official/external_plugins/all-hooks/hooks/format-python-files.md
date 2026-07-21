---
name: format-python-files
description: Automatically format Python files after any Edit operation using black formatter
category: formatting
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# format-python-files

Automatically format Python files after any Edit operation using black formatter

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: formatting

## Environment Variables

None required

## Requirements

- black (pip install black)

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" =~ \.py$ ]]; then
  python3 -m black "$file_path" 2>/dev/null || true
fi
```
