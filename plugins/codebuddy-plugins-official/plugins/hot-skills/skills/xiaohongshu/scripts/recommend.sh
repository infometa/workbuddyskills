#!/bin/bash
# 获取小红书首页推荐列表

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/mcp-call.sh" list_feeds
