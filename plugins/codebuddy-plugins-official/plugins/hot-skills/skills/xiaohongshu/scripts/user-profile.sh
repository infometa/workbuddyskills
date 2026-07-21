#!/bin/bash
# 获取小红书用户主页

USER_ID="$1"
XSEC_TOKEN="$2"

if [ -z "$USER_ID" ] || [ -z "$XSEC_TOKEN" ]; then
    echo "用法: $0 <user_id> <xsec_token>"
    echo ""
    echo "user_id 和 xsec_token 可从搜索或推荐结果中获取"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARGS=$(jq -n --arg uid "$USER_ID" --arg tok "$XSEC_TOKEN" \
  '{"user_id":$uid,"xsec_token":$tok}')
"$SCRIPT_DIR/mcp-call.sh" user_profile "$ARGS"
