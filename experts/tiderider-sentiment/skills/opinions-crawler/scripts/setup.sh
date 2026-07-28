#!/usr/bin/env bash
# setup.sh — OpenCLI 舆情爬虫环境自动安装脚本
# 用法: bash setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- 1. 检查 Node.js ---
info "检查 Node.js 环境..."
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -ge 20 ]; then
        info "Node.js $(node -v) ✓"
    else
        error "Node.js 版本过低 (当前 $(node -v)，需要 >= 20.0.0)，请升级后重试"
        exit 1
    fi
else
    error "未找到 Node.js，请先安装 Node.js >= 20.0.0"
    exit 1
fi

# --- 2. 安装 OpenCLI ---
info "检查 OpenCLI..."
if command -v opencli &>/dev/null; then
    info "OpenCLI 已安装 ($(opencli --version 2>/dev/null || echo '版本未知')) ✓"
else
    info "正在安装 OpenCLI..."
    npm install -g @jackwener/opencli
    if command -v opencli &>/dev/null; then
        info "OpenCLI 安装成功 ✓"
    else
        error "OpenCLI 安装失败，请手动执行: npm install -g @jackwener/opencli"
        exit 1
    fi
fi

# --- 3. 检查 Chrome 扩展 ---
info "检查 OpenCLI Chrome 扩展..."
opencli doctor 2>/dev/null || {
    warn "opencli doctor 检测未通过，请按以下步骤配置 Chrome 扩展："
    echo ""
    echo "  1. 从 https://github.com/jackwener/opencli/releases 下载最新 opencli-extension.zip"
    echo "  2. 解压后打开 chrome://extensions"
    echo "  3. 开启「开发者模式」"
    echo "  4. 点击「加载已解压的扩展程序」，选择解压后的文件夹"
    echo "  5. 在 Chrome 中登录目标社媒网站（B站、微博等）"
    echo ""
    warn "Chrome 扩展配置完成后，重新运行 opencli doctor 验证"
}

# --- 4. 安装 appstore-review-cli (商店评论抓取) ---
info "检查 appstore-review-cli..."
if command -v appstore-reviews &>/dev/null; then
    info "appstore-review-cli 已安装 ✓"
else
    info "正在安装 appstore-review-cli..."
    pip install appstore-review-cli 2>/dev/null || pip3 install appstore-review-cli 2>/dev/null || {
        warn "appstore-review-cli 安装失败，商店评论抓取功能不可用"
        warn "请手动执行: pip install appstore-review-cli"
    }
fi

echo ""
info "========================================="
info "  环境配置完成！"
info "  - OpenCLI: $(command -v opencli 2>/dev/null && echo '已就绪' || echo '未就绪')"
info "  - appstore-review-cli: $(command -v appstore-reviews 2>/dev/null && echo '已就绪' || echo '未就绪')"
info "  - Chrome 扩展: 请运行 opencli doctor 确认"
info "========================================="
