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

- Build tool appropriate for your project (npm, make, etc.)

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
  npm run build 2>/dev/null || true
elif [[ "$file_path" =~ \.(c|cpp|h|hpp)$ ]]; then
  make 2>/dev/null || true
fi
```
