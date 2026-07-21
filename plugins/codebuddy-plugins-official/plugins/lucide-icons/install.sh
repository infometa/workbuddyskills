#!/bin/bash

# Lucide Icons Skill 安装脚本
# 支持 Claude Code 和 CodeBuddy Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "================================"
echo "   Lucide Icons Skill 安装脚本"
echo "================================"
echo ""

# 选择 AI 工具
echo "请选择你使用的 AI 工具:"
echo "  1) Claude Code"
echo "  2) CodeBuddy Code"
echo ""
read -p "请输入选项 [1/2]: " ai_choice

case $ai_choice in
    1)
        AI_NAME="Claude Code"
        SKILLS_DIR="$HOME/.claude/skills/lucide-icons"
        ;;
    2)
        AI_NAME="CodeBuddy Code"
        SKILLS_DIR="$HOME/.codebuddy/skills/lucide-icons"
        ;;
    *)
        echo -e "${RED}无效选项，退出安装${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}已选择: ${AI_NAME}${NC}"
echo ""

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未检测到 Node.js，请先安装 Node.js${NC}"
    echo "  推荐使用 nvm 安装: https://github.com/nvm-sh/nvm"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "检测到 Node.js 版本: ${GREEN}${NODE_VERSION}${NC}"
echo ""

# 检查是否已安装
if [ -d "$SKILLS_DIR" ]; then
    echo -e "${YELLOW}检测到已有安装: ${SKILLS_DIR}${NC}"
    echo ""
    echo "请选择:"
    echo "  1) 覆盖安装"
    echo "  2) 退出"
    echo ""
    read -p "请输入选项 [1/2]: " reinstall_choice
    
    case $reinstall_choice in
        1)
            echo ""
            echo "正在删除旧安装..."
            rm -rf "$SKILLS_DIR"
            ;;
        2)
            echo ""
            echo -e "${YELLOW}已取消安装${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，退出安装${NC}"
            exit 1
            ;;
    esac
fi

# 创建目录
echo "正在创建目录..."
mkdir -p "$SKILLS_DIR/scripts/templates"
mkdir -p "$SKILLS_DIR/cache"

# 复制文件
echo "正在复制文件..."
cp "$SCRIPT_DIR/SKILL.md" "$SKILLS_DIR/"
cp "$SCRIPT_DIR/README.md" "$SKILLS_DIR/"
cp "$SCRIPT_DIR/scripts/lucide.js" "$SKILLS_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/package.json" "$SKILLS_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/package-lock.json" "$SKILLS_DIR/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/scripts/templates/react.template.js" "$SKILLS_DIR/scripts/templates/"

# 复制缓存文件（如果存在）
if [ -f "$SCRIPT_DIR/cache/icons-metadata.json" ]; then
    cp "$SCRIPT_DIR/cache/icons-metadata.json" "$SKILLS_DIR/cache/"
fi

# 安装依赖
echo "正在安装依赖..."
cd "$SKILLS_DIR/scripts"
npm install --silent

# 询问是否安装 lucide-static（离线支持）
echo ""
echo "是否安装 lucide-static 以支持离线使用？"
echo "  这将下载所有图标到本地（约 5MB）"
echo ""
read -p "安装离线支持？[y/N]: " offline_choice

case $offline_choice in
    [Yy]*)
        echo ""
        echo "正在安装 lucide-static..."
        npm install lucide-static --silent
        echo -e "${GREEN}离线支持已安装${NC}"
        ;;
    *)
        echo ""
        echo -e "${YELLOW}跳过离线支持安装${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}   安装完成!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "已安装到:"
echo "  - Skills: $SKILLS_DIR"
echo ""
echo "使用方法:"
echo "  # 搜索图标"
echo "  node $SKILLS_DIR/scripts/lucide.js search heart"
echo ""
echo "  # 下载图标"
echo "  node $SKILLS_DIR/scripts/lucide.js download heart --output ./icons/"
echo ""
echo "  # 下载为 React 组件"
echo "  node $SKILLS_DIR/scripts/lucide.js download heart --format svg,react"
echo ""
echo "在 ${AI_NAME} 中使用:"
echo "  直接询问 \"搜索 heart 相关的图标\" 或 \"下载 star 图标\""
echo ""
