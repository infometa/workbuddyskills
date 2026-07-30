#!/bin/bash

# Education Search Skill - 版本检查脚本
# 使用 OpenClaw 内置的 skills update 命令

SKILL_NAME="education-search"
SKILL_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"
SKILL_FILE="$SKILL_DIR/SKILL.md"
LAST_CHECK_FILE="$SKILL_DIR/.last_check_date"
UPDATE_URL="https://clawhub.ai/kayy123/$SKILL_NAME"

# 获取当前日期
get_today() {
    date +%Y-%m-%d
}

# 获取当前版本
get_local_version() {
    if [ -f "$SKILL_FILE" ]; then
        grep "^version:" "$SKILL_FILE" | head -1 | awk '{print $2}' | tr -d '\r'
    else
        echo "0.0.0"
    fi
}

# 获取远程版本
get_remote_version() {
    curl -sL --max-time 10 "$UPDATE_URL" 2>/dev/null | \
        grep -i 'version' | \
        grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | \
        head -1
}

# 主函数：检查版本并提示更新
check_version() {
    local today=$(get_today)
    local last_check_date=$(cat "$LAST_CHECK_FILE" 2>/dev/null || echo "")

    # 判断是否需要检查（每天最多一次）
    if [ "$last_check_date" = "$today" ]; then
        # 今天已经检查过了
        if [ -f "$SKILL_DIR/.update_available" ]; then
            source "$SKILL_DIR/.update_available" 2>/dev/null || true
            if [ -n "$NEW_VERSION" ]; then
                echo "UPDATE_AVAILABLE:$NEW_VERSION"
                echo "LOCAL_VERSION:$LOCAL_VERSION"
            fi
        fi
        return 0
    fi

    # 记录今天的检查日期
    echo "$today" > "$LAST_CHECK_FILE"

    echo "检查版本..." >&2

    # 获取版本信息
    LOCAL_VERSION=$(get_local_version)
    REMOTE_VERSION=$(get_remote_version)

    # 比较版本
    if [ -z "$REMOTE_VERSION" ]; then
        echo "VERSION_CHECK_FAILED"
        return 1
    fi

    if [ "$REMOTE_VERSION" = "$LOCAL_VERSION" ]; then
        rm -f "$SKILL_DIR/.update_available"
        echo "NO_UPDATE"
        return 0
    fi

    # 有新版本，保存标记
    echo "NEW_VERSION=$REMOTE_VERSION" > "$SKILL_DIR/.update_available"
    echo "LOCAL_VERSION=$LOCAL_VERSION" >> "$SKILL_DIR/.update_available"

    echo "UPDATE_AVAILABLE:$REMOTE_VERSION"
    echo "LOCAL_VERSION:$LOCAL_VERSION"
}

# 执行自动更新（使用 OpenClaw 内置命令）
auto_update() {
    echo "📥 正在更新 $SKILL_NAME..."

    # 使用 OpenClaw 内置的 update 命令
    if openclaw skills update "$SKILL_NAME" 2>&1 | grep -q "Downloaded\|Updated"; then
        # 清理标记文件
        rm -f "$SKILL_DIR/.update_available"

        # 记录更新成功
        NEW_VERSION=$(get_local_version)
        echo "UPDATED_TO_VERSION=$NEW_VERSION" > "$SKILL_DIR/.update_success"

        echo "✅ 已更新到最新版本 $NEW_VERSION"
        return 0
    else
        echo "❌ 更新失败，请手动执行："
        echo "   openclaw skills update education-search"
        return 1
    fi
}

# 生成更新提示
generate_update_prompt() {
    local status="$1"
    local new_version="$2"

    echo ""
    echo "---"

    if [ "$status" = "UPDATED" ]; then
        echo "✅ **已自动更新到最新版本 $new_version**"
        echo ""
        echo "更新内容已生效，您可以继续使用~"
    else
        echo "🔄 **检测到新版本 $new_version**"
        echo ""
        echo "请运行以下命令更新："
        echo "```"
        echo "openclaw skills update education-search"
        echo "```"
    fi
}

# 主入口
main() {
    case "$1" in
        "check")
            check_version
            ;;
        "update")
            auto_update
            ;;
        "prompt")
            generate_update_prompt "$2" "$3"
            ;;
        "status")
            LOCAL_VERSION=$(get_local_version)
            echo "当前版本：$LOCAL_VERSION"
            echo "更新地址：$UPDATE_URL"
            if [ -f "$LAST_CHECK_FILE" ]; then
                echo "上次检查：$(cat $LAST_CHECK_FILE)"
            fi
            ;;
        "force")
            rm -f "$LAST_CHECK_FILE"
            check_version
            ;;
        *)
            check_version
            ;;
    esac
}

main "$@"
