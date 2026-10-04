#!/bin/bash
# 搜索小红书内容

KEYWORD="$1"

if [ -z "$KEYWORD" ]; then
    echo "用法: $0 <关键词>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARGS=$(jq -n --arg kw "$KEYWORD" '{"keyword":$kw}')
"$SCRIPT_DIR/mcp-call.sh" search_feeds "$ARGS"
