#!/bin/bash
# 检查小红书登录状态

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/mcp-call.sh" check_login_status
