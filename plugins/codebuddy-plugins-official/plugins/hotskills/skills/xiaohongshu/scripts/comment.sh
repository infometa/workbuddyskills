#!/bin/bash
# 发表评论到小红书帖子

NOTE_ID="$1"
XSEC_TOKEN="$2"
CONTENT="$3"

if [ -z "$NOTE_ID" ] || [ -z "$XSEC_TOKEN" ] || [ -z "$CONTENT" ]; then
    echo "用法: $0 <note_id> <xsec_token> <评论内容>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARGS=$(jq -n --arg fid "$NOTE_ID" --arg tok "$XSEC_TOKEN" --arg ct "$CONTENT" \
  '{"feed_id":$fid,"xsec_token":$tok,"content":$ct}')
"$SCRIPT_DIR/mcp-call.sh" post_comment_to_feed "$ARGS"
