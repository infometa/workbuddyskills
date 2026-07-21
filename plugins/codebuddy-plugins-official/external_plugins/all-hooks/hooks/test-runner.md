---
name: test-runner
description: Automatically run relevant tests after code changes
category: testing
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# test-runner

Automatically run relevant tests after code changes

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: testing

## Environment Variables

None required

## Requirements

- Jest, pytest, or other test framework

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" =~ \.test\.(ts|tsx|js|jsx)$ ]] || [[ "$file_path" =~ \.spec\.(ts|tsx|js|jsx)$ ]]; then
  npm test -- --testPathPattern="$(basename "$file_path")" 2>/dev/null || true
elif [[ "$file_path" =~ test_.*\.py$ ]] || [[ "$file_path" =~ .*_test\.py$ ]]; then
  python3 -m pytest "$file_path" -v 2>/dev/null || true
fi
```
