#!/bin/bash
# 获取小红书帖子详情

NOTE_ID="$1"
XSEC_TOKEN="$2"

if [ -z "$NOTE_ID" ] || [ -z "$XSEC_TOKEN" ]; then
    echo "用法: $0 <note_id> <xsec_token>"
    echo ""
    echo "note_id 和 xsec_token 可从搜索或推荐结果中获取"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARGS=$(jq -n --arg fid "$NOTE_ID" --arg tok "$XSEC_TOKEN" \
  '{"feed_id":$fid,"xsec_token":$tok}')
"$SCRIPT_DIR/mcp-call.sh" get_feed_detail "$ARGS"
