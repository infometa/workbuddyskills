#!/bin/bash
# 停止小红书 MCP 服务

PID_FILE="$HOME/.xiaohongshu/mcp.pid"
XVFB_PID_FILE="$HOME/.xiaohongshu/xvfb.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "✓ MCP 服务已停止"
    else
        echo "进程不存在，清理 PID 文件"
        rm -f "$PID_FILE"
    fi
else
    echo "MCP 服务未运行"
fi

# 清理 Xvfb
if [ -f "$XVFB_PID_FILE" ]; then
    XVFB_PID=$(cat "$XVFB_PID_FILE")
    if kill -0 "$XVFB_PID" 2>/dev/null; then
        kill "$XVFB_PID"
        echo "✓ Xvfb 已停止"
    fi
    rm -f "$XVFB_PID_FILE" "$HOME/.xiaohongshu/xvfb.display"
fi
