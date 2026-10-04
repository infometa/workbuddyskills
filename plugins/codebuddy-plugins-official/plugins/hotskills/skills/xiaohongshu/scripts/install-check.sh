#!/bin/bash
# 检查小红书 MCP 依赖是否已安装

set -e

echo "检查小红书 MCP 依赖..."
echo ""

XHS_MCP="$HOME/.local/bin/xiaohongshu-mcp"
XHS_LOGIN="$HOME/.local/bin/xiaohongshu-login"

check_binary() {
    local name="$1"
    local path="$2"
    if [ -f "$path" ]; then
        echo "✅ $name: $path"
        return 0
    else
        echo "❌ $name: 未找到"
        return 1
    fi
}

MISSING=0

check_binary "xiaohongshu-mcp" "$XHS_MCP" || MISSING=1
check_binary "xiaohongshu-login" "$XHS_LOGIN" || MISSING=1

echo ""

# 检查 jq（必需，用于安全构建 JSON）
if command -v jq &> /dev/null; then
    echo "✅ jq: $(which jq)"
else
    echo "❌ jq: 未安装（必需，用于安全构建 JSON）"
    echo "   安装: apt-get install jq / brew install jq"
    MISSING=1
fi

# 检查 Python3（track-topic.py 需要）
if command -v python3 &> /dev/null; then
    echo "✅ python3: $(python3 --version)"
else
    echo "⚠️  python3: 未安装（热点跟踪功能需要）"
fi

echo ""

if [ $MISSING -eq 1 ]; then
    echo "=========================================="
    echo "缺少必要依赖，请按以下步骤安装："
    echo ""
    echo "1. 从 GitHub Releases 下载对应平台的二进制文件："
    echo "   https://github.com/xpzouying/xiaohongshu-mcp/releases"
    echo ""
    echo "2. 解压并安装到 ~/.local/bin/："
    echo "   mkdir -p ~/.local/bin"
    echo "   mv xiaohongshu-mcp-linux-amd64 ~/.local/bin/xiaohongshu-mcp"
    echo "   mv xiaohongshu-login-linux-amd64 ~/.local/bin/xiaohongshu-login"
    echo "   chmod +x ~/.local/bin/xiaohongshu-*"
    echo ""
    echo "3. 确保 ~/.local/bin 在 PATH 中（可选）"
    echo "=========================================="
    exit 1
else
    echo "✅ 所有依赖已就绪"
fi
