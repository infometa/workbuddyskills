---
name: performance-monitor
description: Monitor system performance during Claude Code operations
category: performance
event: PostToolUse
matcher: "*"
language: bash
version: 1.0.0
---

# performance-monitor

Monitor system performance during Claude Code operations

## Event Configuration

- **Event Type**: `PostToolUse`
- **Tool Matcher**: `*`
- **Category**: performance

## Environment Variables

None required

## Requirements

None

### Script

```bash
tool_name=$(jq -r '.tool_name // "unknown"')
log_file=".claude/performance.log"
mkdir -p "$(dirname "$log_file")"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
if [[ "$OSTYPE" == "darwin"* ]]; then
  mem_usage=$(vm_stat | awk '/Pages active/ {print $3}' | sed 's/\.//')
else
  mem_usage=$(free -m | awk '/Mem:/ {print $3}')
fi
echo "[$timestamp] Tool: $tool_name, Memory: ${mem_usage}MB" >> "$log_file"
```
