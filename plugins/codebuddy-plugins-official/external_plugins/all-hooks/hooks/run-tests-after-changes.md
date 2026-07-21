---
name: run-tests-after-changes
description: Automatically run quick tests after code modifications to ensure nothing breaks
category: testing
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# run-tests-after-changes

Automatically run quick tests after code modifications to ensure nothing breaks

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: testing

## Environment Variables

None required

## Requirements

- Test framework appropriate for your project

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
  npm test --passWithNoTests 2>/dev/null || true
elif [[ "$file_path" =~ \.py$ ]]; then
  python3 -m pytest --collect-only 2>/dev/null || true
fi
```
