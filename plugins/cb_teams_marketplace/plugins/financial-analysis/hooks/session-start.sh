#!/usr/bin/env bash
# SessionStart hook: 把 financial-analysis 的 rules 作为 additionalContext 注入到会话。
# 纯 bash 实现，不依赖 node/python。
set -euo pipefail

RULES_FILE="${CODEBUDDY_PLUGIN_ROOT}/rules/financial_analysis_rules.md"

# 规则文件缺失时静默退出，不影响会话启动。
if [[ ! -f "$RULES_FILE" ]]; then
  exit 0
fi

json_text=""
line_no=0
in_frontmatter=0

while IFS= read -r line || [[ -n "$line" ]]; do
  line_no=$((line_no + 1))

  if [[ $line_no -eq 1 && "$line" == "---" ]]; then
    in_frontmatter=1
    continue
  fi

  if [[ $in_frontmatter -eq 1 ]]; then
    if [[ "$line" == "---" ]]; then
      in_frontmatter=0
    fi
    continue
  fi

  line=${line//$'\r'/}
  line=${line//\\/\\\\}
  line=${line//\"/\\\"}
  line=${line//$'\t'/\\t}

  if [[ -n "$json_text" ]]; then
    json_text+="\\n"
  fi
  json_text+="$line"
done < "$RULES_FILE"

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"},"suppressOutput":true}' "$json_text"
