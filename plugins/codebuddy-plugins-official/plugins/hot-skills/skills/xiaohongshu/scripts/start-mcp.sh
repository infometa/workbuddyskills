#!/bin/bash
# 启动小红书 MCP 服务

XHS_MCP="$HOME/.local/bin/xiaohongshu-mcp"
PID_FILE="$HOME/.xiaohongshu/mcp.pid"
LOG_FILE="$HOME/.xiaohongshu/mcp.log"
XVFB_PID_FILE="$HOME/.xiaohongshu/xvfb.pid"
XVFB_DISPLAY_FILE="$HOME/.xiaohongshu/xvfb.display"

# Cookies 路径（可通过环境变量覆盖）
# XHS_COOKIES_SRC: 源 cookies 文件（用于远程服务器场景）
# 默认检查 ~/cookies.json 和 ~/.xiaohongshu/cookies.json
COOKIES_DST="/tmp/cookies.json"

mkdir -p "$HOME/.xiaohongshu"

# 检测是否有显示器（桌面环境）
has_display() {
    [ -n "$DISPLAY" ] && xdpyinfo >/dev/null 2>&1
}

# 在无桌面环境下自动启动 Xvfb
ensure_display() {
    if has_display; then
        return 0
    fi

    # 已有 Xvfb 在运行
    if [ -f "$XVFB_PID_FILE" ]; then
        local pid
        pid=$(cat "$XVFB_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            export DISPLAY=$(cat "$XVFB_DISPLAY_FILE" 2>/dev/null || echo ":99")
            echo "复用已有 Xvfb (PID: $pid, DISPLAY=$DISPLAY)"
            return 0
        fi
    fi

    # 检查 Xvfb 是否安装
    if ! command -v Xvfb >/dev/null 2>&1; then
        echo "⚠ 未检测到桌面环境，且未安装 Xvfb。"
        echo "  请安装：sudo apt-get install -y xvfb"
        echo "  安装后重新运行本脚本即可自动配置。"
        exit 1
    fi

    echo "未检测到桌面环境，自动启动 Xvfb 虚拟显示..."

    # 自动选择可用的 display 号（99-109）
    local display_num=""
    local d
    for d in $(seq 99 109); do
        if [ ! -e "/tmp/.X${d}-lock" ]; then
            display_num=$d
            break
        fi
        # 锁文件存在但进程已死，尝试清理后使用
        local lock_pid
        lock_pid=$(cat "/tmp/.X${d}-lock" 2>/dev/null | tr -d ' ')
        if [ -n "$lock_pid" ] && ! kill -0 "$lock_pid" 2>/dev/null; then
            rm -f "/tmp/.X${d}-lock" "/tmp/.X11-unix/X${d}" 2>/dev/null
            if [ ! -e "/tmp/.X${d}-lock" ]; then
                display_num=$d
                break
            fi
        fi
    done

    if [ -z "$display_num" ]; then
        echo "✗ 无法找到可用的 display 号（:99-:109 均被占用）"
        exit 1
    fi

    # -ac: 关闭访问控制，允许 chromium 连接虚拟显示（仅用于 headless 自动化）
    Xvfb ":${display_num}" -screen 0 1024x768x24 -ac >/dev/null 2>&1 &
    echo $! > "$XVFB_PID_FILE"
    echo ":${display_num}" > "$XVFB_DISPLAY_FILE"
    export DISPLAY=":${display_num}"
    sleep 1

    if kill -0 "$(cat "$XVFB_PID_FILE")" 2>/dev/null; then
        echo "✓ Xvfb 已启动 (DISPLAY=:${display_num})"
    else
        echo "✗ Xvfb 启动失败"
        exit 1
    fi
}

# 同步 cookies（支持多个可能的来源）
sync_cookies() {
    local src=""

    # 优先使用环境变量指定的路径
    if [ -n "$XHS_COOKIES_SRC" ] && [ -f "$XHS_COOKIES_SRC" ]; then
        src="$XHS_COOKIES_SRC"
    elif [ -f "$HOME/cookies.json" ]; then
        src="$HOME/cookies.json"
    elif [ -f "$HOME/.xiaohongshu/cookies.json" ]; then
        src="$HOME/.xiaohongshu/cookies.json"
    fi

    if [ -n "$src" ]; then
        if [ ! -f "$COOKIES_DST" ] || [ "$src" -nt "$COOKIES_DST" ]; then
            install -m 600 "$src" "$COOKIES_DST"
            echo "已同步 cookies: $src -> $COOKIES_DST"
        fi
    else
        # 确保已有的 cookies 文件权限正确
        [ -f "$COOKIES_DST" ] && chmod 600 "$COOKIES_DST"
    fi
}

sync_cookies
ensure_display

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "MCP 服务已在运行 (PID: $PID)"
        echo "如需重启，请先运行 stop-mcp.sh"
        exit 0
    fi
fi

# 解析参数
HEADLESS="true"
PORT="${XHS_MCP_PORT:-18060}"
for arg in "$@"; do
    case $arg in
        --headless=false)
            HEADLESS="false"
            ;;
        --port=*)
            PORT="${arg#*=}"
            ;;
    esac
done

# 校验端口号
if [[ ! "$PORT" =~ ^[0-9]+$ ]]; then
    echo "错误: 无效端口号: $PORT"
    exit 1
fi

# 启动服务
echo "启动小红书 MCP 服务..."
if [ "$HEADLESS" = "false" ]; then
    nohup "$XHS_MCP" -port ":${PORT}" -headless=false > "$LOG_FILE" 2>&1 &
else
    nohup "$XHS_MCP" -port ":${PORT}" > "$LOG_FILE" 2>&1 &
fi

echo $! > "$PID_FILE"
sleep 2

# 验证启动
if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "✓ MCP 服务已启动 (PID: $(cat $PID_FILE))"
    echo "  端点: http://localhost:${PORT}/mcp"
    echo "  日志: $LOG_FILE"
else
    echo "✗ 启动失败，查看日志: $LOG_FILE"
    cat "$LOG_FILE"
    exit 1
fi
