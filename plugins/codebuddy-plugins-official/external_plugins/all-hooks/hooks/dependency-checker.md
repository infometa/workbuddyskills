---
name: dependency-checker
description: Monitor and audit dependencies for security vulnerabilities and updates
category: automation
event: PostToolUse
matcher: Edit
language: bash
version: 1.0.0
---

# dependency-checker

Monitor and audit dependencies for security vulnerabilities and updates

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `Edit`
- **Category**: automation

## Environment Variables

- `CLAUDE_TOOL_FILE_PATH`

## Requirements

- npm audit (for Node.js)
- safety (for Python)
- cargo-audit (for Rust)

### Script

```bash
file_path=$(jq -r '.tool_input.file_path // empty')
if [[ "$file_path" == *"package.json" ]]; then
  npm audit --audit-level=high 2>/dev/null || true
elif [[ "$file_path" == *"requirements.txt" ]] || [[ "$file_path" == *"Pipfile" ]]; then
  pip-audit 2>/dev/null || safety check 2>/dev/null || true
elif [[ "$file_path" == *"Cargo.toml" ]]; then
  cargo audit 2>/dev/null || true
fi
```
