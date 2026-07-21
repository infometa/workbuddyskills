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

- ESLint for JavaScript/TypeScript files
- Or other linters based on file type

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" =~ \.(js|jsx|ts|tsx)$ ]]; then
  npx eslint --fix "$file_path" 2>/dev/null || true
elif [[ "$file_path" =~ \.py$ ]]; then
  python3 -m black "$file_path" 2>/dev/null || true
fi
```
